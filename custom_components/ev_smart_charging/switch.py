"""Switch platform for EV Smart Charging."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant


from .const import (
    DEFAULT_NAME,
    ICON,
    SWITCH,
)
from .entity import EVSmartChargingEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """Setup switch platform."""
    _LOGGER.debug("EVSmartCharging.switch.py")
    switch = EVSmartChargingSwitch(entry, hass)
    async_add_devices([switch])


class EVSmartChargingSwitch(EVSmartChargingEntity, SwitchEntity):
    """EV Smart Charging sensor class."""

    def __init__(self, entry, hass):  # pylint: disable=unused-argument
        _LOGGER.debug("EVSmartChargingSwitch.__init__() - beginning")
        super().__init__(entry)
        if self.is_on is None:
            self.turn_off()
            self.update_ha_state()
        _LOGGER.debug("EVSmartChargingSwitch.__init__() - end")

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}_{SWITCH}"

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON

    def turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        self._attr_is_on = True

    def turn_off(self, **kwargs):
        """Turn the entity off."""
        self._attr_is_on = False
