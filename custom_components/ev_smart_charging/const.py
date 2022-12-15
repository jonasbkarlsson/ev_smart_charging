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
ICON_MIN_SOC = "mdi:battery-charging-30"
ICON_START = "mdi:play-circle-outline"
ICON_STOP = "mdi:stop-circle-outline"

# Platforms
SENSOR = Platform.SENSOR
SWITCH = Platform.SWITCH
BUTTON = Platform.BUTTON
PLATFORMS = [SWITCH, SENSOR, BUTTON]
PLATFORM_NORDPOOL = "nordpool"
PLATFORM_VW = "volkswagen_we_connect_id"
PLATFORM_OCPP = "ocpp"

# Entity names
ENTITY_NAME_CHARGING_SENSOR = "Charging"
ENTITY_NAME_ACTIVE_SWITCH = "Smart charging activated"
ENTITY_NAME_APPLY_LIMIT_SWITCH = "Apply price limit"
ENTITY_NAME_CONTINUOUS_SWITCH = "Continuous charging preferred"
ENTITY_NAME_EV_CONNECTED_SWITCH = "EV connected"
ENTITY_NAME_START_BUTTON = "Manually start charging"
ENTITY_NAME_STOP_BUTTON = "Manually stop charging"
ENTITY_NAME_MIN_SOC_NUMBER = "Minimum SOC"

# Configuration and options
CONF_DEVICE_NAME = "device_name"
CONF_PRICE_SENSOR = "price_sensor"
CONF_EV_SOC_SENSOR = "ev_soc_sensor"
CONF_EV_TARGET_SOC_SENSOR = "ev_target_soc_sensor"
CONF_CHARGER_ENTITY = "charger_entity"
CONF_PCT_PER_HOUR = "pct_per_hour"
CONF_READY_HOUR = "ready_hour"
CONF_MAX_PRICE = "maximum_price"
CONF_MIN_SOC = "min_soc"

HOURS = [
    "00:00",
    "01:00",
    "02:00",
    "03:00",
    "04:00",
    "05:00",
    "06:00",
    "07:00",
    "08:00",
    "09:00",
    "10:00",
    "11:00",
    "12:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00",
    "18:00",
    "19:00",
    "20:00",
    "21:00",
    "22:00",
    "23:00",
]

# Defaults
DEFAULT_NAME = DOMAIN
DEFAULT_TARGET_SOC = 100

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
