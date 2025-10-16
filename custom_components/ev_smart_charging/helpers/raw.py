"""Raw data handling for price data"""

from copy import deepcopy
from datetime import datetime, timedelta
import logging
from typing import Any
from homeassistant.util import dt

from custom_components.ev_smart_charging.const import (
    PLATFORM_ENERGIDATASERVICE,
    PLATFORM_ENTSOE,
    PLATFORM_GENERIC,
    PLATFORM_GESPOT,
    PLATFORM_NORDPOOL,
    PLATFORM_TGE,
)

_LOGGER = logging.getLogger(__name__)


class PriceFormat:
    """Described the format of price information"""

    def __init__(self, platform: str | None = None):
        self.start = None  # Can be "start", "time" or "hour"
        self.value = None  # Can be "price" or "value"
        self.start_is_string = None  # True if start is a string in ISO format, False if it is a datetime object

        if platform == PLATFORM_NORDPOOL:
            self.start = "start"
            self.value = "value"
            self.start_is_string = False
        if platform == PLATFORM_GESPOT:
            self.start = "time"
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
        self, raw: list[dict[str, Any]], platform: str | PriceFormat | None = PLATFORM_NORDPOOL
    ) -> None:
        self.data = []
        if raw:
            periodicity_60min = False

            # Handle both string platform and PriceFormat object
            if isinstance(platform, PriceFormat):
                price_format = platform
            else:
                price_format = PriceFormat(platform)

            for item in raw:
                item_new = convert_raw_item(item, price_format)

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
