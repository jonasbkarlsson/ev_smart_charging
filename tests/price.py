"""Test data for prices"""
from datetime import datetime
from zoneinfo import ZoneInfo

def generate_15min_intervals(
    base_date,
    base_price: float,
    interval_count: int = 96,
    price_variation: float = 0.15
):
    """
    Generate realistic 15-minute interval test data for GE-Spot.
    
    Args:
        base_date: Starting date (datetime object)
        base_price: Base price (e.g., 163.08 SEK/MWh)
        interval_count: Number of intervals (96 for normal, 92 for spring DST, 100 for fall DST)
        price_variation: Max price variation as fraction (0.15 = ±15%)
    
    Returns:
        List of price intervals matching GE-Spot format
    """
    from datetime import timedelta
    import math
    
    prices = []
    tz = ZoneInfo(key="Europe/Stockholm")
    
    for i in range(interval_count):
        hour = i // 4  # 4 intervals per hour
        minute = (i % 4) * 15  # 0, 15, 30, 45
        
        # Handle potential overflow (e.g., for 100 intervals on DST fall back)
        if hour >= 24:
            extra_days = hour // 24
            hour = hour % 24
            start_time = base_date.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0,
                tzinfo=tz
            ) + timedelta(days=extra_days)
        else:
            start_time = base_date.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0,
                tzinfo=tz
            )
        
        end_time = start_time + timedelta(minutes=15)
        
        # Create realistic price variation using sine wave
        # Prices typically lower at night, higher during day
        effective_hour = (i / 4) % 24  # Convert interval to hour-of-day
        time_of_day_factor = math.sin((effective_hour / 24) * 2 * math.pi - math.pi / 2)
        
        # Add some randomness per interval
        interval_variation = ((i % 7) - 3) * 0.02  # Small per-interval variation
        
        price = base_price * (1 + (time_of_day_factor * price_variation) + interval_variation)
        
        prices.append({
            "start": start_time,
            "end": end_time,
            "value": round(price, 2),
        })
    
    return prices


