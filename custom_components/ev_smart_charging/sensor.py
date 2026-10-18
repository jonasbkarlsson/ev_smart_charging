"""Sensor platform for EV Smart Charging."""

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.const import PERCENTAGE, STATE_OFF
from homeassistant.helpers.restore_state import ExtraStoredData, RestoreEntity
from homeassistant.util import dt


from .const import (
    DOMAIN,
    ENTITY_KEY_CALCULATED_SOC_SENSOR,
    ENTITY_KEY_CHARGING_SENSOR,
    ENTITY_KEY_STATUS_SENSOR,
    ICON_BATTERY_CHARGING,
    SENSOR,
)
from .entity import EVSmartChargingEntity
from .helpers.soc_estimator import SocEstimator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """Setup sensor platform."""
    _LOGGER.debug("EVSmartCharging.sensor.py")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []
    sensors.append(EVSmartChargingSensorCharging(entry))
    sensors.append(EVSmartChargingSensorStatus(entry))
    if coordinator.soc_estimator is not None:
        sensors.append(EVSmartChargingSensorCalculatedSoc(entry, coordinator))
    async_add_devices(sensors)
    await coordinator.add_sensor(sensors)


class EVSmartChargingSensor(EVSmartChargingEntity, SensorEntity):
    """EV Smart Charging sensor class."""

    def __init__(self, entry):
        _LOGGER.debug("EVSmartChargingSensor.__init__()")
        super().__init__(entry)
        id_name = self._entity_key.replace("_", "").lower()
        self._attr_unique_id = ".".join([entry.entry_id, SENSOR, id_name])
        self.set_entity_id(SENSOR, self._entity_key)


class EVSmartChargingSensorCharging(EVSmartChargingSensor):
    """EV Smart Charging sensor class."""

    _entity_key = ENTITY_KEY_CHARGING_SENSOR

    _unrecorded_attributes = frozenset(
        ["raw_two_days", "charging_schedule"]
    )

    def __init__(self, entry):
        _LOGGER.debug("EVSmartChargingSensor.__init__()")
        super().__init__(entry)
        self._attr_unique_id = ".".join(
            [entry.entry_id, SENSOR]
        )  # Keep to make it backward compatible.
        self._attr_native_value = STATE_OFF

        self._current_price = None
        self._ev_soc = None
        self._ev_target_soc = None
        self._raw_two_days = None
        self._charging_schedule = None

        self._charging_is_planned = False
        self._charging_start_time = None
        self._charging_stop_time = None
        self._charging_number_of_hours = None

        self._opportunistic = False

    def set_state(self, new_state):
        """Set new status."""
        self._attr_native_value = new_state
        self.update_ha_state()

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "current_price": self._current_price,
            "ev_soc": self._ev_soc,
            "ev_target_soc": self._ev_target_soc,
            "charging_is_planned": self._charging_is_planned,
            "charging_start_time": self._charging_start_time,
            "charging_stop_time": self._charging_stop_time,
            "charging_number_of_hours": self._charging_number_of_hours,
            "opportunistic": self._opportunistic,
            "raw_two_days": self._raw_two_days,
            "charging_schedule": self._charging_schedule,
        }

    @property
    def current_price(self):
        """Getter for current_price."""
        return self._current_price

    @current_price.setter
    def current_price(self, new_value):
        self._current_price = new_value
        self.update_ha_state()

    @property
    def ev_soc(self):
        """Getter for ev_soc."""
        return self._ev_soc

    @ev_soc.setter
    def ev_soc(self, new_value):
        self._ev_soc = new_value
        self.update_ha_state()

    @property
    def ev_target_soc(self):
        """Getter for ev_target_soc."""
        return self._ev_target_soc

    @ev_target_soc.setter
    def ev_target_soc(self, new_value):
        self._ev_target_soc = new_value
        self.update_ha_state()

    @property
    def raw_two_days_local(self):
        """Getter for raw_two_days."""
        return self._raw_two_days

    @raw_two_days_local.setter
    def raw_two_days_local(self, new_value):
        self._raw_two_days = new_value
        self.update_ha_state()

    @property
    def charging_schedule(self):
        """Getter for charging_schedule."""
        return self._charging_schedule

    @charging_schedule.setter
    def charging_schedule(self, new_value):
        self._charging_schedule = new_value
        self.update_ha_state()

    @property
    def charging_is_planned(self):
        """Getter for charging_is_planned."""
        return self._charging_is_planned

    @charging_is_planned.setter
    def charging_is_planned(self, new_value):
        self._charging_is_planned = new_value
        self.update_ha_state()

    @property
    def charging_start_time(self):
        """Getter for charging_start_time."""
        return self._charging_start_time

    @charging_start_time.setter
    def charging_start_time(self, new_value):
        self._charging_start_time = new_value
        self.update_ha_state()

    @property
    def charging_stop_time(self):
        """Getter for charging_stop_time."""
        return self._charging_stop_time

    @charging_stop_time.setter
    def charging_stop_time(self, new_value):
        self._charging_stop_time = new_value
        self.update_ha_state()

    @property
    def charging_number_of_quarters(self) -> int:
        """Getter for charging_number_of_quarters."""
        return int(round(self._charging_number_of_hours * 4))

    @charging_number_of_quarters.setter
    def charging_number_of_quarters(self, new_value):
        self._charging_number_of_hours = new_value / 4
        self.update_ha_state()

    @property
    def opportunistic(self):
        """Getter for opportunistic."""
        return self._opportunistic

    @opportunistic.setter
    def opportunistic(self, new_value):
        self._opportunistic = new_value
        self.update_ha_state()


