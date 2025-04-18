"""Test the MockPriceEntityGESpot class."""
import pytest
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry

from tests.helpers.helpers import MockPriceEntityGESpot


async def test_mock_price_entity_gespot(hass: HomeAssistant):
    """Test the MockPriceEntityGESpot class."""
    # Mock the entity registry
    entity_registry = MagicMock(spec=EntityRegistry)
    
    # Create a mock GE-Spot entity
    MockPriceEntityGESpot.create(hass, entity_registry)
    
    # Verify that the entity was registered
    entity_registry.async_get_or_create.assert_called_once()
    
    # Verify that the entity was registered with the correct parameters
    args, kwargs = entity_registry.async_get_or_create.call_args
    assert kwargs["domain"] == "sensor"
    assert kwargs["platform"] == "ge_spot"
    assert kwargs["unique_id"] == "kwh_se3_sek_2_10_0"
    
    # Verify that the entity state was set
    hass.states.async_set.assert_called_once()
    
    # Verify that the entity state was set with the correct parameters
    args, kwargs = hass.states.async_set.call_args
    assert args[0] == "sensor.ge_spot_kwh_se3_sek_2_10_0"
    assert args[1] == "123"
    assert kwargs["current_price"] == 123
    assert len(kwargs["raw_today"]) == 1
    assert kwargs["raw_today"][0]["value"] == 123
    assert kwargs["raw_today"][0]["start"] == "2022-09-30T00:00:00+02:00"
    assert kwargs["raw_today"][0]["end"] == "2022-09-30T01:00:00+02:00"
    assert len(kwargs["raw_tomorrow"]) == 1
    assert kwargs["raw_tomorrow"][0]["value"] == 123
    assert kwargs["raw_tomorrow"][0]["start"] == "2022-10-01T00:00:00+02:00"
    assert kwargs["raw_tomorrow"][0]["end"] == "2022-10-01T01:00:00+02:00"