PRICE_20220930 = [
    {
        "start": datetime(2022, 9, 30, 0, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 1, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 104.95,
    },
    {
        "start": datetime(2022, 9, 30, 1, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 2, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 99.74,
    },
    {
        "start": datetime(2022, 9, 30, 2, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 3, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 93.42,
    },
    {
        "start": datetime(2022, 9, 30, 3, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 4, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 93.25,
    },
    {
        "start": datetime(2022, 9, 30, 4, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 5, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 96.9,
    },
    {
        "start": datetime(2022, 9, 30, 5, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 6, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 137.17,
    },
    {
        "start": datetime(2022, 9, 30, 6, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 7, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 343.4,
    },
    {
        "start": datetime(2022, 9, 30, 7, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 8, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 387.5,
    },
    {
        "start": datetime(2022, 9, 30, 8, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 9, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 388.65,
    },
    {
        "start": datetime(2022, 9, 30, 9, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 10, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 387.5,
    },
    {
        "start": datetime(2022, 9, 30, 10, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 11, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 387.5,
    },
    {
        "start": datetime(2022, 9, 30, 11, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 12, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 387.5,
    },
    {
        "start": datetime(2022, 9, 30, 12, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 13, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 387.5,
    },
    {
        "start": datetime(2022, 9, 30, 13, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 14, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 387.5,
    },
    {
        "start": datetime(2022, 9, 30, 14, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 15, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 387.5,
    },
    {
        "start": datetime(2022, 9, 30, 15, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 16, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 387.5,
    },
    {
        "start": datetime(2022, 9, 30, 16, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 17, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 387.5,
    },
    {
        "start": datetime(2022, 9, 30, 17, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 18, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 387.5,
    },
    {
        "start": datetime(2022, 9, 30, 18, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 19, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 387.5,
    },
    {
        "start": datetime(2022, 9, 30, 19, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 20, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 387.5,
    },
    {
        "start": datetime(2022, 9, 30, 20, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 21, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 387.5,
    },
    {
        "start": datetime(2022, 9, 30, 21, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 22, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 387.5,
    },
    {
        "start": datetime(2022, 9, 30, 22, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 9, 30, 23, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 9, 30, 23, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
]

PRICE_20221001 = [
    {
        "start": datetime(2022, 10, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 1, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 1, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 2, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 2, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 3, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 3, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 4, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 24.2,
    },
    {
        "start": datetime(2022, 10, 1, 4, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 5, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 24.2,
    },
    {
        "start": datetime(2022, 10, 1, 5, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 6, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 24.2,
    },
    {
        "start": datetime(2022, 10, 1, 6, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 7, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 24.2,
    },
    {
        "start": datetime(2022, 10, 1, 7, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 8, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 8, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 9, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 9, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 10, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 10, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 11, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 11, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 12, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 12, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 13, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 13, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 14, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 14, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 15, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 15, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 16, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 16, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 17, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 17, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 18, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 18, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 19, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 19, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 20, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 20, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 21, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 21, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 22, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 22, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 23, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 23, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 2, 0, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
]

PRICE_20220930_ENERGIDATASERVICE = [
    {
        "hour": datetime(2022, 9, 30, 0, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 104.95,
    },
    {
        "hour": datetime(2022, 9, 30, 1, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 99.74,
    },
    {
        "hour": datetime(2022, 9, 30, 2, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 93.42,
    },
    {
        "hour": datetime(2022, 9, 30, 3, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 93.25,
    },
    {
        "hour": datetime(2022, 9, 30, 4, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 96.9,
    },
    {
        "hour": datetime(2022, 9, 30, 5, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 137.17,
    },
    {
        "hour": datetime(2022, 9, 30, 6, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 343.4,
    },
    {
        "hour": datetime(2022, 9, 30, 7, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 387.5,
    },
    {
        "hour": datetime(2022, 9, 30, 8, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 388.65,
    },
    {
        "hour": datetime(2022, 9, 30, 9, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 387.5,
    },
    {
        "hour": datetime(2022, 9, 30, 10, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 387.5,
    },
    {
        "hour": datetime(2022, 9, 30, 11, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 387.5,
    },
    {
        "hour": datetime(2022, 9, 30, 12, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 387.5,
    },
    {
        "hour": datetime(2022, 9, 30, 13, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 387.5,
    },
    {
        "hour": datetime(2022, 9, 30, 14, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 387.5,
    },
    {
        "hour": datetime(2022, 9, 30, 15, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 387.5,
    },
    {
        "hour": datetime(2022, 9, 30, 16, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 387.5,
    },
    {
        "hour": datetime(2022, 9, 30, 17, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 387.5,
    },
    {
        "hour": datetime(2022, 9, 30, 18, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 387.5,
    },
    {
        "hour": datetime(2022, 9, 30, 19, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 387.5,
    },
    {
        "hour": datetime(2022, 9, 30, 20, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 387.5,
    },
    {
        "hour": datetime(2022, 9, 30, 21, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 387.5,
    },
    {
        "hour": datetime(2022, 9, 30, 22, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 9, 30, 23, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
]

PRICE_20221001_ENERGIDATASERVICE = [
    {
        "hour": datetime(2022, 10, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 1, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 2, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 3, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 24.2,
    },
    {
        "hour": datetime(2022, 10, 1, 4, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 24.2,
    },
    {
        "hour": datetime(2022, 10, 1, 5, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 24.2,
    },
    {
        "hour": datetime(2022, 10, 1, 6, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 24.2,
    },
    {
        "hour": datetime(2022, 10, 1, 7, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 8, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 9, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 10, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 11, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 12, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 13, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 14, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 15, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 16, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 17, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 18, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 19, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 20, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 21, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 22, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
    {
        "hour": datetime(2022, 10, 1, 23, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "price": 49.64,
    },
]

# GE-Spot uses the same data format as Nordpool

# GE-Spot v1.2.0 provides 96 15-minute intervals per day
PRICE_20220930_GESPOT = generate_15min_intervals(
    base_date=datetime(2022, 9, 30),
    base_price=163.08,  # Average price for that day
)

PRICE_20221001_GESPOT = generate_15min_intervals(
    base_date=datetime(2022, 10, 1),
    base_price=156.42,  # Average price for that day
)

# Define PRICE_ONE_LIST, PRICE_THIRTEEN_LIST and PRICE_THIRTEEN_LIST_30MIN for testing
PRICE_ONE_LIST = [
    {
        "start": datetime(2022, 10, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 1, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    }
]

# Define PRICE_THIRTEEN_LIST_30MIN with 30-minute intervals
PRICE_THIRTEEN_LIST_30MIN = [
    {
        "start": datetime(2022, 10, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 0, 30, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 0, 30, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 1, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 1, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 1, 30, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 1, 30, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 2, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 2, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 2, 30, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 2, 30, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 3, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 3, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 3, 30, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 24.2,
    },
    {
        "start": datetime(2022, 10, 1, 3, 30, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 4, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 24.2,
    },
    {
        "start": datetime(2022, 10, 1, 4, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 4, 30, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 24.2,
    },
    {
        "start": datetime(2022, 10, 1, 4, 30, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 5, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 24.2,
    },
    {
        "start": datetime(2022, 10, 1, 5, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 5, 30, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 24.2,
    },
    {
        "start": datetime(2022, 10, 1, 5, 30, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 6, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 24.2,
    },
    {
        "start": datetime(2022, 10, 1, 6, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 6, 30, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 24.2,
    }
]

PRICE_THIRTEEN_LIST = [
    {
        "start": datetime(2022, 10, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 1, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 1, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 2, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 2, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 3, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 3, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 4, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 24.2,
    },
    {
        "start": datetime(2022, 10, 1, 4, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 5, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 24.2,
    },
    {
        "start": datetime(2022, 10, 1, 5, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 6, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 24.2,
    },
    {
        "start": datetime(2022, 10, 1, 6, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 7, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 24.2,
    },
    {
        "start": datetime(2022, 10, 1, 7, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 8, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 8, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 9, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 9, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 10, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 10, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 11, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 11, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 12, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    },
    {
        "start": datetime(2022, 10, 1, 12, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "end": datetime(2022, 10, 1, 13, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        "value": 49.64,
    }
]
