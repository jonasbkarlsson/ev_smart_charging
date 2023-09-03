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
from custom_components.ev_smart_charging.sensor import EVSmartChargingSensorCharging

from tests.helpers.helpers import (
    MockChargerEntity,
    MockPriceEntity,
    MockSOCEntity,
    MockTargetSOCEntity,
)
from tests.price import PRICE_20220930, PRICE_20221001
from tests.const import (
    MOCK_CONFIG_KEEP_ON1,
)


# pylint: disable=unused-argument
async def test_coordinator_keep_on1(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    # Test with max price 0.0 and 6.0 PCT/h.
    # This should give 7h charging, 02-09, or 23-00 + 03-09
    # Test "if self.switch_keep_on:"

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_KEEP_ON1, entry_id="test"
    )
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

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
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(False)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of non-continuous charging
    freezer.move_to("2022-09-30T23:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of continuous charging
    freezer.move_to("2022-10-01T02:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    MockSOCEntity.set_state(hass, "80")
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T09:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to after completion time
    freezer.move_to("2022-10-01T10:30:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move back time to recreate the schedule
    freezer.move_to("2022-09-30T20:00:00+02:00")
    MockSOCEntity.set_state(hass, "40")
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    await coordinator.switch_keep_on_update(True)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of non-continuous charging
    freezer.move_to("2022-09-30T23:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of continuous charging
    freezer.move_to("2022-10-01T02:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON
    MockSOCEntity.set_state(hass, "80")
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T09:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Loose some charge
    MockSOCEntity.set_state(hass, "79")
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    # Move time to after completion time
    freezer.move_to("2022-10-01T10:30:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_coordinator_keep_on2(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    # Test with max price 0.0 and 6.0 PCT/h.
    # This should give 7h charging, 02-09, or 23-00 + 03-09
    # Test "if (self.switch_apply_limit is False):"

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_KEEP_ON1, entry_id="test"
    )
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

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
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(True)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of non-continuous charging
    freezer.move_to("2022-09-30T23:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of continuous charging
    freezer.move_to("2022-10-01T02:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    MockSOCEntity.set_state(hass, "80")
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T09:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_coordinator_keep_on3(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    # Test with max price 0.0 and 6.0 PCT/h.
    # This should give 7h charging, 02-09, or 23-00 + 03-09
    # Test "if self.switch_ev_connected:"

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_KEEP_ON1, entry_id="test"
    )
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

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
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(False)
    await coordinator.switch_keep_on_update(True)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of non-continuous charging
    freezer.move_to("2022-09-30T23:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of continuous charging
    freezer.move_to("2022-10-01T02:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T09:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move back time to recreate the schedule
    freezer.move_to("2022-09-30T20:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of non-continuous charging
    freezer.move_to("2022-09-30T23:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of continuous charging
    freezer.move_to("2022-10-01T02:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    MockSOCEntity.set_state(hass, "80")
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T09:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_coordinator_keep_on4(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    # Test with max price 0.0 and 6.0 PCT/h.
    # This should give 7h charging, 02-09, or 23-00 + 03-09
    # Test "if self.ev_soc >= self.ev_target_soc:"

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_KEEP_ON1, entry_id="test"
    )
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

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
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(False)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of non-continuous charging
    freezer.move_to("2022-09-30T23:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of continuous charging
    freezer.move_to("2022-10-01T02:00:00+02:00")
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
    freezer.move_to("2022-09-30T20:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    MockSOCEntity.set_state(hass, "40")
    await coordinator.switch_keep_on_update(True)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of non-continuous charging
    freezer.move_to("2022-09-30T23:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of continuous charging
    freezer.move_to("2022-10-01T02:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # SOC reached Target SOC
    MockSOCEntity.set_state(hass, "80")
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to before the end of scheduled charging time
    freezer.move_to("2022-10-01T08:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T09:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to after scheduled charging time one more time
    freezer.move_to("2022-10-01T10:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move back time to recreate the schedule
    freezer.move_to("2022-09-30T20:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    MockSOCEntity.set_state(hass, "40")
    await coordinator.switch_keep_on_update(True)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of non-continuous charging
    freezer.move_to("2022-09-30T23:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of continuous charging
    freezer.move_to("2022-10-01T02:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # SOC not reached Target SOC
    MockSOCEntity.set_state(hass, "70")
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to before the end of scheduled charging time
    freezer.move_to("2022-10-01T08:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T09:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to after scheduled charging time one more time
    freezer.move_to("2022-10-01T10:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_coordinator_keep_on5(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    # Test with max price 0.0 and 6.0 PCT/h.
    # For the case with non-continuous charging
    # This should give 7h charging, 02-09, or 23-00 + 03-09
    # Test "if self.switch_keep_on:"

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_KEEP_ON1, entry_id="test"
    )
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

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
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(False)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(False)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of non-continuous charging
    freezer.move_to("2022-09-30T23:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    MockSOCEntity.set_state(hass, "45")  # Charge so that the schedule will not change
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    # Move time to scheduled charging time of continuous charging
    freezer.move_to("2022-10-01T02:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to second part of scheduled charging time of non-continuous charging
    freezer.move_to("2022-10-01T03:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T09:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move back time to recreate the schedule
    freezer.move_to("2022-09-30T20:00:00+02:00")
    MockSOCEntity.set_state(hass, "40")  # Restore SOC
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    await coordinator.switch_keep_on_update(True)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of non-continuous charging
    freezer.move_to("2022-09-30T23:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    MockSOCEntity.set_state(hass, "45")  # Charge so that the schedule will not change
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    # Move time to scheduled charging time of continuous charging
    freezer.move_to("2022-10-01T02:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to second part of scheduled charging time of non-continuous charging
    freezer.move_to("2022-10-01T03:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    MockSOCEntity.set_state(hass, "80")
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T09:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_coordinator_keep_on6(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    # Test with max price 0.0 and 6.0 PCT/h.
    # For the case with non-continuous charging
    # This should give 7h charging, 02-09, or 23-00 + 03-09
    # Test "if self.ev_soc >= self.ev_target_soc:"

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_KEEP_ON1, entry_id="test"
    )
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

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
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(False)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(True)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of non-continuous charging
    freezer.move_to("2022-09-30T23:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # SOC reached Target SOC
    MockSOCEntity.set_state(hass, "80")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to scheduled charging time of continuous charging
    freezer.move_to("2022-10-01T02:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to second part of scheduled charging time of non-continuous charging
    freezer.move_to("2022-10-01T03:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T09:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move back time to recreate the schedule
    freezer.move_to("2022-09-30T20:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    MockSOCEntity.set_state(hass, "40")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time of non-continuous charging
    freezer.move_to("2022-09-30T23:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    MockSOCEntity.set_state(hass, "45")  # Charge so that the schedule will not change
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    # Move time to scheduled charging time of continuous charging
    freezer.move_to("2022-10-01T02:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to second part of scheduled charging time of non-continuous charging
    freezer.move_to("2022-10-01T03:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # SOC reached Target SOC
    MockSOCEntity.set_state(hass, "80")
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T09:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()
