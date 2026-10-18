"""Estimation of the EV SOC between reports from the EV"""

from datetime import datetime
import logging
from typing import Any

from homeassistant.util import dt

_LOGGER = logging.getLogger(__name__)


class SocEstimator:
    """Estimates the SOC as the last reported SOC plus the charging done since that report.

    Many EVs only report their SOC now and then, e.g. every 30 minutes or only when
    the car wakes up. The charging time is measured from the time of the last report
    and multiplied by the charging speed.
    """

    def __init__(self) -> None:
        self.reported_soc: float | None = None
        self.reported_at: datetime | None = None
        # Charging periods as [start, stop]. stop is None while charging.
        self.charging_periods: list[list[datetime | None]] = []

    def is_charging(self) -> bool:
        """Return True if charging is ongoing"""
        return bool(self.charging_periods) and self.charging_periods[-1][1] is None

    def set_charging(self, charging: bool, time_now: datetime) -> None:
        """Register the actual charging state"""
        if charging and not self.is_charging():
            self.charging_periods.append([time_now, None])
        if not charging and self.is_charging():
            self.charging_periods[-1][1] = time_now

    def report(self, soc: float, reported_at: datetime | None, time_now: datetime):
        """Register a SOC reported by the EV.

        A new SOC, or a newer report with unchanged SOC, restarts the charging time
        measurement, since charging before the report is included in the reported SOC.
        Returns True if the report was used.
        """
        if reported_at is None or reported_at > time_now:
            # Missing or invalid timestamp. Assume a new SOC is reported now.
            if soc == self.reported_soc:
                return False
            reported_at = time_now
        if soc == self.reported_soc and (
            self.reported_at is not None and reported_at <= self.reported_at
        ):
            return False
        if soc != self.reported_soc and self.reported_at is not None:
            # The timestamp is sometimes updated just after the SOC.
            reported_at = max(reported_at, self.reported_at)
        self.reported_soc = soc
        self.reported_at = reported_at
        self._remove_old_periods()
        return True

    def charging_hours(self, time_now: datetime) -> float:
        """Return the number of hours charged since the last report"""
        if self.reported_at is None:
            return 0.0
        seconds = 0.0
        for start, stop in self.charging_periods:
            start = max(start, self.reported_at)
            stop = time_now if stop is None else min(stop, time_now)
            if stop > start:
                seconds += (stop - start).total_seconds()
        return seconds / 3600

    def get_soc(
        self,
        time_now: datetime,
        pct_per_hour: float,
        max_soc: float | None = None,
    ) -> float | None:
        """Return the estimated SOC"""
        if self.reported_soc is None:
            return None
        limit = 100.0 if max_soc is None else min(max_soc, 100.0)
        soc = self.reported_soc + self.charging_hours(time_now) * pct_per_hour
        # Never estimate below the reported SOC, e.g. if Target SOC < reported SOC.
        return round(max(min(soc, limit), self.reported_soc), 1)

    def _remove_old_periods(self) -> None:
        """Remove charging periods that ended before the last report"""
        self.charging_periods = [
            period
            for period in self.charging_periods
            if period[1] is None or period[1] > self.reported_at
        ]

    def as_dict(self, time_now: datetime) -> dict[str, Any]:
        """Return the state as a dict that can be stored"""
        return {
            "reported_soc": self.reported_soc,
            "reported_at": (
                self.reported_at.isoformat() if self.reported_at is not None else None
            ),
            "charging_periods": [
                [start.isoformat(), stop.isoformat() if stop is not None else None]
                for start, stop in self.charging_periods
            ],
            "saved_at": time_now.isoformat(),
        }

    def restore(self, data: dict[str, Any]) -> None:
        """Restore the state from a dict created by as_dict()"""
        try:
            saved_at = dt.parse_datetime(data["saved_at"])
            self.reported_soc = data["reported_soc"]
            self.reported_at = (
                dt.parse_datetime(data["reported_at"]) if data["reported_at"] else None
            )
            # Charging is unknown while Home Assistant is not running,
            # so end an ongoing charging when the state was saved.
            self.charging_periods = [
                [
                    dt.parse_datetime(start),
                    dt.parse_datetime(stop) if stop is not None else saved_at,
                ]
                for start, stop in data["charging_periods"]
            ]
        except (KeyError, TypeError, ValueError) as err:
            _LOGGER.warning("Could not restore calculated SOC: %s", err)
            self.__init__()
