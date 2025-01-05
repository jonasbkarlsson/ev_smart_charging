"""Test ev_smart_charging/helpers/price_adaptor.py"""

from datetime import datetime
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant
from homeassistant.core import State
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.util import dt

from custom_components.ev_smart_charging.const import (
    BUTTON,
    CONF_PRICE_SENSOR,
    PLATFORM_ENERGIDATASERVICE,
    PLATFORM_ENTSOE,
    PLATFORM_GENERIC,
    PLATFORM_NORDPOOL,
    SENSOR,
)
from custom_components.ev_smart_charging.helpers.config_flow import FindEntity

from custom_components.ev_smart_charging.helpers.price_adaptor import PriceAdaptor

from tests.helpers.helpers import (
    MockPriceEntity,
    MockPriceEntityEnergiDataService,
    MockPriceEntityEntsoe,
    MockPriceEntityGeneric,
)
from tests.price import (
    PRICE_20220930,
    PRICE_20220930_ENERGIDATASERVICE,
    PRICE_20220930_ENTSOE,
    PRICE_20221001,
    PRICE_20221001_ENERGIDATASERVICE,
    PRICE_20221001_ENTSOE,
)
from tests.price_15min import PRICE_20220930_GENERIC_15MIN


# pylint: disable=unused-argument
async def test_is_price_state(hass, freezer):
    """Test is_price_state"""

    dt.set_default_time_zone(ZoneInfo(key="Europe/Stockholm"))

    freezer.move_to("2022-10-01T14:00:00+02:00")

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
            "start": datetime(2022, 10, 1, 14, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
            "stop": datetime(2022, 10, 1, 15, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        }
    ]

    thirteen_list = [
        {
            "value": 1.0,
            "start": datetime(2022, 10, 1, 1, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
            "stop": datetime(2022, 10, 1, 2, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        },
        {
            "value": 2.0,
            "start": datetime(2022, 10, 1, 2, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
            "stop": datetime(2022, 10, 1, 3, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        },
        {
            "value": 3.0,
            "start": datetime(2022, 10, 1, 3, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
            "stop": datetime(2022, 10, 1, 4, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        },
        {
            "value": 4.0,
            "start": datetime(2022, 10, 1, 4, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
            "stop": datetime(2022, 10, 1, 5, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        },
        {
            "value": 5.0,
            "start": datetime(2022, 10, 1, 5, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
            "stop": datetime(2022, 10, 1, 6, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        },
        {
            "value": 6.0,
            "start": datetime(2022, 10, 1, 6, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
            "stop": datetime(2022, 10, 1, 7, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        },
        {
            "value": 7.0,
            "start": datetime(2022, 10, 1, 7, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
            "stop": datetime(2022, 10, 1, 8, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        },
        {
            "value": 8.0,
            "start": datetime(2022, 10, 1, 8, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
            "stop": datetime(2022, 10, 1, 9, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        },
        {
            "value": 9.0,
            "start": datetime(2022, 10, 1, 9, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
            "stop": datetime(2022, 10, 1, 10, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        },
        {
            "value": 10.0,
            "start": datetime(2022, 10, 1, 10, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
            "stop": datetime(2022, 10, 1, 11, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        },
        {
            "value": 11.0,
            "start": datetime(2022, 10, 1, 11, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
            "stop": datetime(2022, 10, 1, 12, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        },
        {
            "value": 12.0,
            "start": datetime(2022, 10, 1, 12, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
            "stop": datetime(2022, 10, 1, 13, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
        },
        {
            "value": 13.0,
            "start": datetime(2022, 10, 1, 13, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
            "stop": datetime(2022, 10, 1, 14, 0, tzinfo=ZoneInfo(key="Europe/Stockholm")),
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
    assert price_adaptor.is_price_state(price_state) is True

    freezer.move_to("2022-10-02T00:00:00+02:00")

    price_state = State(
        entity_id="sensor.test",
        state="12.1",
        attributes={"current_price": 12.1, "raw_today": thirteen_list},
    )
    assert price_adaptor.is_price_state(price_state) is False

async def test_get_raw_today_local(hass, set_cet_timezone, freezer):
    """Test get_raw_today_local"""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    price_adaptor = PriceAdaptor()

    # Test UNKNOWN
    price_adaptor.set_price_platform("UNKNOWN")
    raw_today_local = price_adaptor.get_raw_today_local(None)
    assert raw_today_local is not None
    assert not raw_today_local.data

    # Test PLATFORM_NORDPOOL
    price_adaptor.set_price_platform(PLATFORM_NORDPOOL)

    MockPriceEntity.create(hass, entity_registry)
    await hass.async_block_till_done()
    price_sensor = FindEntity.find_nordpool_sensor(hass)
    assert price_sensor.startswith("sensor.nordpool")
    price_state = hass.states.get(price_sensor)
    assert price_state is not None
    raw_today_local = price_adaptor.get_raw_today_local(price_state)
    assert raw_today_local is not None
    assert not raw_today_local.data

    MockPriceEntity.set_state(hass, PRICE_20220930, None)
    await hass.async_block_till_done()
    price_state = hass.states.get(price_sensor)
    raw_today_local = price_adaptor.get_raw_today_local(price_state)
    assert raw_today_local.data == PRICE_20220930

    # Test PLATFORM_ENERGIDATASERVICE
    price_adaptor.set_price_platform(PLATFORM_ENERGIDATASERVICE)

    MockPriceEntityEnergiDataService.create(hass, entity_registry)
    await hass.async_block_till_done()
    price_sensor = FindEntity.find_energidataservice_sensor(hass)
    assert price_sensor.startswith("sensor.energi")
    price_state = hass.states.get(price_sensor)
    assert price_state is not None
    raw_today_local = price_adaptor.get_raw_today_local(price_state)
    assert raw_today_local is not None
    assert not raw_today_local.data

    MockPriceEntityEnergiDataService.set_state(
        hass, PRICE_20220930_ENERGIDATASERVICE, None
    )
    await hass.async_block_till_done()
    price_state = hass.states.get(price_sensor)
    raw_today_local = price_adaptor.get_raw_today_local(price_state)
    assert raw_today_local.data == PRICE_20220930

    # Test PLATFORM_ENTSOE
    price_adaptor.set_price_platform(PLATFORM_ENTSOE)

    MockPriceEntityEntsoe.create(hass, entity_registry)
    await hass.async_block_till_done()
    price_sensor = FindEntity.find_entsoe_sensor(hass)
    assert price_sensor.startswith("sensor.entsoe")
    price_state = hass.states.get(price_sensor)
    assert price_state is not None
    raw_today_local = price_adaptor.get_raw_today_local(price_state)
    assert raw_today_local is not None
    assert not raw_today_local.data

    MockPriceEntityEntsoe.set_state(hass, PRICE_20220930_ENTSOE, None)
    await hass.async_block_till_done()
    price_state = hass.states.get(price_sensor)
    raw_today_local = price_adaptor.get_raw_today_local(price_state)
    assert raw_today_local.data == PRICE_20220930

    # Test PLATFORM_GENERIC
    price_adaptor.set_price_platform(PLATFORM_GENERIC)

    MockPriceEntityGeneric.create(hass, entity_registry)
    await hass.async_block_till_done()
    price_sensor = FindEntity.find_generic_sensor(hass)
    assert price_sensor.startswith("sensor.generic")
    price_state = hass.states.get(price_sensor)
    assert price_state is not None
    raw_today_local = price_adaptor.get_raw_today_local(price_state)
    assert raw_today_local is not None
    assert not raw_today_local.data

    MockPriceEntityGeneric.set_state(hass, PRICE_20220930_ENTSOE, None)
    await hass.async_block_till_done()
    price_state = hass.states.get(price_sensor)
    raw_today_local = price_adaptor.get_raw_today_local(price_state)
    assert raw_today_local.data == PRICE_20220930

    # Test template sensor with price per 15 minutes
    MockPriceEntityGeneric.set_state(hass, PRICE_20220930_GENERIC_15MIN, None)
    await hass.async_block_till_done()
    price_state = hass.states.get(price_sensor)
    raw_today_local = price_adaptor.get_raw_today_local(price_state)
    assert raw_today_local.data == PRICE_20220930

async def test_get_raw_tomorrow_local(hass, set_cet_timezone, freezer):
    """Test get_raw_tomorrow_local"""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    price_adaptor = PriceAdaptor()

    # Test UNKNOWN
    price_adaptor.set_price_platform("UNKNOWN")
    raw_tomorrow_local = price_adaptor.get_raw_tomorrow_local(None)
    assert raw_tomorrow_local is not None
    assert not raw_tomorrow_local.data

    # Test PLATFORM_NORDPOOL
    price_adaptor.set_price_platform(PLATFORM_NORDPOOL)

    MockPriceEntity.create(hass, entity_registry)
    await hass.async_block_till_done()
    price_sensor = FindEntity.find_nordpool_sensor(hass)
    assert price_sensor.startswith("sensor.nordpool")
    price_state = hass.states.get(price_sensor)
    assert price_state is not None
    raw_tomorrow_local = price_adaptor.get_raw_tomorrow_local(price_state)
    assert raw_tomorrow_local is not None
    assert not raw_tomorrow_local.data

    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    await hass.async_block_till_done()
    price_state = hass.states.get(price_sensor)
    raw_tomorrow_local = price_adaptor.get_raw_tomorrow_local(price_state)
    assert raw_tomorrow_local.data == PRICE_20221001

    # Test PLATFORM_ENERGIDATASERVICE
    price_adaptor.set_price_platform(PLATFORM_ENERGIDATASERVICE)

    MockPriceEntityEnergiDataService.create(hass, entity_registry)
    await hass.async_block_till_done()
    price_sensor = FindEntity.find_energidataservice_sensor(hass)
    assert price_sensor.startswith("sensor.energi")
    price_state = hass.states.get(price_sensor)
    assert price_state is not None
    raw_tomorrow_local = price_adaptor.get_raw_tomorrow_local(price_state)
    assert raw_tomorrow_local is not None
    assert not raw_tomorrow_local.data

    MockPriceEntityEnergiDataService.set_state(
        hass, PRICE_20220930_ENERGIDATASERVICE, PRICE_20221001_ENERGIDATASERVICE
    )
    await hass.async_block_till_done()
    price_state = hass.states.get(price_sensor)
    raw_tomorrow_local = price_adaptor.get_raw_tomorrow_local(price_state)
    assert raw_tomorrow_local.data == PRICE_20221001

    # Test PLATFORM_ENTSOE
    price_adaptor.set_price_platform(PLATFORM_ENTSOE)

    MockPriceEntityEntsoe.create(hass, entity_registry)
    await hass.async_block_till_done()
    price_sensor = FindEntity.find_entsoe_sensor(hass)
    assert price_sensor.startswith("sensor.entsoe")
    price_state = hass.states.get(price_sensor)
    assert price_state is not None
    raw_tomorrow_local = price_adaptor.get_raw_tomorrow_local(price_state)
    assert raw_tomorrow_local is not None
    assert not raw_tomorrow_local.data

    MockPriceEntityEntsoe.set_state(hass, PRICE_20220930_ENTSOE, PRICE_20221001_ENTSOE)
    await hass.async_block_till_done()
    price_state = hass.states.get(price_sensor)
    raw_tomorrow_local = price_adaptor.get_raw_tomorrow_local(price_state)
    assert raw_tomorrow_local.data == PRICE_20221001

    # Test PLATFORM_GENERIC
    price_adaptor.set_price_platform(PLATFORM_GENERIC)

    MockPriceEntityGeneric.create(hass, entity_registry)
    await hass.async_block_till_done()
    price_sensor = FindEntity.find_generic_sensor(hass)
    assert price_sensor.startswith("sensor.generic")
    price_state = hass.states.get(price_sensor)
    assert price_state is not None
    raw_tomorrow_local = price_adaptor.get_raw_tomorrow_local(price_state)
    assert raw_tomorrow_local is not None
    assert not raw_tomorrow_local.data

    MockPriceEntityGeneric.set_state(hass, PRICE_20220930_ENTSOE, PRICE_20221001_ENTSOE)
    await hass.async_block_till_done()
    price_state = hass.states.get(price_sensor)
    raw_tomorrow_local = price_adaptor.get_raw_tomorrow_local(price_state)
    assert raw_tomorrow_local.data == PRICE_20221001


async def test_get_current_price(hass, set_cet_timezone, freezer):
    """Test get_current_price"""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    price_adaptor = PriceAdaptor()

    # Test UNKNOWN
    price_adaptor.set_price_platform("UNKNOWN")
    current_price = price_adaptor.get_current_price(None)
    assert current_price is None

    # Test PLATFORM_NORDPOOL
    price_adaptor.set_price_platform(PLATFORM_NORDPOOL)
    MockPriceEntity.create(hass, entity_registry)
    await hass.async_block_till_done()
    price_sensor = FindEntity.find_nordpool_sensor(hass)
    MockPriceEntity.set_state(hass, PRICE_20220930, None)
    await hass.async_block_till_done()
    price_state = hass.states.get(price_sensor)
    current_price = price_adaptor.get_current_price(price_state)
    assert current_price == 219.48

    # Test PLATFORM_ENERGIDATASERVICE
    price_adaptor.set_price_platform(PLATFORM_ENERGIDATASERVICE)
    MockPriceEntityEnergiDataService.create(hass, entity_registry)
    await hass.async_block_till_done()
    price_sensor = FindEntity.find_energidataservice_sensor(hass)
    MockPriceEntityEnergiDataService.set_state(
        hass, PRICE_20220930_ENERGIDATASERVICE, None
    )
    await hass.async_block_till_done()
    price_state = hass.states.get(price_sensor)
    current_price = price_adaptor.get_current_price(price_state)
    assert current_price == 219.48

    # Test PLATFORM_ENTSOE
    price_adaptor.set_price_platform(PLATFORM_ENTSOE)
    MockPriceEntityEntsoe.create(hass, entity_registry)
    await hass.async_block_till_done()
    price_sensor = FindEntity.find_entsoe_sensor(hass)
    MockPriceEntityEntsoe.set_state(hass, PRICE_20220930_ENTSOE, None)
    await hass.async_block_till_done()
    price_state = hass.states.get(price_sensor)
    current_price = price_adaptor.get_current_price(price_state)
    assert current_price == 219.48

    # Test PLATFORM_GENERIC
    price_adaptor.set_price_platform(PLATFORM_GENERIC)
    MockPriceEntityGeneric.create(hass, entity_registry)
    await hass.async_block_till_done()
    price_sensor = FindEntity.find_generic_sensor(hass)
    MockPriceEntityGeneric.set_state(hass, PRICE_20220930_ENTSOE, None)
    await hass.async_block_till_done()
    price_state = hass.states.get(price_sensor)
    current_price = price_adaptor.get_current_price(price_state)
    assert current_price == 219.48


async def test_validate_price_entity(hass: HomeAssistant):
    """Test the price entity in validate_price_entity."""

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    user_input = {}
    user_input[CONF_PRICE_SENSOR] = "sensor.sensor_kwh_se3_sek_2_10_0"

    # Check with no price entity
    assert PriceAdaptor.validate_price_entity(hass, user_input) == (
        "base",
        "price_not_found",
    )

    # Check with wrong platform
    entity_registry.async_get_or_create(
        domain=SENSOR,
        platform=SENSOR,
        unique_id="kwh_se3_sek_2_10_0",
    )
    assert entity_registry.async_is_registered("sensor.sensor_kwh_se3_sek_2_10_0")
    hass.states.async_set("sensor.sensor_kwh_se3_sek_2_10_0", "123")
    assert PriceAdaptor.validate_price_entity(hass, user_input) == (
        "base",
        "sensor_is_not_price",
    )

    # Check with price entity without attributes
    user_input[CONF_PRICE_SENSOR] = "sensor.nordpool_kwh_se3_sek_2_10_0"
    entity_registry.async_get_or_create(
        domain=SENSOR,
        platform=PLATFORM_NORDPOOL,
        unique_id="kwh_se3_sek_2_10_0",
    )
    assert entity_registry.async_is_registered("sensor.nordpool_kwh_se3_sek_2_10_0")
    hass.states.async_set("sensor.nordpool_kwh_se3_sek_2_10_0", "123")
    assert PriceAdaptor.validate_price_entity(hass, user_input) == (
        "base",
        "sensor_is_not_price",
    )

    # Check with price entity with current_price
    hass.states.async_set(
        "sensor.nordpool_kwh_se3_sek_2_10_0", "123", {"current_price": 123}
    )
    assert PriceAdaptor.validate_price_entity(hass, user_input) == (
        "base",
        "sensor_is_not_price",
    )

    # Check with price entity with current_price and raw_today
    hass.states.async_set(
        "sensor.nordpool_kwh_se3_sek_2_10_0",
        "123",
        {"current_price": 123, "raw_today": None},
    )
    assert PriceAdaptor.validate_price_entity(hass, user_input) == (
        "base",
        "sensor_is_not_price",
    )

    # Check with price entity with current_price, raw_today and raw_tomorrow
    hass.states.async_set(
        "sensor.nordpool_kwh_se3_sek_2_10_0",
        "123",
        {"current_price": 123, "raw_today": None, "raw_tomorrow": None},
    )
    assert PriceAdaptor.validate_price_entity(hass, user_input) is None

    # Check with price entity with invalid state. Is ok since the state is not used.
    hass.states.async_set(
        "sensor.nordpool_kwh_se3_sek_2_10_0",
        "123a",
        {"current_price": 123, "raw_today": None, "raw_tomorrow": None},
    )
    assert PriceAdaptor.validate_price_entity(hass, user_input) is None


async def test_validate_price_entity_entsoe(hass: HomeAssistant):
    """Test the price entity in validate_price_entity."""

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    user_input = {}

    # Check with price entity without attributes
    user_input[CONF_PRICE_SENSOR] = "sensor.entsoe_average_electricity_price"
    entity_registry.async_get_or_create(
        domain=SENSOR,
        platform=PLATFORM_ENTSOE,
        unique_id="average_electricity_price",
    )
    assert entity_registry.async_is_registered(
        "sensor.entsoe_average_electricity_price"
    )
    hass.states.async_set("sensor.entsoe_average_electricity_price", "123")
    assert PriceAdaptor.validate_price_entity(hass, user_input) == (
        "base",
        "sensor_is_not_price",
    )

    # Check with price entity with prices_today
    hass.states.async_set(
        "sensor.entsoe_average_electricity_price",
        "123",
        {"prices_today": None},
    )
    assert PriceAdaptor.validate_price_entity(hass, user_input) == (
        "base",
        "sensor_is_not_price",
    )

    # Check with price entity with prices_today and prices_tomorrow
    hass.states.async_set(
        "sensor.entsoe_average_electricity_price",
        "123",
        {"prices_today": None, "prices_tomorrow": None},
    )
    assert PriceAdaptor.validate_price_entity(hass, user_input) is None

    # Check with price entity with invalid state. Is ok since the state is not used.
    hass.states.async_set(
        "sensor.entsoe_average_electricity_price",
        "123a",
        {"prices_today": None, "prices_tomorrow": None},
    )
    assert PriceAdaptor.validate_price_entity(hass, user_input) is None
