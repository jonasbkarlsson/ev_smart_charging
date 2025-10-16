"""Tests for raw data helper functions."""

from datetime import datetime, timedelta, timezone
import pytest
from custom_components.ev_smart_charging.helpers.raw import (
    convert_raw_item,
    PriceFormat,
)
from custom_components.ev_smart_charging.const import (
    PLATFORM_ENERGIDATASERVICE,
    PLATFORM_ENTSOE,
    PLATFORM_GENERIC,
    PLATFORM_GESPOT,
    PLATFORM_NORDPOOL,
    PLATFORM_TGE,
)


@pytest.mark.parametrize(
    "platform, item, expected_start, expected_value",
    [
        # PLATFORM_NORDPOOL: start is datetime, value is "value"
        (
            PLATFORM_NORDPOOL,
            {"start": datetime(2023, 3, 6, 0, 0, tzinfo=timezone.utc), "value": 145.77},
            datetime(2023, 3, 6, 0, 0, tzinfo=timezone.utc),
            145.77,
        ),
        # PLATFORM_GESPOT: time is datetime, value is "value"
        (
            PLATFORM_GESPOT,
            {"time": datetime(2023, 3, 6, 1, 0, tzinfo=timezone.utc), "value": 200.0},
            datetime(2023, 3, 6, 1, 0, tzinfo=timezone.utc),
            200.0,
        ),
        # PLATFORM_ENERGIDATASERVICE: hour is datetime, value is "price"
        (
            PLATFORM_ENERGIDATASERVICE,
            {"hour": datetime(2023, 3, 6, 2, 0, tzinfo=timezone.utc), "price": 146.96},
            datetime(2023, 3, 6, 2, 0, tzinfo=timezone.utc),
            146.96,
        ),
        # PLATFORM_ENTSOE: time is string, value is "price"
        (
            PLATFORM_ENTSOE,
            {"time": "2023-03-06T03:00:00+00:00", "price": 0.1306},
            datetime.fromisoformat("2023-03-06T03:00:00+00:00"),
            0.1306,
        ),
        # PLATFORM_GENERIC: time is string, value is "price"
        (
            PLATFORM_GENERIC,
            {"time": "2023-03-06T04:00:00+00:00", "price": 0.1406},
            datetime.fromisoformat("2023-03-06T04:00:00+00:00"),
            0.1406,
        ),
        # PLATFORM_TGE: time is datetime, value is "price"
        (
            PLATFORM_TGE,
            {"time": datetime(2023, 3, 6, 5, 0, tzinfo=timezone.utc), "price": 146.96},
            datetime(2023, 3, 6, 5, 0, tzinfo=timezone.utc),
            146.96,
        ),
    ],
)
def test_convert_raw_item_valid(platform, item, expected_start, expected_value):
    """Test convert_raw_item with valid inputs."""
    pf = PriceFormat(platform)
    result = convert_raw_item(item, pf)
    assert result is not None
    assert result["value"] == expected_value
    assert result["start"] == expected_start
    assert result["end"] == expected_start + timedelta(minutes=15)


def test_convert_raw_item_missing_key():
    """Test convert_raw_item with missing keys."""
    pf = PriceFormat(PLATFORM_NORDPOOL)
    item = {"value": 123.45}  # missing "start"
    result = convert_raw_item(item, pf)
    assert result is None


def test_convert_raw_item_invalid_string_date():
    """Test convert_raw_item with invalid string date."""
    pf = PriceFormat(PLATFORM_ENTSOE)
    item = {"time": "not-a-date", "price": 0.1}
    result = convert_raw_item(item, pf)
    assert result is None


def test_convert_raw_item_type_error():
    """Test convert_raw_item with wrong type."""
    pf = PriceFormat(PLATFORM_NORDPOOL)
    item = None  # not a dict
    result = convert_raw_item(item, pf)
    assert result is None
