"""Test ev_smart_charging coordinator."""
from datetime import datetime

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.util import dt as dt_util

from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.const import DOMAIN
from custom_components.ev_smart_charging.sensor import EVSmartChargingSensorCharging

from tests.helpers.helpers import (
    MockChargerEntity,
    MockPriceEntity,
    MockSOCEntity,
    MockTargetSOCEntity,
)
from tests.price import PRICE_20220930, PRICE_20221001
from tests.const import MOCK_CONFIG_ALL, MOCK_CONFIG_MIN_SOC, MOCK_CONFIG_NO_TARGET_SOC


# pylint: disable=unused-argument
async def test_coordinator(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "55")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    # Test default Target SOC
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_NO_TARGET_SOC, entry_id="test"
    )
    config_entry.add_to_hass(hass)
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

    sensor: EVSmartChargingSensorCharging = EVSmartChargingSensorCharging(config_entry)
    assert sensor is not None
    await coordinator.add_sensor([sensor])

    assert coordinator.ev_target_soc == 100

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()

    # Test turn on and off charging
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    config_entry.add_to_hass(hass)
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

    sensor: EVSmartChargingSensorCharging = EVSmartChargingSensorCharging(config_entry)
    assert sensor is not None
    await coordinator.add_sensor([sensor])
    assert coordinator.ev_target_soc == 80

    await coordinator.turn_on_charging()
    assert coordinator.sensor.native_value == STATE_ON
    await coordinator.turn_off_charging()
    assert coordinator.sensor.native_value == STATE_OFF

    # Provide price
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid

    # Turn on switches
    await coordinator.switch_active_update(True)
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time
    freezer.move_to("2022-10-01T03:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # If no change of SOC has been registred, turn of charging at
    # the end of the charging schedule.
    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T08:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move back time to recreate the schedule
    freezer.move_to("2022-09-30T20:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time
    freezer.move_to("2022-10-01T03:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # SOC reached Target SOC
    MockSOCEntity.set_state(hass, "80")
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move back time to recreate the schedule
    MockSOCEntity.set_state(hass, "55")
    freezer.move_to("2022-09-30T20:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Disconnect EV from charger
    await coordinator.switch_ev_connected_update(False)
    await hass.async_block_till_done()

    # Move time to scheduled charging time
    freezer.move_to("2022-10-01T03:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Connect EV to charger
    await coordinator.switch_ev_connected_update(True)
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_coordinator_min_soc1(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator with min soc when max limit is low."""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "11")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 10)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    # Test default Target SOC
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_MIN_SOC, entry_id="test"
    )
    config_entry.add_to_hass(hass)
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator

    sensor: EVSmartChargingSensorCharging = EVSmartChargingSensorCharging(config_entry)
    assert sensor is not None
    await coordinator.add_sensor([sensor])

    # Provide price
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)

    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid

    # Turn on switches
    await coordinator.switch_active_update(True)
    await coordinator.switch_apply_limit_update(True)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)

    # Move time to just before scheduled charging time
    freezer.move_to("2022-10-01T02:50:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time
    freezer.move_to("2022-10-01T03:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Min SOC reached
    MockSOCEntity.set_state(hass, "40")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_coordinator_min_soc2(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator with min soc when max limit is low."""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "11")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 10)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    # Test default Target SOC
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_MIN_SOC, entry_id="test"
    )
    config_entry.add_to_hass(hass)
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator

    sensor: EVSmartChargingSensorCharging = EVSmartChargingSensorCharging(config_entry)
    assert sensor is not None
    await coordinator.add_sensor([sensor])

    # Provide price
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)

    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid

    # Turn on switches
    await coordinator.switch_active_update(True)
    await coordinator.switch_apply_limit_update(True)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)

    # Move time to just before scheduled charging time
    freezer.move_to("2022-10-01T02:50:00+02:00")
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
    assert coordinator.sensor.charging_number_of_hours == 5

    # Move time to scheduled charging time
    freezer.move_to("2022-10-01T03:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to just after scheduled charging time
    freezer.move_to("2022-10-01T08:00:00+02:00")
    await coordinator.update_state()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    assert coordinator.sensor.charging_is_planned is False
    assert coordinator.sensor.charging_start_time is None
    assert coordinator.sensor.charging_stop_time is None
    assert coordinator.sensor.charging_number_of_hours == 0

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_validate_input_sensors(hass: HomeAssistant):
    """Test validate_input_sensors()"""

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    config_entry.add_to_hass(hass)
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    entity_registry: EntityRegistry = async_entity_registry_get(hass)

    assert coordinator.validate_input_sensors() == "Input sensors not ready."
    MockPriceEntity.create(hass, entity_registry, 123)
    assert coordinator.validate_input_sensors() == "Input sensors not ready."
    MockSOCEntity.create(hass, entity_registry, "55")
    assert coordinator.validate_input_sensors() == "Input sensors not ready."
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    assert coordinator.validate_input_sensors() is None

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_get_entity_id_from_unique_id(hass: HomeAssistant):
    """Test get_entity_id_from_unique_id()"""

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    config_entry.add_to_hass(hass)
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    entity_registry: EntityRegistry = async_entity_registry_get(hass)

    MockPriceEntity.create(hass, entity_registry, 123)
    MockSOCEntity.create(hass, entity_registry, "55")
    MockTargetSOCEntity.create(hass, entity_registry, "80")

    assert coordinator.get_entity_id_from_unique_id("foobar") is None

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_coordinator_fix_soc(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "70")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    config_entry.add_to_hass(hass)
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

    sensor: EVSmartChargingSensorCharging = EVSmartChargingSensorCharging(config_entry)
    assert sensor is not None
    await coordinator.add_sensor([sensor])
    assert coordinator.ev_target_soc == 80

    # Provide price
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid

    # Turn on switches. Should give 2h schedule 05:00-07:00
    await coordinator.switch_active_update(True)
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to before scheduled charging time
    freezer.move_to("2022-10-01T04:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time
    freezer.move_to("2022-10-01T05:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T07:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T07:30:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to after ready_hour
    freezer.move_to("2022-10-01T08:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()
