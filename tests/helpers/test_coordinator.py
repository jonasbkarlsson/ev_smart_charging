"""Test ev_smart_charging/helpers/coordinator.py"""

from datetime import datetime

from homeassistant.util import dt as dt_util
from custom_components.ev_smart_charging.const import (
    PLATFORM_ENERGIDATASERVICE,
    PLATFORM_ENTSOE,
    PLATFORM_TGE,
    READY_QUARTER_NONE,
    START_QUARTER_NONE,
)

from custom_components.ev_smart_charging.helpers.coordinator import (
    PriceFormat,
    Raw,
    Scheduler,
    get_charging_quarters,
    get_charging_original,
    get_charging_update,
    get_charging_value,
    get_lowest_quarters,
    get_ready_quarter_utc,
    get_start_quarter_utc,
)
from tests.price import (
    PRICE_20220930,
    PRICE_20220930_ENERGIDATASERVICE,
    PRICE_20220930_ENTSOE,
    PRICE_20220930_TGE,
    PRICE_20221001,
    PRICE_20221001_ENERGIDATASERVICE,
    PRICE_20221001_ENTSOE,
    PRICE_20221001_TGE,
)
from tests.schedule import MOCK_SCHEDULE_20220930

# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
# side of the assertion matches with the right side.


# pylint: disable=unused-argument
async def test_raw(hass, set_cet_timezone, freezer):
    """Test Raw"""

    freezer.move_to("2022-09-30T00:10:00+02:00")

    price = Raw(PRICE_20220930)
    #    assert price.get_raw() == PRICE_20220930
    assert price.is_valid()
    #    assert price.copy().get_raw() == PRICE_20220930
    assert price.max_value() == 388.65
    assert price.last_value() == 49.64
    assert price.number_of_nonzero() == 24 * 4
    assert len(price.copy().today().get_raw()) == 24 * 4
    assert len(price.copy().tomorrow().get_raw()) == 0

    time = datetime(
        2022, 9, 30, 8, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert price.get_value(time) == 388.65
    assert price.get_item(time) == {
        "start": datetime(
            2022, 9, 30, 8, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
        ),
        "end": datetime(
            2022, 9, 30, 8, 15, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
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
    #    assert price.get_raw() == PRICE_20220930
    price.extend(price2)
    assert price.number_of_nonzero() == 48 * 4
    assert len(price.copy().today().get_raw()) == 24 * 4
    assert len(price.copy().tomorrow().get_raw()) == 24 * 4

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
    assert price.last_value() is None

    price = Raw(PRICE_20221001)
    assert len(price.copy().today().get_raw()) == 0


async def test_raw_energidataservice(hass, set_cet_timezone):
    """Test Raw"""

    price_format = PriceFormat(PLATFORM_ENERGIDATASERVICE)
    price = Raw(PRICE_20220930_ENERGIDATASERVICE, price_format)
    #    assert price.get_raw() == PRICE_20220930
    assert price.is_valid()
    #    assert price.copy().get_raw() == PRICE_20220930
    assert price.max_value() == 388.65
    assert price.last_value() == 49.64
    assert price.number_of_nonzero() == 24 * 4

    time = datetime(
        2022, 9, 30, 8, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert price.get_value(time) == 388.65
    assert price.get_item(time) == {
        "start": datetime(
            2022, 9, 30, 8, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
        ),
        "end": datetime(
            2022, 9, 30, 8, 15, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
        ),
        "value": 388.65,
    }
    time = datetime(
        2022, 9, 29, 8, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert price.get_value(time) is None
    assert price.get_item(time) is None

    price2 = Raw(PRICE_20221001_ENERGIDATASERVICE, price_format)
    price.extend(None)
    #    assert price.get_raw() == PRICE_20220930
    price.extend(price2)
    assert price.number_of_nonzero() == 48 * 4

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

    price = Raw([], price_format)
    assert not price.is_valid()
    assert price.last_value() is None


async def test_raw_entsoe(hass, set_cet_timezone, freezer):
    """Test Raw"""

    freezer.move_to("2022-09-30T00:10:00+02:00")
    price_format = PriceFormat(PLATFORM_ENTSOE)
    price = Raw(PRICE_20220930_ENTSOE, price_format)
    #    assert price.get_raw() == PRICE_20220930
    assert price.is_valid()
    #    assert price.copy().get_raw() == PRICE_20220930
    assert price.max_value() == 388.65
    assert price.last_value() == 49.64
    assert price.number_of_nonzero() == 24 * 4

    time = datetime(
        2022, 9, 30, 8, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert price.get_value(time) == 388.65
    assert price.get_item(time) == {
        "start": datetime(
            2022, 9, 30, 8, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
        ),
        "end": datetime(
            2022, 9, 30, 8, 15, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
        ),
        "value": 388.65,
    }
    time = datetime(
        2022, 9, 29, 8, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert price.get_value(time) is None
    assert price.get_item(time) is None

    price2 = Raw(PRICE_20221001_ENTSOE, price_format)
    price.extend(None)
    #    assert price.get_raw() == PRICE_20220930
    price.extend(price2)
    assert price.number_of_nonzero() == 48 * 4

    start = price.data[0]["start"]
    assert start.tzinfo.utcoffset(datetime.now()) == dt_util.get_time_zone(
        "Europe/Stockholm"
    ).utcoffset(datetime.now())
    assert start.hour == 0
    price_utc = price.copy().to_utc()
    start = price_utc.data[0]["start"]
    assert start.tzinfo == dt_util.UTC
    assert start.hour == 22
    price_local = price_utc.copy().to_local()
    start = price_local.data[0]["start"]
    assert start.tzinfo == dt_util.get_time_zone("Europe/Stockholm")
    assert start.hour == 0

    price = Raw([], price_format)
    assert not price.is_valid()
    assert price.last_value() is None


async def test_raw_tge(hass, set_cet_timezone):
    """Test Raw"""

    price_format = PriceFormat(PLATFORM_TGE)
    price = Raw(PRICE_20220930_TGE, price_format)
    #    assert price.get_raw() == PRICE_20220930
    assert price.is_valid()
    #    assert price.copy().get_raw() == PRICE_20220930
    assert price.max_value() == 388.65
    assert price.last_value() == 49.64
    assert price.number_of_nonzero() == 24 * 4

    time = datetime(
        2022, 9, 30, 8, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert price.get_value(time) == 388.65
    assert price.get_item(time) == {
        "start": datetime(
            2022, 9, 30, 8, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
        ),
        "end": datetime(
            2022, 9, 30, 8, 15, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
        ),
        "value": 388.65,
    }
    time = datetime(
        2022, 9, 29, 8, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert price.get_value(time) is None
    assert price.get_item(time) is None

    price2 = Raw(PRICE_20221001_TGE, price_format)
    price.extend(None)
    #    assert price.get_raw() == PRICE_20220930
    price.extend(price2)
    assert price.number_of_nonzero() == 48 * 4

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

    price = Raw([], price_format)
    assert not price.is_valid()
    assert price.last_value() is None


async def test_get_lowest_quarters_non_continuous(hass, set_cet_timezone, freezer):
    """Test get_lowest_quarters()"""

    raw_two_days: Raw = Raw(PRICE_20220930)
    start_quarter: int = START_QUARTER_NONE

    freezer.move_to("2022-09-30T00:10:00+02:00")
    ready_quarter: int = 8 * 4
    quarters: int = 2 * 4
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    ) == list(range(2 * 4, 4 * 4))

    freezer.move_to("2022-09-30T15:10:00+02:00")
    ready_quarter: int = 8 * 4
    quarters: int = 5 * 4
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    ) == list(range(19 * 4, 24 * 4))

    raw2: Raw = Raw(PRICE_20221001)
    raw_two_days.extend(raw2)

    freezer.move_to("2022-09-30T15:10:00+02:00")
    ready_quarter: int = 8 * 4
    quarters: int = 5 * 4
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    ) == list(range(27 * 4, 32 * 4))

    quarters: int = 5 * 4
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    ) == list(range(27 * 4, 32 * 4))

    quarters = 0
    assert not get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    )

    freezer.move_to("2022-09-30T23:10:00+02:00")
    ready_quarter: int = 4 * 4
    quarters: int = 4 * 4
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    ) == list(range(23 * 4, 24 * 4)) + list(range(25 * 4, 28 * 4))

    freezer.move_to("2022-09-30T23:10:00+02:00")
    ready_quarter: int = 4 * 4
    quarters: int = 5 * 4
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    ) == list(range(23 * 4, 28 * 4))

    freezer.move_to("2022-09-30T23:10:00+02:00")
    ready_quarter: int = 4 * 4
    quarters: int = 6 * 4
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    ) == list(range(23 * 4, 28 * 4))

    freezer.move_to("2022-09-30T00:10:00+02:00")
    ready_quarter: int = 8 * 4
    quarters: int = 5 * 4
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    ) == list(range(0 * 4, 5 * 4))

    freezer.move_to("2022-09-30T00:10:00+02:00")
    ready_quarter: int = 8 * 4
    quarters: int = 2 * 4
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    ) == list(range(2 * 4, 4 * 4))

    start_quarter = 4 * 4
    ready_quarter: int = 8 * 4
    quarters: int = 2 * 4
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    ) == list(range(4 * 4, 6 * 4))

    start_quarter: int = 0 * 4
    ready_quarter: int = 8 * 4
    quarters: int = 5 * 4
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        True,
        raw_two_days,
        quarters,
    ) == list(range(0 * 4, 5 * 4))

    start_quarter: int = 15 * 4
    ready_quarter: int = 0 * 4
    quarters: int = 3 * 4
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        True,
        raw_two_days,
        quarters,
    ) == list(range(21 * 4, 24 * 4))


