"""Button platform for EV Smart Charging."""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant

from .const import (
    BUTTON,
    DOMAIN,
    ENTITY_NAME_START_BUTTON,
    ENTITY_NAME_STOP_BUTTON,
    ICON_START,
    ICON_STOP,
)
from .coordinator import EVSmartChargingCoordinator
from .entity import EVSmartChargingEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """Setup button platform."""
    _LOGGER.debug("EVSmartCharging.button.py")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    buttons = []
    buttons.append(EVSmartChargingButtonStart(entry, coordinator))
    buttons.append(EVSmartChargingButtonStop(entry, coordinator))
    async_add_devices(buttons)


class EVSmartChargingButton(EVSmartChargingEntity, ButtonEntity):
    """EV Smart Charging button class."""

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingButton.__init__()")
        super().__init__(entry)
        self.coordinator = coordinator
        id_name = self._attr_name.replace(" ", "").lower()
        self._attr_unique_id = ".".join([entry.entry_id, BUTTON, id_name])
        _LOGGER.debug("self._attr_unique_id = %s", self._attr_unique_id)


class EVSmartChargingButtonStart(EVSmartChargingButton):
    """EV Smart Charging start button class."""

    _attr_name = ENTITY_NAME_START_BUTTON
    _attr_icon = ICON_START

    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.turn_on_charging()


class EVSmartChargingButtonStop(EVSmartChargingButton):
    """EV Smart Charging start button class."""

    _attr_name = ENTITY_NAME_STOP_BUTTON
    _attr_icon = ICON_STOP

    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.turn_off_charging()
