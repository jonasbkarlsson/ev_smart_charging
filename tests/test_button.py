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
from custom_components.ev_smart_charging.const import DOMAIN
from custom_components.ev_smart_charging.button import (
    EVSmartChargingButtonStart,
    EVSmartChargingButtonStop,
)
from custom_components.ev_smart_charging.button import (
    async_setup_entry as button_async_setup_entry,
)
from custom_components.ev_smart_charging.sensor import (
    async_setup_entry as sensor_async_setup_entry,
)

from .const import MOCK_CONFIG_USER_NO_CHARGER


# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
# side of the assertion matches with the right side.

# pylint: disable=unused-argument
async def test_button(hass, bypass_validate_input_sensors):
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

    await button_async_setup_entry(hass, config_entry, dummy)
    assert hass.data[DOMAIN][config_entry.entry_id] is not None
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    button_start = EVSmartChargingButtonStart(config_entry, coordinator)
    assert isinstance(button_start, EVSmartChargingButtonStart)
    button_stop = EVSmartChargingButtonStop(config_entry, coordinator)
    assert isinstance(button_stop, EVSmartChargingButtonStop)

    # Need to set up sensor in order to test
    await sensor_async_setup_entry(hass, config_entry, dummy)

    await button_start.async_press()
    assert coordinator.sensor.native_value == STATE_ON
    await button_stop.async_press()
    assert coordinator.sensor.native_value == STATE_OFF
    await button_start.async_press()
    assert coordinator.sensor.native_value == STATE_ON

    # Unload the entry and verify that the data has been removed
    assert await async_unload_entry(hass, config_entry)
    assert config_entry.entry_id not in hass.data[DOMAIN]
