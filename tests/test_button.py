"""Test ev_smart_charging button."""
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.const import STATE_ON, STATE_OFF

from custom_components.ev_smart_charging import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.const import BUTTON, DOMAIN
from custom_components.ev_smart_charging.button import (
    EVSmartChargingButtonStart,
    EVSmartChargingButtonStop,
)

from .const import MOCK_CONFIG_USER_NO_CHARGER

# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
# side of the assertion matches with the right side.


# pylint: disable=unused-argument
async def test_button(hass, bypass_validate_input_sensors):
    """Test buttons."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_USER_NO_CHARGER, entry_id="test", title="none"
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

    # Get the buttons
    button_start: EVSmartChargingButtonStart = hass.data["entity_components"][
        BUTTON
    ].get_entity("button.none_manually_start_charging")
    button_stop: EVSmartChargingButtonStop = hass.data["entity_components"][
        BUTTON
    ].get_entity("button.none_manually_stop_charging")
    assert button_start
    assert button_stop
    assert isinstance(button_start, EVSmartChargingButtonStart)
    assert isinstance(button_stop, EVSmartChargingButtonStop)

    # Test the butttons
    await button_start.async_press()
    assert coordinator.sensor.native_value == STATE_ON
    await button_stop.async_press()
    assert coordinator.sensor.native_value == STATE_OFF
    await button_start.async_press()
    assert coordinator.sensor.native_value == STATE_ON

    # Unload the entry and verify that the data has been removed
    assert await async_unload_entry(hass, config_entry)
    assert config_entry.entry_id not in hass.data[DOMAIN]
