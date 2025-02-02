"""Test ev_smart_charging sensor."""

from zoneinfo import ZoneInfo
from datetime import datetime

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_OFF, STATE_ON, MAJOR_VERSION, MINOR_VERSION

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ev_smart_charging import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.const import (
    CHARGING_STATUS_CHARGING,
    CHARGING_STATUS_WAITING_CHARGING,
    DOMAIN,
)
from custom_components.ev_smart_charging.sensor import (
    EVSmartChargingSensorCharging,
    EVSmartChargingSensorStatus,
)

from .const import MOCK_CONFIG_ALL


# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
# side of the assertion matches with the right side.


# pylint: disable=unused-argument
async def test_sensor(hass, bypass_validate_input_and_control):
    """Test sensor properties."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
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
    assert coordinator.sensor is not None
    assert isinstance(coordinator.sensor, EVSmartChargingSensorCharging)
    sensor = coordinator.sensor

    assert coordinator.sensor_status is not None
    assert isinstance(coordinator.sensor_status, EVSmartChargingSensorStatus)
    sensor_status = coordinator.sensor_status

    # Test the sensor
    sensor.set_state(STATE_OFF)
    assert sensor.native_value == STATE_OFF
    sensor.set_state(STATE_ON)
    assert sensor.native_value == STATE_ON

    sensor.current_price = 12.1
    assert sensor.current_price == 12.1

    sensor.ev_soc = 56
    assert sensor.ev_soc == 56

    sensor.ev_target_soc = 80
    assert sensor.ev_target_soc == 80

    one_list = [{"value": 1.0}]

    sensor.raw_two_days_local = one_list
    assert sensor.raw_two_days_local == one_list

    sensor.charging_schedule = one_list
    assert sensor.charging_schedule == one_list

    sensor.charging_is_planned = True
    assert sensor.charging_is_planned is True

    sensor.charging_start_time = datetime(
        2022, 9, 30, 1, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")
    )
    assert sensor.charging_start_time == datetime(
        2022, 9, 30, 1, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")
    )

    sensor.charging_stop_time = datetime(
        2022, 9, 30, 5, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")
    )
    assert sensor.charging_stop_time == datetime(
        2022, 9, 30, 5, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")
    )

    extra = sensor.extra_state_attributes
    assert extra["current_price"] == 12.1
    assert extra["ev_soc"] == 56
    assert extra["ev_target_soc"] == 80
    assert extra["charging_is_planned"] is True
    assert extra["charging_start_time"] == datetime(
        2022, 9, 30, 1, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")
    )
    assert extra["charging_stop_time"] == datetime(
        2022, 9, 30, 5, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")
    )

    sensor.charging_number_of_quarters = 5
    extra = sensor.extra_state_attributes
    assert sensor.charging_number_of_quarters == 5
    assert extra["charging_number_of_hours"] == 1.25

    sensor.charging_number_of_quarters = 8
    extra = sensor.extra_state_attributes
    assert sensor.charging_number_of_quarters == 8
    assert extra["charging_number_of_hours"] == 2

    # Test sensor_status
    sensor_status.set_status(CHARGING_STATUS_WAITING_CHARGING)
    assert sensor_status.native_value == CHARGING_STATUS_WAITING_CHARGING
    sensor_status.set_status(CHARGING_STATUS_CHARGING)
    assert sensor_status.native_value == CHARGING_STATUS_CHARGING

    # Unload the entry and verify that the data has been removed
    assert await async_unload_entry(hass, config_entry)
    assert config_entry.entry_id not in hass.data[DOMAIN]
