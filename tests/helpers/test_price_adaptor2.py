"""Test ev_smart_charging/helpers/price_adaptor.py"""


from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.ev_smart_charging.helpers.config_flow import FindEntity

from custom_components.ev_smart_charging.helpers.price_adaptor import PriceAdaptor

from tests.helpers.helpers import (
    MockPriceEntity,
)
from tests.price import (
    PRICE_20220930_EET,
    PRICE_20221001_EET,
)


# pylint: disable=unused-argument
async def test_get_raw_today_local(hass, set_eet_timezone, freezer):
    """Test get_raw_today_local with 1 hour difference between HA timezone and price timezone"""

    freezer.move_to("2022-09-30T14:00:00+03:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    price_adaptor = PriceAdaptor()

    # Test PLATFORM_NORDPOOL
    MockPriceEntity.create(hass, entity_registry)
    MockPriceEntity.set_state(hass, None, None)
    await hass.async_block_till_done()
    price_sensor = FindEntity.find_nordpool_sensor(hass)
    assert price_sensor.startswith("sensor.nordpool")
    price_state = hass.states.get(price_sensor)
    assert price_state is not None
    price_adaptor.initiate(price_state)
    raw_today_local = price_adaptor.get_raw_today_local(price_state)
    assert raw_today_local is not None
    assert not raw_today_local.data

    MockPriceEntity.set_state(hass, PRICE_20220930_EET, None)
    await hass.async_block_till_done()
    price_state = hass.states.get(price_sensor)
    price_adaptor.initiate(price_state)
    raw_today_local = price_adaptor.get_raw_today_local(price_state)
    assert raw_today_local.data[0]['value'] == 104.95  # The price at 00:00 in CET
    assert raw_today_local.data[88]['value'] == 54.27  # The price at 22:00 in CET
    assert len(raw_today_local.data) == 96 - 4  # 15 min resolution, missing one hour.


async def test_get_raw_tomorrow_local(hass, set_eet_timezone, freezer):
    """Test get_raw_tomorrow_local with 1 hour difference between HA timezone and price timezone"""

    freezer.move_to("2022-09-30T14:00:00+03:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    price_adaptor = PriceAdaptor()

    # Test PLATFORM_NORDPOOL
    MockPriceEntity.create(hass, entity_registry)
    await hass.async_block_till_done()
    price_sensor = FindEntity.find_nordpool_sensor(hass)
    assert price_sensor.startswith("sensor.nordpool")
    MockPriceEntity.set_state(hass, PRICE_20220930_EET, PRICE_20221001_EET)
    await hass.async_block_till_done()
    price_state = hass.states.get(price_sensor)
    price_adaptor.initiate(price_state)
    raw_tomorrow_local = price_adaptor.get_raw_tomorrow_local(price_state)
    assert raw_tomorrow_local.data[0]['value'] == 49.64  # The price at 23:00 in CET
    assert raw_tomorrow_local.data[4]['value'] == 68.63  # The price at 00:00 in CET
