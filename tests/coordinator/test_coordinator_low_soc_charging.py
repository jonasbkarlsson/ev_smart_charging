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
from custom_components.ev_smart_charging.sensor import (
    EVSmartChargingSensorCharging,
    EVSmartChargingSensorStatus,
)

from tests.helpers.helpers import (
    MockChargerEntity,
    MockPriceEntity,
    MockSOCEntity,
    MockTargetSOCEntity,
)
from tests.price import PRICE_20220930, PRICE_20221001
from tests.const import (
    MOCK_CONFIG_LOW_PRICE_CHARGING,
)


# pylint: disable=unused-argument
async def test_coordinator_low_soc_charging1(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T10:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    # Test with max price 0.0 and 6.0 PCT/h.
    # This should give 7h charging, 01-08,

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_LOW_PRICE_CHARGING, entry_id="test"
    )
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None

    sensors = []
    sensors.append(EVSmartChargingSensorCharging(config_entry))
    sensors.append(EVSmartChargingSensorStatus(config_entry))
    assert sensors is not None
    await coordinator.add_sensor(sensors)

    # Provide price for today
    MockPriceEntity.set_state(hass, PRICE_20220930, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid is False

    # Turn on switches
    await coordinator.switch_active_update(True)
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(False)
    await coordinator.switch_keep_on_update(False)
    await coordinator.switch_low_price_charging_update(False)
    await coordinator.switch_low_soc_charging_update(True)
    await hass.async_block_till_done()

    assert coordinator.scheduler.get_charging_is_planned() is False
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Lower the SOC and connect the charger to the EV
    MockSOCEntity.set_state(hass, "15")
    await coordinator.switch_ev_connected_update(True)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid is False
    assert coordinator.scheduler.get_charging_is_planned() is False
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Move time to after tomorrow's price is available
    freezer.move_to("2022-09-30T14:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    MockSOCEntity.set_state(hass, "25")
    await coordinator.switch_ev_connected_update(False)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid
    assert coordinator.scheduler.get_charging_is_planned()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Connect charger to EV
    await coordinator.switch_ev_connected_update(True)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Disconnect charger and reduce SOC
    await coordinator.switch_ev_connected_update(False)
    MockSOCEntity.set_state(hass, "15")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Connect charger to EV
    await coordinator.switch_ev_connected_update(True)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.scheduler.get_charging_is_planned()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Increase SOC
    MockSOCEntity.set_state(hass, "20")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()
