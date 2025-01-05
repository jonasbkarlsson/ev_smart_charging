"""PriceAdaptor class"""

# pylint: disable=relative-beyond-top-level
import logging

from typing import Any
from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt

from custom_components.ev_smart_charging.const import (
    CONF_PRICE_SENSOR,
    PLATFORM_ENERGIDATASERVICE,
    PLATFORM_ENTSOE,
    PLATFORM_TGE,
    PLATFORM_GENERIC,
    PLATFORM_NORDPOOL,
)
from custom_components.ev_smart_charging.helpers.general import get_platform
from custom_components.ev_smart_charging.helpers.coordinator import Raw

_LOGGER = logging.getLogger(__name__)


class PriceAdaptor:
    """PriceAdaptor class"""

    def __init__(self) -> None:
        self._price_platform = PLATFORM_NORDPOOL

    def set_price_platform(self, price_platform: str = PLATFORM_NORDPOOL) -> None:
        """Set the Price platform"""
        self._price_platform = price_platform

    def is_price_state(self, price_state: State) -> bool:
        """Check that argument is a Price sensor state"""
        if price_state is not None:
            if price_state.state != "unavailable":
                # Check raw_today
                try:
                    if not self.get_raw_today_local(price_state).is_valid(check_today_local = True):
                        return False
                except KeyError:
                    return False
                except TypeError:
                    return False
                # Don't check raw_tomorrow. It can be missing.
                return True
        return False

    def get_raw_today_local(self, state) -> Raw:
        """Get the today's prices in local timezone"""

        if self._price_platform in (PLATFORM_NORDPOOL, PLATFORM_ENERGIDATASERVICE):
            return Raw(state.attributes["raw_today"], self._price_platform)

        if self._price_platform in (PLATFORM_ENTSOE, PLATFORM_TGE, PLATFORM_GENERIC):
            return Raw(state.attributes["prices_today"], self._price_platform)

        return Raw([])

    def get_raw_tomorrow_local(self, state) -> Raw:
        """Get the tomorrow's prices in local timezone"""

        if self._price_platform in (PLATFORM_NORDPOOL, PLATFORM_ENERGIDATASERVICE):
            return Raw(state.attributes["raw_tomorrow"], self._price_platform)

        if self._price_platform in (PLATFORM_ENTSOE, PLATFORM_TGE, PLATFORM_GENERIC):
            return Raw(state.attributes["prices_tomorrow"], self._price_platform)

        return Raw([])

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

        price_platform = get_platform(hass, user_input[CONF_PRICE_SENSOR])

        if price_platform in (PLATFORM_NORDPOOL, PLATFORM_ENERGIDATASERVICE):
            if not "raw_today" in price_state.attributes.keys():
                _LOGGER.debug("No attribute raw_today in price sensor")
                return ("base", "sensor_is_not_price")
            if not "raw_tomorrow" in price_state.attributes.keys():
                _LOGGER.debug("No attribute raw_tomorrow in price sensor")
                return ("base", "sensor_is_not_price")
            return None

        if price_platform in (PLATFORM_ENTSOE, PLATFORM_TGE, PLATFORM_GENERIC):
            if not "prices_today" in price_state.attributes.keys():
                _LOGGER.debug("No attribute prices today in price sensor")
                return ("base", "sensor_is_not_price")
            if not "prices_tomorrow" in price_state.attributes.keys():
                _LOGGER.debug("No attribute prices tomorrow in price sensor")
                return ("base", "sensor_is_not_price")
            return None

        # Unknown platform
        return ("base", "sensor_is_not_price")
