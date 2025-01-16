"""Test ev_smart_charging coordinator."""

from datetime import datetime
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_OFF, MAJOR_VERSION, MINOR_VERSION

from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.util import dt as dt_util

from custom_components.ev_smart_charging import async_setup_entry
from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.const import DOMAIN

from tests.helpers.helpers import (
    MockChargerEntity,
    MockPriceEntity,
    MockSOCEntity,
    MockTargetSOCEntity,
)
from tests.price import PRICE_20220930, PRICE_20221001, PRICE_20221001_LAST_NEGATIVE
from tests.const import MOCK_CONFIG_ALL


# pylint: disable=unused-argument
async def test_coordinator_opportunistic_type2_1(
    hass: HomeAssistant, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "38")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    if MAJOR_VERSION > 2024 or (MAJOR_VERSION == 2024 and MINOR_VERSION >= 7):
        config_entry.mock_state(hass=hass, state=ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)
    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()
    assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]
    assert isinstance(
        hass.data[DOMAIN][config_entry.entry_id], EVSmartChargingCoordinator
    )
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    # coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

    # Provide price
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid

    # Last price is 72.19. Low prices are 19.05, 18.03, 17.63
    # Set level to 100 (max=72.19) and 26 (max=18.77)
    coordinator.max_price = 40
    coordinator.number_opportunistic_type2_level = 26

    # Turn on switches
    await coordinator.switch_active_update(True)
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(False)
    await coordinator.switch_opportunistic_update(False)
    await coordinator.switch_opportunistic_type2_update(False)
    await hass.async_block_till_done()

    # Ready_hour = 08:00
    # 7 hours => 01:00-08:00
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 1, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 8, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_quarters == 7

    # Turn on switch_apply_limit
    await coordinator.switch_apply_limit_update(True)
    await hass.async_block_till_done()

    # Ready_hour = 08:00, Max price 40.
    # 5 hours => 03:00-08:00
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 3, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 8, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_quarters == 5

    # Turn on switch_opportunistic type 2
    await coordinator.switch_opportunistic_type2_update(True)
    await hass.async_block_till_done()

    # Ready_hour = 08:00, Max price 200. Opportunistic level 26% => max 18.77
    # 2 hours => 05:00-07:00
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 5, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 7, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_quarters == 2

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_coordinator_opportunistic_type2_2(
    hass: HomeAssistant, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "38")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    if MAJOR_VERSION > 2024 or (MAJOR_VERSION == 2024 and MINOR_VERSION >= 7):
        config_entry.mock_state(hass=hass, state=ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)
    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()
    assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]
    assert isinstance(
        hass.data[DOMAIN][config_entry.entry_id], EVSmartChargingCoordinator
    )
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    # coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

    # Provide price
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001_LAST_NEGATIVE)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid

    # Last price is -20. Low prices are -22, -30
    # Set level to 80 (max=-24)
    coordinator.max_price = 40
    coordinator.number_opportunistic_type2_level = 80

    # Turn on switches
    await coordinator.switch_active_update(True)
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(False)
    await coordinator.switch_opportunistic_update(False)
    await coordinator.switch_opportunistic_type2_update(False)
    await hass.async_block_till_done()

    # Ready_hour = 08:00
    # 7 hours => 01:00-08:00
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 1, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 8, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_quarters == 7

    # Turn on switch_apply_limit
    await coordinator.switch_apply_limit_update(True)
    await hass.async_block_till_done()

    # Ready_hour = 08:00, Max price 40.
    # 5 hours => 03:00-08:00
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 3, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 8, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_quarters == 5

    # Turn on switch_opportunistic type 2
    await coordinator.switch_opportunistic_type2_update(True)
    await hass.async_block_till_done()

    # Ready_hour = 08:00, Max price 40. Opportunistic level 80% => max -24
    # 1 hours => 06:00-07:00
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 6, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 7, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_quarters == 1

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()