async def test_get_lowest_quarters_non_continuous_15min(
    hass, set_cet_timezone, freezer
):
    """Test get_lowest_quarters()"""

    raw_two_days: Raw = Raw(PRICE_20220930)
    start_quarter: int = START_QUARTER_NONE

    freezer.move_to("2022-09-30T00:10:00+02:00")
    ready_quarter: int = 9
    quarters: int = 2
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    ) == [7, 8]

    ready_quarter: int = 9
    quarters: int = 4
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    ) == [5, 6, 7, 8]

    ready_quarter: int = 10
    quarters: int = 4
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    ) == [6, 7, 8, 9]

    ready_quarter: int = 20
    quarters: int = 9
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    ) == [8, 9, 10, 11, 12, 13, 14, 15, 16]

    ready_quarter: int = 20
    quarters: int = 11
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    ) == [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]

    freezer.move_to("2022-09-30T14:10:00+02:00")
    ready_quarter: int = 20 * 4
    quarters: int = 10
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        False,
        raw_two_days,
        quarters,
    ) == [58, 59, 60, 61, 62, 63, 76, 77, 78, 79]


async def test_get_lowest_quarters_continuous(hass, set_cet_timezone, freezer):
    """Test get_lowest_quarters()"""

    raw_two_days: Raw = Raw(PRICE_20220930)
    start_quarter: int = START_QUARTER_NONE

    freezer.move_to("2022-09-30T00:10:00+02:00")
    ready_quarter: int = 8
    quarters: int = 2
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        True,
        raw_two_days,
        quarters,
    ) == [
        2,
        3,
    ]

    freezer.move_to("2022-09-30T15:10:00+02:00")
    ready_quarter: int = 8
    quarters: int = 5
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        True,
        raw_two_days,
        quarters,
    ) == [
        19,
        20,
        21,
        22,
        23,
    ]

    raw2: Raw = Raw(PRICE_20221001)
    raw_two_days.extend(raw2)

    freezer.move_to("2022-09-30T15:10:00+02:00")
    ready_quarter: int = 8
    quarters: int = 5
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        True,
        raw_two_days,
        quarters,
    ) == [
        27,
        28,
        29,
        30,
        31,
    ]
    quarters = 0
    assert not get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        True,
        raw_two_days,
        quarters,
    )

    freezer.move_to("2022-09-30T15:10:00+02:00")
    ready_quarter: int = 6
    quarters: int = 5
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        True,
        raw_two_days,
        quarters,
    ) == [
        25,
        26,
        27,
        28,
        29,
    ]

    freezer.move_to("2022-09-30T23:10:00+02:00")
    ready_quarter: int = 6
    quarters: int = 10
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        True,
        raw_two_days,
        quarters,
    ) == [
        23,
        24,
        25,
        26,
        27,
        28,
        29,
    ]

    freezer.move_to("2022-09-30T23:10:00+02:00")
    ready_quarter: int = 4
    quarters: int = 4
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        True,
        raw_two_days,
        quarters,
    ) == [
        24,
        25,
        26,
        27,
    ]

    freezer.move_to("2022-09-30T00:10:00+02:00")
    ready_quarter: int = 8
    quarters: int = 5
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        True,
        raw_two_days,
        quarters,
    ) == [
        0,
        1,
        2,
        3,
        4,
    ]

    freezer.move_to("2022-09-30T00:10:00+02:00")
    ready_quarter: int = 8
    quarters: int = 2
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        True,
        raw_two_days,
        quarters,
    ) == [
        2,
        3,
    ]

    start_quarter: int = 4
    ready_quarter: int = 8
    quarters: int = 2
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        True,
        raw_two_days,
        quarters,
    ) == [
        4,
        5,
    ]

    start_quarter: int = 0
    ready_quarter: int = 8
    quarters: int = 5
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        True,
        raw_two_days,
        quarters,
    ) == [
        0,
        1,
        2,
        3,
        4,
    ]

    start_quarter: int = 15
    ready_quarter: int = 0
    quarters: int = 3
    assert get_lowest_quarters(
        get_start_quarter_utc(start_quarter, ready_quarter),
        get_ready_quarter_utc(ready_quarter),
        True,
        raw_two_days,
        quarters,
    ) == [
        21,
        22,
        23,
    ]


