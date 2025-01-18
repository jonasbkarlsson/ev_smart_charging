"""General helpers"""

# pylint: disable=relative-beyond-top-level
import logging
from typing import Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import State
from homeassistant.util import dt

from custom_components.ev_smart_charging.const import QUARTERS


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


class Utils:
    """Utils"""

    @staticmethod
    def datetime_quarter(time: dt) -> int:
        """Return the quarter of the day"""
        total_minutes = time.hour * 60 + time.minute
        return total_minutes // 15


def get_parameter(config_entry: ConfigEntry, parameter: str, default_val: Any = None):
    """Get parameter from OptionsFlow or ConfigFlow"""
    if parameter in config_entry.options.keys():
        return config_entry.options.get(parameter)
    if parameter in config_entry.data.keys():
        return config_entry.data.get(parameter)
    return default_val


def get_quarter_index(option: str) -> int:
    """Get index of option."""

    # Get index of option in QUARTERS minus 1. If option is "None", return None.
    if option == "None":
        return None
    if option in QUARTERS:
        return QUARTERS.index(option) - 1
    return None
