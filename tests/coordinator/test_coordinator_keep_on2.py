"""Test ev_smart_charging coordinator."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.ev_smart_charging import async_setup_entry
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
from tests.const import (
    MOCK_CONFIG_KEEP_ON1,
    MOCK_CONFIG_KEEP_ON2,
)

# pylint: disable=unused-argument
async def test_coordinator_keep_on_get_entities(
    hass: HomeAssistant, set_cet_timezone, freezer
):
    """Test Coordinator."""

    # Test that switch_apply_limit and switch_keep_on can not be both True

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_KEEP_ON2, entry_id="test"
    )
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

    # Turn on switches
    await coordinator.switch_active_update(True)
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(False)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(True)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    assert coordinator.switch_apply_limit is False
    assert coordinator.switch_keep_on is True

    # Turn on apply_limit and check that keep_on is turned off
    await coordinator.switch_apply_limit_update(True)
    await hass.async_block_till_done()

    assert coordinator.switch_apply_limit is True
    assert coordinator.switch_keep_on is False

    # Turn on keep_on and check that apply_limit is turned off
    await coordinator.switch_keep_on_update(True)
    await hass.async_block_till_done()

    assert coordinator.switch_apply_limit is False
    assert coordinator.switch_keep_on is True


async def test_coordinator_keep_on_schedule(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    # Test that the charging schedule is updated even if the EV is
    # continuously connected to the charger for several days.

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    # Test with max price 0.0 and 6.0 PCT/h.
    # For the case with non-continuous charging
    # This should give 7h charging, 02-09, or 23-00 + 03-09

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_KEEP_ON1, entry_id="test"
    )
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

    sensor: EVSmartChargingSensor = EVSmartChargingSensor(config_entry)
    assert sensor is not None
    await coordinator.add_sensor(sensor)

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

    # Move time to after prices for next day has been published
    freezer.move_to("2022-10-01T14:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, PRICE_20221002)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # The day should now be 2022-10-01, and not 2022-09-30
    assert coordinator.sensor.charging_schedule is not None
    assert coordinator.sensor.charging_schedule[0]["start"].day == 1


async def test_coordinator_keep_on_connect(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    # Test that the charging schedule is updated even if the EV is
    # continuously connected to the charger for several days.
    # Assume ev_connected is used to indicated that the EV is
    # connected to the charger.

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    # Test with max price 0.0 and 6.0 PCT/h.
    # For the case with non-continuous charging
    # This should give 7h charging, 02-09, or 23-00 + 03-09

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_KEEP_ON1, entry_id="test"
    )
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

    sensor: EVSmartChargingSensor = EVSmartChargingSensor(config_entry)
    assert sensor is not None
    await coordinator.add_sensor(sensor)

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

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T09:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Disconnect EV
    await coordinator.switch_ev_connected_update(False)
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_schedule is not None
    assert coordinator.sensor.charging_schedule[0]["start"].day == 1

    # Connect EV
    await coordinator.switch_ev_connected_update(True)
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON
    assert coordinator.sensor.charging_schedule is not None
    assert coordinator.sensor.charging_schedule[0]["start"].day == 1

    # Move time to after prices for next day has been published
    freezer.move_to("2022-10-01T14:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, PRICE_20221002)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    assert coordinator.sensor.charging_schedule is not None
    assert coordinator.sensor.charging_schedule[0]["start"].day == 1

    # Disconnect EV
    await coordinator.switch_ev_connected_update(False)
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_schedule is not None
    assert coordinator.sensor.charging_schedule[0]["start"].day == 1

    # Connect EV
    await coordinator.switch_ev_connected_update(True)
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON
    # The day should now be 2022-10-01
    assert coordinator.sensor.charging_schedule is not None
    assert coordinator.sensor.charging_schedule[0]["start"].day == 1

    # Disconnect EV
    await coordinator.switch_ev_connected_update(False)
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    # The day should now be 2022-10-01
    assert coordinator.sensor.charging_schedule is not None
    assert coordinator.sensor.charging_schedule[0]["start"].day == 1

    # Connect EV with less SOC. The charging should not start.
    # Should lead to a schedule 02-09.
    freezer.move_to("2022-10-01T16:00:00+02:00")
    MockSOCEntity.set_state(hass, "40")
    await coordinator.switch_ev_connected_update(True)
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to just before scheduled charging time
    freezer.move_to("2022-10-02T01:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to just after start of scheduled charging time
    freezer.move_to("2022-10-02T02:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON


async def test_coordinator_keep_on_connect2(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    # Test that the charging schedule is updated even if the EV is
    # continuously connected to the charger for several days.
    # Assume ev_connected is not used.

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    # Test with max price 0.0 and 6.0 PCT/h.
    # For the case with non-continuous charging
    # This should give 7h charging, 02-09, or 23-00 + 03-09

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_KEEP_ON1, entry_id="test"
    )
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

    sensor: EVSmartChargingSensor = EVSmartChargingSensor(config_entry)
    assert sensor is not None
    await coordinator.add_sensor(sensor)

    # Provide price
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid

    # Turn on switches
    await coordinator.switch_active_update(True)
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(False)
    await coordinator.switch_ev_connected_update(True)  # Set to True and don't change
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

    # Move time to after scheduled charging time
    freezer.move_to("2022-10-01T09:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to after prices for next day has been published
    freezer.move_to("2022-10-01T14:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, PRICE_20221002)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # The day should now be 2022-10-01, and not 2022-09-30
    assert coordinator.sensor.charging_schedule is not None
    assert coordinator.sensor.charging_schedule[0]["start"].day == 1

    # Disconnect
    await coordinator.switch_ev_connected_update(False)
    await hass.async_block_till_done()

    # Connected with less SOC. The charging should not start.
    # Should lead to a schedule 02-09.
    freezer.move_to("2022-10-01T16:00:00+02:00")
    MockSOCEntity.set_state(hass, "40")
    await coordinator.switch_ev_connected_update(True)
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to just before scheduled charging time
    freezer.move_to("2022-10-02T01:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to just after start of scheduled charging time
    freezer.move_to("2022-10-02T02:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON


async def test_coordinator_keep_on_connect3(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    # Test that the charging is turned on when connecting
    # the EV when it does not need charging.

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "80")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)
    # Provide price
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)

    # Test with max price 0.0 and 6.0 PCT/h.
    # For the case with non-continuous charging
    # This should give 7h charging, 02-09, or 23-00 + 03-09

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_KEEP_ON1, entry_id="test"
    )
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

    sensor: EVSmartChargingSensor = EVSmartChargingSensor(config_entry)
    assert sensor is not None
    await coordinator.add_sensor(sensor)
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

    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Lower the SOC. The charging should not stop.
    freezer.move_to("2022-09-30T16:00:00+02:00")
    await coordinator.update_state()
    await hass.async_block_till_done()
    MockSOCEntity.set_state(hass, "40")
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Higer the SOC. The charging should not stop.
    freezer.move_to("2022-09-30T23:00:00+02:00")
    await coordinator.update_state()
    await hass.async_block_till_done()
    MockSOCEntity.set_state(hass, "80")
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Lower the SOC. The charging should not stop.
    freezer.move_to("2022-10-01T11:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_state()
    await hass.async_block_till_done()
    MockSOCEntity.set_state(hass, "40")
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON
