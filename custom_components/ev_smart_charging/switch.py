"""Switch platform for EV Smart Charging."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant


from .const import (
    DOMAIN,
    ENTITY_NAME_ACTIVE_SWITCH,
    ENTITY_NAME_IGNORE_LIMIT_SWITCH,
    SWITCH,
)
from .entity import EVSmartChargingEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_devices
):  # pylint: disable=unused-argument
    """Setup switch platform."""
    _LOGGER.debug("EVSmartCharging.switch.py")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    switches = []
    switches.append(
        EVSmartChargingSwitchActive(
            entry,
        )
    )
    switches.append(
        EVSmartChargingSwitchIgnoreLimit(
            entry,
        )
    )
    async_add_devices(switches)
    # TODO: coordinator.add_switches(switches)


class EVSmartChargingSwitch(EVSmartChargingEntity, SwitchEntity):
    """EV Smart Charging switch class."""

    def __init__(self, entry):
        _LOGGER.debug("EVSmartChargingSwitch.__init__()")
        super().__init__(entry)
        id_name = self._attr_name.replace(" ", "").lower()
        self._attr_unique_id = ".".join([entry.entry_id, SWITCH, id_name])

    def turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        self._attr_is_on = True

    def turn_off(self, **kwargs):
        """Turn the entity off."""
        self._attr_is_on = False


class EVSmartChargingSwitchActive(EVSmartChargingSwitch):
    """EV Smart Charging switch class."""

    _attr_name = ENTITY_NAME_ACTIVE_SWITCH

    def __init__(self, entry):
        _LOGGER.debug("EVSmartChargingSwitchActive.__init__()")
        super().__init__(entry)
        if self.is_on is None:
            self.turn_on()
            self.update_ha_state()


class EVSmartChargingSwitchIgnoreLimit(EVSmartChargingSwitch):
    """EV Smart Charging switch class."""

    _attr_name = ENTITY_NAME_IGNORE_LIMIT_SWITCH

    def __init__(self, entry):
        _LOGGER.debug("EVSmartChargingSwitchIgnoreLimit.__init__()")
        super().__init__(entry)
        if self.is_on is None:
            self.turn_off()
            self.update_ha_state()
