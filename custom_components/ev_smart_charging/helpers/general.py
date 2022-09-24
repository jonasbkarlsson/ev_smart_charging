"""General helpers"""

# pylint: disable=relative-beyond-top-level
from typing import Any
from homeassistant.core import State

from .coordinator import Raw


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
    def is_nordpool_state(nordpool_state: State) -> bool:
        """Check that argument is a Nordpool sensor state"""
        if nordpool_state is not None:
            if nordpool_state.state != "unavailable":
                # Check current_price
                if not Validator.is_float(nordpool_state.attributes["current_price"]):
                    return False
                # Check raw_today
                if not Raw(nordpool_state.attributes["raw_today"]).is_valid():
                    return False
                # Don't check raw_tomorrow. It can be missing.
        return True
