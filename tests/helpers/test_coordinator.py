"""Test ev_smart_charging/helpers/coordinator.py"""
from datetime import datetime
import pytest

from homeassistant.util import dt as dt_util

from custom_components.ev_smart_charging.helpers.coordinator import (
    Raw,
    get_charging_hours,
    get_charging_original,
    get_charging_update,
    get_charging_value,
    get_lowest_hours,
)
from tests.price import PRICE_20220930, PRICE_20221001
from tests.schedule import MOCK_SCHEDULE_20220930

# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
# side of the assertion matches with the right side.

# pylint: disable=unused-argument
async def test_raw(hass):
    """Test Raw"""

    price = Raw(PRICE_20220930)
    assert price.get_raw() == PRICE_20220930
    assert price.is_valid()
    assert price.copy().get_raw() == PRICE_20220930
    assert price.max_value() == 388.65
    assert price.number_of_nonzero() == 24

    time = datetime(
        2022, 9, 30, 8, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert price.get_value(time) == 388.65
    time = datetime(
        2022, 9, 29, 8, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert price.get_value(time) is None

    price2 = Raw(PRICE_20221001)
    price.extend(None)
    assert price.get_raw() == PRICE_20220930
    price.extend(price2)
    assert price.number_of_nonzero() == 48


# pylint: disable=unused-argument
@pytest.mark.freeze_time
async def test_get_lowest_hours(hass, set_cet_timezone, freezer):
    """Test get_lowest_hours()"""

    raw_two_days: Raw = Raw(PRICE_20220930)
    raw2: Raw = Raw(PRICE_20221001)
    raw_two_days.extend(raw2)

    freezer.move_to("2022-09-30 15:10:00+02:00")
    ready_hour: int = 8
    hours: int = 5
    assert get_lowest_hours(ready_hour, raw_two_days, hours) == [27, 28, 29, 30, 31]
    hours = 0
    assert not get_lowest_hours(ready_hour, raw_two_days, hours)

    freezer.move_to("2022-09-30 15:10:00+02:00")
    ready_hour: int = 6
    hours: int = 5
    assert get_lowest_hours(ready_hour, raw_two_days, hours) == [25, 26, 27, 28, 29]

    freezer.move_to("2022-09-30 23:10:00+02:00")
    ready_hour: int = 6
    hours: int = 10
    assert get_lowest_hours(ready_hour, raw_two_days, hours) == [
        23,
        24,
        25,
        26,
        27,
        28,
        29,
    ]


# pylint: disable=unused-argument
@pytest.mark.freeze_time
async def test_get_charging_original(hass, set_cet_timezone, freezer):
    """Test get_charging_original()"""

    raw_two_days: Raw = Raw(PRICE_20220930)
    raw2: Raw = Raw(PRICE_20221001)
    raw_two_days.extend(raw2)

    freezer.move_to("2022-09-30 15:10:00+02:00")
    lowest_hours = [27, 28, 29, 30, 31]
    result: list = get_charging_original(lowest_hours, raw_two_days)
    assert result[26]["value"] == 0
    assert result[27]["value"] != 0
    assert result[31]["value"] != 0
    assert result[32]["value"] == 0
    assert result[27]["start"] == "2022-10-01T03:00:00+0200"


async def test_get_charging_update(hass):
    """Test get_charging_update()"""

    charging_original: list = MOCK_SCHEDULE_20220930
    active = False
    apply_limit = False
    max_price = 20
    value_in_graph = 99

    # Test not active
    result = get_charging_update(
        charging_original, active, apply_limit, max_price, value_in_graph
    )
    assert result[27]["value"] == 0
    assert result[31]["value"] == 0

    # Test active
    active = True
    result = get_charging_update(
        charging_original, active, apply_limit, max_price, value_in_graph
    )
    assert result[27]["value"] == 99
    assert result[31]["value"] == 99

    # Test max_price
    apply_limit = True
    result = get_charging_update(
        charging_original, active, apply_limit, max_price, value_in_graph
    )
    assert result[27]["value"] == 0
    assert result[28]["value"] == 99
    assert result[30]["value"] == 99
    assert result[31]["value"] == 0


async def test_get_charging_hours(hass):
    """Test get_charging_hours()"""

    ev_soc = 50
    ev_target_soc = 80
    charing_pct_per_hour = 8
    assert get_charging_hours(ev_soc, ev_target_soc, charing_pct_per_hour) == 4


@pytest.mark.freeze_time
async def test_get_charging_value(hass, set_cet_timezone, freezer):
    """Test get_charging_value()"""

    charging: list = MOCK_SCHEDULE_20220930

    freezer.move_to("2022-10-01T02:10:00+0200")
    assert get_charging_value(charging) == 0
    freezer.move_to("2022-10-01T03:10:00+0200")
    assert get_charging_value(charging) == 24.2
    freezer.move_to("2022-10-02T00:00:00+0200")
    assert get_charging_value(charging) is None


# TODO: Add more tests
