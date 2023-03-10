"""Test ev_smart_charging/helpers/price_adaptor.py"""

from datetime import datetime

from homeassistant.core import State

from custom_components.ev_smart_charging.helpers.price_adaptor import PriceAdaptor


# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
# side of the assertion matches with the right side.


# pylint: disable=unused-argument
async def test_is_price_state(hass):
    """Test is_price_state"""

    price_adaptor = PriceAdaptor()

    assert price_adaptor.is_price_state(None) is False
    price_state = State(entity_id="sensor.test", state="unavailable")
    assert price_adaptor.is_price_state(price_state) is False
    price_state = State(entity_id="sensor.test", state="12.1")
    assert price_adaptor.is_price_state(price_state) is False
    price_state = State(
        entity_id="sensor.test", state="12.1", attributes={"current_price": 12.1}
    )
    assert price_adaptor.is_price_state(price_state) is False
    price_state = State(
        entity_id="sensor.test",
        state="12.1",
        attributes={"current_price": 12.1, "raw_today": None},
    )
    assert price_adaptor.is_price_state(price_state) is False
    price_state = State(
        entity_id="sensor.test",
        state="12.1",
        attributes={"current_price": 12.1, "raw_today": 12.1},
    )
    assert price_adaptor.is_price_state(price_state) is False
    price_state = State(
        entity_id="sensor.test",
        state="12.1",
        attributes={"current_price": 12.1, "raw_today": []},
    )
    assert price_adaptor.is_price_state(price_state) is False

    one_list = [
        {
            "value": 0.0,
            "start": datetime(2022, 10, 1, 14),
            "stop": datetime(2022, 10, 1, 15),
        }
    ]

    thirteen_list = [
        {
            "value": 1.0,
            "start": datetime(2022, 10, 1, 1),
            "stop": datetime(2022, 10, 1, 2),
        },
        {
            "value": 2.0,
            "start": datetime(2022, 10, 1, 2),
            "stop": datetime(2022, 10, 1, 3),
        },
        {
            "value": 3.0,
            "start": datetime(2022, 10, 1, 3),
            "stop": datetime(2022, 10, 1, 4),
        },
        {
            "value": 4.0,
            "start": datetime(2022, 10, 1, 4),
            "stop": datetime(2022, 10, 1, 5),
        },
        {
            "value": 5.0,
            "start": datetime(2022, 10, 1, 5),
            "stop": datetime(2022, 10, 1, 6),
        },
        {
            "value": 6.0,
            "start": datetime(2022, 10, 1, 6),
            "stop": datetime(2022, 10, 1, 7),
        },
        {
            "value": 7.0,
            "start": datetime(2022, 10, 1, 7),
            "stop": datetime(2022, 10, 1, 8),
        },
        {
            "value": 8.0,
            "start": datetime(2022, 10, 1, 8),
            "stop": datetime(2022, 10, 1, 9),
        },
        {
            "value": 9.0,
            "start": datetime(2022, 10, 1, 9),
            "stop": datetime(2022, 10, 1, 10),
        },
        {
            "value": 10.0,
            "start": datetime(2022, 10, 1, 10),
            "stop": datetime(2022, 10, 1, 11),
        },
        {
            "value": 11.0,
            "start": datetime(2022, 10, 1, 11),
            "stop": datetime(2022, 10, 1, 12),
        },
        {
            "value": 12.0,
            "start": datetime(2022, 10, 1, 12),
            "stop": datetime(2022, 10, 1, 13),
        },
        {
            "value": 13.0,
            "start": datetime(2022, 10, 1, 13),
            "stop": datetime(2022, 10, 1, 14),
        },
    ]

    price_state = State(
        entity_id="sensor.test",
        state="12.1",
        attributes={"current_price": 12.1, "raw_today": one_list},
    )
    assert price_adaptor.is_price_state(price_state) is False

    price_state = State(
        entity_id="sensor.test",
        state="12.1",
        attributes={"current_price": None, "raw_today": one_list},
    )
    assert price_adaptor.is_price_state(price_state) is False

    price_state = State(
        entity_id="sensor.test",
        state="12.1",
        attributes={"current_price": 12.1, "raw_today": thirteen_list},
    )
    assert price_adaptor.is_price_state(price_state) is True

    price_state = State(
        entity_id="sensor.test",
        state="12.1",
        attributes={"current_price": None, "raw_today": thirteen_list},
    )
    assert price_adaptor.is_price_state(price_state) is False
