"""Test ev_smart_charging coordinator."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_OFF
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.const import (
    CHARGING_STATUS_CHARGING,
    CHARGING_STATUS_DISCONNECTED,
    CHARGING_STATUS_KEEP_ON,
    CHARGING_STATUS_NO_PLAN,
    CHARGING_STATUS_NOT_ACTIVE,
    CHARGING_STATUS_WAITING_CHARGING,
    CHARGING_STATUS_WAITING_NEW_PRICE,
    DOMAIN,
)
from custom_components.ev_smart_charging.sensor import (
    EVSmartChargingSensorCharging,
    EVSmartChargingSensorStatus,
)
from tests.const import MOCK_CONFIG_ALL

from tests.helpers.helpers import (
    MockChargerEntity,
    MockPriceEntity,
    MockSOCEntity,
    MockTargetSOCEntity,
)
from tests.price import PRICE_20220930, PRICE_20221001


# pylint: disable=unused-argument
async def test_coordinator_status(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator status."""

    # Ready hour 08:00.

    # CHARGING_STATUS_NOT_ACTIVE
    # CHARGING_STATUS_DISCONNECTED
    # CHARGING_STATUS_WAITING_NEW_PRICE
    # CHARGING_STATUS_NO_PLAN
    # CHARGING_STATUS_WAITING_CHARGING
    # CHARGING_STATUS_CHARGING
    # CHARGING_STATUS_KEEP_ON

    freezer.move_to("2022-09-30T02:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "80")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)
    MockPriceEntity.set_state(hass, PRICE_20220930, None)
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    config_entry.add_to_hass(hass)
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None
    sensors = []
    sensors.append(EVSmartChargingSensorCharging(config_entry))
    sensors.append(EVSmartChargingSensorStatus(config_entry))
    assert sensors[0] is not None
    assert sensors[1] is not None
    await coordinator.add_sensor(sensors)
    await hass.async_block_till_done()
    await coordinator.switch_active_update(False)
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(False)
    await coordinator.switch_keep_on_update(False)
    await hass.async_block_till_done()

    assert coordinator.sensor_status.native_value == CHARGING_STATUS_NOT_ACTIVE

    await coordinator.switch_active_update(True)
    await hass.async_block_till_done()
    assert coordinator.sensor_status.native_value == CHARGING_STATUS_DISCONNECTED

    await coordinator.switch_ev_connected_update(True)
    await hass.async_block_till_done()
    assert coordinator.sensor_status.native_value == CHARGING_STATUS_NO_PLAN

    freezer.move_to("2022-09-30T11:00:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.sensor_status.native_value == CHARGING_STATUS_WAITING_NEW_PRICE

    freezer.move_to("2022-09-30T14:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    await hass.async_block_till_done()
    assert coordinator.sensor_status.native_value == CHARGING_STATUS_NO_PLAN

    # Ready hour 08:00. Charge 04:00-07:00
    MockSOCEntity.set_state(hass, "67")
    await coordinator.switch_keep_on_update(True)
    await hass.async_block_till_done()
    assert coordinator.sensor_status.native_value == CHARGING_STATUS_WAITING_CHARGING

    freezer.move_to("2022-10-01T04:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await hass.async_block_till_done()
    assert coordinator.sensor_status.native_value == CHARGING_STATUS_CHARGING

    MockSOCEntity.set_state(hass, "80")
    await hass.async_block_till_done()
    assert coordinator.sensor_status.native_value == CHARGING_STATUS_KEEP_ON

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()
