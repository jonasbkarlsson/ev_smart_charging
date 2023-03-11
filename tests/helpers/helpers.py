"""Helper functions"""

from homeassistant.const import STATE_OFF
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.util import dt as dt_util

from custom_components.ev_smart_charging.const import (
    PLATFORM_ENERGIDATASERVICE,
    PLATFORM_ENTSOE,
    PLATFORM_NORDPOOL,
    PLATFORM_OCPP,
    PLATFORM_VW,
    SENSOR,
    SWITCH,
)
from custom_components.ev_smart_charging.helpers.coordinator import Raw


class MockPriceEntity:
    """Mockup for price entity"""

    @staticmethod
    def create(
        hass: HomeAssistant, entity_registry: EntityRegistry, price: float = 123
    ):
        """Create a correct price entity"""
        entity_registry.async_get_or_create(
            domain=SENSOR,
            platform=PLATFORM_NORDPOOL,
            unique_id="kwh_se3_sek_2_10_0",
        )
        MockPriceEntity.set_state(hass, None, None, price)

    @staticmethod
    def set_state(
        hass: HomeAssistant,
        new_raw_today: list,
        new_raw_tomorrow: list,
        new_price: float = None,
    ):
        """Set state of MockPriceEntity"""

        # Find current price
        if new_price is None:
            new_price = "unavailable"
            if price := Raw(new_raw_today).get_value(dt_util.now()):
                new_price = price
            if price := Raw(new_raw_tomorrow).get_value(dt_util.now()):
                new_price = price

        # Set state
        hass.states.async_set(
            "sensor.nordpool_kwh_se3_sek_2_10_0",
            f"{new_price}",
            {
                "current_price": new_price,
                "raw_today": new_raw_today,
                "raw_tomorrow": new_raw_tomorrow,
            },
        )


class MockPriceEntityEnergiDataService:
    """Mockup for price entity Energi Data Service"""

    @staticmethod
    def create(
        hass: HomeAssistant, entity_registry: EntityRegistry, price: float = 123
    ):
        """Create a correct price entity"""
        entity_registry.async_get_or_create(
            domain=SENSOR,
            platform=PLATFORM_ENERGIDATASERVICE,
            unique_id="energi_data_service",
        )
        MockPriceEntityEnergiDataService.set_state(hass, None, None, price)

    @staticmethod
    def set_state(
        hass: HomeAssistant,
        new_raw_today: list,
        new_raw_tomorrow: list,
        new_price: float = None,
    ):
        """Set state of MockPriceEntity"""

        # Find current price
        if new_price is None:
            new_price = "unavailable"
            if price := Raw(new_raw_today, PLATFORM_ENERGIDATASERVICE).get_value(
                dt_util.now()
            ):
                new_price = price
            if price := Raw(new_raw_tomorrow, PLATFORM_ENERGIDATASERVICE).get_value(
                dt_util.now()
            ):
                new_price = price

        # Set state
        hass.states.async_set(
            "sensor.energidataservice_energi_data_service",
            f"{new_price}",
            {
                "current_price": new_price,
                "raw_today": new_raw_today,
                "raw_tomorrow": new_raw_tomorrow,
            },
        )


class MockPriceEntityEntsoe:
    """Mockup for price entity Entsoe"""

    @staticmethod
    def create(
        hass: HomeAssistant, entity_registry: EntityRegistry, price: float = 123
    ):
        """Create a correct price entity"""
        entity_registry.async_get_or_create(
            domain=SENSOR,
            platform=PLATFORM_ENTSOE,
            unique_id="average_electricity_price_today",
        )
        MockPriceEntityEntsoe.set_state(hass, None, None, price)

    @staticmethod
    def set_state(
        hass: HomeAssistant,
        new_raw_today: list,
        new_raw_tomorrow: list,
        new_price: float = None,
    ):
        """Set state of MockPriceEntity"""

        # Find current price
        if new_price is None:
            new_price = "unavailable"
            if price := Raw(new_raw_today, PLATFORM_ENTSOE).get_value(dt_util.now()):
                new_price = price
            if price := Raw(new_raw_tomorrow, PLATFORM_ENTSOE).get_value(dt_util.now()):
                new_price = price

        # Set state
        hass.states.async_set(
            "sensor.entsoe_average_electricity_price_today",
            f"{new_price}",
            {
                "prices_today": new_raw_today,
                "prices_tomorrow": new_raw_tomorrow,
            },
        )


class MockSOCEntity:
    """Mockup for SOC entity"""

    @staticmethod
    def create(hass: HomeAssistant, entity_registry: EntityRegistry, value: str = "55"):
        """Create a correct soc entity"""
        entity_registry.async_get_or_create(
            domain=SENSOR,
            platform=PLATFORM_VW,
            unique_id="state_of_charge",
        )
        MockSOCEntity.set_state(hass, value)

    @staticmethod
    def set_state(hass: HomeAssistant, new_state: str):
        """Set state"""
        hass.states.async_set(
            "sensor.volkswagen_we_connect_id_state_of_charge", new_state
        )


class MockTargetSOCEntity:
    """Mockup for SOC entity"""

    @staticmethod
    def create(hass: HomeAssistant, entity_registry: EntityRegistry, value: str = "80"):
        """Create a correct target soc entity"""
        entity_registry.async_get_or_create(
            domain=SENSOR,
            platform=PLATFORM_VW,
            unique_id="target_state_of_charge",
        )
        MockTargetSOCEntity.set_state(hass, value)

    @staticmethod
    def set_state(hass: HomeAssistant, new_state: str):
        """Set state"""
        hass.states.async_set(
            "sensor.volkswagen_we_connect_id_target_state_of_charge", new_state
        )


class MockChargerEntity:
    """Mockup for charger entity"""

    @staticmethod
    def create(
        hass: HomeAssistant, entity_registry: EntityRegistry, value: str = STATE_OFF
    ):
        """Create a correct charge control entity"""
        entity_registry.async_get_or_create(
            domain=SWITCH,
            platform=PLATFORM_OCPP,
            unique_id="charge_control",
        )
        MockChargerEntity.set_state(hass, value)

    @staticmethod
    def set_state(hass: HomeAssistant, new_state: str):
        """Set state"""
        hass.states.async_set("switch.ocpp_charge_control", new_state)
