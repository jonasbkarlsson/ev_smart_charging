"""Test the Raw class with GE-Spot data."""
from datetime import datetime, timedelta

from homeassistant.util import dt as dt_util

from custom_components.ev_smart_charging.const import PLATFORM_GESPOT
from custom_components.ev_smart_charging.helpers.coordinator import Raw


# pylint: disable=unused-argument
async def test_raw_gespot_simple(hass, set_cet_timezone):
    """Test Raw class with GE-Spot data format."""
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
    assert len(raw.data) == 24
    assert raw.data[0]["value"] == 100
    assert raw.data[0]["start"] == datetime(2022, 9, 30, 0, 0)
    assert raw.data[0]["end"] == datetime(2022, 9, 30, 1, 0)
    
    # Verify that is_valid returns True
    assert raw.is_valid()
    
    # Verify that get_raw returns the original data
    assert raw.get_raw() == test_data
    
    # Test max_value
    assert raw.max_value() == 123  # 100 + 23 = 123
    
    # Test last_value
    assert raw.last_value() == 123  # Last value is 100 + 23 = 123
    
    # Test number_of_nonzero
    assert raw.number_of_nonzero() == 24
