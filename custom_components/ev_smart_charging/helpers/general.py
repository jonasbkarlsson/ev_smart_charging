"""General helpers"""

# pylint: disable=relative-beyond-top-level
import logging
from typing import Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import State

from ..const import PLATFORM_NORDPOOL
from .coordinator import Raw

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
        if price_state is not None:
            if price_state.state != "unavailable":
                # Check current_price
                try:
                    if not Validator.is_float(price_state.attributes["current_price"]):
                        return False
                except KeyError:
                    return False
                # Check raw_today
                try:
                    if not Raw(
                        price_state.attributes["raw_today"], price_platform
                    ).is_valid():
                        return False
                except KeyError:
                    return False
                except TypeError:
                    return False
                # Don't check raw_tomorrow. It can be missing.
                return True
        return False


def get_parameter(config_entry: ConfigEntry, parameter: str, default_val: Any = None):
    """Get parameter from OptionsFlow or ConfigFlow"""
    if parameter in config_entry.options.keys():
        return config_entry.options.get(parameter)
    if parameter in config_entry.data.keys():
        return config_entry.data.get(parameter)
    return default_val
