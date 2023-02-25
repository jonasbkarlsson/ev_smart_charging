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

from tests.helpers.helpers import (
    MockChargerEntity,
    MockPriceEntity,
    MockSOCEntity,
    MockTargetSOCEntity,
)
from tests.price import PRICE_20220930, PRICE_20221001
from tests.const import (
    MOCK_CONFIG_KEEP_ON1,
    MOCK_CONFIG_KEEP_ON2,
)

# pylint: disable=unused-argument
async def test_coordinator_keep_on_issue98(
    hass: HomeAssistant, set_cet_timezone, freezer
):
    """Test Coordinator."""

    # Test a specific case with keep_on, where the EV SOC level is dropped
    # after charging is completed and the car is still connected to the charger.

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
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(True)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True

    # Move time to next day
    freezer.move_to("2022-10-01T02:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to 08:00. Fully charged.
    freezer.move_to("2022-10-01T08:00:00+02:00")
    MockSOCEntity.set_state(hass, "80")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON
    assert coordinator.sensor.charging_is_planned is False

    # Move time to 08:30, before the charge completion time (09:00). Lose some charge.
    freezer.move_to("2022-10-01T08:30:00+02:00")
    MockSOCEntity.set_state(hass, "78")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON
    assert coordinator.sensor.charging_is_planned is False

    # Move time to 08:45. Fully charged.
    freezer.move_to("2022-10-01T08:45:00+02:00")
    MockSOCEntity.set_state(hass, "80")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON
    assert coordinator.sensor.charging_is_planned is False

    # Move time to 10:30, after the charge completion time (09:00). Lose some charge.
    freezer.move_to("2022-10-01T10:30:00+02:00")
    MockSOCEntity.set_state(hass, "78")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON
    assert coordinator.sensor.charging_is_planned is False

    # Disconnect
    await coordinator.switch_ev_connected_update(False)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is False

    # Move time to 11:00, and connect
    freezer.move_to("2022-10-01T11:00:00+02:00")
    await coordinator.switch_ev_connected_update(True)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is False


async def test_coordinator_keep_on_issue104(
    hass: HomeAssistant, set_cet_timezone, freezer
):
    """Test Coordinator."""

    # Test a specific case with keep_on, where keep on is activated during charging if EV SOC
    # reaches 98% and the wish is to keep the charger on beyond the planned charging period.

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    # Test with max price 40.0 and 6.0 PCT/h. Ready hour = 10:00.
    # This should give 5h charging, 03-08

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
    await coordinator.switch_apply_limit_update(True)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(False)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is True

    # Move time to next day
    freezer.move_to("2022-10-01T02:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to charging period
    freezer.move_to("2022-10-01T03:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to 05:00. 70% charged.
    freezer.move_to("2022-10-01T05:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    MockSOCEntity.set_state(hass, "70")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    freezer.move_to("2022-10-01T05:30:00+02:00")
    await coordinator.switch_keep_on_update(True)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to 08:00
    freezer.move_to("2022-10-01T08:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON
