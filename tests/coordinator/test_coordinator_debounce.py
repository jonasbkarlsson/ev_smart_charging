"""Test ev_smart_charging coordinator."""

import asyncio
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from freezegun import freeze_time

from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.const import (
    DOMAIN,
)
from custom_components.ev_smart_charging.sensor import EVSmartChargingSensor
from tests.const import MOCK_CONFIG_ALL

from tests.helpers.helpers import (
    MockChargerEntity,
    MockPriceEntity,
    MockSOCEntity,
    MockTargetSOCEntity,
)
from tests.price import PRICE_20220930

# pylint: disable=unused-argument
@pytest.mark.ensure_debounce
@freeze_time("2022-09-30T02:00:00+02:00", tick=True)
async def test_coordinator_debounce(
    hass: HomeAssistant,
    skip_service_calls,
    set_cet_timezone,
    freezer,
    skip_update_hourly,
):
    """Test Coordinator debounce."""

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "67")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)
    MockPriceEntity.set_state(hass, PRICE_20220930, None)
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator is not None
    sensor: EVSmartChargingSensor = EVSmartChargingSensor(config_entry)
    assert sensor is not None
    await coordinator.add_sensor(sensor)
    await hass.async_block_till_done()
    await coordinator.switch_active_update(False)
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(False)
    await coordinator.switch_keep_on_update(False)
    await hass.async_block_till_done()
    assert coordinator.sensor.state == STATE_OFF

    await coordinator.turn_on_charging()
    await asyncio.sleep(2)
    await hass.async_block_till_done()
    assert coordinator.sensor.state == STATE_ON

    await coordinator.turn_off_charging()
    await asyncio.sleep(0.1)
    await hass.async_block_till_done()
    assert coordinator.sensor.state == STATE_ON
    await coordinator.turn_on_charging()
    await asyncio.sleep(2)
    await hass.async_block_till_done()
    assert coordinator.sensor.state == STATE_ON

    await coordinator.turn_off_charging()
    await asyncio.sleep(2)
    await hass.async_block_till_done()
    assert coordinator.sensor.state == STATE_OFF

    await coordinator.turn_on_charging()
    await asyncio.sleep(0.1)
    await hass.async_block_till_done()
    assert coordinator.sensor.state == STATE_OFF
    await coordinator.turn_off_charging()
    await asyncio.sleep(2)
    await hass.async_block_till_done()
    assert coordinator.sensor.state == STATE_OFF
