"""Coordinator for EV Smart Charging"""

from datetime import datetime
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers.event import (
    async_track_state_change,
    async_track_time_change,
)
from homeassistant.const import STATE_ON, STATE_OFF

from .helpers.coordinator import (
    Raw,
    get_charging_hours,
    get_charging_original,
    get_charging_update,
    get_lowest_hours,
    get_charging_value,
)
from .const import (
    CHARGER_TYPE_OCPP,
    CONF_CHARGER_ENTITY,
    CONF_CHARGER_TYPE,
    CONF_MAX_PRICE,
    CONF_PCT_PER_HOUR,
    CONF_READY_HOUR,
    CONF_NORDPOOL_SENSOR,
    CONF_EV_SOC_SENSOR,
    CONF_EV_TARGET_SOC_SENSOR,
)
from .sensor import EVSmartChargingSensor

_LOGGER = logging.getLogger(__name__)


class EVSmartChargingCoordinator:
    """Coordinator class"""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize."""
        self.hass = hass
        self.config_entry = config_entry
        self.platforms = []
        self.listeners = []

        self.sensor = None
        self.switch_active = None
        self.switch_ignore_limit = None
        self.nordpool_entity_id = None
        self.ev_soc_entity_id = None
        self.ev_target_soc_entity_id = None

        self.charger_switch = None
        if self.config_entry.data.get(CONF_CHARGER_TYPE) == CHARGER_TYPE_OCPP:
            self.charger_switch = self._get_existing_param(CONF_CHARGER_ENTITY)

        self.ev_soc = None
        self.ev_target_soc = None
        self.raw_today = None
        self.raw_tomorrow = None
        self.tomorrow_valid = False

        self.raw_two_days = None
        self._charging_original = None
        self._charging = None
        self._charging_pct_per_hour = self._get_existing_param(CONF_PCT_PER_HOUR)
        if self._charging_pct_per_hour is None or self._charging_pct_per_hour <= 0.0:
            self._charging_pct_per_hour = 6.0
        self._ready_hour = int(self._get_existing_param(CONF_READY_HOUR)[0:2])
        self._max_price = float(self._get_existing_param(CONF_MAX_PRICE))

        # Do work once per hour.
        self.listeners.append(
            async_track_time_change(hass, self.new_hour, minute=0, second=0)
        )

    def _get_existing_param(self, parameter: str, default_val: any = None):
        if parameter in self.config_entry.options.keys():
            return self.config_entry.options.get(parameter)
        if parameter in self.config_entry.data.keys():
            return self.config_entry.data.get(parameter)
        return default_val

    @callback
    def new_hour(self, date_time: datetime = None):  # pylint: disable=unused-argument
        """Called every hour"""
        _LOGGER.debug("EVSmartChargingCoordinator.new_hour()")
        if self._charging is not None:
            charging_value = get_charging_value(self._charging)
            _LOGGER.debug("charging_value = %s", charging_value)
            turn_on_charging = (
                charging_value is not None
                and charging_value != 0
                and (
                    self.sensor.current_price < self._max_price
                    or self._max_price == 0.0
                    or self.switch_ignore_limit is True
                )
            )
            _LOGGER.debug("turn_on_charging = %s", turn_on_charging)
            current_value = self.sensor.native_value == STATE_ON
            _LOGGER.debug("current_value = %s", current_value)
            if turn_on_charging and not current_value:
                # Turn on charging
                self.turn_on_charging()
            if not turn_on_charging and current_value:
                # Turn off charging
                self.turn_off_charging()

    def turn_on_charging(self):
        """Turn on charging"""
        _LOGGER.debug("Turn on charging")
        self.sensor.native_value = STATE_ON
        if self.charger_switch is not None:
            self.hass.states.async_set(self.charger_switch, STATE_ON)

    def turn_off_charging(self):
        """Turn off charging"""
        _LOGGER.debug("Turn off charging")
        self.sensor.native_value = STATE_OFF
        if self.charger_switch is not None:
            self.hass.states.async_set(self.charger_switch, STATE_OFF)

    def add_sensor(self, sensor: EVSmartChargingSensor):
        """Set up sensor"""
        self.sensor = sensor

        self.nordpool_entity_id = self._get_existing_param(CONF_NORDPOOL_SENSOR)
        self.ev_soc_entity_id = self._get_existing_param(CONF_EV_SOC_SENSOR)
        self.ev_target_soc_entity_id = self.config_entry.data.get(
            CONF_EV_TARGET_SOC_SENSOR
        )

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
        # TODO: Set self._charging to all 0 for intial value.
        self.update_sensors()

    def switch_active_update(self, state: bool):
        """Handle the Active switch"""
        self.switch_active = state
        _LOGGER.debug("switch_active_update = %s", state)
        self.update_sensors()

    def switch_ignore_limit_update(self, state: bool):
        """Handle the Active switch"""
        self.switch_ignore_limit = state
        _LOGGER.debug("switch_ignore_limit_update = %s", state)
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
            if nordpool_state.state != "unavailable":
                self.sensor.current_price = nordpool_state.attributes["current_price"]
                self.raw_today = Raw(nordpool_state.attributes["raw_today"])
                self.raw_tomorrow = Raw(nordpool_state.attributes["raw_tomorrow"])
                self.tomorrow_valid = self.raw_tomorrow.is_valid()
                self.raw_two_days = self.raw_today.copy()
                self.raw_two_days.extend(self.raw_tomorrow)
                self.sensor.raw_two_days = self.raw_two_days.get_raw()

        ev_soc_state = self.hass.states.get(self.ev_soc_entity_id)
        if ev_soc_state is not None:
            if ev_soc_state.state != "unavailable":
                self.sensor.ev_soc = ev_soc_state.state
                self.ev_soc = float(ev_soc_state.state)

        ev_target_soc_state = self.hass.states.get(self.ev_target_soc_entity_id)
        if ev_target_soc_state is not None:
            if ev_target_soc_state.state != "unavailable":
                self.sensor.ev_target_soc = ev_target_soc_state.state
                self.ev_target_soc = float(ev_target_soc_state.state)

        # Calculate charging schedule
        if (
            self.tomorrow_valid
            and self.ev_soc is not None
            and self.ev_target_soc is not None
        ):
            charging_hours = get_charging_hours(
                self.ev_soc, self.ev_target_soc, self._charging_pct_per_hour
            )
            _LOGGER.debug("charging_hours = %s", charging_hours)
            lowest_hours = get_lowest_hours(
                self._ready_hour, self.raw_two_days, charging_hours
            )
            _LOGGER.debug("lowest_hours = %s", lowest_hours)
            self._charging_original = get_charging_original(
                lowest_hours, self.raw_two_days
            )
        if (
            self._charging_original is not None
            and self.switch_active is not None
            and self.switch_ignore_limit is not None
        ):
            self._charging = get_charging_update(
                self._charging_original,
                self.switch_active,
                self.switch_ignore_limit,
                self._max_price,
            )
            self.sensor.charging_schedule = self._charging

        _LOGGER.debug("self._max_price = %s", self._max_price)
        _LOGGER.debug("Current price = %s", self.sensor.current_price)
        self.new_hour()  # Update the charging status

    def validate_input_sensors(self) -> str:
        """Check that all input sensors returns values."""

        nordpool = self._get_existing_param(CONF_NORDPOOL_SENSOR)
        nordpool_state = self.hass.states.get(nordpool)
        if nordpool_state is None:
            return "Input sensors not ready."

        ev_soc = self._get_existing_param(CONF_EV_SOC_SENSOR)
        ev_soc_state = self.hass.states.get(ev_soc).state
        if ev_soc_state is None:
            return "Input sensors not ready."

        ev_target_soc = self._get_existing_param(CONF_EV_TARGET_SOC_SENSOR)
        ev_target_soc_state = self.hass.states.get(ev_target_soc).state
        if ev_target_soc_state is None:
            return "Input sensors not ready."

        return None
