"""Test ev_smart_charging number."""
from unittest.mock import patch
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.components.number import NumberExtraStoredData

from custom_components.ev_smart_charging import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ev_smart_charging.const import (
    CONF_MAX_PRICE,
    CONF_MIN_SOC,
    CONF_OPPORTUNISTIC_LEVEL,
    CONF_PCT_PER_HOUR,
    DOMAIN,
    NUMBER,
)
from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.number import (
    EVSmartChargingNumberChargingSpeed,
    EVSmartChargingNumberOpportunistic,
    EVSmartChargingNumberPriceLimit,
    EVSmartChargingNumberMinSOC,
)

from .const import MOCK_CONFIG_ALL, MOCK_CONFIG_MIN_SOC

# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
# side of the assertion matches with the right side.


# pylint: disable=unused-argument
async def test_number(hass, bypass_validate_input_sensors):
    """Test sensor properties."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_MIN_SOC, entry_id="test", title="none"
    )

    # Set up the entry and assert that the values set during setup are where we expect
    # them to be.
    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]
    assert isinstance(
        hass.data[DOMAIN][config_entry.entry_id], EVSmartChargingCoordinator
    )
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Get the numbers
    number_charging_speed: EVSmartChargingNumberChargingSpeed = hass.data[
        "entity_components"
    ][NUMBER].get_entity("number.none_charging_speed")
    number_price_limit: EVSmartChargingNumberPriceLimit = hass.data[
        "entity_components"
    ][NUMBER].get_entity("number.none_electricity_price_limit")
    number_min_soc: EVSmartChargingNumberMinSOC = hass.data["entity_components"][
        NUMBER
    ].get_entity("number.none_minimum_ev_soc")
    number_opportunistic: EVSmartChargingNumberOpportunistic = hass.data[
        "entity_components"
    ][NUMBER].get_entity("number.none_opportunistic_level")
    assert number_charging_speed
    assert number_price_limit
    assert number_min_soc
    assert number_opportunistic
    assert isinstance(number_charging_speed, EVSmartChargingNumberChargingSpeed)
    assert isinstance(number_price_limit, EVSmartChargingNumberPriceLimit)
    assert isinstance(number_min_soc, EVSmartChargingNumberMinSOC)
    assert isinstance(number_opportunistic, EVSmartChargingNumberOpportunistic)

    # Test the numbers

    assert number_charging_speed.native_value == MOCK_CONFIG_MIN_SOC[CONF_PCT_PER_HOUR]
    assert number_price_limit.native_value == MOCK_CONFIG_MIN_SOC[CONF_MAX_PRICE]
    assert number_min_soc.native_value == MOCK_CONFIG_MIN_SOC[CONF_MIN_SOC]
    assert (
        number_opportunistic.native_value
        == MOCK_CONFIG_MIN_SOC[CONF_OPPORTUNISTIC_LEVEL]
    )

    await number_charging_speed.async_set_native_value(3.2)
    assert coordinator.charging_pct_per_hour == 3.2

    await number_price_limit.async_set_native_value(123)
    assert coordinator.max_price == 123

    await number_min_soc.async_set_native_value(33)
    assert coordinator.number_min_soc == 33

    await number_opportunistic.async_set_native_value(55)
    assert coordinator.number_opportunistic_level == 55

    # Unload the entry and verify that the data has been removed
    assert await async_unload_entry(hass, config_entry)
    assert config_entry.entry_id not in hass.data[DOMAIN]


@pytest.fixture(name="mock_last_state_number")
def mock_last_state_number_fixture():
    """Mock last state."""

    restored: NumberExtraStoredData = NumberExtraStoredData.from_dict(
        {
            "native_max_value": 100,
            "native_min_value": 0,
            "native_step": 1,
            "native_unit_of_measurement": None,
            "native_value": 55,
        }
    )
    with patch(
        "homeassistant.components.number.RestoreNumber.async_get_last_number_data",
        return_value=restored,
    ):
        yield


async def test_number_restore(
    hass: HomeAssistant, bypass_validate_input_sensors, mock_last_state_number
):
    """Test sensor properties."""

    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test", title="none"
    )
    await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    number_charging_speed: EVSmartChargingNumberChargingSpeed = hass.data[
        "entity_components"
    ][NUMBER].get_entity("number.none_charging_speed")

    await number_charging_speed.async_set_native_value(45)
    assert number_charging_speed.native_value == 45

    await number_charging_speed.async_added_to_hass()
    assert number_charging_speed.native_value == 55
