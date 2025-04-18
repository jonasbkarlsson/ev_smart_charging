"""Test the Validator.is_price_state method with GE-Spot data."""
import pytest
from unittest.mock import MagicMock

from homeassistant.core import State

from custom_components.ev_smart_charging.helpers.general import Validator
from custom_components.ev_smart_charging.const import (
    PLATFORM_GESPOT,
    PLATFORM_NORDPOOL,
    PLATFORM_ENERGIDATASERVICE,
)


def test_is_price_state_with_gespot():
    """Test the Validator.is_price_state method with GE-Spot data."""
    # Test with a valid GE-Spot state
    state = MagicMock(spec=State)
    state.state = "123.45"
    state.attributes = {
        "current_price": 123.45,
        "raw_today": [
            {
                "value": 123.45,
                "start": "2022-09-30T00:00:00+02:00",
                "end": "2022-09-30T01:00:00+02:00",
            }
        ],
        "raw_tomorrow": [
            {
                "value": 123.45,
                "start": "2022-10-01T00:00:00+02:00",
                "end": "2022-10-01T01:00:00+02:00",
            }
        ],
    }
    assert Validator.is_price_state(state, PLATFORM_GESPOT) is True

    # Test with an invalid GE-Spot state (missing current_price)
    state = MagicMock(spec=State)
    state.state = "123.45"
    state.attributes = {
        "raw_today": [
            {
                "value": 123.45,
                "start": "2022-09-30T00:00:00+02:00",
                "end": "2022-09-30T01:00:00+02:00",
            }
        ],
        "raw_tomorrow": [
            {
                "value": 123.45,
                "start": "2022-10-01T00:00:00+02:00",
                "end": "2022-10-01T01:00:00+02:00",
            }
        ],
    }
    assert Validator.is_price_state(state, PLATFORM_GESPOT) is False

    # Test with an invalid GE-Spot state (missing raw_today)
    state = MagicMock(spec=State)
    state.state = "123.45"
    state.attributes = {
        "current_price": 123.45,
        "raw_tomorrow": [
            {
                "value": 123.45,
                "start": "2022-10-01T00:00:00+02:00",
                "end": "2022-10-01T01:00:00+02:00",
            }
        ],
    }
    assert Validator.is_price_state(state, PLATFORM_GESPOT) is False

    # Test with an invalid GE-Spot state (invalid raw_today)
    state = MagicMock(spec=State)
    state.state = "123.45"
    state.attributes = {
        "current_price": 123.45,
        "raw_today": [],
        "raw_tomorrow": [
            {
                "value": 123.45,
                "start": "2022-10-01T00:00:00+02:00",
                "end": "2022-10-01T01:00:00+02:00",
            }
        ],
    }
    assert Validator.is_price_state(state, PLATFORM_GESPOT) is False

    # Test with a valid Nordpool state
    state = MagicMock(spec=State)
    state.state = "123.45"
    state.attributes = {
        "current_price": 123.45,
        "raw_today": [
            {
                "value": 123.45,
                "start": "2022-09-30T00:00:00+02:00",
                "end": "2022-09-30T01:00:00+02:00",
            }
        ],
        "raw_tomorrow": [
            {
                "value": 123.45,
                "start": "2022-10-01T00:00:00+02:00",
                "end": "2022-10-01T01:00:00+02:00",
            }
        ],
    }
    assert Validator.is_price_state(state, PLATFORM_NORDPOOL) is True

    # Test with a valid Energi Data Service state
    state = MagicMock(spec=State)
    state.state = "123.45"
    state.attributes = {
        "current_price": 123.45,
        "raw_today": [
            {
                "hour": "2022-09-30T00:00:00+02:00",
                "price": 123.45,
            }
        ],
        "raw_tomorrow": [
            {
                "hour": "2022-10-01T00:00:00+02:00",
                "price": 123.45,
            }
        ],
    }
    assert Validator.is_price_state(state, PLATFORM_ENERGIDATASERVICE) is True

    # Test with None state
    assert Validator.is_price_state(None, PLATFORM_GESPOT) is False

    # Test with unavailable state
    state = MagicMock(spec=State)
    state.state = "unavailable"
    assert Validator.is_price_state(state, PLATFORM_GESPOT) is False
