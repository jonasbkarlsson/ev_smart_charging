"""Test ev_smart_charging coordinator."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_OFF
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
from tests.price import PRICE_20220930, PRICE_20221001_NEGATIVE
from tests.const import (
    MOCK_CONFIG_NEGATIVE_PRICE_0,
    MOCK_CONFIG_NEGATIVE_PRICE_5,
)


# pylint: disable=unused-argument
async def test_coordinator_negative_price_5(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    # Test with max price -5.0 and 6.0 PCT/h.
    # This should give 2h charging, 05-07

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_NEGATIVE_PRICE_5, entry_id="test"
    )
    config_entry.add_to_hass(hass)
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

    sensor: EVSmartChargingSensorCharging = EVSmartChargingSensorCharging(config_entry)
    assert sensor is not None
    await coordinator.add_sensor([sensor])

    # Provide price
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001_NEGATIVE)
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

    # This should give 1h charging, 05-07
    assert coordinator.scheduler.charging_number_of_hours == 2
    assert coordinator.scheduler.charging_start_time.hour == 5

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_coordinator_negative_price_0(
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
    # This should give 3h charging, 04-07

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_NEGATIVE_PRICE_0, entry_id="test"
    )
    config_entry.add_to_hass(hass)
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

    sensor: EVSmartChargingSensorCharging = EVSmartChargingSensorCharging(config_entry)
    assert sensor is not None
    await coordinator.add_sensor([sensor])

    # Provide price
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001_NEGATIVE)
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

    # This should give 1h charging, 05-07
    assert coordinator.scheduler.charging_number_of_hours == 3
    assert coordinator.scheduler.charging_start_time.hour == 4

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()
