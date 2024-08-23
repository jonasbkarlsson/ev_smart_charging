"""Number platform for EV Smart Charging."""

import logging
from typing import Union

from homeassistant.components.number import (
    RestoreNumber,
    NumberExtraStoredData,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from .const import (
    CONF_LOW_PRICE_CHARGING_LEVEL,
    CONF_LOW_SOC_CHARGING_LEVEL,
    CONF_MAX_CHARGING_CURRENT,
    CONF_MAX_PRICE,
    CONF_MIN_CHARGING_CURRENT,
    CONF_MIN_SOC,
    CONF_NORMAL_CHARGING_CURRENT,
    CONF_OPPORTUNISTIC_LEVEL,
    CONF_PCT_PER_HOUR,
    CONF_SOLAR_CHARGING_OFF_DELAY,
    DOMAIN,
    ENTITY_KEY_CONF_LOW_PRICE_CHARGING_NUMBER,
    ENTITY_KEY_CONF_LOW_SOC_CHARGING_NUMBER,
    ENTITY_KEY_CONF_MAX_CHARGING_CURRENT_NUMBER,
    ENTITY_KEY_CONF_MIN_CHARGING_CURRENT_NUMBER,
    ENTITY_KEY_CONF_NORMAL_CHARGING_CURRENT_NUMBER,
    ENTITY_KEY_CONF_OPPORTUNISTIC_LEVEL_NUMBER,
    ENTITY_KEY_CONF_PCT_PER_HOUR_NUMBER,
    ENTITY_KEY_CONF_MAX_PRICE_NUMBER,
    ENTITY_KEY_CONF_MIN_SOC_NUMBER,
    ENTITY_KEY_CONF_SOLAR_CHARGING_OFF_DELAY_NUMBER,
    ICON_BATTERY_50,
    ICON_CASH,
    ICON_TIMER,
    NUMBER,
)
from .coordinator import EVSmartChargingCoordinator
from .entity import EVSmartChargingEntity
from .helpers.general import get_parameter

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_devices
):  # pylint: disable=unused-argument
    """Setup number platform."""
    _LOGGER.debug("EVSmartCharging.number.py")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    numbers = []
    numbers.append(EVSmartChargingNumberChargingSpeed(entry, coordinator))
    numbers.append(EVSmartChargingNumberPriceLimit(entry, coordinator))
    numbers.append(EVSmartChargingNumberMinSOC(entry, coordinator))
    numbers.append(EVSmartChargingNumberOpportunistic(entry, coordinator))
    numbers.append(EVSmartChargingNumberLowPriceCharging(entry, coordinator))
    numbers.append(EVSmartChargingNumberLowSocCharging(entry, coordinator))
    numbers.append(EVSmartChargingNumberMaxChargingCurrent(entry, coordinator))
    numbers.append(EVSmartChargingNumberMinChargingCurrent(entry, coordinator))
    numbers.append(EVSmartChargingNumberNormalChargingCurrent(entry, coordinator))
    numbers.append(EVSmartChargingNumberSolarChargingOffDelay(entry, coordinator))
    async_add_devices(numbers)


# pylint: disable=abstract-method
class EVSmartChargingNumber(EVSmartChargingEntity, RestoreNumber):
    """EV Smart Charging number class."""

    # To support HA 2022.7
    _attr_native_value: Union[float, None] = None  # Using Union to support Python 3.9

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingNumber.__init__()")
        super().__init__(entry)
        self.coordinator = coordinator
        id_name = self._entity_key.replace("_", "").lower()
        self._attr_unique_id = ".".join([entry.entry_id, NUMBER, id_name])
        self.set_entity_id(NUMBER, self._entity_key)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        self._attr_native_value = value

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug("EVSmartChargingNumber.async_added_to_hass()")
        restored: NumberExtraStoredData = await self.async_get_last_number_data()
        if restored is not None:
            await self.async_set_native_value(restored.native_value)
            _LOGGER.debug(
                "EVSmartChargingNumber.async_added_to_hass() %s",
                self._attr_native_value,
            )


class EVSmartChargingNumberChargingSpeed(EVSmartChargingNumber):
    """EV Smart Charging active number class."""

    _entity_key = ENTITY_KEY_CONF_PCT_PER_HOUR_NUMBER
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0.1
    _attr_native_max_value = 100.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "%/h"

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingNumberChargingSpeed.__init__()")
        super().__init__(entry, coordinator)
        if self.value is None:
            self._attr_native_value = get_parameter(entry, CONF_PCT_PER_HOUR, 6.0)
            self.update_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await super().async_set_native_value(value)
        self.coordinator.charging_pct_per_hour = value
        await self.coordinator.update_configuration()


class EVSmartChargingNumberPriceLimit(EVSmartChargingNumber):
    """EV Smart Charging apply limit number class."""

    _entity_key = ENTITY_KEY_CONF_MAX_PRICE_NUMBER
    _attr_icon = ICON_CASH
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = -10000.0
    _attr_native_max_value = 10000.0
    _attr_native_step = 0.01

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingNumberPriceLimit.__init__()")
        super().__init__(entry, coordinator)
        if self.value is None:
            self._attr_native_value = get_parameter(entry, CONF_MAX_PRICE, 0.0)
            self.update_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await super().async_set_native_value(value)
        self.coordinator.max_price = value
        await self.coordinator.update_configuration()


