"""Test for FindEntity.find_gespot_sensor function."""
import unittest
from unittest.mock import MagicMock, patch
from collections import UserDict

import sys
import os

# Add the custom_components directory to the path
sys.path.append('/tmp/ev_PR')

from custom_components.ev_smart_charging.const import PLATFORM_GESPOT
from custom_components.ev_smart_charging.helpers.config_flow import FindEntity


class TestFindGESpotSensor(unittest.TestCase):
    """Test FindEntity.find_gespot_sensor function."""

    def test_find_gespot_sensor(self):
        """Test FindEntity.find_gespot_sensor function."""
        # Mock HomeAssistant
        hass = MagicMock()
        
        # Mock EntityRegistry
        entity_registry = MagicMock()
        
        # Create a mock entry for a GE-Spot entity
        mock_entry = MagicMock()
        mock_entry.platform = PLATFORM_GESPOT
        mock_entry.entity_id = "sensor.ge_spot_kwh_se3_sek_2_10_0"
        
        # Create a mock UserDict for entities
        entities = UserDict()
        entities["entity_id"] = mock_entry
        
        # Set up the entity_registry.entities.items() to return our mock entry
        entity_registry.entities.items.return_value = [("entity_id", mock_entry)]
        
        # Patch async_entity_registry_get to return our mock entity_registry
        with patch('custom_components.ev_smart_charging.helpers.config_flow.async_entity_registry_get', return_value=entity_registry):
            # Call the function
            result = FindEntity.find_gespot_sensor(hass)
            
            # Verify the result
            self.assertEqual(result, "sensor.ge_spot_kwh_se3_sek_2_10_0")
            
            # Verify that async_entity_registry_get was called with hass
            from custom_components.ev_smart_charging.helpers.config_flow import async_entity_registry_get
            async_entity_registry_get.assert_called_once_with(hass)
            
            # Verify that entity_registry.entities.items was called
            entity_registry.entities.items.assert_called_once()


if __name__ == "__main__":
    unittest.main()
