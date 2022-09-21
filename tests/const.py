"""Constants for ev_smart_charging tests."""
from custom_components.ev_smart_charging.const import (
    CHARGER_TYPE_OCPP,
    CONF_CHARGER_ENTITY,
    CONF_CHARGER_TYPE,
    CONF_DEVICE_NAME,
    CONF_MAX_PRICE,
    CONF_NORDPOOL_SENSOR,
    CONF_EV_SOC_SENSOR,
    CONF_EV_TARGET_SOC_SENSOR,
    CONF_PCT_PER_HOUR,
    CONF_READY_HOUR,
    NAME,
)

# Mock config data to be used across multiple tests
MOCK_CONFIG_USER = {
    CONF_NORDPOOL_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.id_4_gtx_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "number.id_4_gtx_target_state_of_charge",
    CONF_CHARGER_TYPE: CHARGER_TYPE_OCPP,
    CONF_CHARGER_ENTITY: "switch.charger_charge_control",
}

MOCK_CONFIG_CHARGER = {
    CONF_PCT_PER_HOUR: 6.0,
    CONF_READY_HOUR: "08:00",
    CONF_MAX_PRICE: 0.0,
}

MOCK_CONFIG_CHARGER_EXTRA = {
    CONF_DEVICE_NAME: NAME,
    CONF_PCT_PER_HOUR: 6.0,
    CONF_READY_HOUR: "08:00",
    CONF_MAX_PRICE: 0.0,
}

MOCK_CONFIG_ALL = {
    CONF_NORDPOOL_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.id_4_gtx_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "number.id_4_gtx_target_state_of_charge",
    CONF_CHARGER_TYPE: CHARGER_TYPE_OCPP,
    CONF_CHARGER_ENTITY: "switch.charger_charge_control",
    CONF_PCT_PER_HOUR: 6.0,
    CONF_READY_HOUR: "08:00",
    CONF_MAX_PRICE: 0.0,
}
