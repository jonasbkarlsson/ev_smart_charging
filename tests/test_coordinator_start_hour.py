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
from custom_components.ev_smart_charging.sensor import EVSmartChargingSensor

from tests.helpers.helpers import (
    MockChargerEntity,
    MockPriceEntity,
    MockSOCEntity,
    MockTargetSOCEntity,
)
from tests.price import PRICE_20221001, PRICE_20221002
from .const import MOCK_CONFIG_START_HOUR, MOCK_CONFIG_START_HOUR2

# pylint: disable=unused-argument
async def test_coordinator_start_hour(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-10-01T05:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "66")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)
    MockPriceEntity.set_state(hass, PRICE_20221001, None)

    # Start_hour = 09:00, Ready_hour = 22:00
    # 5 hours => 10:00-15:00
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_START_HOUR, entry_id="test"
    )
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

    sensor: EVSmartChargingSensor = EVSmartChargingSensor(config_entry)
    assert sensor is not None
    await coordinator.add_sensor(sensor)
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid is False

    # Continuous charging
    await coordinator.switch_active_update(True)
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(False)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 10, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 15, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_hours == 5

    # Non-continuous charging
    await coordinator.switch_continuous_update(False)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 10, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 15, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_hours == 5

    # 8 hours => 09:00-17:00 or 09:00-16:00 + 21:00-22:00
    # Continuous charging
    MockSOCEntity.set_state(hass, "58")
    await coordinator.switch_continuous_update(True)
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 9, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 17, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_hours == 8

    # Non-continuous charging
    await coordinator.switch_continuous_update(False)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 9, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 22, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_hours == 8

    # Continuous charging - maximum time
    MockSOCEntity.set_state(hass, "0")
    await coordinator.switch_continuous_update(True)
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 9, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 22, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_hours == 13

    freezer.move_to("2022-10-01T11:00:00+02:00")
    # Start_hour = 09:00, Ready_hour = 22:00
    # 5 hours => 11:00-16:00
    # Continuous charging
    MockSOCEntity.set_state(hass, "66")
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 11, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 16, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_hours == 5

    # Non-continuous charging
    await coordinator.switch_ev_connected_update(False)  # Disconnect
    await coordinator.update_sensors()
    await coordinator.switch_continuous_update(False)
    MockSOCEntity.set_state(hass, "67")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    await coordinator.switch_ev_connected_update(True)  # Connect
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 11, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 16, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_hours == 5

    freezer.move_to("2022-10-01T14:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, PRICE_20221002)
    MockSOCEntity.set_state(hass, "66")
    # Start_hour = 09:00, Ready_hour = 22:00
    # 5 hours => 14:00-19:00 or 14:00-17:00 + 20:00-22:00
    # Continuous charging
    await coordinator.switch_ev_connected_update(False)  # Disconnect
    await coordinator.update_sensors()
    await coordinator.switch_continuous_update(True)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    await coordinator.switch_ev_connected_update(True)  # Connect
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 14, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 19, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_hours == 5

    # Non-continuous charging
    await coordinator.switch_ev_connected_update(False)  # Disconnect
    await coordinator.update_sensors()
    await coordinator.switch_continuous_update(False)
    MockSOCEntity.set_state(hass, "67")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    await coordinator.switch_ev_connected_update(True)  # Connect
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 14, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 1, 22, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_hours == 5


async def test_coordinator_start_hour2(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-10-01T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "66")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)
    MockPriceEntity.set_state(hass, PRICE_20221001, PRICE_20221002)

    # Start_hour = 20:00, Ready_hour = 04:00
    # 5 hours => 23:00-04:00, or 21:00-22:00 + 00:00-04:00
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_START_HOUR2, entry_id="test"
    )
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

    sensor: EVSmartChargingSensor = EVSmartChargingSensor(config_entry)
    assert sensor is not None
    await coordinator.add_sensor(sensor)
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid is True

    # Continuous charging
    await coordinator.switch_active_update(True)
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(False)
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 23, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 2, 4, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_hours == 5

    # Non-continuous charging
    await coordinator.switch_continuous_update(False)
    await hass.async_block_till_done()
    MockSOCEntity.set_state(hass, "67")
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 1, 21, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 2, 4, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_hours == 5

    freezer.move_to("2022-10-01T22:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, PRICE_20221002)
    MockSOCEntity.set_state(hass, "70")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    # Start_hour = 20:00, Ready_hour = 04:00
    # 4 hours => 00:00-04:00
    # Continuous charging
    await coordinator.switch_continuous_update(True)
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 2, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 2, 4, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_hours == 4

    # Non-continuous charging
    await coordinator.switch_continuous_update(False)
    await hass.async_block_till_done()
    MockSOCEntity.set_state(hass, "69")
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 10, 2, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 10, 2, 4, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_hours == 4

    # # Continuous charging - maximum time
    # MockSOCEntity.set_state(hass, "0")
    # await coordinator.switch_continuous_update(True)
    # await coordinator.update_sensors()
    # await hass.async_block_till_done()

    # assert coordinator.auto_charging_state == STATE_OFF
    # assert coordinator.sensor.state == STATE_OFF
    # assert coordinator.sensor.charging_is_planned is True
    # assert coordinator.sensor.charging_start_time == datetime(
    #     2022, 10, 1, 9, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    # )
    # assert coordinator.sensor.charging_stop_time == datetime(
    #     2022, 10, 1, 22, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    # )
    # assert coordinator.sensor.charging_number_of_hours == 13
