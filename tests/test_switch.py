"""Test ev_smart_charging switch."""
from unittest.mock import patch
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant, State

from custom_components.ev_smart_charging import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ev_smart_charging.const import DOMAIN, SWITCH
from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.switch import (
    EVSmartChargingSwitchActive,
    EVSmartChargingSwitchApplyLimit,
    EVSmartChargingSwitchContinuous,
    EVSmartChargingSwitchEVConnected,
)

from .const import MOCK_CONFIG_USER_NO_CHARGER

# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
# side of the assertion matches with the right side.

# pylint: disable=unused-argument
async def test_switch(hass, bypass_validate_input_sensors):
    """Test sensor properties."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_USER_NO_CHARGER, entry_id="test"
    )

    # Set up the entry and assert that the values set during setup are where we expect
    # them to be. Because we have patched the BlueprintDataUpdateCoordinator.async_get_data
    # call, no code from custom_components/integration_blueprint/api.py actually runs.
    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]
    assert isinstance(
        hass.data[DOMAIN][config_entry.entry_id], EVSmartChargingCoordinator
    )
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Get the switches
    switch_active: EVSmartChargingSwitchActive = hass.data["entity_components"][
        SWITCH
    ].get_entity("switch.none_smart_charging_activated")
    switch_limit: EVSmartChargingSwitchApplyLimit = hass.data["entity_components"][
        SWITCH
    ].get_entity("switch.none_apply_price_limit")
    switch_continuous: EVSmartChargingSwitchContinuous = hass.data["entity_components"][
        SWITCH
    ].get_entity("switch.none_continuous_charging_preferred")
    switch_ev_connected: EVSmartChargingSwitchEVConnected = hass.data[
        "entity_components"
    ][SWITCH].get_entity("switch.none_ev_connected")
    assert switch_active
    assert switch_limit
    assert switch_continuous
    assert switch_ev_connected
    assert isinstance(switch_active, EVSmartChargingSwitchActive)
    assert isinstance(switch_limit, EVSmartChargingSwitchApplyLimit)
    assert isinstance(switch_continuous, EVSmartChargingSwitchContinuous)
    assert isinstance(switch_ev_connected, EVSmartChargingSwitchEVConnected)

    # Test the switches
    await switch_active.async_turn_on()
    assert coordinator.switch_active is True
    await switch_active.async_turn_off()
    assert coordinator.switch_active is False
    await switch_active.async_turn_on()
    assert coordinator.switch_active is True

    await switch_limit.async_turn_on()
    assert coordinator.switch_apply_limit is True
    await switch_limit.async_turn_off()
    assert coordinator.switch_apply_limit is False
    await switch_limit.async_turn_on()
    assert coordinator.switch_apply_limit is True

    await switch_continuous.async_turn_on()
    assert coordinator.switch_continuous is True
    await switch_continuous.async_turn_off()
    assert coordinator.switch_continuous is False
    await switch_continuous.async_turn_on()
    assert coordinator.switch_continuous is True

    await switch_ev_connected.async_turn_on()
    assert coordinator.switch_ev_connected is True
    await switch_ev_connected.async_turn_off()
    assert coordinator.switch_ev_connected is False
    await switch_ev_connected.async_turn_on()
    assert coordinator.switch_ev_connected is True

    # Unload the entry and verify that the data has been removed
    assert await async_unload_entry(hass, config_entry)
    assert config_entry.entry_id not in hass.data[DOMAIN]


@pytest.fixture(name="mock_last_state_off")
def mock_last_state_off_fixture():
    """Mock last state."""

    restored = State(entity_id="switch.none_smart_charging_activated", state=STATE_OFF)
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state",
        return_value=restored,
    ):
        yield


async def test_switch_off_restore(
    hass: HomeAssistant, bypass_validate_input_sensors, mock_last_state_off
):
    """Test sensor properties."""

    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_USER_NO_CHARGER, entry_id="test"
    )
    await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    switch_active: EVSmartChargingSwitchActive = hass.data["entity_components"][
        SWITCH
    ].get_entity("switch.none_smart_charging_activated")

    await switch_active.async_turn_on()
    assert switch_active.is_on is True

    await switch_active.async_added_to_hass()
    assert switch_active.is_on is False


@pytest.fixture(name="mock_last_state_on")
def mock_last_state_on_fixture():
    """Mock last state."""

    restored = State(entity_id="switch.none_smart_charging_activated", state=STATE_ON)
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state",
        return_value=restored,
    ):
        yield


async def test_switch_on_restore(
    hass: HomeAssistant, bypass_validate_input_sensors, mock_last_state_on
):
    """Test sensor properties."""

    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_USER_NO_CHARGER, entry_id="test"
    )
    await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    switch_active: EVSmartChargingSwitchActive = hass.data["entity_components"][
        SWITCH
    ].get_entity("switch.none_smart_charging_activated")

    await switch_active.async_turn_on()
    assert switch_active.is_on is True

    await switch_active.async_added_to_hass()
    assert switch_active.is_on is True
