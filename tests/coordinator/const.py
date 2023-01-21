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
    CONF_READY_HOUR,
    CONF_START_HOUR,
)

MOCK_CONFIG_START_HOUR_1A = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_HOUR: "03:00",
    CONF_READY_HOUR: "12:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_HOUR_1B = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_HOUR: "09:00",
    CONF_READY_HOUR: "22:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_HOUR_1C = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_HOUR: "15:00",
    CONF_READY_HOUR: "22:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_HOUR_2A = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_HOUR: "12:00",
    CONF_READY_HOUR: "03:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_HOUR_2B = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_HOUR: "22:00",
    CONF_READY_HOUR: "09:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_HOUR_2C = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_HOUR: "22:00",
    CONF_READY_HOUR: "15:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_HOUR_3A = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_HOUR: "10:00",
    CONF_READY_HOUR: "10:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_HOUR_3B = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_HOUR: "18:00",
    CONF_READY_HOUR: "18:00",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_HOUR_4A = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_HOUR: "10:00",
    CONF_READY_HOUR: "None",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}

MOCK_CONFIG_START_HOUR_4B = {
    CONF_PRICE_SENSOR: "sensor.nordpool_kwh_se3_sek_2_10_0",
    CONF_EV_SOC_SENSOR: "sensor.volkswagen_we_connect_id_state_of_charge",
    CONF_EV_TARGET_SOC_SENSOR: "sensor.volkswagen_we_connect_id_target_state_of_charge",
    CONF_CHARGER_ENTITY: "switch.ocpp_charge_control",
    CONF_PCT_PER_HOUR: 3.0,
    CONF_START_HOUR: "18:00",
    CONF_READY_HOUR: "None",
    CONF_MAX_PRICE: 0.0,
    CONF_OPPORTUNISTIC_LEVEL: 50.0,
    CONF_MIN_SOC: 30.0,
}
