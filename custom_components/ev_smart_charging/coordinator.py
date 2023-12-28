"""Coordinator for EV Smart Charging"""

from datetime import datetime
import logging
from homeassistant.config_entries import (
    ConfigEntry,
)
from homeassistant.const import SERVICE_TURN_ON, SERVICE_TURN_OFF
from homeassistant.core import HomeAssistant, State, callback, Event
from homeassistant.helpers.device_registry import EVENT_DEVICE_REGISTRY_UPDATED
from homeassistant.helpers.device_registry import async_get as async_device_registry_get
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.event import (
    async_track_state_change,
    async_track_time_change,
)
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import (
    EntityRegistry,
    async_entries_for_config_entry,
)
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.util import dt

from custom_components.ev_smart_charging.helpers.price_adaptor import PriceAdaptor

from .const import (
    CHARGING_STATUS_CHARGING,
    CHARGING_STATUS_DISCONNECTED,
    CHARGING_STATUS_KEEP_ON,
    CHARGING_STATUS_NO_PLAN,
    CHARGING_STATUS_NOT_ACTIVE,
    CHARGING_STATUS_WAITING_CHARGING,
    CHARGING_STATUS_WAITING_NEW_PRICE,
    CHARGING_STATUS_LOW_PRICE_CHARGING,
    CHARGING_STATUS_LOW_SOC_CHARGING,
    CONF_CHARGER_ENTITY,
    CONF_EV_CONTROLLED,
    CONF_LOW_PRICE_CHARGING_LEVEL,
    CONF_LOW_SOC_CHARGING_LEVEL,
    CONF_MAX_PRICE,
    CONF_MIN_SOC,
    CONF_OPPORTUNISTIC_LEVEL,
    CONF_PCT_PER_HOUR,
    CONF_READY_HOUR,
    CONF_PRICE_SENSOR,
    CONF_EV_SOC_SENSOR,
    CONF_EV_TARGET_SOC_SENSOR,
    CONF_START_HOUR,
    DEFAULT_TARGET_SOC,
    READY_HOUR_NONE,
    START_HOUR_NONE,
    SWITCH,
)
from .helpers.coordinator import (
    Raw,
    Scheduler,
    get_charging_value,
    get_ready_hour_utc,
    get_start_hour_utc,
)
from .helpers.general import Validator, get_parameter, get_platform
from .sensor import (
    EVSmartChargingSensor,
    EVSmartChargingSensorCharging,
    EVSmartChargingSensorStatus,
)

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
        self.sensor_status = None
        self.switch_active = None
        self.switch_apply_limit = None
        self.switch_apply_limit_entity_id = None
        self.switch_apply_limit_unique_id = None
        self.switch_continuous = None
        self.switch_ev_connected = None
        self.after_ev_connected = False
        self.switch_keep_on = None
        self.switch_keep_on_entity_id = None
        self.switch_keep_on_unique_id = None
        self.switch_keep_on_completion_time = None
        self.switch_opportunistic = None
        self.switch_opportunistic_entity_id = None
        self.switch_opportunistic_unique_id = None
        self.switch_low_price_charging = None
        self.switch_low_soc_charging = None
        self.price_entity_id = None
        self.price_adaptor = PriceAdaptor()
        self.ev_soc_entity_id = None
        self.ev_target_soc_entity_id = None

        self.charger_switch = None
        if len(get_parameter(self.config_entry, CONF_CHARGER_ENTITY)) > 0:
            self.charger_switch = get_parameter(self.config_entry, CONF_CHARGER_ENTITY)

        self.scheduler = Scheduler()

        self.ev_soc = None
        self.ev_soc_before_last_charging = -1
        self.ev_soc_previous = -1
        self.ev_target_soc = None
        self.raw_today_local = None
        self.raw_tomorrow_local = None
        self.tomorrow_valid = False
        self.tomorrow_valid_previous = False

        self.raw_two_days = None
        self._charging_schedule = None
        self.charging_pct_per_hour = get_parameter(
            self.config_entry, CONF_PCT_PER_HOUR, 6.0
        )

        try:
            self.start_hour_local = int(
                get_parameter(self.config_entry, CONF_START_HOUR)[0:2]
            )
        except (ValueError, TypeError):
            # Don't use start_hour. Select a time in the past.
            self.start_hour_local = START_HOUR_NONE

        try:
            self.ready_hour_local = int(
                get_parameter(self.config_entry, CONF_READY_HOUR, "08:00")[0:2]
            )
        except (ValueError, TypeError):
            # Don't use ready_hour. Select a time in the far future.
            self.ready_hour_local = READY_HOUR_NONE
        if self.ready_hour_local == 0:
            # Treat 00:00 as 24:00
            self.ready_hour_local = 24
        self.ready_hour_first = True  # True for first update_sensor the ready_hour

        self.max_price = float(get_parameter(self.config_entry, CONF_MAX_PRICE, 0.0))
        self.number_min_soc = int(get_parameter(self.config_entry, CONF_MIN_SOC, 0.0))
        self.number_opportunistic_level = int(
            get_parameter(self.config_entry, CONF_OPPORTUNISTIC_LEVEL, 50.0)
        )
        self.low_price_charging = float(
            get_parameter(self.config_entry, CONF_LOW_PRICE_CHARGING_LEVEL, 0.0)
        )
        self.low_soc_charging = float(
            get_parameter(self.config_entry, CONF_LOW_SOC_CHARGING_LEVEL, 20.0)
        )

        self.auto_charging_state = STATE_OFF
        self.low_price_charging_state = STATE_OFF
        self.low_soc_charging_state = STATE_OFF

        # Update state once per hour.
        self.listeners.append(
            async_track_time_change(hass, self.update_hourly, minute=0, second=0)
        )
        # Listen for changes to the device.
        self.listeners.append(
            hass.bus.async_listen(EVENT_DEVICE_REGISTRY_UPDATED, self.device_updated)
        )

    def unsubscribe_listeners(self):
        """Unsubscribed to listeners"""
        for unsub in self.listeners:
            unsub()

    @callback
    async def device_updated(self, event: Event):  # pylint: disable=unused-argument
        """Called when device is updated"""
        _LOGGER.debug("EVSmartChargingCoordinator.device_updated()")
        if "device_id" in event.data:
            entity_registry: EntityRegistry = async_entity_registry_get(self.hass)
            all_entities = async_entries_for_config_entry(
                entity_registry, self.config_entry.entry_id
            )
            if all_entities:
                device_id = all_entities[0].device_id
                if event.data["device_id"] == device_id:
                    if "changes" in event.data:
                        if "name_by_user" in event.data["changes"]:
                            # If the device name is changed, update the integration name
                            device_registry: DeviceRegistry = async_device_registry_get(
                                self.hass
                            )
                            device = device_registry.async_get(device_id)
                            if device.name_by_user != self.config_entry.title:
                                self.hass.config_entries.async_update_entry(
                                    self.config_entry, title=device.name_by_user
                                )

    @callback
    async def update_hourly(
        self, date_time: datetime = None
    ):  # pylint: disable=unused-argument
        """Called every hour"""
        _LOGGER.debug("EVSmartChargingCoordinator.update_hourly()")
        await self.update_sensors()

    @callback
    async def update_state(
        self, date_time: datetime = None
    ):  # pylint: disable=unused-argument
        """Called every hour"""
        _LOGGER.debug("EVSmartChargingCoordinator.update_state()")
        if self._charging_schedule is not None:
            charging_value = get_charging_value(self._charging_schedule)
            _LOGGER.debug("charging_value = %s", charging_value)
            turn_on_charging = (
                self.ev_soc is not None
                and self.number_min_soc is not None
                and charging_value is not None
                and charging_value != 0
                and self.sensor.current_price is not None
                and (
                    self.sensor.current_price < self.max_price
                    or self.switch_apply_limit is False
                    or self.ev_soc < self.number_min_soc
                )
                and self.switch_ev_connected is True
                and self.switch_active is True
            )

            if (
                self.switch_active is True
                and self.switch_ev_connected is True
                and self.switch_low_price_charging is True
                and self.sensor.current_price is not None
                and self.sensor.current_price <= self.low_price_charging
            ):
                turn_on_charging = True
                self.low_price_charging_state = STATE_ON
            else:
                self.low_price_charging_state = STATE_OFF

            if (
                self.switch_active is True
                and self.switch_ev_connected is True
                and self.switch_low_soc_charging is True
                and self.ev_soc is not None
                and self.ev_soc < self.low_soc_charging
            ):
                turn_on_charging = True
                self.low_soc_charging_state = STATE_ON
            else:
                self.low_soc_charging_state = STATE_OFF

            if (
                self.ev_soc is not None
                and self.ev_target_soc is not None
                and self.ev_soc >= self.ev_target_soc
            ):
                turn_on_charging = False
                self.low_price_charging_state = STATE_OFF
                self.low_soc_charging_state = STATE_OFF

            time_now = dt.now()
            current_value = self.auto_charging_state == STATE_ON

            # Handle self.switch_keep_on
            if self.switch_keep_on:
                # Only if price limit is not used and the EV is connected
                # Note: if switch_keep_on is True, then switch_apply_limit should be False
                if self.switch_apply_limit is False and self.switch_ev_connected:
                    # Only if SOC has reached Target SOC or there are no more scheduled charging
                    if (
                        self.ev_soc is not None
                        and self.ev_target_soc is not None
                        and self.ev_soc >= self.ev_target_soc
                    ):
                        # Keep charger on.
                        self.switch_keep_on_completion_time = time_now
                        turn_on_charging = True

                    if self.switch_keep_on_completion_time is not None and (
                        time_now >= self.switch_keep_on_completion_time
                    ):
                        # Keep charger on.
                        turn_on_charging = True

            # Handle conencted EV for EV controlled charging
            if self.after_ev_connected:
                self.after_ev_connected = False
                # Make sure charging command is sent
                current_value = not turn_on_charging

            _LOGGER.debug("turn_on_charging = %s", turn_on_charging)
            _LOGGER.debug("current_value = %s", current_value)
            if turn_on_charging and not current_value:
                # Turn on charging
                self.auto_charging_state = STATE_ON
                self.ev_soc_before_last_charging = self.ev_soc
                if self.scheduler.get_charging_is_planned():
                    self.switch_keep_on_completion_time = (
                        self.scheduler.get_charging_stop_time()
                    )
                await self.turn_on_charging()
            if not turn_on_charging and current_value:
                # Turn off charging
                self.auto_charging_state = STATE_OFF
                await self.turn_off_charging()

            if (
                self.scheduler.charging_stop_time is not None
                and time_now < self.scheduler.charging_stop_time
            ):
                _LOGGER.debug("Charging summary shown")
                self.sensor.charging_is_planned = (
                    self.scheduler.get_charging_is_planned()
                )
                self.sensor.charging_start_time = (
                    self.scheduler.get_charging_start_time()
                )
                self.sensor.charging_stop_time = self.scheduler.get_charging_stop_time()
                self.sensor.charging_number_of_hours = (
                    self.scheduler.get_charging_number_of_hours()
                )
                if self.sensor_status:
                    if self.low_soc_charging_state == STATE_ON:
                        self.sensor_status.set_status(CHARGING_STATUS_LOW_SOC_CHARGING)
                    elif self.low_price_charging_state == STATE_ON:
                        self.sensor_status.set_status(
                            CHARGING_STATUS_LOW_PRICE_CHARGING
                        )
                    elif self.auto_charging_state == STATE_ON:
                        self.sensor_status.set_status(CHARGING_STATUS_CHARGING)
                    else:
                        self.sensor_status.set_status(CHARGING_STATUS_WAITING_CHARGING)
            else:
                _LOGGER.debug("Charging summary removed")
                self.sensor.charging_is_planned = False
                self.sensor.charging_start_time = None
                self.sensor.charging_stop_time = None
                self.sensor.charging_number_of_hours = 0
                if self.sensor_status:
                    if not self.switch_active:
                        self.sensor_status.set_status(CHARGING_STATUS_NOT_ACTIVE)
                    elif not self.switch_ev_connected:
                        self.sensor_status.set_status(CHARGING_STATUS_DISCONNECTED)
                    elif self.low_soc_charging_state == STATE_ON:
                        self.sensor_status.set_status(CHARGING_STATUS_LOW_SOC_CHARGING)
                    elif self.low_price_charging_state == STATE_ON:
                        self.sensor_status.set_status(
                            CHARGING_STATUS_LOW_PRICE_CHARGING
                        )
                    elif self.switch_keep_on and self.auto_charging_state == STATE_ON:
                        self.sensor_status.set_status(CHARGING_STATUS_KEEP_ON)
                    elif (
                        time_now.hour >= self.ready_hour_local
                        and not self.tomorrow_valid
                    ):
                        self.sensor_status.set_status(CHARGING_STATUS_WAITING_NEW_PRICE)
                    else:
                        self.sensor_status.set_status(CHARGING_STATUS_NO_PLAN)
                self._charging_schedule = Scheduler.get_empty_schedule()
                self.sensor.charging_schedule = self._charging_schedule

    async def turn_on_charging(self, state: bool = True):
        """Turn on charging"""

        if state is True:
            _LOGGER.debug("Turn on charging")
            self.sensor.set_state(STATE_ON)
            if self.charger_switch is not None:
                _LOGGER.debug(
                    "Before service call switch.turn_on: %s", self.charger_switch
                )
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_ON,
                    target={"entity_id": self.charger_switch},
                )
        else:
            _LOGGER.debug("Turn off charging")
            self.sensor.set_state(STATE_OFF)
            if self.charger_switch is not None:
                _LOGGER.debug(
                    "Before service call switch.turn_off: %s", self.charger_switch
                )
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_OFF,
                    target={"entity_id": self.charger_switch},
                )

    async def turn_off_charging(self):
        """Turn off charging"""
        await self.turn_on_charging(False)

    async def add_sensor(self, sensors: list[EVSmartChargingSensor]):
        """Set up sensor"""
        for sensor in sensors:
            if isinstance(sensor, EVSmartChargingSensorCharging):
                self.sensor = sensor
            if isinstance(sensor, EVSmartChargingSensorStatus):
                self.sensor_status = sensor

        self.price_entity_id = get_parameter(self.config_entry, CONF_PRICE_SENSOR)
        self.price_adaptor.set_price_platform(
            get_platform(self.hass, self.price_entity_id)
        )
        self.ev_soc_entity_id = get_parameter(self.config_entry, CONF_EV_SOC_SENSOR)
        self.ev_target_soc_entity_id = get_parameter(
            self.config_entry, CONF_EV_TARGET_SOC_SENSOR
        )

        self.listeners.append(
            async_track_state_change(
                self.hass,
                [
                    self.price_entity_id,
                    self.ev_soc_entity_id,
                ],
                self.update_sensors,
            )
        )
        if len(self.ev_target_soc_entity_id) > 0:
            self.listeners.append(
                async_track_state_change(
                    self.hass,
                    [
                        self.ev_target_soc_entity_id,
                    ],
                    self.update_sensors,
                )
            )
        else:
            # Set default Target SOC when there is no sensor
            self.sensor.ev_target_soc = DEFAULT_TARGET_SOC
            self.ev_target_soc = DEFAULT_TARGET_SOC

        self._charging_schedule = Scheduler.get_empty_schedule()
        self.sensor.charging_schedule = self._charging_schedule
        await self.update_sensors()

    async def switch_active_update(self, state: bool):
        """Handle the Active switch"""
        self.switch_active = state
        _LOGGER.debug("switch_active_update = %s", state)
        await self.update_configuration()

    async def switch_apply_limit_update(self, state: bool):
        """Handle the Apply Limit switch"""
        self.switch_apply_limit = state
        _LOGGER.debug("switch_apply_limit_update = %s", state)
        # If state is True and Keep charger on is True, then turn off Keep charger on
        if state and self.switch_keep_on:
            # Get the entity_id
            if self.switch_keep_on_entity_id is None:
                self.switch_keep_on_entity_id = self.get_entity_id_from_unique_id(
                    self.switch_keep_on_unique_id
                )
            # Turn off Keep charger on
            if self.switch_keep_on_entity_id is not None:
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_OFF,
                    target={"entity_id": self.switch_keep_on_entity_id},
                )
        # If state is True and Opportunistic is True, then turn off Opportunistic
        if not state and self.switch_opportunistic:
            # Get the entity_id
            if self.switch_opportunistic_entity_id is None:
                self.switch_opportunistic_entity_id = self.get_entity_id_from_unique_id(
                    self.switch_opportunistic_unique_id
                )
            # Turn off Opportunistic
            if self.switch_opportunistic_entity_id is not None:
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_OFF,
                    target={"entity_id": self.switch_opportunistic_entity_id},
                )
        await self.update_configuration()

    async def switch_continuous_update(self, state: bool):
        """Handle the Continuous switch"""
        self.switch_continuous = state
        _LOGGER.debug("switch_continuous_update = %s", state)
        await self.update_configuration()

    async def switch_ev_connected_update(self, state: bool):
        """Handle the EV Connected switch"""
        self.switch_ev_connected = state
        _LOGGER.debug("switch_ev_connected_update = %s", state)
        if state:
            # Clear schedule when connected to charger
            self.scheduler.set_empty_schedule()
            self._charging_schedule = Scheduler.get_empty_schedule()
            self.switch_keep_on_completion_time = None
            # Make sure the charger is turned off, when connected to charger
            # and the car is used to start/stop charging.
            if self.switch_active is True:
                if get_parameter(self.config_entry, CONF_EV_CONTROLLED):
                    self.after_ev_connected = True
        else:
            # Make sure the charger is turned off, but only if smart charging is active.
            if self.switch_active is True:
                await self.turn_off_charging()
        await self.update_configuration()

    async def switch_keep_on_update(self, state: bool):
        """Handle the Keep charger on switch"""
        self.switch_keep_on = state
        _LOGGER.debug("switch_keep_on_update = %s", state)
        # If state is True and Apply price limit is True, then turn off Apply price limit
        if state and self.switch_apply_limit:
            # Get the entity_id
            if self.switch_apply_limit_entity_id is None:
                self.switch_apply_limit_entity_id = self.get_entity_id_from_unique_id(
                    self.switch_apply_limit_unique_id
                )
            # Turn off Apply price limit
            if self.switch_apply_limit_entity_id is not None:
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_OFF,
                    target={"entity_id": self.switch_apply_limit_entity_id},
                )
        # If state is True and Opportunistic is True, then turn off Opportunistic
        if state and self.switch_opportunistic:
            # Get the entity_id
            if self.switch_opportunistic_entity_id is None:
                self.switch_opportunistic_entity_id = self.get_entity_id_from_unique_id(
                    self.switch_opportunistic_unique_id
                )
            # Turn off Opportunistic
            if self.switch_opportunistic_entity_id is not None:
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_OFF,
                    target={"entity_id": self.switch_opportunistic_entity_id},
                )
        await self.update_configuration()

    async def switch_opportunistic_update(self, state: bool):
        """Handle the opportunistic charging switch"""
        self.switch_opportunistic = state
        _LOGGER.debug("switch_opportunistic_update = %s", state)
        # If state is True and Apply price limit is False, then turn on Apply price limit
        if state and not self.switch_apply_limit:
            # Get the entity_id
            if self.switch_apply_limit_entity_id is None:
                self.switch_apply_limit_entity_id = self.get_entity_id_from_unique_id(
                    self.switch_apply_limit_unique_id
                )
            # Turn on Apply price limit
            if self.switch_apply_limit_entity_id is not None:
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_ON,
                    target={"entity_id": self.switch_apply_limit_entity_id},
                )
        # If state is True and Keep charger on is True, then turn off Keep charger on
        if state and self.switch_keep_on:
            # Get the entity_id
            if self.switch_keep_on_entity_id is None:
                self.switch_keep_on_entity_id = self.get_entity_id_from_unique_id(
                    self.switch_keep_on_unique_id
                )
            # Turn off Keep charger on
            if self.switch_keep_on_entity_id is not None:
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_OFF,
                    target={"entity_id": self.switch_keep_on_entity_id},
                )
        await self.update_configuration()

    async def switch_low_price_charging_update(self, state: bool):
        """Handle the low price charging switch"""
        self.switch_low_price_charging = state
        _LOGGER.debug("switch_low_price_charging_update = %s", state)
        await self.update_configuration()

    async def switch_low_soc_charging_update(self, state: bool):
        """Handle the low SOC charging switch"""
        self.switch_low_soc_charging = state
        _LOGGER.debug("switch_low_soc_charging_update = %s", state)
        await self.update_configuration()

    async def update_configuration(self):
        """Called when the configuration has been updated"""
        await self.update_sensors(configuration_updated=True)

    @callback
    async def update_sensors(
        self,
        entity_id: str = None,
        old_state: State = None,
        new_state: State = None,
        configuration_updated: bool = False,
    ):  # pylint: disable=unused-argument
        """Price or EV sensors have been updated."""

        _LOGGER.debug("EVSmartChargingCoordinator.update_sensors()")
        _LOGGER.debug("entity_id = %s", entity_id)
        # _LOGGER.debug("old_state = %s", old_state)
        _LOGGER.debug("new_state = %s", new_state)

        # To handle non-live SOC
        if configuration_updated:
            self.ev_soc_before_last_charging = -1

        if self.price_entity_id is None:
            _LOGGER.error("Price entity id not set.")
            return

        price_state = self.hass.states.get(self.price_entity_id)
        if self.price_adaptor.is_price_state(price_state):
            self.sensor.current_price = self.price_adaptor.get_current_price(
                price_state
            )
            self.raw_today_local = self.price_adaptor.get_raw_today_local(price_state)
            self.raw_tomorrow_local = self.price_adaptor.get_raw_tomorrow_local(
                price_state
            )
            self.tomorrow_valid = self.raw_tomorrow_local.is_valid()

            # Fix to take care of Nordpool bug
            # https://github.com/custom-components/nordpool/issues/235
            if self.tomorrow_valid:
                datetime_today = self.raw_today_local.get_raw()[0]["start"]
                datetime_tomorrow = self.raw_tomorrow_local.get_raw()[0]["start"]
                if datetime_today == datetime_tomorrow:
                    _LOGGER.debug("Nordpool bug detected and avoided")
                    self.raw_tomorrow_local = Raw([])
                    self.tomorrow_valid = False

            # Change to UTC time
            self.raw_two_days = self.raw_today_local.copy().to_utc()
            self.raw_two_days.extend(self.raw_tomorrow_local.copy().to_utc())
            # Change to local time
            self.sensor.raw_two_days_local = (
                self.raw_two_days.copy().to_local().get_raw()
            )
            # To handle non-live SOC
            # Update self.ev_soc_last if new price and ready_hour == None
            if self.tomorrow_valid and not self.tomorrow_valid_previous:
                if self.ready_hour_local == READY_HOUR_NONE:
                    self.ev_soc_before_last_charging = -1
            self.tomorrow_valid_previous = self.tomorrow_valid
        else:
            _LOGGER.error("Price sensor not valid")

        ev_soc_state = self.hass.states.get(self.ev_soc_entity_id)
        if Validator.is_soc_state(ev_soc_state):
            self.sensor.ev_soc = ev_soc_state.state
            self.ev_soc = float(ev_soc_state.state)
            # To handle non-live SOC
            if self.ev_soc != self.ev_soc_previous:
                self.ev_soc_previous = self.ev_soc
                self.ev_soc_before_last_charging = -1
        else:
            _LOGGER.error("SOC sensor not valid: %s", ev_soc_state)

        if len(self.ev_target_soc_entity_id) > 0:
            ev_target_soc_state = self.hass.states.get(self.ev_target_soc_entity_id)
            if Validator.is_soc_state(ev_target_soc_state):
                self.sensor.ev_target_soc = ev_target_soc_state.state
                self.ev_target_soc = float(ev_target_soc_state.state)
            else:
                _LOGGER.error("Target SOC sensor not valid: %s", ev_target_soc_state)

        # Check if Opportunistic charging should be used
        if self.switch_opportunistic is True and (
            self.raw_two_days.last_value()
            < (self.max_price * self.number_opportunistic_level / 100.0)
        ):
            max_price = self.max_price * self.number_opportunistic_level / 100.0
        else:
            max_price = self.max_price

        scheduling_params = {
            "ev_soc": self.ev_soc,
            "ev_target_soc": self.ev_target_soc,
            "min_soc": self.number_min_soc,
            "charging_pct_per_hour": self.charging_pct_per_hour,
            "start_hour": get_start_hour_utc(
                self.start_hour_local, self.ready_hour_local
            ),
            "ready_hour": get_ready_hour_utc(self.ready_hour_local),
            "switch_active": self.switch_active,
            "switch_apply_limit": self.switch_apply_limit,
            "switch_continuous": self.switch_continuous,
            "max_price": max_price,
        }

        time_now_local = dt.now()
        time_now_hour_local = dt.now().hour

        # To handle non-live SOC
        # # To enable rescheduling after ready_hour if no live SOC is available
        if time_now_hour_local == self.ready_hour_local:
            if self.ready_hour_first:
                self.ev_soc_before_last_charging = -1
                self.ready_hour_first = False
        else:
            self.ready_hour_first = True

        not_charging = True
        if self._charging_schedule is not None:
            not_charging = (
                not self.switch_ev_connected
                or get_charging_value(self._charging_schedule) is None
                or get_charging_value(self._charging_schedule) == 0
            )
            # Handle self.switch_keep_on
            if self.switch_keep_on:
                # Only if price limit is not used and the EV is connected
                # Note: if switch_keep_on is True, then switch_apply_limit should be False
                if self.switch_apply_limit is False and self.switch_ev_connected:
                    # Only if SOC has reached Target SOC or there are no more scheduled charging
                    if (
                        self.ev_soc is not None
                        and self.ev_target_soc is not None
                        and self.ev_soc >= self.ev_target_soc
                    ):
                        # Don't reschedule due to keep_on
                        not_charging = False

                    if self.switch_keep_on_completion_time is not None and (
                        time_now_local >= self.switch_keep_on_completion_time
                    ):
                        # Don't reschedule due to keep_on
                        not_charging = False

        if (
            (self.ev_soc is not None and self.ev_target_soc is not None)
            and (self.ev_soc > self.ev_soc_before_last_charging)
            and (
                (self.ev_soc >= self.ev_target_soc)
                or (
                    (self.tomorrow_valid or time_now_hour_local < self.ready_hour_local)
                    and (not_charging or configuration_updated)
                )
            )
        ):
            self.scheduler.create_base_schedule(scheduling_params, self.raw_two_days)

        # If the ready_hour is updated to next day before next day's prices are available,
        # then remove the schedule
        if (
            not self.tomorrow_valid
            and time_now_hour_local > self.ready_hour_local
            and configuration_updated
        ):
            self.scheduler.set_empty_schedule()

        if self.scheduler.base_schedule_exists() is True:
            max_value = self.raw_two_days.max_value()
            # Make sure max_value > 0
            if max_value <= 0:
                max_value = 0.1  # pragma: no cover
            scheduling_params.update({"value_in_graph": max_value * 0.75})
            new_charging = self.scheduler.get_schedule(scheduling_params)
            if new_charging is not None:
                self._charging_schedule = new_charging
                self.sensor.charging_schedule = (
                    Raw(self._charging_schedule).copy().to_local().get_raw()
                )

        _LOGGER.debug("self._max_price = %s", self.max_price)
        _LOGGER.debug("Current price = %s", self.sensor.current_price)
        await self.update_state()  # Update the charging status

    def get_entity_id_from_unique_id(self, unique_id: str) -> str:
        """Get the Entity ID for the entity with the unique_id"""
        entity_registry: EntityRegistry = async_entity_registry_get(self.hass)
        all_entities = async_entries_for_config_entry(
            entity_registry, self.config_entry.entry_id
        )
        entity = [entity for entity in all_entities if entity.unique_id == unique_id]
        if len(entity) == 1:
            return entity[0].entity_id

        return None

    def validate_input_sensors(self) -> str:
        """Check that all input sensors returns values."""

        price = get_parameter(self.config_entry, CONF_PRICE_SENSOR)
        price_state = self.hass.states.get(price)
        if price_state is None or price_state.state is None:
            return "Input sensors not ready."

        ev_soc = get_parameter(self.config_entry, CONF_EV_SOC_SENSOR)
        ev_soc_state = self.hass.states.get(ev_soc)
        if ev_soc_state is None or ev_soc_state.state is None:
            return "Input sensors not ready."

        ev_target_soc = get_parameter(self.config_entry, CONF_EV_TARGET_SOC_SENSOR)
        if len(ev_target_soc) > 0:  # Check if the sensor exists
            ev_target_soc_state = self.hass.states.get(ev_target_soc)
            if ev_target_soc_state is None or ev_target_soc_state.state is None:
                return "Input sensors not ready."

        return None
