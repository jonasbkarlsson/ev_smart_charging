"""Constants file"""

from homeassistant.const import Platform
from homeassistant.const import __version__ as HA_VERSION

NAME = "EV Smart Charging"
DOMAIN = "ev_smart_charging"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.1.0"
ISSUE_URL = "https://github.com/jonasbkarlsson/ev_smart_charging/issues"

# Icons
ICON = "mdi:flash"
ICON_BATTERY_50 = "mdi:battery-50"
ICON_CASH = "mdi:cash"
ICON_CONNECTION = "mdi:connection"
ICON_MIN_SOC = "mdi:battery-charging-30"
ICON_START = "mdi:play-circle-outline"
ICON_STOP = "mdi:stop-circle-outline"
ICON_TIME = "mdi:clock-time-four-outline"
ICON_TIMER = "mdi:camera-timer"

# Platforms
SENSOR = Platform.SENSOR
SWITCH = Platform.SWITCH
BUTTON = Platform.BUTTON
NUMBER = Platform.NUMBER
SELECT = Platform.SELECT
PLATFORMS = [SENSOR, SWITCH, BUTTON, NUMBER, SELECT]
PLATFORM_NORDPOOL = "nordpool"
PLATFORM_ENERGIDATASERVICE = "energidataservice"
PLATFORM_ENTSOE = "entsoe"
PLATFORM_TGE = "tge"
PLATFORM_VW = "volkswagen_we_connect_id"
PLATFORM_OCPP = "ocpp"
PLATFORM_GENERIC = "generic"

# Entity keys
ENTITY_KEY_CHARGING_SENSOR = "charging"
ENTITY_KEY_CHARGING_CURRENT_SENSOR = "charging_current"
ENTITY_KEY_CHARGING_PHASES_SENSOR = "charging_phases"
ENTITY_KEY_STATUS_SENSOR = "status"
ENTITY_KEY_SOLAR_STATUS_SENSOR = "solar_status"
ENTITY_KEY_ACTIVE_SWITCH = "smart_charging_activated"
ENTITY_KEY_APPLY_LIMIT_SWITCH = "apply_price_limit"
ENTITY_KEY_CONTINUOUS_SWITCH = "continuous_charging_preferred"
ENTITY_KEY_EV_CONNECTED_SWITCH = "ev_connected"
ENTITY_KEY_KEEP_ON_SWITCH = "keep_charger_on"
ENTITY_KEY_OPPORTUNISTIC_SWITCH = "opportunistic_charging"
ENTITY_KEY_OPPORTUNISTIC_TYPE2_SWITCH = "opportunistic_type2_charging"
ENTITY_KEY_LOW_PRICE_CHARGING_SWITCH = "low_price_charging"
ENTITY_KEY_LOW_SOC_CHARGING_SWITCH = "low_soc_charging"
ENTITY_KEY_ACTIVE_PRICE_SWITCH = "price_charging_activated"
ENTITY_KEY_ACTIVE_SOLAR_SWITCH = "solar_charging_activated"
ENTITY_KEY_START_BUTTON = "manually_start_charging"
ENTITY_KEY_STOP_BUTTON = "manually_stop_charging"
ENTITY_KEY_PHASE_SWITCH_MODE_SELECT = "phase_switch_mode"
ENTITY_KEY_CONF_PCT_PER_HOUR_NUMBER = "charging_speed"
ENTITY_KEY_CONF_MAX_PRICE_NUMBER = "electricity_price_limit"
ENTITY_KEY_CONF_OPPORTUNISTIC_LEVEL_NUMBER = "opportunistic_level"
ENTITY_KEY_CONF_OPPORTUNISTIC_TYPE2_LEVEL_NUMBER = "opportunistic_type2_level"
ENTITY_KEY_CONF_LOW_PRICE_CHARGING_NUMBER = "low_price_charging_level"
ENTITY_KEY_CONF_LOW_SOC_CHARGING_NUMBER = "low_soc_charging_level"
ENTITY_KEY_CONF_MIN_SOC_NUMBER = "minimum_ev_soc"
ENTITY_KEY_CONF_MAX_CHARGING_CURRENT_NUMBER = "max_charging_current"
ENTITY_KEY_CONF_MIN_CHARGING_CURRENT_NUMBER = "min_charging_current"
ENTITY_KEY_CONF_DEFAULT_CHARGING_CURRENT_NUMBER = "default_charging_current"
ENTITY_KEY_CONF_SOLAR_CHARGING_OFF_DELAY_NUMBER = "solar_charging_off_delay"
ENTITY_KEY_CONF_START_QUARTER = "charge_start_time"
ENTITY_KEY_CONF_READY_QUARTER = "charge_completion_time"
ENTITY_KEY_CONF_THREE_PHASE_CHARGING = "three_phase_charging"