async def test_get_charging_original(hass, set_cet_timezone, freezer):
    """Test get_charging_original()"""

    raw_two_days: Raw = Raw(PRICE_20220930)
    raw2: Raw = Raw(PRICE_20221001)
    raw_two_days.extend(raw2)

    freezer.move_to("2022-09-30T15:10:00+02:00")
    lowest_quarters = [27, 28, 29, 30, 31]
    result: list = get_charging_original(lowest_quarters, raw_two_days)
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


async def test_get_charging_quarters(hass):
    """Test get_charging_quarters()"""

    ev_soc = 50
    ev_target_soc = 80
    charing_pct_per_hour = 8
    assert get_charging_quarters(ev_soc, ev_target_soc, charing_pct_per_hour) == 4


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
        "start_quarter": get_start_quarter_utc(START_QUARTER_NONE, 7),
        "ready_quarter": get_ready_quarter_utc(7),
        "switch_active": True,
        "switch_continuous": True,
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
    assert scheduler.get_charging_number_of_quarters() == 4

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
    assert scheduler.get_charging_number_of_quarters() == 8

    scheduler.set_empty_schedule()
    assert scheduler.get_charging_is_planned() is False
    assert scheduler.get_charging_start_time() is None
    assert scheduler.get_charging_stop_time() is None
    assert scheduler.get_charging_number_of_quarters() == 0


