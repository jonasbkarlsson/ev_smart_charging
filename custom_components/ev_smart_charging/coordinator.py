"""Coordinator for EV Smart Charging"""

from datetime import datetime
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers.event import (
    async_track_state_change,
    async_track_time_change,
)

from custom_components.ev_smart_charging.sensor import EVSmartChargingSensor

from .const import (
    CONF_NORDPOOL_SENSOR,
    CONF_EV_SOC_SENSOR,
    CONF_EV_TARGET_SOC_SENSOR,
)

_LOGGER = logging.getLogger(__name__)


class EVSmartChargingCoordinator:
    """Coordinator class"""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.hass = hass
        self.entry = entry
        self.platforms = []
        self.listeners = []

        self.sensor = None
        self.nordpool_entity_id = None
        self.ev_soc_entity_id = None
        self.ev_target_soc_entity_id = None

        self.ev_soc = None
        self.ev_target_soc = None
        self.raw_today = None
        self.raw_tomorrow = None
        self.tomorrow_valid = False

        # Do work once per hour.
        self.listeners.append(
            async_track_time_change(hass, self.new_hour, minute=0, second=0)
        )

    @callback
    def new_hour(self, date_time: datetime):  # pylint: disable=unused-argument
        """Called every hour"""
        _LOGGER.debug("EVSmartChargingCoordinator.new_hour()")
        # TODO: Add code here

    def add_sensor(self, sensor: EVSmartChargingSensor):
        """Set up sensor"""
        self.sensor = sensor

        self.nordpool_entity_id = self.entry.data.get(CONF_NORDPOOL_SENSOR)
        self.ev_soc_entity_id = self.entry.data.get(CONF_EV_SOC_SENSOR)
        self.ev_target_soc_entity_id = self.entry.data.get(CONF_EV_TARGET_SOC_SENSOR)

        cb_sensors = async_track_state_change(
            self.hass,
            [
                self.nordpool_entity_id,
                self.ev_soc_entity_id,
                self.ev_target_soc_entity_id,
            ],
            self.update_sensors,
        )
        self.listeners.append(cb_sensors)
        self.update_sensors()

    @callback
    def update_sensors(
        self, entity_id: str = None, old_state: State = None, new_state: State = None
    ):  # pylint: disable=unused-argument
        """Nordpool or EV sensors have been updated."""

        _LOGGER.debug("EVSmartChargingCoordinator.update_sensors()")
        _LOGGER.debug("entity_id = %s", entity_id)
        # _LOGGER.debug("old_state = %s", old_state)
        _LOGGER.debug("new_state = %s", new_state)

        nordpool_state = self.hass.states.get(self.nordpool_entity_id)
        if nordpool_state is not None:
            if nordpool_state.state is not "unavailable":
                self.sensor.current_price = nordpool_state.attributes["current_price"]
                self.raw_today = nordpool_state.attributes["raw_today"]
                self.raw_tomorrow = nordpool_state.attributes["raw_tomorrow"]
                self.tomorrow_valid = nordpool_state.attributes["tomorrow_valid"]

        ev_soc_state = self.hass.states.get(self.ev_soc_entity_id)
        if ev_soc_state is not None:
            if ev_soc_state.state is not "unavailable":
                self.sensor.ev_soc = ev_soc_state.state
                self.ev_soc = ev_soc_state.state

        ev_target_soc_state = self.hass.states.get(self.ev_target_soc_entity_id)
        if ev_target_soc_state is not None:
            if ev_target_soc_state.state is not "unavailable":
                self.sensor.ev_target_soc = ev_target_soc_state.state
                self.ev_target_soc = ev_target_soc_state.state

    def validate_input_sensors(self) -> str:
        """Check that all input sensors returns values."""

        nordpool = self.entry.data.get(CONF_NORDPOOL_SENSOR)
        nordpool_state = self.hass.states.get(nordpool)
        if nordpool_state is None:
            return "Input sensors not ready."

        ev_soc = self.entry.data.get(CONF_EV_SOC_SENSOR)
        ev_soc_state = self.hass.states.get(ev_soc).state
        if ev_soc_state is None:
            return "Input sensors not ready."

        ev_target_soc = self.entry.data.get(CONF_EV_TARGET_SOC_SENSOR)
        ev_target_soc_state = self.hass.states.get(ev_target_soc).state
        if ev_target_soc_state is None:
            return "Input sensors not ready."

        return None
