"""Test ev_smart_charging coordinator."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry

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
from tests.price import PRICE_20220930, PRICE_20221001, PRICE_20221002
from .const import MOCK_CONFIG_LATE

# pylint: disable=unused-argument
async def test_coordinator_late_ready(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T10:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "55")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)
    MockPriceEntity.set_state(hass, PRICE_20220930, None)

    # Ready by 18:00
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_LATE, entry_id="test"
    )
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

    sensor: EVSmartChargingSensor = EVSmartChargingSensor(config_entry)
    assert sensor is not None
    await coordinator.add_sensor(sensor)

    # Provide price. This should give a 12:00-17:00 schedule
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid is False

    # Turn on switches
    await coordinator.switch_active_update(True)
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(False)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

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

    # Move time after scheduled charging time
    # This should create a schedule 03:00-08:00
    freezer.move_to("2022-09-30T18:30:00+02:00")
    #    await coordinator.update_state()
    # TODO: it should not be update_sensors() here!
    # In practice this should be ok. Not likely that
    # charging should start directly after ready_hour.
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True

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

    MockSOCEntity.set_state(hass, "70")  # Will give 2h charging, 12:00-14:00
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True

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

    # Move time to after ready_hour # Will give 2h charging, 05:00-07:00
    freezer.move_to("2022-10-01T18:00:00+02:00")
    #    await coordinator.update_state()
    # TODO: it should not be update_sensors() here!
    # In practice this should be ok. Not likely that
    # charging should start directly after ready_hour.
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True
