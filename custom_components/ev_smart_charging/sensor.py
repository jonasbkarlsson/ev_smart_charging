"""Sensor platform for EV Smart Charging."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    ICON,
    SENSOR,
)
from .entity import EVSmartChargingEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """Setup sensor platform."""
    _LOGGER.debug("EVSmartCharging.sensor.py")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensor = EVSmartChargingSensor(entry, hass)
    async_add_devices([sensor])
    coordinator.add_sensor(sensor)


class EVSmartChargingSensor(EVSmartChargingEntity, SensorEntity):
    """EV Smart Charging sensor class."""

    def __init__(self, entry, hass):
        _LOGGER.debug("EVSmartChargingSensor.__init__() - beginning")
        super().__init__(entry)
        self.hass = hass
        self._native_value = 0  # None

        self._current_price = None
        self._ev_soc = None
        self._ev_target_soc = None

        _LOGGER.debug("EVSmartChargingSensor.__init__() - end")

    def update_ha_state(self):
        """Update the HA state"""
        if self.entity_id is not None:
            self.async_schedule_update_ha_state()

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}_{SENSOR}"

    # @property
    # def native_value(self):
    #     """Return the native value of the sensor."""
    #     return self._native_value

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON

    # @property
    # def native_unit_of_measurement(self) -> str:
    #     """Return the unit of measurement this sensor expresses itself in."""
    #     _currency = self._currency
    #     if self._use_cents is True:
    #         # Convert unit of measurement to cents based on chosen currency
    #         _currency = _CURRENCY_TO_CENTS[_currency]
    #     return f"{_currency}/{self._price_type}"

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "current_price": self._current_price,
            "EV SOC": self._ev_soc,
            "EV target SOC": self._ev_target_soc,
            "raw_today": 1,
            "raw_tomorrow": 2,
        }

    # @property
    # def unit(self) -> str:
    #     """Property unit"""
    #     return self._price_type

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
