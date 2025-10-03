"""Test GE-Spot DST transition handling."""
import pytest
from datetime import datetime

from homeassistant.core import State

from custom_components.ev_smart_charging.const import PLATFORM_GESPOT
from custom_components.ev_smart_charging.helpers.general import Validator
from custom_components.ev_smart_charging.helpers.raw import Raw

from tests.price import generate_15min_intervals


class TestGESpotDST:
    """Test DST transition handling for GE-Spot."""

    async def test_normal_day_96_intervals(self, hass, set_cet_timezone):
        """Test normal day with 96 intervals."""
        prices = generate_15min_intervals(
            base_date=datetime(2025, 10, 3),
            base_price=155.0,
            interval_count=96
        )
        
        assert len(prices) == 96, "Normal day should have 96 intervals"
        
        # Verify validator accepts it
        state = State(
            entity_id="sensor.gespot_current_price",
            state="155.0",
            attributes={
                "current_price": 155.0,
                "raw_today": prices,
                "raw_tomorrow": [],
            },
        )
        
        assert Validator.is_price_state(state, PLATFORM_GESPOT) is True
        
        # Verify Raw handler processes it
        raw = Raw(prices, PLATFORM_GESPOT)
        assert raw.is_valid() is True
        assert len(raw.data) == 96

    async def test_dst_spring_92_intervals(self, hass, set_cet_timezone):
        """Test spring DST transition with 92 intervals.
        
        In spring, clocks move forward, so we lose an hour (4 intervals).
        For example, on March 30, 2025, at 02:00 CET, clocks jump to 03:00 CEST.
        This means 02:00-02:59 doesn't exist, so we have only 92 intervals.
        """
        # Generate normal 96, then remove the skipped hour
        all_prices = generate_15min_intervals(
            base_date=datetime(2025, 3, 30),
            base_price=150.0,
            interval_count=96
        )
        
        # Remove 02:00-02:59 (indices 8-11: hour 2, 4 intervals)
        prices_spring = all_prices[:8] + all_prices[12:]
        
        assert len(prices_spring) == 92, "Spring DST day should have 92 intervals"
        
        # Verify validator accepts it (with fallback flag since data might be incomplete)
        state = State(
            entity_id="sensor.gespot_current_price",
            state="150.0",
            attributes={
                "current_price": 150.0,
                "raw_today": prices_spring,
                "raw_tomorrow": [],
                "source_info": {"is_using_fallback": True},
            },
        )
        
        # The validator should accept this because fallback is true
        assert Validator.is_price_state(state, PLATFORM_GESPOT) is True
        
        # Verify Raw handler processes it
        raw = Raw(prices_spring, PLATFORM_GESPOT)
        assert raw.is_valid() is True
        assert len(raw.data) == 92

    async def test_dst_fall_100_intervals(self, hass, set_cet_timezone):
        """Test fall DST transition with 100 intervals.
        
        In fall, clocks move backward, so we repeat an hour (4 extra intervals).
        For example, on October 26, 2025, at 03:00 CEST, clocks go back to 02:00 CET.
        This means 02:00-02:59 happens twice, so we have 100 intervals.
        """
        # Generate normal 96, then duplicate the repeated hour
        all_prices = generate_15min_intervals(
            base_date=datetime(2025, 10, 26),
            base_price=145.0,
            interval_count=96
        )
        
        # Duplicate 02:00-02:59 (indices 8-11)
        repeated_hour = all_prices[8:12]
        prices_fall = all_prices[:12] + repeated_hour + all_prices[12:]
        
        assert len(prices_fall) == 100, "Fall DST day should have 100 intervals"
        
        # Verify validator accepts it
        state = State(
            entity_id="sensor.gespot_current_price",
            state="145.0",
            attributes={
                "current_price": 145.0,
                "raw_today": prices_fall,
                "raw_tomorrow": [],
            },
        )
        
        assert Validator.is_price_state(state, PLATFORM_GESPOT) is True
        
        # Verify Raw handler processes it
        raw = Raw(prices_fall, PLATFORM_GESPOT)
        assert raw.is_valid() is True
        assert len(raw.data) == 100

    async def test_dst_edge_case_validation(self, hass, set_cet_timezone):
        """Test that various interval counts are handled correctly."""
        # Test a range of interval counts
        for interval_count in [92, 96, 100]:
            prices = generate_15min_intervals(
                base_date=datetime(2025, 10, 3),
                base_price=155.0,
                interval_count=interval_count
            )
            
            raw = Raw(prices, PLATFORM_GESPOT)
            assert raw.is_valid() is True, f"Raw handler should accept {interval_count} intervals"
            assert len(raw.data) == interval_count, f"Raw handler should preserve {interval_count} intervals"
