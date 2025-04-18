"""Test the FindEntity.find_gespot_sensor function."""
import pytest
from unittest.mock import MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.ev_smart_charging.helpers.config_flow import (
    FindEntity,
    get_platform,
)
from custom_components.ev_smart_charging.const import (
    PLATFORM_GESPOT,
    PLATFORM_NORDPOOL,
    PLATFORM_ENERGIDATASERVICE,
)


async def test_find_gespot_sensor(hass: HomeAssistant):
    """Test the FindEntity.find_gespot_sensor function."""
    # Mock the entity registry
    entity_registry = MagicMock(spec=EntityRegistry)
    
    # Mock the async_entity_registry_get function
    with patch('custom_components.ev_smart_charging.helpers.config_flow.async_entity_registry_get', return_value=entity_registry):
        # Test with no GE-Spot entities
        entity_registry.entities.items.return_value = []
        assert FindEntity.find_gespot_sensor(hass) == ""
        
        # Test with a GE-Spot entity
        mock_entry = MagicMock()
        mock_entry.platform = PLATFORM_GESPOT
        mock_entry.entity_id = "sensor.ge_spot_current_price"
        entity_registry.entities.items.return_value = [("entity_id", mock_entry)]
        assert FindEntity.find_gespot_sensor(hass) == "sensor.ge_spot_current_price"
        
        # Test with multiple entities including a GE-Spot entity
        mock_entry1 = MagicMock()
        mock_entry1.platform = PLATFORM_NORDPOOL
        mock_entry1.entity_id = "sensor.nordpool_current_price"
        
        mock_entry2 = MagicMock()
        mock_entry2.platform = PLATFORM_ENERGIDATASERVICE
        mock_entry2.entity_id = "sensor.energidataservice_current_price"
        
        mock_entry3 = MagicMock()
        mock_entry3.platform = PLATFORM_GESPOT
        mock_entry3.entity_id = "sensor.ge_spot_current_price"
        
        entity_registry.entities.items.return_value = [
            ("entity_id1", mock_entry1),
            ("entity_id2", mock_entry2),
            ("entity_id3", mock_entry3),
        ]
        assert FindEntity.find_gespot_sensor(hass) == "sensor.ge_spot_current_price"


async def test_get_platform_with_gespot(hass: HomeAssistant):
    """Test the get_platform function with a GE-Spot entity."""
    # Mock the entity registry
    entity_registry = MagicMock(spec=EntityRegistry)
    
    # Mock the async_entity_registry_get function
    with patch('custom_components.ev_smart_charging.helpers.config_flow.async_entity_registry_get', return_value=entity_registry):
        # Test with no entity
        assert get_platform(hass, None) is None
        
        # Test with a non-existent entity
        entity_registry.entities = {}
        assert get_platform(hass, "non_existent_entity") is None
        
        # Test with a GE-Spot entity
        mock_entry = MagicMock()
        mock_entry.platform = PLATFORM_GESPOT
        entity_registry.entities = {"sensor.ge_spot_current_price": mock_entry}
        assert get_platform(hass, "sensor.ge_spot_current_price") == PLATFORM_GESPOT
        
        # Test with a Nordpool entity
        mock_entry = MagicMock()
        mock_entry.platform = PLATFORM_NORDPOOL
        entity_registry.entities = {"sensor.nordpool_current_price": mock_entry}
        assert get_platform(hass, "sensor.nordpool_current_price") == PLATFORM_NORDPOOL
        
        # Test with an Energi Data Service entity
        mock_entry = MagicMock()
        mock_entry.platform = PLATFORM_ENERGIDATASERVICE
        entity_registry.entities = {"sensor.energidataservice_current_price": mock_entry}
        assert get_platform(hass, "sensor.energidataservice_current_price") == PLATFORM_ENERGIDATASERVICE
