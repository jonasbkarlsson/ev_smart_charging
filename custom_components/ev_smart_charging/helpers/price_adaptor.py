"""PriceAdaptor class"""

# pylint: disable=relative-beyond-top-level
from datetime import datetime
import logging

from typing import Any
from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt

from custom_components.ev_smart_charging.const import (
    CONF_PRICE_SENSOR,
)
from custom_components.ev_smart_charging.helpers.coordinator import PriceFormat, Raw

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

        if "raw_today" in price_state.attributes:
            self._price_attribute_today = "raw_today"
            self._price_attribute_tomorrow = "raw_tomorrow"
        elif "prices_today" in price_state.attributes:
            self._price_attribute_today = "prices_today"
            self._price_attribute_tomorrow = "prices_tomorrow"
        else:
            return False

        # Set _price_key.start and _price_key.value
        try:
            if "start" in price_state.attributes[self._price_attribute_today][0]:
                self._price_format.start = "start"
            elif "time" in price_state.attributes[self._price_attribute_today][0]:
                self._price_format.start = "time"
            elif "hour" in price_state.attributes[self._price_attribute_today][0]:
                self._price_format.start = "hour"
            else:
                return False
            if "price" in price_state.attributes[self._price_attribute_today][0]:
                self._price_format.value = "price"
            elif "value" in price_state.attributes[self._price_attribute_today][0]:
                self._price_format.value = "value"
            else:
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
        return Raw(state.attributes[self._price_attribute_today], self._price_format)

    def get_raw_tomorrow_local(self, state) -> Raw:
        """Get the tomorrow's prices in local timezone"""
        return Raw(state.attributes[self._price_attribute_tomorrow], self._price_format)

    def get_current_price(self, state) -> float:
        """Return current price."""
        time_now = dt.now()
        return self.get_raw_today_local(state).get_value(time_now)

    @staticmethod
    def validate_price_entity(
        hass: HomeAssistant, user_input: dict[str, Any]
    ) -> list[str]:
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
