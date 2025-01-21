"""Helpers for coordinator"""

from copy import deepcopy
from datetime import datetime, timedelta
import logging
from math import ceil
from typing import Any
from homeassistant.util import dt

from custom_components.ev_smart_charging.const import (
    PLATFORM_ENERGIDATASERVICE,
    PLATFORM_ENTSOE,
    PLATFORM_GENERIC,
    PLATFORM_NORDPOOL,
    PLATFORM_TGE,
    READY_QUARTER_NONE,
    START_QUARTER_NONE,
)
from custom_components.ev_smart_charging.helpers.general import Utils

_LOGGER = logging.getLogger(__name__)


class PriceFormat:
    """Described the format of price information"""

    def __init__(self, platform: str = None):
        self.start = None  # Can be "start", "time" or "hour"
        self.value = None  # Can be "price" or "value"
        self.start_is_string = None  # True if start is a string in ISO format, False if it is a datetime object

        if platform == PLATFORM_NORDPOOL:
            self.start = "start"
            self.value = "value"
            self.start_is_string = False
        if platform == PLATFORM_ENERGIDATASERVICE:
            self.start = "hour"
            self.value = "price"
            self.start_is_string = False
        if platform in [PLATFORM_ENTSOE, PLATFORM_GENERIC]:
            self.start = "time"
            self.value = "price"
            self.start_is_string = True
        if platform == PLATFORM_TGE:
            self.start = "time"
            self.value = "price"
            self.start_is_string = False


def convert_raw_item(item: dict[str, Any], price_format: PriceFormat) -> dict[str, Any]:
    """Convert raw item to the internal format"""

    try:
        item_new = {}
        item_new["value"] = item[price_format.value]
        if price_format.start_is_string:
            item_new["start"] = datetime.fromisoformat(item[price_format.start])
        else:
            item_new["start"] = item[price_format.start]
        item_new["end"] = item_new["start"] + timedelta(minutes=15)
    except (KeyError, ValueError, TypeError):
        return None

    # PLATFORM_NORDPOOL:
    #
    # Array of item = {
    #   "start": datetime,
    #   "end": datetime,
    #   "value": float,
    # }
    # {'start': datetime.datetime(2023, 3, 6, 0, 0,
    #           tzinfo=zoneinfo.ZoneInfo(key='Europe/Stockholm')),
    #  'end': datetime.datetime(2023, 3, 6, 1, 0,
    #         tzinfo=zoneinfo.ZoneInfo(key='Europe/Stockholm')),
    #  'value': 145.77}

    # PLATFORM_ENERGIDATASERVICE
    #
    # Array of item = {
    #   "hour": datetime,
    #   "price": float,
    # }
    # {'hour': datetime.datetime(2023, 3, 6, 0, 0,
    #          tzinfo=<DstTzInfo 'Europe/Stockholm' CET+1:00:00 STD>),
    #  'price': 146.96}

    # PLATFORM_ENTSOE
    #
    # Array of item = {
    #   "time": string,
    #   "price": float,
    # }
    # {'time': '2023-03-06 00:00:00+01:00', 'price': 0.1306} time is not datetime

    # PLATFORM_TGE
    #
    # Array of item = {
    #   "time": datetime,
    #   "price": float,
    # }
    # {'time': datetime.datetime(2023, 3, 6, 0, 0,
    #          tzinfo=<DstTzInfo 'Europe/Stockholm' CET+1:00:00 STD>),
    #  'price': 146.96}

    # PLATFORM_GENERIC
    #
    # Array of item = {
    #   "time": string,
    #   "price": float,
    # }
    # {'time': '2023-03-06 00:00:00+01:00', 'price': 0.1306} time is not datetime

    return item_new


