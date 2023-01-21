"""Select platform for EV Smart Charging."""
import logging
from typing import Union

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_READY_HOUR,
    CONF_START_HOUR,
    DOMAIN,
    ENTITY_NAME_CONF_READY_HOUR,
    ENTITY_NAME_CONF_START_HOUR,
    HOURS,
    ICON_TIME,
    SELECT,
    START_HOUR_NONE,
)
from .coordinator import EVSmartChargingCoordinator
from .entity import EVSmartChargingEntity
from .helpers.general import get_parameter

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_devices
):  # pylint: disable=unused-argument
    """Setup select platform."""
    _LOGGER.debug("EVSmartCharging.select.py")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    selects = []
    selects.append(EVSmartChargingSelectStartHour(entry, coordinator))
    selects.append(EVSmartChargingSelectReadyHour(entry, coordinator))
    async_add_devices(selects)


class EVSmartChargingSelect(EVSmartChargingEntity, SelectEntity, RestoreEntity):
    """EV Smart Charging switch class."""

    _attr_current_option: Union[str, None] = None  # Using Union to support Python 3.9

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSelect.__init__()")
        super().__init__(entry)
        self.coordinator = coordinator
        id_name = self._attr_name.replace(" ", "").lower()
        self._attr_unique_id = ".".join([entry.entry_id, SELECT, id_name])

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self._attr_current_option = option

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        restored: State = await self.async_get_last_state()
        if restored is not None:
            await self.async_select_option(restored.state)


class EVSmartChargingSelectStartHour(EVSmartChargingSelect):
    """EV Smart Charging start_hour select class."""

    _attr_name = ENTITY_NAME_CONF_START_HOUR
    _attr_icon = ICON_TIME
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = HOURS

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSelectReadyHour.__init__()")
        super().__init__(entry, coordinator)
        if self.state is None:
            self._attr_current_option = get_parameter(entry, CONF_START_HOUR, "None")
            self.update_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await super().async_select_option(option)
        if self.state:
            try:
                self.coordinator.start_hour_local = int(self.state[0:2])
            except ValueError:
                # Don't use start_hour. Select a time in the past.
                self.coordinator.start_hour_local = START_HOUR_NONE
            await self.coordinator.update_configuration()


class EVSmartChargingSelectReadyHour(EVSmartChargingSelect):
    """EV Smart Charging ready_hour select class."""

    _attr_name = ENTITY_NAME_CONF_READY_HOUR
    _attr_icon = ICON_TIME
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = HOURS

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSelectReadyHour.__init__()")
        super().__init__(entry, coordinator)
        if self.state is None:
            self._attr_current_option = get_parameter(entry, CONF_READY_HOUR, "08:00")
            self.update_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await super().async_select_option(option)
        if self.state:
            try:
                self.coordinator.ready_hour_local = int(self.state[0:2])
            except ValueError:
                # Don't use ready_hour. Select a time in the far future.
                self.coordinator.ready_hour_local = 72
            if self.coordinator.ready_hour_local == 0:
                # Treat 00:00 as 24:00
                self.coordinator.ready_hour_local = 24
            await self.coordinator.update_configuration()
