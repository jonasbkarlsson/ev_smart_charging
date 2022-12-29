"""Select platform for EV Smart Charging."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from .const import (
    CONF_READY_HOUR,
    DOMAIN,
    ENTITY_NAME_CONF_READY_HOUR,
    HOURS,
    ICON_TIME,
    SELECT,
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
    selects.append(EVSmartChargingSelectReadyHour(entry, coordinator))
    async_add_devices(selects)


class EVSmartChargingSelect(EVSmartChargingEntity, SelectEntity):
    """EV Smart Charging switch class."""

    _attr_current_option: str | None = None

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSelect.__init__()")
        super().__init__(entry)
        self.coordinator = coordinator
        id_name = self._attr_name.replace(" ", "").lower()
        self._attr_unique_id = ".".join([entry.entry_id, SELECT, id_name])

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self._attr_current_option = option


class EVSmartChargingSelectReadyHour(EVSmartChargingSelect):
    """EV Smart Charging active switch class."""

    _attr_name = ENTITY_NAME_CONF_READY_HOUR
    _attr_icon = ICON_TIME
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = HOURS

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSelectReadyHour.__init__()")
        super().__init__(entry, coordinator)
        if self.state is None:
            self._attr_current_option = get_parameter(entry, CONF_READY_HOUR)
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
            await self.coordinator.update_sensors()