class EVSmartChargingSensorStatus(EVSmartChargingSensor):
    """EV Smart Charging sensor class."""

    _entity_key = ENTITY_KEY_STATUS_SENSOR

    def __init__(self, entry):
        _LOGGER.debug("EVSmartChargingSensorStatus.__init__()")
        super().__init__(entry)

    def set_status(self, new_status):
        """Set new status."""
        self._attr_native_value = new_status
        self.update_ha_state()


class CalculatedSocExtraStoredData(ExtraStoredData):
    """Stored state of the SOC estimator"""

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    def as_dict(self) -> dict[str, Any]:
        return self.data


class EVSmartChargingSensorCalculatedSoc(EVSmartChargingSensor, RestoreEntity):
    """EV Smart Charging calculated SOC sensor class."""

    _entity_key = ENTITY_KEY_CALCULATED_SOC_SENSOR
    _attr_icon = ICON_BATTERY_CHARGING
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, entry, coordinator):
        _LOGGER.debug("EVSmartChargingSensorCalculatedSoc.__init__()")
        super().__init__(entry)
        self.coordinator = coordinator
        self.soc_estimator: SocEstimator = coordinator.soc_estimator
        self._attr_native_value = None
        self._charging_hours = 0.0

    async def async_added_to_hass(self) -> None:
        """Restore the SOC estimator."""
        await super().async_added_to_hass()
        restored = await self.async_get_last_extra_data()
        if restored is not None:
            self.soc_estimator.restore(restored.as_dict())
            if self.coordinator.sensor is not None:
                await self.coordinator.update_sensors()

    @property
    def extra_restore_state_data(self) -> CalculatedSocExtraStoredData:
        return CalculatedSocExtraStoredData(self.soc_estimator.as_dict(dt.now()))

    @property
    def extra_state_attributes(self) -> dict:
        reported_at = self.soc_estimator.reported_at
        return {
            "reported_soc": self.soc_estimator.reported_soc,
            "reported_at": reported_at.isoformat() if reported_at else None,
            "charging_hours": round(self._charging_hours, 2),
        }

    def set_soc(self, soc: float | None, charging_hours: float):
        """Set new calculated SOC."""
        self._attr_native_value = soc
        self._charging_hours = charging_hours
        self.update_ha_state()
