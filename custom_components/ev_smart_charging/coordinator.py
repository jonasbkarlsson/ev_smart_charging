"""Coordinator for EV Smart Charging"""

from datetime import datetime
import logging
from homeassistant.config_entries import (
    ConfigEntry,
)
from homeassistant.const import (
    SERVICE_TURN_ON,
    SERVICE_TURN_OFF,
    MAJOR_VERSION,
    MINOR_VERSION,
)

from homeassistant.core import (
    HomeAssistant,
    State,
    callback,
    Event,
)

try:
    from homeassistant.core import (  # pylint: disable=no-name-in-module, unused-import
        EventStateChangedData,
    )
except ImportError:

    class EventStateChangedData:
        """Dummy class for HA 2024.5.4 and older."""


from homeassistant.helpers.device_registry import EVENT_DEVICE_REGISTRY_UPDATED
from homeassistant.helpers.device_registry import async_get as async_device_registry_get
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change,
    async_track_time_change,
    async_track_state_change_event,
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
    CONF_OPPORTUNISTIC_TYPE2_LEVEL,
    CONF_PCT_PER_HOUR,
    CONF_READY_QUARTER,
    CONF_PRICE_SENSOR,
    CONF_EV_SOC_SENSOR,
    CONF_EV_TARGET_SOC_SENSOR,
    CONF_START_QUARTER,
    DEFAULT_TARGET_SOC,
    READY_QUARTER_NONE,
    START_QUARTER_NONE,
    SWITCH,
)
from .helpers.coordinator import (
    Scheduler,
    get_charging_value,
    get_ready_quarter_utc,
    get_start_quarter_utc,
)
from .helpers.raw import Raw
from .helpers.general import Utils, Validator, get_parameter, get_quarter_index
from .sensor import (
    EVSmartChargingSensor,
    EVSmartChargingSensorCharging,
    EVSmartChargingSensorStatus,
)

_LOGGER = logging.getLogger(__name__)


class ChargerSwitch:
    """Charger switch class"""

    def __init__(self, hass, entity_id: str) -> None:
        """Initialize."""

        self.entity_id = entity_id
        self.domain = None

        if len(entity_id) > 0:
            entity = hass.states.get(entity_id)
            if entity and entity.domain:
                self.domain = entity.domain


