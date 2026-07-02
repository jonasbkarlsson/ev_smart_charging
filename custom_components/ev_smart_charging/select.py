"""Select platform for EV Smart Charging."""

import logging
from typing import Union

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_READY_QUARTER,
    CONF_READY_DAY,
    CONF_START_QUARTER,
    CONF_START_DAY,
    DOMAIN,
    ENTITY_KEY_CONF_READY_QUARTER,
    ENTITY_KEY_CONF_READY_DAY,
    ENTITY_KEY_CONF_START_QUARTER,
    ENTITY_KEY_CONF_START_DAY,
    QUARTERS,
    READY_DAYS,
    READY_DAYS_NO_PREDICTION,
    START_DAYS,
    START_DAYS_NO_PREDICTION,
    ICON_TIME,
    ICON_DAY,
    READY_QUARTER_NONE,
    SELECT,
    START_QUARTER_NONE,
    ENTITY_KEY_CONF_BLACKOUT_START_TIME,
    ENTITY_KEY_CONF_BLACKOUT_END_TIME,
    CONF_BLACKOUT_START_TIME,
    CONF_BLACKOUT_END_TIME,
    ICON_BLACKOUT_START,
    ICON_BLACKOUT_END,
)
from .coordinator import EVSmartChargingCoordinator
from .entity import EVSmartChargingEntity
from .helpers.general import get_parameter, get_quarter_index

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_devices
):  # pylint: disable=unused-argument
    """Setup select platform."""
    _LOGGER.debug("EVSmartCharging.select.py")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    selects = []
    selects.append(EVSmartChargingSelectStartQuarter(entry, coordinator))
    selects.append(EVSmartChargingSelectStartDay(entry, coordinator))
    selects.append(EVSmartChargingSelectReadyQuarter(entry, coordinator))
    selects.append(EVSmartChargingSelectReadyDay(entry, coordinator))
    selects.append(EVSmartChargingSelectBlackoutStart(entry, coordinator))
    selects.append(EVSmartChargingSelectBlackoutEnd(entry, coordinator))
    async_add_devices(selects)


class EVSmartChargingSelect(EVSmartChargingEntity, SelectEntity, RestoreEntity):
    """EV Smart Charging switch class."""

    _attr_current_option: Union[str, None] = None  # Using Union to support Python 3.9

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSelect.__init__()")
        super().__init__(entry)
        self.coordinator = coordinator
        id_name = self._entity_key.replace("_", "").lower()
        self._attr_unique_id = ".".join([entry.entry_id, SELECT, id_name])
        self.set_entity_id(SELECT, self._entity_key)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self._attr_current_option = option

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        restored: State = await self.async_get_last_state()
        if restored is not None:
            await self.async_select_option(restored.state)


class EVSmartChargingSelectStartQuarter(EVSmartChargingSelect):
    """EV Smart Charging start_quarter select class."""

    _entity_key = ENTITY_KEY_CONF_START_QUARTER
    _attr_icon = ICON_TIME
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = QUARTERS

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSelectReadyQuarter.__init__()")
        super().__init__(entry, coordinator)
        if self.state is None:
            self._attr_current_option = get_parameter(entry, CONF_START_QUARTER, "None")
            self.update_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await super().async_select_option(option)
        if self.state:
            self.coordinator.start_quarter_local = get_quarter_index(self.state)
            if self.coordinator.start_quarter_local is None:
                self.coordinator.start_quarter_local = START_QUARTER_NONE
            await self.coordinator.update_configuration()


class EVSmartChargingSelectReadyQuarter(EVSmartChargingSelect):
    """EV Smart Charging ready_quarter select class."""

    _entity_key = ENTITY_KEY_CONF_READY_QUARTER
    _attr_icon = ICON_TIME
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = QUARTERS

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSelectReadyQuarter.__init__()")
        super().__init__(entry, coordinator)
        if self.state is None:
            self._attr_current_option = get_parameter(
                entry, CONF_READY_QUARTER, "08:00"
            )
            self.update_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await super().async_select_option(option)
        if self.state:
            self.coordinator.ready_quarter_local = get_quarter_index(self.state)
            if self.coordinator.ready_quarter_local is None:
                self.coordinator.ready_quarter_local = READY_QUARTER_NONE
            if self.coordinator.ready_quarter_local == 0:
                # Treat 00:00 as 24:00
                self.coordinator.ready_quarter_local = 24 * 4
            await self.coordinator.update_configuration()


class EVSmartChargingSelectReadyDay(EVSmartChargingSelect):
    """EV Smart Charging ready_day select class."""

    _entity_key = ENTITY_KEY_CONF_READY_DAY
    _attr_icon = ICON_DAY
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def options(self):
        """Return available options depending on predicted price mode."""
        if self.coordinator.switch_use_predicted_epex_data:
            return READY_DAYS
        return READY_DAYS_NO_PREDICTION

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSelectReadyDay.__init__()")
        super().__init__(entry, coordinator)
        if self.state is None:
            self._attr_current_option = get_parameter(entry, CONF_READY_DAY, "Auto")
            self.update_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in self.options:
            option = READY_DAYS_NO_PREDICTION[0]
        await super().async_select_option(option)
        if self.state:
            await self.coordinator.set_ready_day(self.state)


class EVSmartChargingSelectStartDay(EVSmartChargingSelect):
    """EV Smart Charging start_day select class."""

    _entity_key = ENTITY_KEY_CONF_START_DAY
    _attr_icon = ICON_DAY
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def options(self):
        """Return available options depending on predicted price mode."""
        if self.coordinator.switch_use_predicted_epex_data:
            return START_DAYS
        return START_DAYS_NO_PREDICTION

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSelectStartDay.__init__()")
        super().__init__(entry, coordinator)
        if self.state is None:
            self._attr_current_option = get_parameter(entry, CONF_START_DAY, "Auto")
            self.update_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in self.options:
            option = START_DAYS_NO_PREDICTION[0]
        await super().async_select_option(option)
        if self.state:
            await self.coordinator.set_start_day(self.state)


class EVSmartChargingSelectBlackoutStart(EVSmartChargingSelect):
    """EV Smart Charging blackout_start_time select class."""

    _entity_key = ENTITY_KEY_CONF_BLACKOUT_START_TIME
    _attr_icon = ICON_BLACKOUT_START
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = QUARTERS

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSelectBlackoutStart.__init__()")
        super().__init__(entry, coordinator)
        if self.state is None:
            self._attr_current_option = get_parameter(
                entry, CONF_BLACKOUT_START_TIME, "None"
            )
            self.update_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await super().async_select_option(option)
        if self.state:
            self.coordinator.blackout_start_local = get_quarter_index(self.state)
            if self.coordinator.blackout_start_local is None:
                self.coordinator.blackout_start_local = START_QUARTER_NONE
            await self.coordinator.update_configuration()


class EVSmartChargingSelectBlackoutEnd(EVSmartChargingSelect):
    """EV Smart Charging blackout_end_time select class."""

    _entity_key = ENTITY_KEY_CONF_BLACKOUT_END_TIME
    _attr_icon = ICON_BLACKOUT_END
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = QUARTERS

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSelectBlackoutEnd.__init__()")
        super().__init__(entry, coordinator)
        if self.state is None:
            self._attr_current_option = get_parameter(
                entry, CONF_BLACKOUT_END_TIME, "None"
            )
            self.update_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await super().async_select_option(option)
        if self.state:
            self.coordinator.blackout_end_local = get_quarter_index(self.state)
            if self.coordinator.blackout_end_local is None:
                self.coordinator.blackout_end_local = START_QUARTER_NONE
            await self.coordinator.update_configuration()
