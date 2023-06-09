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
    PLATFORM_NORDPOOL,
    READY_HOUR_NONE,
    START_HOUR_NONE,
)

_LOGGER = logging.getLogger(__name__)


def convert_raw_item(
    item: dict[str, Any], platform: str = PLATFORM_NORDPOOL
) -> dict[str, Any]:
    """Convert raw item to the internal format"""

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

    if platform == PLATFORM_NORDPOOL:
        if item["value"] is not None and isinstance(item["start"], datetime):
            return item

    # Array of item = {
    #   "hour": datetime,
    #   "price": float,
    # }
    # {'hour': datetime.datetime(2023, 3, 6, 0, 0,
    #          tzinfo=<DstTzInfo 'Europe/Stockholm' CET+1:00:00 STD>),
    #  'price': 146.96}
    if platform == PLATFORM_ENERGIDATASERVICE:
        if item["price"] is not None and isinstance(item["hour"], datetime):
            item_new = {}
            item_new["value"] = item["price"]
            item_new["start"] = item["hour"]
            item_new["end"] = item["hour"] + timedelta(hours=1)
            return item_new

    # Array of item = {
    #   "time": datetime,
    #   "price": float,
    # }
    # {'time': '2023-03-06 00:00:00+01:00', 'price': 0.1306} time is not datetime
    if platform == PLATFORM_ENTSOE:
        if item["price"] is not None and isinstance(item["time"], str):
            item_new = {}
            item_new["value"] = item["price"]
            item_new["start"] = datetime.fromisoformat(item["time"])
            item_new["end"] = item_new["start"] + timedelta(hours=1)
            return item_new

    return None


class Raw:
    """Class to handle raw data

    Array of item = {
        "start": datetime,
        "end": datetime,
        "value": float,
    }"""

    def __init__(
        self, raw: list[dict[str, Any]], platform: str = PLATFORM_NORDPOOL
    ) -> None:
        self.data = []
        if raw:
            for item in raw:
                item_new = convert_raw_item(item, platform)
                if item_new is not None:
                    self.data.append(item_new)

            self.valid = len(self.data) > 12
        else:
            self.valid = False

    def get_raw(self):
        """Get raw data"""
        return self.data

    def is_valid(self) -> bool:
        """Get valid"""
        return self.valid

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


def get_lowest_hours(
    start_hour: datetime,
    ready_hour: datetime,
    continuous: bool,
    raw_two_days: Raw,
    hours: int,
) -> list:
    """From the two-day prices, calculate the cheapest set of hours"""

    if continuous:
        return get_lowest_hours_continuous(start_hour, ready_hour, raw_two_days, hours)

    return get_lowest_hours_non_continuous(start_hour, ready_hour, raw_two_days, hours)


def get_lowest_hours_non_continuous(
    start_hour: datetime, ready_hour: datetime, raw_two_days: Raw, hours: int
) -> list:
    """From the two-day prices, calculate the cheapest non-continues set of hours

    A non-continues range of hours will be choosen."""

    _LOGGER.debug("ready_hour = %s", ready_hour)

    if hours == 0:
        return []

    price = []
    for item in raw_two_days.get_raw():
        price.append(item["value"])
    time_start = dt.utcnow()
    if start_hour > time_start:
        time_start = start_hour
    time_end = ready_hour
    time_start_index = None
    time_end_index = None
    for index in range(len(price)):
        item = raw_two_days.get_raw()[index]
        if item["end"] > time_start and time_start_index is None:
            time_start_index = index
        if item["start"] < time_end:
            time_end_index = index

    if (time_end_index - time_start_index) < hours:
        return list(range(time_start_index, time_end_index + 1))

    prices = price[time_start_index : time_end_index + 1]
    sorted_index = sorted(range(len(prices)), key=prices.__getitem__)
    lowest_hours = [x + time_start_index for x in sorted(sorted_index[0:hours])]

    return lowest_hours


def get_lowest_hours_continuous(
    start_hour: datetime, ready_hour: datetime, raw_two_days: Raw, hours: int
) -> list:
    """From the two-day prices, calculate the cheapest continues set of hours

    A continues range of hours will be choosen."""

    _LOGGER.debug("ready_hour = %s", ready_hour)

    if hours == 0:
        return []

    price = []
    for item in raw_two_days.get_raw():
        price.append(item["value"])
    lowest_index = None
    lowest_price = None
    time_start = dt.utcnow()
    if start_hour > time_start:
        time_start = start_hour
    time_end = ready_hour
    # time_end = dt.now().replace(
    #     hour=ready_hour, minute=0, second=0, microsecond=0
    # ) + timedelta(days=1)
    time_start_index = None
    time_end_index = None
    for index in range(len(price)):
        item = raw_two_days.get_raw()[index]
        if item["end"] > time_start and time_start_index is None:
            time_start_index = index
        if item["start"] < time_end:
            time_end_index = index

    if (time_end_index - time_start_index) < hours:
        return list(range(time_start_index, time_end_index + 1))

    for index in range(time_start_index, time_end_index - hours + 2):
        if lowest_index is None:
            lowest_index = index
            lowest_price = sum(price[index : (index + hours)])
            continue
        new_price = sum(price[index : (index + hours)])
        if new_price < lowest_price:
            lowest_index = index
            lowest_price = new_price

    res = list(range(lowest_index, lowest_index + hours))
    return res


