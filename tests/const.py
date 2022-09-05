"""Constants for ev_smart_charging tests."""
from custom_components.ev_smart_charging.const import (
    CONF_NORDPOOL_SENSOR,
    CONF_EV_SOC_SENSOR,
    CONF_EV_TARGET_SOC_SENSOR,
)

# Mock config data to be used across multiple tests
MOCK_CONFIG = {
    CONF_NORDPOOL_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.id_4_gtx_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "number.id_4_gtx_target_state_of_charge",
}
