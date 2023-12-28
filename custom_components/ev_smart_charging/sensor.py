"""Sensor platform for EV Smart Charging."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_OFF


from .const import (
    CHARGING_STATUS_NOT_ACTIVE,
    DOMAIN,
    ENTITY_NAME_CHARGING_SENSOR,
    ENTITY_NAME_STATUS_SENSOR,
    SENSOR,
)
from .entity import EVSmartChargingEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """Setup sensor platform."""
    _LOGGER.debug("EVSmartCharging.sensor.py")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []
    sensors.append(EVSmartChargingSensorCharging(entry))
    sensors.append(EVSmartChargingSensorStatus(entry))
    async_add_devices(sensors)
    await coordinator.add_sensor(sensors)


class EVSmartChargingSensor(EVSmartChargingEntity, SensorEntity):
    """EV Smart Charging sensor class."""

    def __init__(self, entry):
        _LOGGER.debug("EVSmartChargingSensor.__init__()")
        super().__init__(entry)
        id_name = self._attr_name.replace(" ", "").lower()
        self._attr_unique_id = ".".join([entry.entry_id, SENSOR, id_name])


class EVSmartChargingSensorCharging(EVSmartChargingSensor):
    """EV Smart Charging sensor class."""

    _attr_name = ENTITY_NAME_CHARGING_SENSOR

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

    def set_state(self, new_state):
        """Set new status."""
        self._attr_native_value = new_state
        self.update_ha_state()

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "current_price": self._current_price,
            "EV SOC": self._ev_soc,
            "EV target SOC": self._ev_target_soc,
            "Charging is planned": self._charging_is_planned,
            "Charging start time": self._charging_start_time,
            "Charging stop time": self._charging_stop_time,
            "Charging number of hours": self._charging_number_of_hours,
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
    def charging_number_of_hours(self):
        """Getter for charging_number_of_hours."""
        return self._charging_number_of_hours

    @charging_number_of_hours.setter
    def charging_number_of_hours(self, new_value):
        self._charging_number_of_hours = new_value
        self.update_ha_state()


class EVSmartChargingSensorStatus(EVSmartChargingSensor):
    """EV Smart Charging sensor class."""

    _attr_name = ENTITY_NAME_STATUS_SENSOR

    def __init__(self, entry):
        _LOGGER.debug("EVSmartChargingSensorStatus.__init__()")
        super().__init__(entry)

        self._attr_native_value = CHARGING_STATUS_NOT_ACTIVE

    def set_status(self, new_status):
        """Set new status."""
        self._attr_native_value = new_status
        self.update_ha_state()