def get_charging_original(lowest_hours: list[int], raw_two_days: Raw) -> list:
    """Calculate charging information"""

    result = []
    hour = 0
    for item in raw_two_days.get_raw():
        new_item = deepcopy(item)
        if hour not in lowest_hours:
            new_item["value"] = None
        result.append(new_item)
        hour = hour + 1

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


def get_charging_hours(
    ev_soc: float, ev_target_soc: float, charing_pct_per_hour: float
) -> int:
    """Calculate the number of charging hours"""
    charging_hours = ceil(
        min(max(((ev_target_soc - ev_soc) / charing_pct_per_hour), 0), 24)
    )
    return charging_hours


def get_charging_value(charging):
    """Get value for charging now"""
    time_now = dt.now()
    for item in charging:
        if item["start"] <= time_now < item["end"]:
            return item["value"]
    return None


def get_ready_hour_utc(ready_hour_local: int) -> datetime:
    """Get the UTC time for the ready hour"""

    # if now_local <= ready_hour_local THEN ready_hour_utc is today
    # if now_local > ready_hour_local THEN ready_hour_utc is tomorrow

    time_local: datetime = dt.now()
    if time_local.hour >= ready_hour_local or ready_hour_local == 24:
        time_local = time_local + timedelta(days=1)
    if ready_hour_local == READY_HOUR_NONE:
        time_local = time_local + timedelta(days=3)
    time_local = time_local.replace(
        hour=ready_hour_local % 24, minute=0, second=0, microsecond=0
    )
    return dt.as_utc(time_local)


def get_start_hour_utc(start_hour_local: int, ready_hour_local: int) -> datetime:
    """Get the UTC time for the ready hour"""

    # if now_local <= ready_hour_local THEN ready_hour_utc is today
    # if now_local > ready_hour_local THEN ready_hour_utc is tomorrow

    time_local: datetime = dt.now()
    if start_hour_local == START_HOUR_NONE:
        time_local = time_local + timedelta(days=-2)
    elif ready_hour_local != READY_HOUR_NONE:
        if start_hour_local < ready_hour_local:
            if time_local.hour >= ready_hour_local:
                time_local = time_local + timedelta(days=1)
        else:
            if time_local.hour < ready_hour_local:
                time_local = time_local + timedelta(days=-1)

    time_local = time_local.replace(
        hour=start_hour_local % 24, minute=0, second=0, microsecond=0
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
        self.charging_number_of_hours = 0

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

        charging_hours: int = get_charging_hours(
            params["ev_soc"],
            params["ev_target_soc"],
            params["charging_pct_per_hour"],
        )
        _LOGGER.debug("charging_hours = %s", charging_hours)
        lowest_hours = get_lowest_hours(
            params["start_hour"],
            params["ready_hour"],
            params["switch_continuous"],
            raw_two_days,
            charging_hours,
        )
        _LOGGER.debug("lowest_hours = %s", lowest_hours)
        self.schedule_base = get_charging_original(lowest_hours, raw_two_days)

        if params["min_soc"] == 0.0:
            self.schedule_base_min_soc = []
            return

        charging_hours: int = get_charging_hours(
            params["ev_soc"],
            params["min_soc"],
            params["charging_pct_per_hour"],
        )
        _LOGGER.debug("charging_hours_min_soc = %s", charging_hours)
        lowest_hours = get_lowest_hours(
            params["start_hour"],
            params["ready_hour"],
            params["switch_continuous"],
            raw_two_days,
            charging_hours,
        )
        _LOGGER.debug("lowest_hours_min_soc = %s", lowest_hours)
        self.schedule_base_min_soc = get_charging_original(lowest_hours, raw_two_days)

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

        number_of_hours = 0
        first_start = None
        last_stop = None
        if self.schedule is not None:
            for item in self.schedule:
                if item["value"] != 0.0:
                    number_of_hours = number_of_hours + 1
                    last_stop = dt.as_local(item["end"])
                    if first_start is None:
                        first_start = dt.as_local(item["start"])

        self.charging_is_planned = number_of_hours != 0
        self.charging_number_of_hours = number_of_hours
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

    def get_charging_number_of_hours(self):
        """Get charging_number_of_hours"""
        return self.charging_number_of_hours

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
        end_time = start_time + timedelta(hours=1)
        result = []
        for hour in range(48):  # pylint: disable=unused-variable
            item = {
                "start": start_time,
                "end": end_time,
                "value": 0.0,
            }
            result.append(item)
            start_time = start_time + timedelta(hours=1)
            end_time = end_time + timedelta(hours=1)

        return result


def main():  # pragma: no cover
    """Main function to test code."""

    result = []
    value = [1, 4, 6, 6, 5, 3, 2, 2, 4, 4]
    start_time = dt.now().replace(minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)
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
    lowest = get_lowest_hours_continuous(start_time, end_time, raw2, 2)
    print("lowest = " + str(lowest))
    lowest = get_lowest_hours_non_continuous(start_time, end_time, raw2, 2)
    print("lowest = " + str(lowest))


if __name__ == "__main__":  # pragma: no cover
    main()
