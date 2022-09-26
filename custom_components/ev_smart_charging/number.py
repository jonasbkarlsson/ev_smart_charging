"""Number platform for EV Smart Charging."""
import logging

from homeassistant.components.number import RestoreNumber, NumberExtraStoredData
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    ENTITY_NAME_MIN_SOC_NUMBER,
    ICON_MIN_SOC,
    NUMBER,
)
from .coordinator import EVSmartChargingCoordinator
from .entity import EVSmartChargingEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """Setup number platform."""
    _LOGGER.debug("EVSmartCharging.number.py")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    numbers = []
    numbers.append(EVSmartChargingNumberMinSOC(entry, coordinator))
    async_add_devices(numbers)


class EVSmartChargingNumber(EVSmartChargingEntity, RestoreNumber):
    """EV Smart Charging button class."""

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingNumber.__init__()")
        super().__init__(entry)
        self.coordinator = coordinator
        id_name = self._attr_name.replace(" ", "").lower()
        self._attr_unique_id = ".".join([entry.entry_id, NUMBER, id_name])
        _LOGGER.debug("self._attr_unique_id = %s", self._attr_unique_id)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        restored: NumberExtraStoredData = await self.async_get_last_number_data()
        if restored is not None:
            self._attr_native_value = restored.native_value


class EVSmartChargingNumberMinSOC(EVSmartChargingNumber):
    """EV Smart Charging min SOC number class."""

    _attr_name = ENTITY_NAME_MIN_SOC_NUMBER
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 5.0
    _attr_native_value = 0.0
    _attr_native_unit_of_measurement = "%"
    _attr_icon = ICON_MIN_SOC

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        await self.coordinator.number_min_soc_update(self._attr_native_value)

    async def async_set_native_value(self, value: float) -> None:
        """Run when entity about to be added to hass."""
        self._attr_native_value = value
        await self.coordinator.number_min_soc_update(self._attr_native_value)
