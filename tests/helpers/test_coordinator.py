"""Test ev_smart_charging/helpers/coordinator.py"""
from datetime import datetime

from homeassistant.util import dt as dt_util

from custom_components.ev_smart_charging.helpers.coordinator import (
    Raw,
    Scheduler,
    get_charging_hours,
    get_charging_original,
    get_charging_update,
    get_charging_value,
    get_lowest_hours,
    get_ready_hour_utc,
)
from tests.price import PRICE_20220930, PRICE_20221001
from tests.schedule import MOCK_SCHEDULE_20220930

# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
# side of the assertion matches with the right side.


# pylint: disable=unused-argument
async def test_raw(hass, set_cet_timezone):
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
    assert price.get_item(time) == {
        "start": datetime(
            2022, 9, 30, 8, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
        ),
        "end": datetime(
            2022, 9, 30, 9, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
        ),
        "value": 388.65,
    }
    time = datetime(
        2022, 9, 29, 8, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert price.get_value(time) is None
    assert price.get_item(time) is None

    price2 = Raw(PRICE_20221001)
    price.extend(None)
    assert price.get_raw() == PRICE_20220930
    price.extend(price2)
    assert price.number_of_nonzero() == 48

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

    price = Raw([])
    assert not price.is_valid()


async def test_get_lowest_hours(hass, set_cet_timezone, freezer):
    """Test get_lowest_hours()"""

    raw_two_days: Raw = Raw(PRICE_20220930)
    raw2: Raw = Raw(PRICE_20221001)
    raw_two_days.extend(raw2)

    freezer.move_to("2022-09-30T15:10:00+02:00")
    ready_hour: int = 8
    hours: int = 5
    assert get_lowest_hours(get_ready_hour_utc(ready_hour), raw_two_days, hours) == [
        27,
        28,
        29,
        30,
        31,
    ]
    hours = 0
    assert not get_lowest_hours(get_ready_hour_utc(ready_hour), raw_two_days, hours)

    freezer.move_to("2022-09-30T15:10:00+02:00")
    ready_hour: int = 6
    hours: int = 5
    assert get_lowest_hours(get_ready_hour_utc(ready_hour), raw_two_days, hours) == [
        25,
        26,
        27,
        28,
        29,
    ]

    freezer.move_to("2022-09-30T23:10:00+02:00")
    ready_hour: int = 6
    hours: int = 10
    assert get_lowest_hours(get_ready_hour_utc(ready_hour), raw_two_days, hours) == [
        23,
        24,
        25,
        26,
        27,
        28,
        29,
    ]


async def test_get_charging_original(hass, set_cet_timezone, freezer):
    """Test get_charging_original()"""

    raw_two_days: Raw = Raw(PRICE_20220930)
    raw2: Raw = Raw(PRICE_20221001)
    raw_two_days.extend(raw2)

    freezer.move_to("2022-09-30T15:10:00+02:00")
    lowest_hours = [27, 28, 29, 30, 31]
    result: list = get_charging_original(lowest_hours, raw_two_days)
    assert result[26]["value"] is None
    assert result[27]["value"] is not None
    assert result[31]["value"] is not None
    assert result[32]["value"] is None
    assert result[27]["start"] == datetime(
        2022, 10, 1, 3, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )


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


async def test_get_charging_value(hass, set_cet_timezone, freezer):
    """Test get_charging_value()"""

    charging: list = MOCK_SCHEDULE_20220930

    freezer.move_to("2022-10-01T02:10:00+0200")
    assert get_charging_value(charging) == 0
    freezer.move_to("2022-10-01T03:10:00+0200")
    assert get_charging_value(charging) == 24.2
    freezer.move_to("2022-10-02T00:00:00+0200")
    assert get_charging_value(charging) is None


async def test_scheduler(hass, set_cet_timezone, freezer):
    """Test Scheduler"""

    new_raw_today = Raw(PRICE_20220930)
    new_raw_tomorrow = Raw(PRICE_20221001)
    raw_two_days = new_raw_today.copy()
    raw_two_days.extend(new_raw_tomorrow)

    scheduler = Scheduler()
    freezer.move_to("2022-09-30T14:10:00+0200")
    scheduling_params = {}
    scheduler.create_base_schedule(scheduling_params, raw_two_days)
    assert not scheduler.base_schedule_exists()

    scheduling_params = {
        "ev_soc": 50,
        "ev_target_soc": 80,
        "min_soc": 0,
        "charging_pct_per_hour": 4,
        "ready_hour": get_ready_hour_utc(7),
        "switch_active": True,
        "max_price": 30,
    }
    scheduler.create_base_schedule(scheduling_params, raw_two_days)
    assert scheduler.base_schedule_exists()
    assert scheduler.schedule_base
    assert not scheduler.schedule_base_min_soc

    scheduling_params.update({"min_soc": 40})

    scheduler.create_base_schedule(scheduling_params, raw_two_days)
    assert scheduler.base_schedule_exists()
    assert scheduler.schedule_base
    assert scheduler.schedule_base_min_soc

    scheduling_params.update({"value_in_graph": 300})

    new_charging: list = scheduler.get_schedule(scheduling_params)
    assert not new_charging

    scheduling_params.update({"switch_apply_limit": True})

    new_charging: list = scheduler.get_schedule(scheduling_params)
    assert new_charging
    assert new_charging[26]["value"] == 0
    assert new_charging[27]["value"] == 300

    assert scheduler.get_charging_is_planned() is True
    assert scheduler.get_charging_start_time() == datetime(
        2022, 10, 1, 3, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert scheduler.get_charging_stop_time() == datetime(
        2022, 10, 1, 7, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert scheduler.get_charging_number_of_hours() == 4

    scheduling_params.update({"min_soc": 80})
    scheduler.create_base_schedule(scheduling_params, raw_two_days)
    new_charging: list = scheduler.get_schedule(scheduling_params)
    assert new_charging
    assert new_charging[22]["value"] == 0
    assert new_charging[23]["value"] == 300

    assert scheduler.get_charging_is_planned() is True
    assert scheduler.get_charging_start_time() == datetime(
        2022, 9, 30, 23, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert scheduler.get_charging_stop_time() == datetime(
        2022, 10, 1, 7, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert scheduler.get_charging_number_of_hours() == 8


async def test_get_empty_schedule(hass, set_cet_timezone, freezer):
    """Test Scheduler.get_empty_schedule()"""

    freezer.move_to("2022-10-01T02:10:00+0200")
    empty_schedule: list = Scheduler.get_empty_schedule()
    assert len(empty_schedule) == 48
    assert empty_schedule[0]["start"] == datetime(
        2022, 10, 1, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert empty_schedule[0]["end"] == datetime(
        2022, 10, 1, 1, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert empty_schedule[0]["value"] == 0
    assert empty_schedule[47]["start"] == datetime(
        2022, 10, 2, 23, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert empty_schedule[47]["end"] == datetime(
        2022, 10, 3, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert empty_schedule[47]["value"] == 0