class EVSmartChargingCoordinator:
    """Coordinator class"""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize."""
        self.hass = hass
        self.config_entry = config_entry
        self.platforms = []
        self.listeners = []
        self.setup_timestamp = None

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
        self.switch_opportunistic_type2 = None
        self.switch_opportunistic_type2_entity_id = None
        self.switch_opportunistic_type2_unique_id = None
        self.price_entity_id = None
        self.price_adaptor = PriceAdaptor()
        self.ev_soc_entity_id = None
        self.ev_target_soc_entity_id = None

        self.charger_switch = ChargerSwitch(
            hass, get_parameter(self.config_entry, CONF_CHARGER_ENTITY)
        )

        self.scheduler = Scheduler()

        self.ev_soc = None
        self.ev_soc_before_last_charging = -1
        self.ev_soc_previous = -1
        self.ev_target_soc = None
        self.raw_today_local = None
        self.raw_tomorrow_local = None
        self.tomorrow_valid = False
        self.tomorrow_valid_previous = False

        self.ev_soc_valid = False
        self.ev_target_soc_valid = False
        self.opportunistic_feature_triggered = False

        self.raw_two_days = None
        self._charging_schedule = None
        self.charging_pct_per_hour = get_parameter(
            self.config_entry, CONF_PCT_PER_HOUR, 6.0
        )

        self.start_quarter_local = get_quarter_index(
            get_parameter(self.config_entry, CONF_START_QUARTER)
        )
        if self.start_quarter_local is None:
            self.start_quarter_local = START_QUARTER_NONE

        self.ready_quarter_local = get_quarter_index(
            get_parameter(self.config_entry, CONF_READY_QUARTER, "08:00")
        )
        if self.ready_quarter_local is None:
            self.ready_quarter_local = READY_QUARTER_NONE
        if self.ready_quarter_local == 0:
            # Treat 00:00 as 24:00
            self.ready_quarter_local = 24 * 4
        self.ready_quarter_first = (
            True  # True for first update_sensor the ready_quarter
        )

        self.max_price = float(get_parameter(self.config_entry, CONF_MAX_PRICE, 0.0))
        self.number_min_soc = int(get_parameter(self.config_entry, CONF_MIN_SOC, 0.0))
        self.number_opportunistic_level = int(
            get_parameter(self.config_entry, CONF_OPPORTUNISTIC_LEVEL, 50.0)
        )
        self.number_opportunistic_type2_level = int(
            get_parameter(self.config_entry, CONF_OPPORTUNISTIC_TYPE2_LEVEL, 90.0)
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

        # Update state once per quarter.
        self.listeners.append(
            async_track_time_change(
                hass, self.update_quarterly, minute=[0, 15, 30, 45], second=0
            )
        )
        # Listen for changes to the device.
        self.listeners.append(
            hass.bus.async_listen(EVENT_DEVICE_REGISTRY_UPDATED, self.device_updated)
        )
        # Update state once after intitialization
        self.listeners.append(async_call_later(hass, 10.0, self.update_initial))

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
    async def update_quarterly(
        self, date_time: datetime = None
    ):  # pylint: disable=unused-argument
        """Called every quarter"""
        _LOGGER.debug("EVSmartChargingCoordinator.update_quarterly()")
        await self.update_sensors()

    @callback
    async def update_initial(
        self, date_time: datetime = None
    ):  # pylint: disable=unused-argument
        """Called once"""
        _LOGGER.debug("EVSmartChargingCoordinator.update_initial()")
        await self.update_configuration()

    def is_during_intialization(self) -> bool:
        """Checks if the integration is being intialized"""
        # Assumes initialization takes less than 5 seconds.
        now_timestamp = dt.now().timestamp()
        time_since_start = now_timestamp - self.setup_timestamp
        return time_since_start < 5

    @callback
    async def update_state(
        self, date_time: datetime = None
    ):  # pylint: disable=unused-argument
        """Called every quarter"""
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

            # Don't turn on charging if initialization is not complete.
            # Initialization is assumed to be finished in 5 seconds.
            if self.is_during_intialization():
                turn_on_charging = False
                _LOGGER.debug("is_during_intialization() = True")

            # Handle connected EV for EV controlled charging
            if self.after_ev_connected and not self.is_during_intialization():
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
                self.sensor.charging_number_of_quarters = (
                    self.scheduler.get_charging_number_of_quarters()
                )
                if self.sensor_status:
                    if not self.switch_ev_connected:
                        self.sensor_status.set_status(CHARGING_STATUS_DISCONNECTED)
                    elif self.low_soc_charging_state == STATE_ON:
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
                self.sensor.charging_number_of_quarters = 0
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
                        Utils.datetime_quarter(time_now) >= self.ready_quarter_local
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
            if (
                self.charger_switch.entity_id is not None
                and self.charger_switch.domain is not None
            ):
                _LOGGER.debug(
                    "Before service call switch.turn_on: %s",
                    self.charger_switch.entity_id,
                )
                await self.hass.services.async_call(
                    domain=self.charger_switch.domain,
                    service=SERVICE_TURN_ON,
                    target={"entity_id": self.charger_switch.entity_id},
                )
        else:
            _LOGGER.debug("Turn off charging")
            self.sensor.set_state(STATE_OFF)
            if (
                self.charger_switch.entity_id is not None
                and self.charger_switch.domain is not None
            ):
                _LOGGER.debug(
                    "Before service call switch.turn_off: %s",
                    self.charger_switch.entity_id,
                )
                await self.hass.services.async_call(
                    domain=self.charger_switch.domain,
                    service=SERVICE_TURN_OFF,
                    target={"entity_id": self.charger_switch.entity_id},
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
        price_state = self.hass.states.get(self.price_entity_id)
        self.price_adaptor.initiate(price_state)
        self.ev_soc_entity_id = get_parameter(self.config_entry, CONF_EV_SOC_SENSOR)
        self.ev_target_soc_entity_id = get_parameter(
            self.config_entry, CONF_EV_TARGET_SOC_SENSOR
        )

        if MAJOR_VERSION <= 2023 or (MAJOR_VERSION == 2024 and MINOR_VERSION <= 5):
            # Use for Home Assistant 2024.5 or older
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
        else:
            # Use for Home Assistant 2024.6 or newer
            self.listeners.append(
                async_track_state_change_event(
                    self.hass,
                    [
                        self.price_entity_id,
                        self.ev_soc_entity_id,
                    ],
                    self.update_sensors_new,
                )
            )
        if len(self.ev_target_soc_entity_id) > 0:
            if MAJOR_VERSION <= 2023 or (MAJOR_VERSION == 2024 and MINOR_VERSION <= 5):
                # Use for Home Assistant 2024.5 or older
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
                # Use for Home Assistant 2024.6 or newer
                self.listeners.append(
                    async_track_state_change_event(
                        self.hass,
                        [
                            self.ev_target_soc_entity_id,
                        ],
                        self.update_sensors_new,
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

    def get_all_entity_ids(self):
        """Get all entity ids from unique ids"""

        if self.switch_apply_limit_entity_id is None:
            self.switch_apply_limit_entity_id = self.get_entity_id_from_unique_id(
                self.switch_apply_limit_unique_id
            )
        if self.switch_keep_on_entity_id is None:
            self.switch_keep_on_entity_id = self.get_entity_id_from_unique_id(
                self.switch_keep_on_unique_id
            )
        if self.switch_opportunistic_entity_id is None:
            self.switch_opportunistic_entity_id = self.get_entity_id_from_unique_id(
                self.switch_opportunistic_unique_id
            )
        if self.switch_opportunistic_type2_entity_id is None:
            self.switch_opportunistic_type2_entity_id = (
                self.get_entity_id_from_unique_id(
                    self.switch_opportunistic_type2_unique_id
                )
            )

    async def switch_apply_limit_update(self, state: bool):
        """Handle the Apply Limit switch"""
        self.switch_apply_limit = state
        _LOGGER.debug("switch_apply_limit_update = %s", state)
        self.get_all_entity_ids()
        # If state is True and Keep charger on is True, then turn off Keep charger on
        if state and self.switch_keep_on:
            # Turn off Keep charger on
            if self.switch_keep_on_entity_id is not None:
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_OFF,
                    target={"entity_id": self.switch_keep_on_entity_id},
                )
        # If state is False and Opportunistic is True, then turn off Opportunistic
        if not state and self.switch_opportunistic:
            # Turn off Opportunistic
            if self.switch_opportunistic_entity_id is not None:
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_OFF,
                    target={"entity_id": self.switch_opportunistic_entity_id},
                )
        # If state is True and the price limit is set to zero,
        # then make a notification to warn the user.
        if state and self.max_price == 0 and not self.is_during_intialization():
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": "Apply price limit is turn on, but the price limit is set to zero.",
                    "title": "EV Smart Charging",
                },
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
        self.get_all_entity_ids()
        # If state is True and Opportunistic is True, then turn off Opportunistic
        if state and self.switch_opportunistic:
            # Turn off Opportunistic
            if self.switch_opportunistic_entity_id is not None:
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_OFF,
                    target={"entity_id": self.switch_opportunistic_entity_id},
                )
        # If state is True and Opportunistic Type2 is True, then turn off Opportunistic Type2
        if state and self.switch_opportunistic_type2:
            # Turn off Opportunistic Type2
            if self.switch_opportunistic_type2_entity_id is not None:
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_OFF,
                    target={"entity_id": self.switch_opportunistic_type2_entity_id},
                )
        # If state is True and Apply price limit is True, then turn off Apply price limit
        if state and self.switch_apply_limit:
            # Turn off Apply price limit
            if self.switch_apply_limit_entity_id is not None:
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_OFF,
                    target={"entity_id": self.switch_apply_limit_entity_id},
                )
        await self.update_configuration()

    async def switch_opportunistic_update(self, state: bool):
        """Handle the opportunistic charging switch"""
        turn_on_apply_price_limit = False
        turn_off_keep_charger_on = False
        turn_off_opportunistic_type2 = False

        self.switch_opportunistic = state
        _LOGGER.debug("switch_opportunistic_update = %s", state)
        self.get_all_entity_ids()

        # If state is True and Apply price limit is False, then turn on Apply price limit
        if state and not self.switch_apply_limit:
            turn_on_apply_price_limit = True

        # If state is True and Keep charger on is True, then turn off Keep charger on
        if state and self.switch_keep_on:
            turn_off_keep_charger_on = True

        # If state is True and Opportunistic Type2 is True, then turn off Opportunistic Type2
        if state and self.switch_opportunistic_type2:
            turn_off_opportunistic_type2 = True

        if turn_on_apply_price_limit:
            # Turn on Apply price limit
            if self.switch_apply_limit_entity_id is not None:
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_ON,
                    target={"entity_id": self.switch_apply_limit_entity_id},
                )

        if turn_off_keep_charger_on:
            # Turn off Keep charger on
            if self.switch_keep_on_entity_id is not None:
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_OFF,
                    target={"entity_id": self.switch_keep_on_entity_id},
                )

        if turn_off_opportunistic_type2:
            # Turn off Opportunistic Type2
            if self.switch_opportunistic_type2_entity_id is not None:
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_OFF,
                    target={"entity_id": self.switch_opportunistic_type2_entity_id},
                )

        await self.update_configuration()

    async def switch_opportunistic_type2_update(self, state: bool):
        """Handle the opportunistic type2 switch"""

        self.switch_opportunistic_type2 = state
        _LOGGER.debug("switch_opportunistic_type2_update = %s", state)
        self.get_all_entity_ids()
        # If state is True and Keep charger on is True, then turn off Keep charger on
        if state and self.switch_keep_on:
            # Turn off Keep charger on
            if self.switch_keep_on_entity_id is not None:
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_OFF,
                    target={"entity_id": self.switch_keep_on_entity_id},
                )
        # If state is True and Opportunistic is True, then turn off Opportunistic
        if state and self.switch_opportunistic:
            # Turn off Opportunistic
            if self.switch_opportunistic_entity_id is not None:
                await self.hass.services.async_call(
                    domain=SWITCH,
                    service=SERVICE_TURN_OFF,
                    target={"entity_id": self.switch_opportunistic_entity_id},
                )
        await self.update_configuration()

    async def switch_low_price_charging_update(self, state: bool):
        """Handle the low price charging switch"""
        self.switch_low_price_charging = state
        _LOGGER.debug("switch_low_price_charging_update = %s", state)
        # If state is True and low price charging level is set to zero,
        # then make a notification to warn the user.
        if (
            state
            and self.low_price_charging == 0
            and not self.is_during_intialization()
        ):
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": "Low price charging is turn on, "
                    "but the low price charging level is set to zero.",
                    "title": "EV Smart Charging",
                },
            )
        await self.update_configuration()

    async def switch_low_soc_charging_update(self, state: bool):
        """Handle the low SOC charging switch"""
        self.switch_low_soc_charging = state
        _LOGGER.debug("switch_low_soc_charging_update = %s", state)
        # If state is True and low SOC charging level is set to zero,
        # then make a notification to warn the user.
        if state and self.low_soc_charging == 0 and not self.is_during_intialization():
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": "Low SOC charging is turn on, "
                    "but the low SOC charging level is set to zero.",
                    "title": "EV Smart Charging",
                },
            )
        await self.update_configuration()

    async def update_configuration(self):
        """Called when the configuration has been updated"""
        await self.update_sensors(configuration_updated=True)

    @callback
    async def update_sensors_new(
        self,
        event: Event,  # Event[EventStateChangedData]
        configuration_updated: bool = False,
    ):  # pylint: disable=unused-argument
        """Price or EV sensors have been updated.
        EventStateChangedData is supported from Home Assistant 2024.5.5"""

        # Allowed from HA 2024.4
        entity_id = event.data["entity_id"]
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]

        await self.update_sensors(
            entity_id=entity_id,
            old_state=old_state,
            new_state=new_state,
            configuration_updated=configuration_updated,
        )

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

        # Update schedule and reset keep_on if EV SOC Target is updated
        if self.ev_target_soc_entity_id and (entity_id == self.ev_target_soc_entity_id):
            configuration_updated = True
            self.switch_keep_on_completion_time = None

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
            # Update self.ev_soc_last if new price and ready_quarter == None
            if self.tomorrow_valid and not self.tomorrow_valid_previous:
                if self.ready_quarter_local == READY_QUARTER_NONE:
                    self.ev_soc_before_last_charging = -1
            self.tomorrow_valid_previous = self.tomorrow_valid
        else:
            # If the problem occured directly after midnight, ignore it.
            # Most likely due to the price entity updating its state in multiple steps,
            # resulting in invalid information before all the updates have been done.
            if dt.now().hour == 0 and dt.now().minute < 10:
                _LOGGER.debug(
                    "Price sensor not valid directly after midnight. "
                    "Can usually be ignored."
                )
                _LOGGER.debug("Price state: %s", price_state)
            else:
                _LOGGER.error("Price sensor not valid")
                _LOGGER.error("Price state: %s", price_state)

        ev_soc_state = self.hass.states.get(self.ev_soc_entity_id)
        if Validator.is_soc_state(ev_soc_state):
            self.ev_soc_valid = True
            self.sensor.ev_soc = ev_soc_state.state
            self.ev_soc = float(ev_soc_state.state)
            # To handle non-live SOC
            if self.ev_soc != self.ev_soc_previous:
                self.ev_soc_previous = self.ev_soc
                self.ev_soc_before_last_charging = -1
        else:
            if self.ev_soc_valid:
                # Make only one error message per outage.
                _LOGGER.error("SOC sensor not valid: %s", ev_soc_state)
            self.ev_soc_valid = False

        if len(self.ev_target_soc_entity_id) > 0:
            ev_target_soc_state = self.hass.states.get(self.ev_target_soc_entity_id)
            if Validator.is_soc_state(ev_target_soc_state):
                self.ev_target_soc_valid = True
                self.sensor.ev_target_soc = ev_target_soc_state.state
                self.ev_target_soc = float(ev_target_soc_state.state)
            else:
                if self.ev_target_soc_valid:
                    # Make only one error message per outage.
                    _LOGGER.error(
                        "Target SOC sensor not valid: %s", ev_target_soc_state
                    )
                self.ev_target_soc_valid = False

        # Check if Opportunistic charging should be used
        if (
            self.switch_opportunistic is True
            and self.raw_two_days
            and (
                self.raw_two_days.last_value()
                < (self.max_price * self.number_opportunistic_level / 100.0)
            )
        ):
            max_price = self.max_price * self.number_opportunistic_level / 100.0
            self.opportunistic_feature_triggered = True
        else:
            max_price = self.max_price
            self.opportunistic_feature_triggered = False

        # Check if Opportunistic type2 charging should be used
        if self.switch_opportunistic_type2 is True and self.raw_two_days:
            if self.raw_two_days.last_value() >= 0:
                max_price = (
                    self.raw_two_days.last_value()
                    * self.number_opportunistic_type2_level
                    / 100.0
                )
            else:
                max_price = (
                    self.raw_two_days.last_value()
                    * (200 - self.number_opportunistic_type2_level)
                    / 100.0
                )
            self.opportunistic_feature_triggered = True
            if self.switch_apply_limit:
                if self.max_price < max_price:
                    max_price = self.max_price
                    self.opportunistic_feature_triggered = False

        if self.sensor.opportunistic != self.opportunistic_feature_triggered:
            self.sensor.opportunistic = self.opportunistic_feature_triggered

        scheduling_params = {
            "ev_soc": self.ev_soc,
            "ev_target_soc": self.ev_target_soc,
            "min_soc": self.number_min_soc,
            "charging_pct_per_hour": self.charging_pct_per_hour,
            "start_quarter": get_start_quarter_utc(
                self.start_quarter_local, self.ready_quarter_local
            ),
            "ready_quarter": get_ready_quarter_utc(self.ready_quarter_local),
            "switch_active": self.switch_active,
            "switch_apply_limit": self.switch_apply_limit
            or self.opportunistic_feature_triggered,
            "switch_continuous": self.switch_continuous,
            "max_price": max_price,
        }

        time_now_local = dt.now()
        time_now_quarter_local = Utils.datetime_quarter(dt.now())

        # To handle non-live SOC
        # # To enable rescheduling after ready_quarter if no live SOC is available
        if time_now_quarter_local == self.ready_quarter_local:
            if self.ready_quarter_first:
                self.ev_soc_before_last_charging = -1
                self.ready_quarter_first = False
        else:
            self.ready_quarter_first = True

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
                    (
                        self.tomorrow_valid
                        or time_now_quarter_local < self.ready_quarter_local
                    )
                    and (not_charging or configuration_updated)
                )
            )
        ):
            if self.raw_two_days is not None:
                self.scheduler.create_base_schedule(
                    scheduling_params, self.raw_two_days
                )
            else:
                _LOGGER.debug(
                    "Deferring schedule creation: price data not yet available"
                )

        # If the ready_quarter is updated to next day before next day's prices are available,
        # then remove the schedule
        if (
            not self.tomorrow_valid
            and time_now_quarter_local > self.ready_quarter_local
            and configuration_updated
        ):
            self.scheduler.set_empty_schedule()

        if (
            self.scheduler.base_schedule_exists() is True
            and self.raw_two_days is not None
        ):
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

    def validate_control_entities(self) -> str:
        """Check that all control entities are ready."""

        if self.charger_switch.entity_id:
            if self.charger_switch.domain is None:
                return "Control entities not ready."

        return None
