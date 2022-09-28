"""Constants for ev_smart_charging/helpers tests."""
from custom_components.ev_smart_charging.const import (
    CONF_MIN_SOC,
    CONF_PCT_PER_HOUR,
)

MOCK_CONFIG_DATA = {
    CONF_PCT_PER_HOUR: 6.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_OPTIONS = {
    CONF_PCT_PER_HOUR: 8.0,
}
