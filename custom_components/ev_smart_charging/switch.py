"""Switch platform for EV Smart Charging."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant


from .const import ENTITY_NAME_ACTIVE_SWITCH, SWITCH
from .entity import EVSmartChargingEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_devices
):  # pylint: disable=unused-argument
    """Setup switch platform."""
    _LOGGER.debug("EVSmartCharging.switch.py")
    switch = EVSmartChargingSwitch(entry)
    async_add_devices([switch])


class EVSmartChargingSwitch(EVSmartChargingEntity, SwitchEntity):
    """EV Smart Charging sensor class."""

    _attr_name = ENTITY_NAME_ACTIVE_SWITCH

    def __init__(self, entry):
        _LOGGER.debug("EVSmartChargingSwitch.__init__()")
        super().__init__(entry)
        self._attr_unique_id = ".".join([entry.entry_id, SWITCH])
        if self.is_on is None:
            self.turn_off()
            self.update_ha_state()

    def turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        self._attr_is_on = True

    def turn_off(self, **kwargs):
        """Turn the entity off."""
        self._attr_is_on = False
