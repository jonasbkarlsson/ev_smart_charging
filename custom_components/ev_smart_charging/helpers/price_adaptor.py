"""PriceAdaptor class"""

# pylint: disable=relative-beyond-top-level
from datetime import datetime, date, timedelta
import logging

from typing import Any, Optional
from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt

from custom_components.ev_smart_charging.const import (
    CONF_PRICE_SENSOR,
)
from custom_components.ev_smart_charging.helpers.raw import PriceFormat, Raw

_LOGGER = logging.getLogger(__name__)


class PriceAdaptor:
    """PriceAdaptor class"""

    # The price entity shall have the following format:
    #
    # There shall be an attribute "raw_today" or "prices_today".
    # If there is an attribute "raw_today", there shall also be an attribute "raw_tomorrow".
    # If there is an attribute "prices_today", there shall also be an attribute "prices_tomorrow".
    # All the above attributes shall be arrays of prices.
    #
    # A price shall be a dictionary with at least the following keys:
    # "start", "time" or "hour" - start time of the price period
    # "price" or "value" - price value
    #
    # The start time shall be a string in the format "YYYY-MM-DD HH:MM:SS±HH:MM"
    # or a datetime object with timezone information.
    # For example: "2023-03-06 00:00:00+01:00"
    # or datetime.datetime(2023, 3, 6, 0, 0, tzinfo=<DstTzInfo 'Europe/Stockholm' CET+1:00:00 STD>)
    #
    # The price value shall be a float.

    def __init__(self) -> None:
        self._price_attribute_today = None
        self._price_attribute_tomorrow = None
        self._price_format = PriceFormat()

    def initiate(self, price_state: State) -> bool:
        """Set the price format"""

        if not price_state:
            # This should only happen when testing
            return True

        # First try for the attributes used by integration using
        # separate attributes for today and tomorrow.
        if "prices_today" in price_state.attributes:
            self._price_attribute_today = "prices_today"
            self._price_attribute_tomorrow = "prices_tomorrow"
        elif "raw_today" in price_state.attributes:
            self._price_attribute_today = "raw_today"
            self._price_attribute_tomorrow = "raw_tomorrow"
        # Check for GE-Spot dictionary format attributes
        elif "interval_prices" in price_state.attributes:
            self._price_attribute_today = "interval_prices"
            self._price_attribute_tomorrow = "tomorrow_interval_prices"
        # Check for GE-Spot with timestamps
        elif "today_with_timestamps" in price_state.attributes:
            self._price_attribute_today = "today_with_timestamps"
            self._price_attribute_tomorrow = "tomorrow_with_timestamps"

        # Then try for the attributes used by integration using
        # the same attribute for today and tomorrow.
        else:
            self._price_attribute_today = next(
                (
                    attr
                    for attr in ["prices", "data", "forecast"]
                    if attr in price_state.attributes
                ),
                None,
            )
            self._price_attribute_tomorrow = self._price_attribute_today

        if not self._price_attribute_today:
            return False

        # Check if the data is in dictionary format (GE-Spot style)
        price_data = price_state.attributes[self._price_attribute_today]
        if isinstance(price_data, dict):
            # GE-Spot uses dictionary with time keys
            self._price_format.start = "time"  # Will be the dict key
            self._price_format.value = "price"  # Will be the dict value
            self._price_format.start_is_string = True
            return True

        # Set _price_key.start and _price_key.value for array format
        try:
            keys = price_data[0]
            start_keys = ["time", "start", "hour", "start_time", "datetime"]
            value_keys = ["price", "value", "price_ct_per_kwh", "electricity_price"]

            self._price_format.start = next(
                (key for key in start_keys if key in keys), None
            )
            self._price_format.value = next(
                (key for key in value_keys if key in keys), None
            )

            if not self._price_format.start or not self._price_format.value:
                return False
        except (KeyError, IndexError, TypeError):
            return False

        # Determine if the start key is a string in ISO format or a datetime object
        start_value = price_state.attributes[self._price_attribute_today][0][
            self._price_format.start
        ]
        if isinstance(start_value, str):
            try:
                datetime.fromisoformat(start_value)
                self._price_format.start_is_string = True
            except ValueError:
                return False
        elif isinstance(start_value, datetime):
            self._price_format.start_is_string = False
        else:
            return False

        return True

    def _convert_dict_to_list(self, price_dict: dict, reference_date: Optional[date] = None) -> list:
        """Convert GE-Spot dictionary format to list format.
        
        Args:
            price_dict: Dictionary with time strings as keys and prices as values
            reference_date: Optional reference date to use for creating full datetime objects
        
        Returns:
            List of dictionaries with 'start', 'end', and 'value' keys
        """
        if not isinstance(price_dict, dict):
            return price_dict  # Already in list format
        
        result = []
        if reference_date is None:
            reference_date = dt.now().date()
        
        for time_str, price in sorted(price_dict.items()):
            try:
                # Parse time string (e.g., "14:30")
                time_parts = time_str.split(":")
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                
                # Create datetime using dt.start_of_local_day() for proper timezone handling
                day_start = dt.start_of_local_day(dt.now().replace(
                    year=reference_date.year,
                    month=reference_date.month,
                    day=reference_date.day
                ))
                start_time = day_start + timedelta(hours=hour, minutes=minute)
                end_time = start_time + timedelta(minutes=15)  # GE-Spot uses 15-min intervals
                
                result.append({
                    "start": start_time,
                    "end": end_time,
                    "value": float(price)
                })
            except (ValueError, IndexError, KeyError) as e:
                _LOGGER.warning("Failed to parse time '%s': %s", time_str, e)
                continue
        
        return result

    def is_price_state(self, price_state: State) -> bool:
        """Check that argument is a Price sensor state"""
        if price_state is not None:
            if price_state.state != "unavailable":

                # Make sure the adaptor is initiated. Is needed when testing.
                if not self._price_attribute_today:
                    self.initiate(price_state)

                # Check raw_today
                try:
                    if not self.get_raw_today_local(price_state).is_valid(
                        check_today_local=True
                    ):
                        return False
                except KeyError:
                    return False
                except TypeError:
                    return False
                except AttributeError:
                    return False
                # Don't check raw_tomorrow. It can be missing.
                return True
        return False

    def get_raw_today_local(self, state) -> Raw:
        """Get the today's prices in local timezone"""
        price_data = state.attributes[self._price_attribute_today]
        
        # Convert dictionary format to list format if needed (GE-Spot)
        if isinstance(price_data, dict):
            price_data = self._convert_dict_to_list(price_data, dt.now().date())
            # Data is now in the correct format, no need for PriceFormat
            return Raw(price_data).today()
        
        return Raw(price_data, self._price_format).today()

    def get_raw_tomorrow_local(self, state) -> Raw:
        """Get the tomorrow's prices in local timezone"""
        price_data = state.attributes[self._price_attribute_tomorrow]
        
        # Convert dictionary format to list format if needed (GE-Spot)
        if isinstance(price_data, dict):
            tomorrow = dt.now().date() + timedelta(days=1)
            price_data = self._convert_dict_to_list(price_data, tomorrow)
            # Data is now in the correct format, no need for PriceFormat
            return Raw(price_data).tomorrow()
        
        return Raw(price_data, self._price_format).tomorrow()

    def get_current_price(self, state) -> float:
        """Return current price."""
        time_now = dt.now()
        return self.get_raw_today_local(state).get_value(time_now)

    @staticmethod
    def validate_price_entity(
        hass: HomeAssistant, user_input: dict[str, Any]
    ) -> tuple[str, str] | None:
        """Validate Price entity"""

        # Validate Price entity
        price_state = hass.states.get(user_input[CONF_PRICE_SENSOR])
        if price_state is None:
            return ("base", "price_not_found")

        adaptor = PriceAdaptor()
        if not adaptor.initiate(price_state):
            return ("base", "sensor_is_not_price")

        if not adaptor.is_price_state(price_state):
            return ("base", "sensor_is_not_price")

        return None
