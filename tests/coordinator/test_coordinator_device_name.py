"""Test ev_smart_charging coordinator."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.helpers.device_registry import async_get as async_device_registry_get
from homeassistant.helpers.device_registry import DeviceRegistry, DeviceEntry
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import (
    EntityRegistry,
    async_entries_for_config_entry,
)

from custom_components.ev_smart_charging import (
    async_reload_entry,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.const import DOMAIN

from tests.const import MOCK_CONFIG_ALL


# pylint: disable=unused-argument
async def test_coordinator_device_name(hass, bypass_validate_input_sensors):
    """Test entry setup with new integration name."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")

    # Set up the entry and assert that the values set during setup are where we expect
    # them to be.
    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()
    assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]
    assert isinstance(
        hass.data[DOMAIN][config_entry.entry_id], EVSmartChargingCoordinator
    )

    # Change device title
    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    all_entities = async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    )
    device_id = all_entities[0].device_id
    device_registry: DeviceRegistry = async_device_registry_get(hass)
    device: DeviceEntry = device_registry.async_get(device_id)
    device_registry.async_update_device(device.id, name_by_user="New title")
    await hass.async_block_till_done()

    assert config_entry.title == "New title"

    # Reload the entry and assert that the data from above is still there
    assert await async_reload_entry(hass, config_entry) is None
    await hass.async_block_till_done()
    assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]
    assert isinstance(
        hass.data[DOMAIN][config_entry.entry_id], EVSmartChargingCoordinator
    )

    assert config_entry.title == "New title"

    # Unload the entry and verify that the data has been removed
    assert await async_unload_entry(hass, config_entry)
    await hass.async_block_till_done()
    assert config_entry.entry_id not in hass.data[DOMAIN]
