"""Switch platform for EV Smart Charging."""
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    ENTITY_NAME_ACTIVE_SWITCH,
    ENTITY_NAME_IGNORE_LIMIT_SWITCH,
    SWITCH,
)
from .coordinator import EVSmartChargingCoordinator
from .entity import EVSmartChargingEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_devices
):  # pylint: disable=unused-argument
    """Setup switch platform."""
    _LOGGER.debug("EVSmartCharging.switch.py")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    switches = []
    switches.append(EVSmartChargingSwitchActive(entry, coordinator))
    switches.append(EVSmartChargingSwitchIgnoreLimit(entry, coordinator))
    async_add_devices(switches)


class EVSmartChargingSwitch(EVSmartChargingEntity, SwitchEntity):
    """EV Smart Charging switch class."""

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSwitch.__init__()")
        super().__init__(entry)
        self.coordinator = coordinator
        id_name = self._attr_name.replace(" ", "").lower()
        self._attr_unique_id = ".".join([entry.entry_id, SWITCH, id_name])

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        self._attr_is_on = True

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        self._attr_is_on = False


class EVSmartChargingSwitchActive(EVSmartChargingSwitch):
    """EV Smart Charging switch class."""

    _attr_name = ENTITY_NAME_ACTIVE_SWITCH

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSwitchActive.__init__()")
        super().__init__(entry, coordinator)
        if self.is_on is None:
            self._attr_is_on = True
            self.update_ha_state()
        self.coordinator.switch_active = self.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on(**kwargs)
        self.coordinator.switch_active_update(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        self.coordinator.switch_active_update(False)


class EVSmartChargingSwitchIgnoreLimit(EVSmartChargingSwitch):
    """EV Smart Charging switch class."""

    _attr_name = ENTITY_NAME_IGNORE_LIMIT_SWITCH

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSwitchIgnoreLimit.__init__()")
        super().__init__(entry, coordinator)
        if self.is_on is None:
            self._attr_is_on = False
            self.update_ha_state()
        self.coordinator.switch_ignore_limit = self.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on(**kwargs)
        self.coordinator.switch_ignore_limit_update(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        self.coordinator.switch_ignore_limit_update(False)
