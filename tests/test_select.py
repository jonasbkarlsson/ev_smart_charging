"""Test ev_smart_charging select."""

from unittest.mock import patch
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import MAJOR_VERSION, MINOR_VERSION
from homeassistant.core import HomeAssistant, State

from custom_components.ev_smart_charging import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ev_smart_charging.const import (
    CONF_READY_QUARTER,
    CONF_START_QUARTER,
    DOMAIN,
    READY_QUARTER_NONE,
    SELECT,
    START_QUARTER_NONE,
)
from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.select import (
    EVSmartChargingSelectReadyQuarter,
    EVSmartChargingSelectStartQuarter,
)

from .const import MOCK_CONFIG_ALL, MOCK_CONFIG_MIN_SOC

# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
# side of the assertion matches with the right side.


# pylint: disable=unused-argument
async def test_select(hass, bypass_validate_input_sensors):
    """Test sensor properties."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG_MIN_SOC,
        entry_id="test",
        title="ev_smart_charging",
    )
    if MAJOR_VERSION > 2024 or (MAJOR_VERSION == 2024 and MINOR_VERSION >= 7):
        config_entry.mock_state(hass=hass, state=ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)

    # Set up the entry and assert that the values set during setup are where we expect
    # them to be.
    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]
    assert isinstance(
        hass.data[DOMAIN][config_entry.entry_id], EVSmartChargingCoordinator
    )
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Get the selects
    select_start_quarter: EVSmartChargingSelectStartQuarter = hass.data[
        "entity_components"
    ][SELECT].get_entity("select.ev_smart_charging_charge_start_time")
    select_ready_quarter: EVSmartChargingSelectReadyQuarter = hass.data[
        "entity_components"
    ][SELECT].get_entity("select.ev_smart_charging_charge_completion_time")
    assert select_start_quarter
    assert select_ready_quarter
    assert isinstance(select_start_quarter, EVSmartChargingSelectStartQuarter)
    assert isinstance(select_ready_quarter, EVSmartChargingSelectReadyQuarter)

    # Test the selects

    assert select_start_quarter.state == MOCK_CONFIG_MIN_SOC[CONF_START_QUARTER]
    assert select_ready_quarter.state == MOCK_CONFIG_MIN_SOC[CONF_READY_QUARTER]

    await select_start_quarter.async_select_option("00:00")
    assert coordinator.start_quarter_local == 0
    await select_start_quarter.async_select_option("13:00")
    assert coordinator.start_quarter_local == 13 * 4
    await select_start_quarter.async_select_option("None")
    assert coordinator.start_quarter_local == START_QUARTER_NONE

    await select_ready_quarter.async_select_option("00:00")
    assert coordinator.ready_quarter_local == 24 * 4
    await select_ready_quarter.async_select_option("13:00")
    assert coordinator.ready_quarter_local == 13 * 4
    await select_ready_quarter.async_select_option("None")
    assert coordinator.ready_quarter_local == READY_QUARTER_NONE

    # Unload the entry and verify that the data has been removed
    assert await async_unload_entry(hass, config_entry)
    assert config_entry.entry_id not in hass.data[DOMAIN]


@pytest.fixture(name="mock_last_state_select")
def mock_last_state_select_fixture():
    """Mock last state."""

    restored: State = State(
        entity_id="select.ev_smart_charging_charge_completion_time", state="11:00"
    )
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state",
        return_value=restored,
    ):
        yield


async def test_select_restore(
    hass: HomeAssistant, bypass_validate_input_sensors, mock_last_state_select
):
    """Test sensor properties."""

    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test", title="ev_smart_charging"
    )
    if MAJOR_VERSION > 2024 or (MAJOR_VERSION == 2024 and MINOR_VERSION >= 7):
        config_entry.mock_state(hass=hass, state=ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)
    await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    select_ready_quarter: EVSmartChargingSelectReadyQuarter = hass.data[
        "entity_components"
    ][SELECT].get_entity("select.ev_smart_charging_charge_completion_time")

    await select_ready_quarter.async_select_option("10:00")
    assert select_ready_quarter.state == "10:00"

    await select_ready_quarter.async_added_to_hass()
    assert select_ready_quarter.state == "11:00"

    # Unload the entry and verify that the data has been removed
    assert await async_unload_entry(hass, config_entry)
    await hass.async_block_till_done()
    assert config_entry.entry_id not in hass.data[DOMAIN]
