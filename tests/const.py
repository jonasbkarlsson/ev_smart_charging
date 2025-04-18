"""Constants for ev_smart_charging tests."""
from custom_components.ev_smart_charging.const import (
    CONF_CHARGER_ENTITY,
    CONF_DEVICE_NAME,
    CONF_MAX_PRICE,
    CONF_MIN_SOC,
    CONF_OPPORTUNISTIC_LEVEL,
    CONF_PRICE_SENSOR,
    CONF_EV_SOC_SENSOR,
    CONF_EV_TARGET_SOC_SENSOR,
    CONF_PCT_PER_HOUR,
    CONF_READY_HOUR,
    CONF_START_HOUR,
    NAME,
)

# Mock config data to be used across multiple tests
MOCK_CONFIG_USER = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
}

MOCK_CONFIG_USER_WRONG_PRICE = {
    CONF_PRICE_SENSOR: "button.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
}

MOCK_CONFIG_USER_NO_CHARGER = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "",
}

MOCK_CONFIG_USER_WRONG_CHARGER = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "button.ocpp_charge_control",
}

MOCK_CONFIG_CHARGER = {
    CONF_PCT_PER_HOUR: 6.0,
    CONF_START_HOUR: "None",
    CONF_READY_HOUR: "08:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_CHARGER_EXTRA = {
    CONF_DEVICE_NAME: NAME,
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
}

MOCK_CONFIG_ALL_V1 = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 6.0,
    CONF_READY_HOUR: "08:00",
    CONF_MAX_PRICE: 0.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_ALL_V2 = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 6.0,
    CONF_START_HOUR: "None",
    CONF_READY_HOUR: "08:00",
    CONF_MAX_PRICE: 0.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_ALL = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 6.0,
    CONF_START_HOUR: "None",
    CONF_READY_HOUR: "08:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_LATE = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 6.0,
    CONF_START_HOUR: "None",
    CONF_READY_HOUR: "18:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_LATE24 = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 6.0,
    CONF_START_HOUR: "None",
    CONF_READY_HOUR: "00:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_NO_READY = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_HOUR: "None",
    CONF_READY_HOUR: "None",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_USER_NO_CHARGER = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "",
    CONF_PCT_PER_HOUR: 6.0,
    CONF_START_HOUR: "None",
    CONF_READY_HOUR: "08:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_NO_TARGET_SOC = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 6.0,
    CONF_START_HOUR: "None",
    CONF_READY_HOUR: "08:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_MIN_SOC = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 6.0,
    CONF_START_HOUR: "None",
    CONF_READY_HOUR: "08:00",
    CONF_MAX_PRICE: 20.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 40.0,
}

MOCK_CONFIG_TIME1 = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 6.0,
    CONF_START_HOUR: "None",
    CONF_READY_HOUR: "04:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_KEEP_ON1 = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 6.0,
    CONF_START_HOUR: "None",
    CONF_READY_HOUR: "10:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_KEEP_ON2 = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 6.0,
    CONF_START_HOUR: "None",
    CONF_READY_HOUR: "10:00",
    CONF_MAX_PRICE: 40.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_KEEP_ON_ISSUE = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 8.0,
    CONF_START_HOUR: "None",
    CONF_READY_HOUR: "12:00",
    CONF_MAX_PRICE: 100.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 40.0,
}

MOCK_CONFIG_OPPORTUNISTIC = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_HOUR: "None",
    CONF_READY_HOUR: "08:00",
    CONF_MAX_PRICE: 200.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 40.0,
}