# Configuration and options
CONF_DEVICE_NAME = "device_name"
CONF_PRICE_SENSOR = "price_sensor"
CONF_EV_SOC_SENSOR = "ev_soc_sensor"
CONF_EV_TARGET_SOC_SENSOR = "ev_target_soc_sensor"
CONF_CHARGER_ENTITY = "charger_entity"
CONF_EV_CONTROLLED = "ev_controlled"
CONF_PCT_PER_HOUR = "pct_per_hour"  # Config entity
CONF_START_QUARTER = "start_quarter"  # Config entity
CONF_READY_QUARTER = "ready_quarter"  # Config entity
CONF_MAX_PRICE = "maximum_price"  # Config entity
CONF_OPPORTUNISTIC_LEVEL = "opportunistic_level"  # Config entity
CONF_OPPORTUNISTIC_TYPE2_LEVEL = "opportunistic_type2_level"
CONF_LOW_PRICE_CHARGING_LEVEL = "low_price_charging_level"  # Config entity
CONF_LOW_SOC_CHARGING_LEVEL = "low_soc_charging_level"  # Config entity
CONF_MIN_SOC = "min_soc"  # Config entity
CONF_SOLAR_CHARGING_CONFIGURED = "solar_charging_configured"
CONF_GRID_USAGE_SENSOR = "grid_usage_sensor"
CONF_GRID_VOLTAGE = "grid_voltage"

QUARTERS = [
    "None",
    "00:00",
    "00:15",
    "00:30",
    "00:45",
    "01:00",
    "01:15",
    "01:30",
    "01:45",
    "02:00",
    "02:15",
    "02:30",
    "02:45",
    "03:00",
    "03:15",
    "03:30",
    "03:45",
    "04:00",
    "04:15",
    "04:30",
    "04:45",
    "05:00",
    "05:15",
    "05:30",
    "05:45",
    "06:00",
    "06:15",
    "06:30",
    "06:45",
    "07:00",
    "07:15",
    "07:30",
    "07:45",
    "08:00",
    "08:15",
    "08:30",
    "08:45",
    "09:00",
    "09:15",
    "09:30",
    "09:45",
    "10:00",
    "10:15",
    "10:30",
    "10:45",
    "11:00",
    "11:15",
    "11:30",
    "11:45",
    "12:00",
    "12:15",
    "12:30",
    "12:45",
    "13:00",
    "13:15",
    "13:30",
    "13:45",
    "14:00",
    "14:15",
    "14:30",
    "14:45",
    "15:00",
    "15:15",
    "15:30",
    "15:45",
    "16:00",
    "16:15",
    "16:30",
    "16:45",
    "17:00",
    "17:15",
    "17:30",
    "17:45",
    "18:00",
    "18:15",
    "18:30",
    "18:45",
    "19:00",
    "19:15",
    "19:30",
    "19:45",
    "20:00",
    "20:15",
    "20:30",
    "20:45",
    "21:00",
    "21:15",
    "21:30",
    "21:45",
    "22:00",
    "22:15",
    "22:30",
    "22:45",
    "23:00",
    "23:15",
    "23:30",
    "23:45",
]
START_QUARTER_NONE = -48 * 4  # TODO: Does this need to be changed?
READY_QUARTER_NONE = 72 * 4  # TODO: Does this need to be changed?

PHASE_SWITCH_MODE_ONE = "one_phase"
PHASE_SWITCH_MODE_THREE = "three_phases"
PHASE_SWITCH_MODE_DYNAMIC = "dynamic"

PHASE_SWITCH_MODES = [
    PHASE_SWITCH_MODE_ONE,
    PHASE_SWITCH_MODE_THREE,
    PHASE_SWITCH_MODE_DYNAMIC,
]

CHARGING_STATUS_WAITING_NEW_PRICE = "waiting_for_new_prices"
CHARGING_STATUS_NO_PLAN = "no_charging_planned"
CHARGING_STATUS_WAITING_CHARGING = "waiting_for_charging_to_begin"
CHARGING_STATUS_CHARGING = "charging"
CHARGING_STATUS_KEEP_ON = "keeping_charger_on"
CHARGING_STATUS_DISCONNECTED = "disconnected"
CHARGING_STATUS_PRICE_NOT_ACTIVE = "price_not_active"
CHARGING_STATUS_NOT_ACTIVE = "smart_charging_not_active"
CHARGING_STATUS_LOW_PRICE_CHARGING = "low_price_charging"
CHARGING_STATUS_LOW_SOC_CHARGING = "low_soc_charging"

SOLAR_CHARGING_STATUS_NOT_ACTIVATED = "not_activated"
SOLAR_CHARGING_STATUS_WAITING = "waiting"
SOLAR_CHARGING_STATUS_CHARGING = "charging"
SOLAR_CHARGING_STATUS_PHASE_SWITCHING = "phase_switching"
SOLAR_CHARGING_STATUS_CHARGING_COMPLETED = "charging_completed"

# Defaults
DEFAULT_NAME = DOMAIN
DEFAULT_TARGET_SOC = 100
DEFAULT_PHASE_SWITCH_DELAY = 90

DEBUG = False

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
Home Assistant: {HA_VERSION}
-------------------------------------------------------------------
"""
