"""Test ev_smart_charging switch."""
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant

from custom_components.ev_smart_charging import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ev_smart_charging.const import DOMAIN, SWITCH
from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.sensor import (
    async_setup_entry as sensor_async_setup_entry,
)
from custom_components.ev_smart_charging.switch import (
    EVSmartChargingSwitchActive,
    EVSmartChargingSwitchApplyLimit,
    async_setup_entry as switch_async_setup_entry,
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
    assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]
    assert isinstance(
        hass.data[DOMAIN][config_entry.entry_id], EVSmartChargingCoordinator
    )

    def dummy(var1):
        pass

    await switch_async_setup_entry(hass, config_entry, dummy)
    assert hass.data[DOMAIN][config_entry.entry_id] is not None
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    switch_active = EVSmartChargingSwitchActive(config_entry, coordinator)
    assert isinstance(switch_active, EVSmartChargingSwitchActive)
    switch_limit = EVSmartChargingSwitchApplyLimit(config_entry, coordinator)
    assert isinstance(switch_limit, EVSmartChargingSwitchApplyLimit)

    # Need to set up sensor in order to test
    await sensor_async_setup_entry(hass, config_entry, dummy)

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

    # Unload the entry and verify that the data has been removed
    assert await async_unload_entry(hass, config_entry)
    assert config_entry.entry_id not in hass.data[DOMAIN]


# pylint: disable=unused-argument
async def test_switch_restore(hass: HomeAssistant, bypass_validate_input_sensors):
    """Test sensor properties."""
    # TODO: This seems not to test what is intendend. The async_get_last_state() call
    # in EVSmartChargingSwitch.async_added_to_hass() only returns None.

    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_USER_NO_CHARGER, entry_id="test"
    )
    await async_setup_entry(hass, config_entry)

    def dummy(var1):
        pass

    await sensor_async_setup_entry(hass, config_entry, dummy)
    await switch_async_setup_entry(hass, config_entry, dummy)
    await hass.async_block_till_done()

    switch_active: EVSmartChargingSwitchActive = hass.data["entity_components"][
        SWITCH
    ].get_entity("switch.none_smart_charging_activated")

    await switch_active.async_turn_on()
    assert switch_active.is_on is True
    switch_active.update_ha_state()
    await hass.async_block_till_done()

    # Unload the entry and verify that the data has been removed
    assert await async_unload_entry(hass, config_entry)

    # Test Restore state

    await async_setup_entry(hass, config_entry)
    await sensor_async_setup_entry(hass, config_entry, dummy)
    await switch_async_setup_entry(hass, config_entry, dummy)
    await hass.async_block_till_done()

    switch_active = hass.data["entity_components"][SWITCH].get_entity(
        "switch.none_smart_charging_activated"
    )

    assert switch_active.is_on is True

    await switch_active.async_turn_off()
    assert switch_active.is_on is False
    switch_active.update_ha_state()
    await hass.async_block_till_done()

    # Unload the entry and verify that the data has been removed
    assert await async_unload_entry(hass, config_entry)

    # Test Restore state

    await async_setup_entry(hass, config_entry)
    await sensor_async_setup_entry(hass, config_entry, dummy)
    await switch_async_setup_entry(hass, config_entry, dummy)
    await hass.async_block_till_done()

    switch_active = hass.data["entity_components"][SWITCH].get_entity(
        "switch.none_smart_charging_activated"
    )

    assert switch_active.is_on is False
