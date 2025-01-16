"""Constants for ev_smart_charging/coordinator tests."""

from custom_components.ev_smart_charging.const import (
    CONF_CHARGER_ENTITY,
    CONF_MAX_PRICE,
    CONF_MIN_SOC,
    CONF_OPPORTUNISTIC_LEVEL,
    CONF_PRICE_SENSOR,
    CONF_EV_SOC_SENSOR,
    CONF_EV_TARGET_SOC_SENSOR,
    CONF_PCT_PER_HOUR,
    CONF_READY_QUARTER,
    CONF_START_QUARTER,
)

MOCK_CONFIG_START_QUARTER_1A = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_QUARTER: "03:00",
    CONF_READY_QUARTER: "12:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_QUARTER_1B = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_QUARTER: "09:00",
    CONF_READY_QUARTER: "22:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_QUARTER_1C = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_QUARTER: "15:00",
    CONF_READY_QUARTER: "22:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_QUARTER_2A = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_QUARTER: "12:00",
    CONF_READY_QUARTER: "03:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_QUARTER_2B = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_QUARTER: "22:00",
    CONF_READY_QUARTER: "09:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_QUARTER_2C = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_QUARTER: "22:00",
    CONF_READY_QUARTER: "15:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_QUARTER_3A = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_QUARTER: "10:00",
    CONF_READY_QUARTER: "10:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_QUARTER_3B = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_QUARTER: "18:00",
    CONF_READY_QUARTER: "18:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_QUARTER_4A = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_QUARTER: "10:00",
    CONF_READY_QUARTER: "None",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_QUARTER_4B = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_QUARTER: "18:00",
    CONF_READY_QUARTER: "None",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}
