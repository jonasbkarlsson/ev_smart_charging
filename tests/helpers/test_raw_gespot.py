"""Test the Raw class with GE-Spot data."""
from datetime import datetime
import pytest

from homeassistant.util import dt as dt_util
from custom_components.ev_smart_charging.const import (
    PLATFORM_GESPOT,
    READY_HOUR_NONE,
    START_HOUR_NONE,
)

from custom_components.ev_smart_charging.helpers.coordinator import Raw
from tests.price import (
    PRICE_20220930,
    PRICE_20220930_GESPOT,
    PRICE_20221001,
    PRICE_20221001_GESPOT,
)


# pylint: disable=unused-argument
async def test_raw_gespot(hass, set_cet_timezone):
    """Test Raw with GE-Spot data format"""

    # Test with GE-Spot data
    price = Raw(PRICE_20220930_GESPOT, PLATFORM_GESPOT)
    assert price.get_raw() == PRICE_20220930
    assert price.is_valid()
    assert price.copy().get_raw() == PRICE_20220930
    assert price.max_value() == 388.65
    assert price.last_value() == 49.64
    assert price.number_of_nonzero() == 24

    # Test getting value for a specific time
    time = datetime(
        2022, 9, 30, 8, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert price.get_value(time) == 388.65
    assert price.get_item(time) == {
        "start": datetime(
            2022, 9, 30, 8, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
        ),
        "end": datetime(
            2022, 9, 30, 9, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
        ),
        "value": 388.65,
    }

    # Test getting value for a time not in the data
    time = datetime(
        2022, 9, 29, 8, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert price.get_value(time) is None
    assert price.get_item(time) is None

    # Test extending with another day's data
    price2 = Raw(PRICE_20221001_GESPOT, PLATFORM_GESPOT)
    price.extend(None)
    assert price.get_raw() == PRICE_20220930
    price.extend(price2)
    assert price.number_of_nonzero() == 48

    # Test timezone conversion
    start = price.data[0]["start"]
    assert start.tzinfo == dt_util.get_time_zone("Europe/Stockholm")
    assert start.hour == 0
    price_utc = price.copy().to_utc()
    start = price_utc.data[0]["start"]
    assert start.tzinfo == dt_util.UTC
    assert start.hour == 22
    price_local = price_utc.copy().to_local()
    start = price_local.data[0]["start"]
    assert start.tzinfo == dt_util.get_time_zone("Europe/Stockholm")
    assert start.hour == 0

    # Test with empty data
    price = Raw([], PLATFORM_GESPOT)
    assert not price.is_valid()
    assert price.last_value() is None
