"""Test ev_smart_charging/helpers/soc_estimator.py"""

from datetime import datetime, timedelta

from homeassistant.util import dt

from custom_components.ev_smart_charging.helpers.soc_estimator import SocEstimator

T0 = datetime(2026, 10, 18, 6, 0, tzinfo=dt.UTC)


def at(minutes: float) -> datetime:
    """Return T0 plus minutes"""
    return T0 + timedelta(minutes=minutes)


async def test_soc_estimator_no_report():
    """Test the estimator before any report."""
    estimator = SocEstimator()
    assert estimator.get_soc(T0, 10.0) is None
    assert estimator.charging_hours(T0) == 0.0


async def test_soc_estimator_charging():
    """Test that charging since the report is added."""
    estimator = SocEstimator()
    assert estimator.report(40.0, at(0), at(0))
    assert estimator.get_soc(at(30), 10.0) == 40.0

    estimator.set_charging(True, at(30))
    assert estimator.is_charging()
    assert estimator.get_soc(at(90), 10.0) == 50.0
    estimator.set_charging(False, at(120))
    assert not estimator.is_charging()
    assert estimator.get_soc(at(180), 10.0) == 55.0

    # Capped at the Target SOC and 100%
    assert estimator.get_soc(at(180), 100.0, 80.0) == 80.0
    assert estimator.get_soc(at(180), 100.0, 120.0) == 100.0
    # Never below the reported SOC
    assert estimator.get_soc(at(180), 10.0, 30.0) == 40.0


async def test_soc_estimator_report_restarts_measurement():
    """Test that a new report only counts charging after the report."""
    estimator = SocEstimator()
    estimator.report(40.0, at(0), at(0))
    estimator.set_charging(True, at(0))

    # The EV reports at 60 minutes, received at 70 minutes
    assert estimator.report(50.0, at(60), at(70))
    assert estimator.get_soc(at(90), 10.0) == 55.0

    # A newer report with unchanged SOC moves the measurement start
    assert estimator.report(50.0, at(90), at(91))
    assert estimator.get_soc(at(120), 10.0) == 55.0

    # The same report again is ignored
    assert not estimator.report(50.0, at(90), at(130))
    assert estimator.get_soc(at(150), 10.0) == 60.0

    # Charging periods that ended before the report are removed
    estimator.set_charging(False, at(150))
    estimator.report(60.0, at(160), at(160))
    assert not estimator.charging_periods


async def test_soc_estimator_timestamp_after_soc():
    """Test a SOC that is updated before its timestamp."""
    estimator = SocEstimator()
    estimator.report(40.0, at(0), at(0))
    estimator.set_charging(True, at(0))

    # New SOC with the old timestamp, then the new timestamp
    assert estimator.report(50.0, at(0), at(60))
    assert estimator.report(50.0, at(60), at(60))
    assert estimator.get_soc(at(90), 10.0) == 55.0


async def test_soc_estimator_invalid_timestamp():
    """Test that a missing or future timestamp is replaced by the current time."""
    estimator = SocEstimator()
    estimator.report(40.0, None, at(10))
    assert estimator.reported_at == at(10)
    estimator.report(45.0, at(60), at(20))
    assert estimator.reported_at == at(20)
    # Unchanged SOC without a valid timestamp is not a new report
    assert not estimator.report(45.0, None, at(30))
    assert estimator.reported_at == at(20)


async def test_soc_estimator_restore():
    """Test storing and restoring the estimator."""
    estimator = SocEstimator()
    estimator.report(40.0, at(0), at(0))
    estimator.set_charging(True, at(0))
    data = estimator.as_dict(at(60))

    restored = SocEstimator()
    restored.restore(data)
    assert restored.reported_soc == 40.0
    assert restored.reported_at == at(0)
    # Charging is ended when the state was saved
    assert not restored.is_charging()
    assert restored.get_soc(at(120), 10.0) == 50.0

    # Invalid data is ignored
    restored.restore({"reported_soc": 40.0})
    assert restored.reported_soc is None
    assert restored.charging_periods == []
