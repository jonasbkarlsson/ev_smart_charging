"""Constants file"""

NAME = "EV Smart Charging"
DOMAIN = "ev_smart_charging"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.1.0"
ISSUE_URL = "https://github.com/jonasbkarlsson/ev_smart_charging/issues"

# Icons
ICON = "mdi:flash"

# Platforms
SENSOR = "sensor"
PLATFORMS = [SENSOR]
PLATFORM_NORDPOOL = "nordpool"
PLATFORM_VW = "volkswagen_we_connect_id"

# Configuration and options
CONF_NORDPOOL_SENSOR = "nordpool_sensor"
CONF_EV_SOC_SENSOR = "ev_soc_sensor"
CONF_EV_TARGET_SOC_SENSOR = "ev_target_soc_sensor"

# Defaults
DEFAULT_NAME = DOMAIN

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

# Events
EVENT_NEW_HOUR = "ev_smart_charger_new_hour"
