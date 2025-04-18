"""Simple test for GE-Spot integration."""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

import sys
import os

# Add the custom_components directory to the path
sys.path.append('/tmp/ev_PR')

from custom_components.ev_smart_charging.const import PLATFORM_GESPOT
from custom_components.ev_smart_charging.helpers.coordinator import Raw


class TestGESpotIntegration(unittest.TestCase):
    """Test GE-Spot integration."""

    def test_raw_gespot_init(self):
        """Test Raw class initialization with GE-Spot data."""
        # Create test data with 24 hours
        test_data = []
        for hour in range(24):
            test_data.append({
                "value": 100 + hour,
                "start": datetime(2022, 9, 30, hour, 0),
                "end": datetime(2022, 9, 30, hour, 0) + timedelta(hours=1),
            })
        
        # Initialize Raw with GE-Spot data
        raw = Raw(test_data, PLATFORM_GESPOT)
        
        # Verify that the data was processed correctly
        self.assertEqual(len(raw.data), 24)
        self.assertEqual(raw.data[0]["value"], 100)
        self.assertEqual(raw.data[0]["start"], datetime(2022, 9, 30, 0, 0))
        self.assertEqual(raw.data[0]["end"], datetime(2022, 9, 30, 1, 0))
        
        # Verify that is_valid returns True
        self.assertTrue(raw.is_valid())
        
        # Verify that get_raw returns the original data
        self.assertEqual(raw.get_raw(), test_data)
        
        # Test max_value
        self.assertEqual(raw.max_value(), 123)  # 100 + 23 = 123
        
        # Test last_value
        self.assertEqual(raw.last_value(), 123)  # Last value is 100 + 23 = 123


if __name__ == "__main__":
    unittest.main()
