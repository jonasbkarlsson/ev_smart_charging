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
    CONF_MAX_PRICE,
    CONF_MIN_SOC,
    CONF_OPPORTUNISTIC_LEVEL,
    CONF_PCT_PER_HOUR,
    DOMAIN,
    ENTITY_NAME_CONF_LOW_PRICE_CHARGING_NUMBER,
    ENTITY_NAME_CONF_LOW_SOC_CHARGING_NUMBER,
    ENTITY_NAME_CONF_OPPORTUNISTIC_LEVEL_NUMBER,
    ENTITY_NAME_CONF_PCT_PER_HOUR_NUMBER,
    ENTITY_NAME_CONF_MAX_PRICE_NUMBER,
    ENTITY_NAME_CONF_MIN_SOC_NUMBER,
    ICON_BATTERY_50,
    ICON_CASH,
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
    async_add_devices(numbers)


class EVSmartChargingNumber(EVSmartChargingEntity, RestoreNumber):
    """EV Smart Charging number class."""

    # To support HA 2022.7
    _attr_native_value: Union[float, None] = None  # Using Union to support Python 3.9

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingNumber.__init__()")
        super().__init__(entry)
        self.coordinator = coordinator
        id_name = self._attr_name.replace(" ", "").lower()
        self._attr_unique_id = ".".join([entry.entry_id, NUMBER, id_name])

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

    _attr_name = ENTITY_NAME_CONF_PCT_PER_HOUR_NUMBER
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0.1
    _attr_native_max_value = 100.0
    _attr_native_step = 0.1

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

    _attr_name = ENTITY_NAME_CONF_MAX_PRICE_NUMBER
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

    _attr_name = ENTITY_NAME_CONF_MIN_SOC_NUMBER
    _attr_icon = ICON_BATTERY_50
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0

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

    _attr_name = ENTITY_NAME_CONF_OPPORTUNISTIC_LEVEL_NUMBER
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0

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

    _attr_name = ENTITY_NAME_CONF_LOW_PRICE_CHARGING_NUMBER
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

    _attr_name = ENTITY_NAME_CONF_LOW_SOC_CHARGING_NUMBER
    _attr_icon = ICON_BATTERY_50
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0

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