class Raw:
    """Class to handle raw data

    Array of item = {
        "start": datetime,
        "end": datetime,
        "value": float,
    }"""

    def add_three_extra_items(self, item: dict[str, Any]) -> None:
        """Add three extra items"""

        extra_item1 = {}
        extra_item1["value"] = item["value"]
        extra_item1["start"] = item["start"] + timedelta(minutes=15)
        extra_item1["end"] = item["start"] + timedelta(minutes=30)
        self.data.append(extra_item1)
        extra_item2 = {}
        extra_item2["value"] = item["value"]
        extra_item2["start"] = item["start"] + timedelta(minutes=30)
        extra_item2["end"] = item["start"] + timedelta(minutes=45)
        self.data.append(extra_item2)
        extra_item3 = {}
        extra_item3["value"] = item["value"]
        extra_item3["start"] = item["start"] + timedelta(minutes=45)
        extra_item3["end"] = item["start"] + timedelta(minutes=60)
        self.data.append(extra_item3)

    def __init__(
        self, raw: list[dict[str, Any]], price_format: PriceFormat = None
    ) -> None:
        self.data = []
        if raw:
            periodicity_60min = False
            for item in raw:
                if price_format:
                    item_new = convert_raw_item(item, price_format)
                else:
                    item_new = convert_raw_item(item, PriceFormat(PLATFORM_NORDPOOL))

                if len(self.data) == 1:
                    if item_new["start"].minute - self.data[-1]["start"].minute == 0:
                        # 60 minutes periodicity
                        periodicity_60min = True
                        self.add_three_extra_items(self.data[-1])
                    elif item_new["start"].minute - self.data[-1]["start"].minute == 15:
                        # 15 minutes periodicity
                        pass
                    else:
                        # Other periodicities not supported
                        _LOGGER.error(
                            "Periodicity %s minutes not supported",
                            item_new["start"].minute - self.data[-1]["start"].minute,
                        )
                        self.data = []
                        self.valid = False
                        return

                self.data.append(item_new)
                if periodicity_60min and len(self.data) > 1:
                    self.add_three_extra_items(self.data[-1])

            self.valid = len(self.data) > 12
        else:
            self.valid = False

    def get_raw(self):
        """Get raw data"""
        return self.data

    def is_valid(self, check_today_local=False) -> bool:
        """Get valid"""
        if not self.valid:
            return False
        if not check_today_local:
            return True
        else:
            # Check that self.data contains at least 12 valid prices for today
            nrof_valid_prices = 0
            for item in self.data:
                if item["start"].day == dt.now().day:
                    nrof_valid_prices = nrof_valid_prices + 1

            if nrof_valid_prices > 12:
                return True
            else:
                _LOGGER.debug(
                    "Less than 12 valid prices for today found in %s", self.data
                )
                return False

    def copy(self):
        """Get a copy of Raw"""
        return Raw(deepcopy(self.data))

    def extend(self, raw2):
        """Extend raw data with data from raw2."""
        if self.valid and raw2 is not None and raw2.is_valid():
            self.data.extend(raw2.get_raw())
        return self

    def max_value(self) -> float:
        """Return the largest value"""
        largest = None
        for item in self.data:
            if largest is None:
                largest = item["value"]
                continue
            if item["value"] > largest:
                largest = item["value"]
        return largest

    def last_value(self) -> float:
        """Return the last value"""
        if len(self.data) == 0:
            return None
        else:
            return self.data[-1]["value"]

    def number_of_nonzero(self) -> int:
        """Return the number of nonzero values"""
        number_items = 0
        for item in self.data:
            if item["value"] > 0.0:
                number_items = number_items + 1
        return number_items

    def get_value(self, time: datetime) -> float:
        """Get the value at time dt"""
        for item in self.data:
            if item["start"] <= time < item["end"]:
                return item["value"]
        return None

    def get_item(self, time: datetime) -> dict[str, Any]:
        """Get the item at time dt"""
        for item in self.data:
            if item["start"] <= time < item["end"]:
                return item
        return None

    def to_utc(self):
        """Change to UTC timezone"""
        for item in self.data:
            item["start"] = dt.as_utc(item["start"])
            item["end"] = dt.as_utc(item["end"])
        return self

    def to_local(self):
        """Change to local timezone"""
        for item in self.data:
            item["start"] = dt.as_local(item["start"])
            item["end"] = dt.as_local(item["end"])
        return self

    def today(self):
        """Only keep today's data"""
        today = dt.now().date()
        self.data = [item for item in self.data if item["start"].date() == today]
        self.valid = len(self.data) > 12
        return self

    def tomorrow(self):
        """Only keep tomorrow's data"""
        tomorrow = dt.now().date() + timedelta(days=1)
        self.data = [item for item in self.data if item["start"].date() == tomorrow]
        self.valid = len(self.data) > 12
        return self


