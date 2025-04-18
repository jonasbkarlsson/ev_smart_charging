"""Helper classes for tests"""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.ev_smart_charging.const import (
    PLATFORM_ENERGIDATASERVICE,
    PLATFORM_GESPOT,
    PLATFORM_NORDPOOL,
    PLATFORM_OCPP,
    PLATFORM_VW,
    SENSOR,
    SWITCH,
)


class MockPriceEntity:
    """Mock price entity"""

    @staticmethod
    def create(hass: HomeAssistant, entity_registry: EntityRegistry):
        """Create a mock price entity"""
        entity_registry.async_get_or_create(
            domain=SENSOR,
            platform=PLATFORM_NORDPOOL,
            unique_id="kwh_se3_sek_2_10_0",
        )
        assert entity_registry.async_is_registered("sensor.nordpool_kwh_se3_sek_2_10_0")
        hass.states.async_set(
            "sensor.nordpool_kwh_se3_sek_2_10_0",
            "123",
            {
                "current_price": 123,
                "raw_today": [
                    {
                        "value": 123,
                        "start": "2022-09-30T00:00:00+02:00",
                        "end": "2022-09-30T01:00:00+02:00",
                    }
                ],
                "raw_tomorrow": [
                    {
                        "value": 123,
                        "start": "2022-10-01T00:00:00+02:00",
                        "end": "2022-10-01T01:00:00+02:00",
                    }
                ],
            },
        )


class MockPriceEntityEnergiDataService:
    """Mock price entity for Energi Data Service"""

    @staticmethod
    def create(hass: HomeAssistant, entity_registry: EntityRegistry):
        """Create a mock price entity"""
        entity_registry.async_get_or_create(
            domain=SENSOR,
            platform=PLATFORM_ENERGIDATASERVICE,
            unique_id="kwh_dk1_dkk_2_10_0",
        )
        assert entity_registry.async_is_registered(
            "sensor.energidataservice_kwh_dk1_dkk_2_10_0"
        )
        hass.states.async_set(
            "sensor.energidataservice_kwh_dk1_dkk_2_10_0",
            "123",
            {
                "current_price": 123,
                "raw_today": [
                    {
                        "hour": "2022-09-30T00:00:00+02:00",
                        "price": 123,
                    }
                ],
                "raw_tomorrow": [
                    {
                        "hour": "2022-10-01T00:00:00+02:00",
                        "price": 123,
                    }
                ],
            },
        )


class MockPriceEntityGESpot:
    """Mock price entity for GE-Spot"""

    @staticmethod
    def create(hass: HomeAssistant, entity_registry: EntityRegistry):
        """Create a mock price entity"""
        entity_registry.async_get_or_create(
            domain=SENSOR,
            platform=PLATFORM_GESPOT,
            unique_id="kwh_se3_sek_2_10_0",
        )
        assert entity_registry.async_is_registered(
            "sensor.ge_spot_kwh_se3_sek_2_10_0"
        )
        hass.states.async_set(
            "sensor.ge_spot_kwh_se3_sek_2_10_0",
            "123",
            {
                "current_price": 123,
                "raw_today": [
                    {
                        "value": 123,
                        "start": "2022-09-30T00:00:00+02:00",
                        "end": "2022-09-30T01:00:00+02:00",
                    }
                ],
                "raw_tomorrow": [
                    {
                        "value": 123,
                        "start": "2022-10-01T00:00:00+02:00",
                        "end": "2022-10-01T01:00:00+02:00",
                    }
                ],
            },
        )


class MockSOCEntity:
    """Mock SOC entity"""

    @staticmethod
    def create(hass: HomeAssistant, entity_registry: EntityRegistry):
        """Create a mock SOC entity"""
        entity_registry.async_get_or_create(
            domain=SENSOR,
            platform=PLATFORM_VW,
            unique_id="state_of_charge",
        )
        assert entity_registry.async_is_registered(
            "sensor.volkswagen_we_connect_id_state_of_charge"
        )
        hass.states.async_set(
            "sensor.volkswagen_we_connect_id_state_of_charge",
            "55",
        )


class MockTargetSOCEntity:
    """Mock Target SOC entity"""

    @staticmethod
    def create(hass: HomeAssistant, entity_registry: EntityRegistry):
        """Create a mock Target SOC entity"""
        entity_registry.async_get_or_create(
            domain=SENSOR,
            platform=PLATFORM_VW,
            unique_id="target_state_of_charge",
        )
        assert entity_registry.async_is_registered(
            "sensor.volkswagen_we_connect_id_target_state_of_charge"
        )
        hass.states.async_set(
            "sensor.volkswagen_we_connect_id_target_state_of_charge",
            "80",
        )


class MockChargerEntity:
    """Mock Charger entity"""

    @staticmethod
    def create(hass: HomeAssistant, entity_registry: EntityRegistry):
        """Create a mock Charger entity"""
        entity_registry.async_get_or_create(
            domain=SWITCH,
            platform=PLATFORM_OCPP,
            unique_id="charge_control",
        )
        assert entity_registry.async_is_registered("switch.ocpp_charge_control")
        hass.states.async_set(
            "switch.ocpp_charge_control",
            "off",
        )
