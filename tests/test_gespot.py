"""Test GE-Spot integration."""
import pytest
from unittest.mock import MagicMock, patch
from collections import UserDict
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity_registry import EntityRegistry, async_get as async_entity_registry_get
from homeassistant.util import dt

from custom_components.ev_smart_charging.const import (
    PLATFORM_ENERGIDATASERVICE,
    PLATFORM_ENTSOE,
    PLATFORM_GESPOT,
    PLATFORM_NORDPOOL,
)
from custom_components.ev_smart_charging.helpers.config_flow import FindEntity
from custom_components.ev_smart_charging.helpers.general import Validator
from custom_components.ev_smart_charging.helpers.raw import Raw

from tests.price import (
    PRICE_20220930,
    PRICE_20220930_GESPOT,
    PRICE_20221001,
    PRICE_20221001_GESPOT,
)


class TestGESpotIntegration:
    """Test GE-Spot integration."""

    async def test_find_gespot_sensor(self, hass: HomeAssistant):
        """Test the FindEntity.find_gespot_sensor function."""
        # Mock the entity registry
        entity_registry = MagicMock()
        entity_registry.entities = MagicMock()
        
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

    async def test_validator_gespot(self, hass, set_cet_timezone, freezer):
        """Test Validator.is_price_state with GE-Spot data."""
        freezer.move_to("2022-09-30T14:00:00+02:00")
        
        # Test with valid GE-Spot data
        price_state = State(
            entity_id="sensor.ge_spot_kwh_se3_sek_2_10_0",
            state="123",
            attributes={
                "current_price": 123,
                "raw_today": PRICE_20220930_GESPOT,
                "raw_tomorrow": PRICE_20221001_GESPOT,
            },
        )
        assert Validator.is_price_state(price_state, PLATFORM_GESPOT) is True
        
        # Test with invalid GE-Spot data
        price_state = State(
            entity_id="sensor.ge_spot_kwh_se3_sek_2_10_0",
            state="123",
            attributes={
                "current_price": 123,
                "raw_today": [],
                "raw_tomorrow": [],
            },
        )
        assert Validator.is_price_state(price_state, PLATFORM_GESPOT) is False
        
        # Test with GE-Spot data using fallback
        price_state = State(
            entity_id="sensor.ge_spot_kwh_se3_sek_2_10_0",
            state="123",
            attributes={
                "current_price": 123,
                "raw_today": [],
                "raw_tomorrow": [],
                "source_info": {"is_using_fallback": True},
            },
        )
        assert Validator.is_price_state(price_state, PLATFORM_GESPOT) is True

        # Test with an invalid GE-Spot state (missing current_price)
        price_state = State(
            entity_id="sensor.ge_spot_kwh_se3_sek_2_10_0",
            state="123",
            attributes={
                "raw_today": PRICE_20220930_GESPOT,
                "raw_tomorrow": PRICE_20221001_GESPOT,
            },
        )
        assert Validator.is_price_state(price_state, PLATFORM_GESPOT) is False

        # Test with an invalid GE-Spot state (missing raw_today)
        price_state = State(
            entity_id="sensor.ge_spot_kwh_se3_sek_2_10_0",
            state="123",
            attributes={
                "current_price": 123,
                "raw_tomorrow": PRICE_20221001_GESPOT,
            },
        )
        assert Validator.is_price_state(price_state, PLATFORM_GESPOT) is False

        # Test with None state
        assert Validator.is_price_state(None, PLATFORM_GESPOT) is False

        # Test with unavailable state
        price_state = State(
            entity_id="sensor.ge_spot_kwh_se3_sek_2_10_0",
            state="unavailable",
        )
        assert Validator.is_price_state(price_state, PLATFORM_GESPOT) is False

    async def test_96_interval_data(self, hass, set_cet_timezone):
        """Verify GE-Spot v1.2.0 data with 96 intervals works."""
        # Verify test data has correct structure
        assert len(PRICE_20220930_GESPOT) == 96, "Should have 96 15-minute intervals"
        assert len(PRICE_20221001_GESPOT) == 96, "Should have 96 15-minute intervals"
        
        # Verify each interval is 15 minutes
        for i in range(len(PRICE_20220930_GESPOT) - 1):
            current = PRICE_20220930_GESPOT[i]
            next_item = PRICE_20220930_GESPOT[i + 1]
            
            duration = (current["end"] - current["start"]).total_seconds() / 60
            assert duration == 15, f"Interval {i} should be 15 minutes, got {duration}"
            
            # Verify continuous (no gaps)
            assert current["end"] == next_item["start"], f"Gap between intervals {i} and {i+1}"
        
        # Verify validator accepts this data
        price_state = State(
            entity_id="sensor.gespot_current_price",
            state="163.08",
            attributes={
                "current_price": 163.08,
                "raw_today": PRICE_20220930_GESPOT,
                "raw_tomorrow": PRICE_20221001_GESPOT,
            },
        )
        
        assert Validator.is_price_state(price_state, PLATFORM_GESPOT) is True

    async def test_raw_price_handler_96_intervals(self, hass, set_cet_timezone):
        """Test that Raw price handler processes 96 intervals correctly."""
        # Create Raw object with 96-interval data
        raw = Raw(PRICE_20220930_GESPOT, PLATFORM_GESPOT)
        
        # Verify it's valid
        assert raw.is_valid() is True
        
        # Verify it processes all 96 intervals
        assert raw.data is not None
        assert len(raw.data) == 96
        
        # Verify first and last interval
        first = raw.data[0]
        last = raw.data[-1]
        
        assert first["start"].hour == 0
        assert first["start"].minute == 0
        assert last["start"].hour == 23
        assert last["start"].minute == 45
