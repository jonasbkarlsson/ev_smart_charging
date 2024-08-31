"""Test ev_smart_charging coordinator."""

from datetime import datetime

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF, MAJOR_VERSION, MINOR_VERSION
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
from tests.price import PRICE_20220930, PRICE_20221001, PRICE_20221002
from tests.const import MOCK_CONFIG_LATE, MOCK_CONFIG_LATE24


# pylint: disable=unused-argument
async def test_coordinator_late_ready(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T10:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "50")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)
    MockPriceEntity.set_state(hass, PRICE_20220930, None)

    # Ready by 18:00
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_LATE, entry_id="test"
    )
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
    assert coordinator is not None

    # Provide price. This should give a 12:00-17:00 schedule
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid is False

    # Turn on switches
    await coordinator.switch_active_update(True)
    await coordinator.switch_active_price_charging_update(True)
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(False)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 9, 30, 12, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 9, 30, 17, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_quarters == 5 * 4

    # Move time to scheduled charging time
    freezer.move_to("2022-09-30T12:30:00+02:00")
    await coordinator.update_state()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to after new price is available
    freezer.move_to("2022-09-30T13:30:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time after scheduled charging time
    # This should not create a new schedule
    freezer.move_to("2022-09-30T17:30:00+02:00")
    await coordinator.update_state()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is False

    MockSOCEntity.set_state(hass, "80")
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    # Move time after scheduled charging time
    # This should create a schedule 03:00-08:00
    freezer.move_to("2022-09-30T18:30:00+02:00")
    await coordinator.update_state()
    # TODO: it should not be update_sensors() here!
    # In practice this should be ok. Not likely that
    # charging should start directly after ready_quarter.
    MockSOCEntity.set_state(hass, "50")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 3, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 8, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_quarters == 5 * 4

    # Move time to after midnight
    freezer.move_to("2022-10-01T00:30:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time
    freezer.move_to("2022-10-01T03:00:00+02:00")
    await coordinator.update_state()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    MockSOCEntity.set_state(hass, "80")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is False

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T10:00:00+02:00")
    await coordinator.update_state()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    MockSOCEntity.set_state(hass, "68")  # Will give 2h charging, 12:00-14:00
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 12, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 14, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_quarters == 2 * 4

    # Move time to scheduled charging time
    freezer.move_to("2022-10-01T12:30:00+02:00")
    await coordinator.update_state()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to new prices
    freezer.move_to("2022-10-01T13:30:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, PRICE_20221002)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T15:00:00+02:00")
    await coordinator.update_state()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is False

    # Move time to after ready_quarter # Will give 2h charging, 05:00-07:00
    freezer.move_to("2022-10-01T18:00:00+02:00")
    #    await coordinator.update_state()
    # TODO: it should not be update_sensors() here!
    # In practice this should be ok. Not likely that
    # charging should start directly after ready_quarter.
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 2, 5, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 2, 7, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_quarters == 2 * 4

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_coordinator_late_ready2(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T10:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "50")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)
    MockPriceEntity.set_state(hass, PRICE_20220930, None)

    # Ready by 00:00, that is 24:00
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_LATE24, entry_id="test"
    )
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
    assert coordinator is not None

    # Provide price. This should give a 5h schedule, 19:00-24:00 schedule
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid is False

    # Turn on switches
    await coordinator.switch_active_update(True)
    await coordinator.switch_active_price_charging_update(True)
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(False)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 9, 30, 19, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_quarters == 5 * 4

    # Move time to after new price is available
    freezer.move_to("2022-09-30T13:30:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True

    # Move time to scheduled charging time
    freezer.move_to("2022-09-30T19:30:00+02:00")
    await coordinator.update_state()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_coordinator_late_ready3(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "50")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)

    # Ready by 00:00, that is 24:00
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_LATE24, entry_id="test"
    )
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
    assert coordinator is not None

    # Provide price.
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid is True

    # Turn on switches
    await coordinator.switch_active_update(True)
    await coordinator.switch_active_price_charging_update(True)
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(False)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True

    # Move time to after midnight
    # This should give a 5h schedule, 03:00-08:00 schedule
    freezer.move_to("2022-10-01T00:30:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 3, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 8, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_quarters == 5 * 4

    # Move time to scheduled charging time
    freezer.move_to("2022-10-01T03:00:00+02:00")
    await coordinator.update_state()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()