def get_lowest_quarters(
    start_quarter: datetime,
    ready_quarter: datetime,
    continuous: bool,
    raw_two_days: Raw,
    quarters: int,
) -> list:
    """From the two-day prices, calculate the cheapest set of quarters"""

    if continuous:
        return get_lowest_quarters_continuous(
            start_quarter, ready_quarter, raw_two_days, quarters
        )

    return get_lowest_quarters_non_continuous(
        start_quarter, ready_quarter, raw_two_days, quarters
    )


def get_lowest_quarters_non_continuous(
    start_quarter: datetime, ready_quarter: datetime, raw_two_days: Raw, quarters: int
) -> list:
    """From the two-day prices, calculate the cheapest non-continues set of quarters

    A non-continues range of quarters will be choosen."""

    _LOGGER.debug("ready_quarter = %s", ready_quarter)

    if quarters == 0:
        return []

    price = []
    for item in raw_two_days.get_raw():
        price.append(item["value"])
    time_start = dt.utcnow()
    if start_quarter > time_start:
        time_start = start_quarter
    time_end = ready_quarter
    time_start_index = None
    time_end_index = None
    for index in range(len(price)):
        item = raw_two_days.get_raw()[index]
        if item["end"] > time_start and time_start_index is None:
            time_start_index = index
        if item["start"] < time_end:
            time_end_index = index

    if time_start_index is None or time_end_index is None:  # pragma: no cover
        _LOGGER.error("Is not able to calculate charging schedule!")
        _LOGGER.error("start_quarter = %s", start_quarter)
        _LOGGER.error("ready_quarter = %s", ready_quarter)
        _LOGGER.error("quarters = %s", quarters)
        if raw_two_days:
            if raw_two_days.data:
                _LOGGER.error("raw_two_days.data = %s", raw_two_days.data)
            else:
                _LOGGER.error("raw_two_days.data = None")
        else:
            _LOGGER.error("raw_two_days = None")
        return []

    if (time_end_index - time_start_index) < quarters:
        return list(range(time_start_index, time_end_index + 1))

    prices = price[time_start_index : time_end_index + 1]
    sorted_index = sorted(range(len(prices)), key=prices.__getitem__)

    # Find the lowest quarters. If the quarter with highest selected quarter has exactly the same price
    # as some of the not selected quarters, then the selected the quarters with that price which are
    # closest to the quarters with the second highest price.
    selected_quarters = sorted_index[0:quarters]
    highest_selected_price = prices[selected_quarters[-1]]
    # Find quarters in the same hour as the last selected quarter
    same_hour_quarters = [
        i
        for i in range(len(prices))
        if prices[i] == highest_selected_price
        and ((i + time_start_index) // 4)
        == ((selected_quarters[-1] + time_start_index) // 4)
    ]
    if same_hour_quarters[0] - 1 in selected_quarters:
        # If the quarter before "same_hour_quarters" selected, then do nothing.
        pass
    elif same_hour_quarters[-1] + 1 in selected_quarters:
        # If the quarter after "same_hour_quarters" selected, then make sure the selected quarters
        # within "same_hour_quarter" are as late as possible within that hour, and in reverse order.
        q1 = [i for i in selected_quarters if i not in same_hour_quarters]
        n1 = len([i for i in same_hour_quarters if i in selected_quarters])
        q2 = same_hour_quarters[::-1][0:n1]
        selected_quarters = q1 + q2

    lowest_quarters = [x + time_start_index for x in sorted(selected_quarters)]

    return lowest_quarters


def get_lowest_quarters_continuous(
    start_quarter: datetime, ready_quarter: datetime, raw_two_days: Raw, quarters: int
) -> list:
    """From the two-day prices, calculate the cheapest continues set of quarters

    A continues range of quarters will be choosen."""

    _LOGGER.debug("ready_quarter = %s", ready_quarter)

    if quarters == 0:
        return []

    price = []
    for item in raw_two_days.get_raw():
        price.append(item["value"])
    lowest_index = None
    lowest_price = None
    time_start = dt.utcnow()
    if start_quarter > time_start:
        time_start = start_quarter
    time_end = ready_quarter
    # time_end = dt.now().replace(
    #     quarter=ready_quarter, minute=0, second=0, microsecond=0
    # ) + timedelta(days=1)
    time_start_index = None
    time_end_index = None
    for index in range(len(price)):
        item = raw_two_days.get_raw()[index]
        if item["end"] > time_start and time_start_index is None:
            time_start_index = index
        if item["start"] < time_end:
            time_end_index = index

    if time_start_index is None or time_end_index is None:  # pragma: no cover
        _LOGGER.error("Is not able to calculate charging schedule!")
        _LOGGER.error("start_quarter = %s", start_quarter)
        _LOGGER.error("ready_quarter = %s", ready_quarter)
        _LOGGER.error("quarters = %s", quarters)
        if raw_two_days:
            if raw_two_days.data:
                _LOGGER.error("raw_two_days.data = %s", raw_two_days.data)
            else:
                _LOGGER.error("raw_two_days.data = None")
        else:
            _LOGGER.error("raw_two_days = None")
        return []

    if (time_end_index - time_start_index) < quarters:
        return list(range(time_start_index, time_end_index + 1))

    for index in range(time_start_index, time_end_index - quarters + 2):
        if lowest_index is None:
            lowest_index = index
            lowest_price = sum(price[index : (index + quarters)])
            continue
        new_price = sum(price[index : (index + quarters)])
        if new_price < lowest_price:
            lowest_index = index
            lowest_price = new_price

    res = list(range(lowest_index, lowest_index + quarters))
    return res


def get_charging_original(lowest_quarters: list[int], raw_two_days: Raw) -> list:
    """Calculate charging information"""

    result = []
    quarter = 0
    for item in raw_two_days.get_raw():
        new_item = deepcopy(item)
        if quarter not in lowest_quarters:
            new_item["value"] = None
        result.append(new_item)
        quarter = quarter + 1

    return result


def get_charging_update(
    charging_original: list,
    active: bool,
    apply_limit: bool,
    max_price: float,
    value_in_graph: float,
) -> list:
    """Update the charging schedule"""

    result = deepcopy(charging_original)  # Make a copy, not a reference.
    for item in result:
        if item["value"] is None:
            item["value"] = 0.0
        elif not active:
            item["value"] = 0.0
        elif apply_limit and item["value"] > max_price:
            item["value"] = 0.0
        else:
            item["value"] = value_in_graph

    return result


def get_charging_quarters(
    ev_soc: float, ev_target_soc: float, charing_pct_per_hour: float
) -> int:
    """Calculate the number of charging quarters"""
    charging_quarters = ceil(
        min(max(((ev_target_soc - ev_soc) / charing_pct_per_hour * 4), 0), 24 * 4)
    )
    return charging_quarters


def get_charging_value(charging):
    """Get value for charging now"""
    time_now = dt.now()
    for item in charging:
        if item["start"] <= time_now < item["end"]:
            return item["value"]
    return None


def get_ready_quarter_utc(ready_quarter_local: int) -> datetime:
    """Get the UTC time for the ready quarter"""

    # if now_local <= ready_quarter_local THEN ready_quarter_utc is today
    # if now_local > ready_quarter_local THEN ready_quarter_utc is tomorrow

    time_local: datetime = dt.now()
    if Utils.datetime_quarter(
        time_local
    ) >= ready_quarter_local or ready_quarter_local == (
        24 * 4
    ):  # TODO is * 4 correct?
        time_local = time_local + timedelta(days=1)
    if ready_quarter_local == READY_QUARTER_NONE:
        time_local = time_local + timedelta(days=3)
    time_local = time_local.replace(
        hour=(ready_quarter_local // 4) % 24,
        minute=(ready_quarter_local % 4) * 15,
        second=0,
        microsecond=0,
    )
    return dt.as_utc(time_local)


def get_start_quarter_utc(
    start_quarter_local: int, ready_quarter_local: int
) -> datetime:
    """Get the UTC time for the ready quarter"""

    # if now_local <= ready_quarter_local THEN ready_quarter_utc is today
    # if now_local > ready_quarter_local THEN ready_quarter_utc is tomorrow

    time_local: datetime = dt.now()
    if start_quarter_local == START_QUARTER_NONE:
        time_local = time_local + timedelta(days=-2)
    elif ready_quarter_local != READY_QUARTER_NONE:
        if start_quarter_local < ready_quarter_local:
            if Utils.datetime_quarter(time_local) >= ready_quarter_local:
                time_local = time_local + timedelta(days=1)
        else:
            if Utils.datetime_quarter(time_local) < ready_quarter_local:
                time_local = time_local + timedelta(days=-1)

    time_local = time_local.replace(
        hour=(start_quarter_local // 4) % 24,
        minute=(start_quarter_local % 4) * 15,
        second=0,
        microsecond=0,
    )
    return dt.as_utc(time_local)


class Scheduler:
    """Class to handle charging schedules"""

    def __init__(self) -> None:
        self.schedule_base = []
        self.schedule_base_min_soc = []
        self.schedule = None
        self.charging_is_planned = False
        self.charging_start_time = None
        self.charging_stop_time = None
        self.charging_number_of_quarters = 0

    def create_base_schedule(
        self,
        params: dict[str, Any],
        raw_two_days: Raw,
    ) -> None:
        """Create the base schedule"""

        if (
            "ev_soc" not in params
            or "ev_target_soc" not in params
            or "min_soc" not in params
        ):
            return

        charging_quarters: int = get_charging_quarters(
            params["ev_soc"],
            params["ev_target_soc"],
            params["charging_pct_per_hour"],
        )
        _LOGGER.debug("charging_quarters = %s", charging_quarters)
        lowest_quarters = get_lowest_quarters(
            params["start_quarter"],
            params["ready_quarter"],
            params["switch_continuous"],
            raw_two_days,
            charging_quarters,
        )
        _LOGGER.debug("lowest_quarters = %s", lowest_quarters)
        self.schedule_base = get_charging_original(lowest_quarters, raw_two_days)

        if params["min_soc"] == 0.0:
            self.schedule_base_min_soc = []
            return

        charging_quarters: int = get_charging_quarters(
            params["ev_soc"],
            params["min_soc"],
            params["charging_pct_per_hour"],
        )
        _LOGGER.debug("charging_quarters_min_soc = %s", charging_quarters)
        lowest_quarters = get_lowest_quarters(
            params["start_quarter"],
            params["ready_quarter"],
            params["switch_continuous"],
            raw_two_days,
            charging_quarters,
        )
        _LOGGER.debug("lowest_quarters_min_soc = %s", lowest_quarters)
        self.schedule_base_min_soc = get_charging_original(
            lowest_quarters, raw_two_days
        )

    def base_schedule_exists(self) -> bool:
        """Return true if base schedule exists"""
        return len(self.schedule_base) > 0

    def get_schedule(self, params: dict[str, Any]) -> list:
        """Calculate the schedule"""

        if "switch_active" not in params or "switch_apply_limit" not in params:
            self.schedule = None
            self.calc_schedule_summary()
            return self.schedule

        schedule = get_charging_update(
            self.schedule_base,
            params["switch_active"],
            params["switch_apply_limit"],
            params["max_price"],
            params["value_in_graph"],
        )
        schedule_min_soc = get_charging_update(
            self.schedule_base_min_soc,
            params["switch_active"],
            False,
            params["max_price"],
            params["value_in_graph"],
        )
        _LOGGER.debug(
            "Raw(schedule).number_of_nonzero() = %s", Raw(schedule).number_of_nonzero()
        )
        _LOGGER.debug(
            "Raw(schedule_min_soc).number_of_nonzero() = %s",
            Raw(schedule_min_soc).number_of_nonzero(),
        )
        if (
            Raw(schedule).number_of_nonzero()
            < Raw(schedule_min_soc).number_of_nonzero()
        ):
            _LOGGER.debug("Use schedule_min_soc")
            self.schedule = schedule_min_soc
            self.calc_schedule_summary()
            return self.schedule

        _LOGGER.debug("Use schedule")
        self.schedule = schedule
        self.calc_schedule_summary()
        return self.schedule

    def calc_schedule_summary(self):
        """Calculate summary of schedule"""

        number_of_quarters = 0
        first_start = None
        last_stop = None
        if self.schedule is not None:
            for item in self.schedule:
                if item["value"] != 0.0:
                    number_of_quarters = number_of_quarters + 1
                    last_stop = dt.as_local(item["end"])
                    if first_start is None:
                        first_start = dt.as_local(item["start"])

        self.charging_is_planned = number_of_quarters != 0
        self.charging_number_of_quarters = number_of_quarters
        self.charging_start_time = first_start
        self.charging_stop_time = last_stop

    def get_charging_is_planned(self):
        """Get charging_is_planned"""
        return self.charging_is_planned

    def get_charging_start_time(self):
        """Get charging_start_time"""
        return self.charging_start_time

    def get_charging_stop_time(self):
        """Get charging_stop_time"""
        return self.charging_stop_time

    def get_charging_number_of_quarters(self):
        """Get charging_number_of_quarters"""
        return self.charging_number_of_quarters

    def set_empty_schedule(self):
        """Create an empty schedule"""
        self.schedule_base = []
        self.schedule_base_min_soc = []
        self.schedule = None
        self.calc_schedule_summary()

    @staticmethod
    def get_empty_schedule() -> list:
        """Create empty charging information"""

        start_time = dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=15)
        result = []
        for quarter in range(48 * 4):  # pylint: disable=unused-variable
            item = {
                "start": start_time,
                "end": end_time,
                "value": 0.0,
            }
            result.append(item)
            start_time = start_time + timedelta(minutes=15)
            end_time = end_time + timedelta(minutes=15)

        return result


def main():  # pragma: no cover
    """Main function to test code."""

    result = []
    value = [1, 4, 6, 6, 5, 3, 2, 2, 4, 4]
    start_time = dt.now().replace(minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(minutes=15)
    for nnnn in range(10):
        item = {
            "start": start_time,
            "end": end_time,
            "value": value[nnnn],
        }
        result.append(item)
    raw2 = Raw(result)
    print("r2.raw = " + str(raw2.get_raw()))
    print("price = ", value)
    lowest = get_lowest_quarters_continuous(start_time, end_time, raw2, 2)
    print("lowest = " + str(lowest))
    lowest = get_lowest_quarters_non_continuous(start_time, end_time, raw2, 2)
    print("lowest = " + str(lowest))


if __name__ == "__main__":  # pragma: no cover
    main()