class EVSmartChargingNumberMinSOC(EVSmartChargingNumber):
    """EV Smart Charging continuous number class."""

    _entity_key = ENTITY_KEY_CONF_MIN_SOC_NUMBER
    _attr_icon = ICON_BATTERY_50
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "%"

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingNumberMinSOC.__init__()")
        super().__init__(entry, coordinator)
        if self.value is None:
            self._attr_native_value = get_parameter(entry, CONF_MIN_SOC, 0.0)
            self.update_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await super().async_set_native_value(value)
        self.coordinator.number_min_soc = value
        await self.coordinator.update_configuration()


class EVSmartChargingNumberOpportunistic(EVSmartChargingNumber):
    """EV Smart Charging opportunistic number class."""

    _entity_key = ENTITY_KEY_CONF_OPPORTUNISTIC_LEVEL_NUMBER
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "%"

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingNumberOpportunistic.__init__()")
        super().__init__(entry, coordinator)
        if self.value is None:
            self._attr_native_value = get_parameter(
                entry, CONF_OPPORTUNISTIC_LEVEL, 50.0
            )
            _LOGGER.debug(
                "EVSmartChargingNumberOpportunistic.__init__() %s",
                self._attr_native_value,
            )
            self.update_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await super().async_set_native_value(value)
        self.coordinator.number_opportunistic_level = value
        await self.coordinator.update_configuration()


class EVSmartChargingNumberLowPriceCharging(EVSmartChargingNumber):
    """EV Smart Charging low price charging number class."""

    _entity_key = ENTITY_KEY_CONF_LOW_PRICE_CHARGING_NUMBER
    _attr_icon = ICON_CASH
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = -10000.0
    _attr_native_max_value = 10000.0
    _attr_native_step = 0.01

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingNumberLowPriceCharging.__init__()")
        super().__init__(entry, coordinator)
        if self.value is None:
            self._attr_native_value = get_parameter(
                entry, CONF_LOW_PRICE_CHARGING_LEVEL, 0.0
            )
            self.update_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await super().async_set_native_value(value)
        self.coordinator.low_price_charging = value
        await self.coordinator.update_configuration()


class EVSmartChargingNumberLowSocCharging(EVSmartChargingNumber):
    """EV Smart Charging low SOC charging number class."""

    _entity_key = ENTITY_KEY_CONF_LOW_SOC_CHARGING_NUMBER
    _attr_icon = ICON_BATTERY_50
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "%"

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingNumberLowSocCharging.__init__()")
        super().__init__(entry, coordinator)
        if self.value is None:
            self._attr_native_value = get_parameter(
                entry, CONF_LOW_SOC_CHARGING_LEVEL, 20.0
            )
            self.update_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await super().async_set_native_value(value)
        self.coordinator.low_soc_charging = value
        await self.coordinator.update_configuration()


class EVSmartChargingNumberMaxChargingCurrent(EVSmartChargingNumber):
    """EV Smart Charging maximum charging current number class."""

    _entity_key = ENTITY_KEY_CONF_MAX_CHARGING_CURRENT_NUMBER
    #    _attr_icon = ICON_BATTERY_50
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 1.0
    _attr_native_max_value = 32.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "A"

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingNumberMaxChargingCurrent.__init__()")
        super().__init__(entry, coordinator)
        if self.value is None:
            self._attr_native_value = get_parameter(
                entry, CONF_MAX_CHARGING_CURRENT, 16.0
            )
            self.update_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await super().async_set_native_value(value)
        self.coordinator.max_charging_current = value
        await self.coordinator.update_configuration()


class EVSmartChargingNumberMinChargingCurrent(EVSmartChargingNumber):
    """EV Smart Charging minimum charging current number class."""

    _entity_key = ENTITY_KEY_CONF_MIN_CHARGING_CURRENT_NUMBER
    #    _attr_icon = ICON_BATTERY_50
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 1.0
    _attr_native_max_value = 32.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "A"

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingNumberMinChargingCurrent.__init__()")
        super().__init__(entry, coordinator)
        if self.value is None:
            self._attr_native_value = get_parameter(
                entry, CONF_MIN_CHARGING_CURRENT, 6.0
            )
            self.update_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await super().async_set_native_value(value)
        self.coordinator.min_charging_current = value
        await self.coordinator.update_configuration()


class EVSmartChargingNumberNormalChargingCurrent(EVSmartChargingNumber):
    """EV Smart Charging normal charging current number class."""

    _entity_key = ENTITY_KEY_CONF_NORMAL_CHARGING_CURRENT_NUMBER
    #    _attr_icon = ICON_BATTERY_50
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 1.0
    _attr_native_max_value = 32.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "A"

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingNumberNormalChargingCurrent.__init__()")
        super().__init__(entry, coordinator)
        if self.value is None:
            self._attr_native_value = get_parameter(
                entry, CONF_NORMAL_CHARGING_CURRENT, 16.0
            )
            self.update_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await super().async_set_native_value(value)
        self.coordinator.normal_charging_current = value
        await self.coordinator.update_configuration()


class EVSmartChargingNumberSolarChargingOffDelay(EVSmartChargingNumber):
    """EV Smart Charging Solar Charging Off Delay number class."""

    _entity_key = ENTITY_KEY_CONF_SOLAR_CHARGING_OFF_DELAY_NUMBER
    _attr_icon = ICON_TIMER
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 1.0
    _attr_native_max_value = 60.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "minutes"

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingNumberSolarChargingOffDelay.__init__()")
        super().__init__(entry, coordinator)
        if self.value is None:
            self._attr_native_value = get_parameter(
                entry, CONF_SOLAR_CHARGING_OFF_DELAY, 5.0
            )
            self.update_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await super().async_set_native_value(value)
        self.coordinator.solar_charging_off_delay = value
        await self.coordinator.update_configuration()
