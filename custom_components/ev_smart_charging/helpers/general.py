"""General helpers"""

# pylint: disable=relative-beyond-top-level
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import State
from homeassistant.util import dt

from custom_components.ev_smart_charging.const import (
    PLATFORM_ENERGIDATASERVICE,
    PLATFORM_ENTSOE,
    PLATFORM_GESPOT,
    PLATFORM_NORDPOOL,
    QUARTERS,
)
from .raw import Raw


_LOGGER = logging.getLogger(__name__)


class Validator:
    """Validator"""

    @staticmethod
    def is_float(element: Any) -> bool:
        """Check that argument is a float"""
        try:
            float(element)
            return True
        except ValueError:
            return False
        except TypeError:
            return False

    @staticmethod
    def is_soc_state(soc_state: State) -> bool:
        """Check that argument is a SOC state"""
        if soc_state is not None:
            if soc_state.state != "unavailable":
                soc = soc_state.state
                if not Validator.is_float(soc):
                    return False
                if 0.0 <= float(soc) <= 100.0:
                    return True
        return False

    @staticmethod
    def is_price_state(
        price_state: State, price_platform: str = PLATFORM_NORDPOOL
    ) -> bool:
        """Check that argument is a Price sensor state"""
        if price_state is None or price_state.state == "unavailable":
            return False

        # Check current_price
        try:
            if not Validator.is_float(price_state.attributes["current_price"]):
                return False
        except KeyError:
            return False

        # Check raw_today
        try:
            # For GE-Spot, try multiple price formats if the initial validation fails
            if price_platform == PLATFORM_GESPOT:
                # First try with GE-Spot's default format (same as Nordpool)
                if Raw(price_state.attributes["raw_today"], PLATFORM_GESPOT).is_valid():
                    return True

                # If that fails, try with other formats that GE-Spot might be using
                # based on its configured primary source
                for alt_platform in [PLATFORM_NORDPOOL, PLATFORM_ENERGIDATASERVICE, PLATFORM_ENTSOE]:
                    if Raw(price_state.attributes["raw_today"], alt_platform).is_valid():
                        return True

                # If all validations fail, check if GE-Spot has fallback data
                if "source_info" in price_state.attributes:
                    source_info = price_state.attributes["source_info"]
                    # If GE-Spot is using a fallback source, it's still valid
                    if isinstance(source_info, dict) and "is_using_fallback" in source_info:
                        return True

                # All validation attempts failed
                return False
            else:
                # For other platforms, use the standard validation
                if not Raw(price_state.attributes["raw_today"], price_platform).is_valid():
                    return False
        except KeyError:
            return False
        except TypeError:
            return False

        # Don't check raw_tomorrow. It can be missing.
        return True


class Utils:
    """Utils"""

    @staticmethod
    def datetime_quarter(time=None) -> int:
        """Return the quarter index (0-95) using Home Assistant's local time.

        If time is None, dt.now() is used. If a naive datetime is passed,
        it will be converted to local time with dt.as_local for safety.
        """
        if time is None:
            time = dt.now()
        elif getattr(time, "tzinfo", None) is None:  # naive -> local
            time = dt.as_local(time)
        total_minutes = time.hour * 60 + time.minute
        return total_minutes // 15


def get_parameter(config_entry: ConfigEntry, parameter: str, default_val: Any = None):
    """Get parameter from OptionsFlow or ConfigFlow"""
    if parameter in config_entry.options.keys():
        return config_entry.options.get(parameter)
    if parameter in config_entry.data.keys():
        return config_entry.data.get(parameter)
    return default_val


def get_quarter_index(option: str) -> int | None:
    """Get index of option."""

    # Get index of option in QUARTERS minus 1. If option is "None", return None.
    if option == "None":
        return None
    if option in QUARTERS:
        return QUARTERS.index(option) - 1
    return None