async def test_get_empty_schedule(hass, set_cet_timezone, freezer):
    """Test Scheduler.get_empty_schedule()"""

    freezer.move_to("2022-10-01T02:10:00+0200")
    empty_schedule: list = Scheduler.get_empty_schedule()
    assert len(empty_schedule) == 48 * 4
    assert empty_schedule[0]["start"] == datetime(
        2022, 10, 1, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert empty_schedule[0]["end"] == datetime(
        2022, 10, 1, 0, 15, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert empty_schedule[0]["value"] == 0
    assert empty_schedule[191]["start"] == datetime(
        2022, 10, 2, 23, 45, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert empty_schedule[191]["end"] == datetime(
        2022, 10, 3, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert empty_schedule[191]["value"] == 0


async def test_get_ready_quarter_utc(hass, set_cet_timezone, freezer):
    """Test get_ready_quarter_utc()"""

    freezer.move_to("2022-10-01T12:00:00+0200")

    datetime1 = get_ready_quarter_utc(4 * 4)
    assert datetime1 == datetime(
        2022, 10, 2, 4, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )

    datetime1 = get_ready_quarter_utc(14 * 4)
    assert datetime1 == datetime(
        2022, 10, 1, 14, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )

    datetime1 = get_ready_quarter_utc(24 * 4)
    assert datetime1 == datetime(
        2022, 10, 2, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )

    datetime1 = get_ready_quarter_utc(READY_QUARTER_NONE)
    assert datetime1 == datetime(
        2022, 10, 4, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )


async def test_get_start_quarter_utc(hass, set_cet_timezone, freezer):
    """Test get_ready_quarter_utc()"""

    # IF start < end
    #   IF time < end
    #     start is today, end is today
    #   IF time >= end
    #     start is tomorrow, end is tomorrow

    start_quarter_local = 5 * 4
    ready_quarter_local = 8 * 4

    freezer.move_to("2022-10-01T03:00:00+0200")
    datetime1 = get_start_quarter_utc(start_quarter_local, ready_quarter_local)
    assert datetime1 == datetime(
        2022, 10, 1, 5, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    freezer.move_to("2022-10-01T06:00:00+0200")
    datetime1 = get_start_quarter_utc(start_quarter_local, ready_quarter_local)
    assert datetime1 == datetime(
        2022, 10, 1, 5, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    freezer.move_to("2022-10-01T08:00:00+0200")
    datetime1 = get_start_quarter_utc(start_quarter_local, ready_quarter_local)
    assert datetime1 == datetime(
        2022, 10, 2, 5, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    freezer.move_to("2022-10-01T09:00:00+0200")
    datetime1 = get_start_quarter_utc(start_quarter_local, ready_quarter_local)
    assert datetime1 == datetime(
        2022, 10, 2, 5, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )

    # IF start > end
    #   IF time < end
    #     start is yesterday, end is today
    #   IF time >= end
    #     start is today, end is tomorrow

    start_quarter_local = 15 * 4
    ready_quarter_local = 5 * 4

    freezer.move_to("2022-10-01T03:00:00+0200")
    datetime1 = get_start_quarter_utc(start_quarter_local, ready_quarter_local)
    assert datetime1 == datetime(
        2022, 9, 30, 15, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    freezer.move_to("2022-10-01T05:00:00+0200")
    datetime1 = get_start_quarter_utc(start_quarter_local, ready_quarter_local)
    assert datetime1 == datetime(
        2022, 10, 1, 15, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    freezer.move_to("2022-10-01T06:00:00+0200")
    datetime1 = get_start_quarter_utc(start_quarter_local, ready_quarter_local)
    assert datetime1 == datetime(
        2022, 10, 1, 15, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    freezer.move_to("2022-10-01T16:00:00+0200")
    datetime1 = get_start_quarter_utc(start_quarter_local, ready_quarter_local)
    assert datetime1 == datetime(
        2022, 10, 1, 15, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )

    # IF start == end
    #     IF time < end
    #         start is yesterday, end is today
    #     IF time >= end
    #         start is today, end is tomorrow

    start_quarter_local = 10 * 4
    ready_quarter_local = 10 * 4

    freezer.move_to("2022-10-01T03:00:00+0200")
    datetime1 = get_start_quarter_utc(start_quarter_local, ready_quarter_local)
    assert datetime1 == datetime(
        2022, 9, 30, 10, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    freezer.move_to("2022-10-01T10:00:00+0200")
    datetime1 = get_start_quarter_utc(start_quarter_local, ready_quarter_local)
    assert datetime1 == datetime(
        2022, 10, 1, 10, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    freezer.move_to("2022-10-01T16:00:00+0200")
    datetime1 = get_start_quarter_utc(start_quarter_local, ready_quarter_local)
    assert datetime1 == datetime(
        2022, 10, 1, 10, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )

    # IF only end
    #     IF time < end
    #          end is today
    #     IF time >= end
    #         end is tomorrow

    start_quarter_local = START_QUARTER_NONE
    ready_quarter_local = 10 * 4

    freezer.move_to("2022-10-01T03:00:00+0200")
    datetime1 = get_start_quarter_utc(start_quarter_local, ready_quarter_local)
    assert datetime1 == datetime(
        2022, 9, 29, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )

    # IF only start
    #      start is today

    start_quarter_local = 10 * 4
    ready_quarter_local = READY_QUARTER_NONE

    freezer.move_to("2022-10-01T03:00:00+0200")
    datetime1 = get_start_quarter_utc(start_quarter_local, ready_quarter_local)
    assert datetime1 == datetime(
        2022, 10, 1, 10, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    freezer.move_to("2022-10-01T13:00:00+0200")
    datetime1 = get_start_quarter_utc(start_quarter_local, ready_quarter_local)
    assert datetime1 == datetime(
        2022, 10, 1, 10, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
