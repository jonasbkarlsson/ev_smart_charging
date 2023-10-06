"""Test ev_smart_charging coordinator."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_OFF
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.ev_smart_charging import (
    async_setup_entry,
    async_unload_entry,
)
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
from tests.const import MOCK_CONFIG_ALL


# pylint: disable=unused-argument
async def test_coordinator_ev_connected(hass: HomeAssistant, set_cet_timezone, freezer):
    """Test Coordinator."""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "70")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    config_entry.add_to_hass(hass)
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
    await coordinator.switch_ev_connected_update(False)
    await coordinator.switch_keep_on_update(False)
    await coordinator.switch_opportunistic_update(False)
    await hass.async_block_till_done()

    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # This should give 1h charging, 05-07
    assert coordinator.scheduler.charging_number_of_hours == 2
    assert coordinator.scheduler.charging_start_time.hour == 5

    # EV Connected == False

    # Move time to scheduled charging time of charging
    freezer.move_to("2022-10-01T05:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to next hour
    freezer.move_to("2022-10-01T06:05:00+02:00")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # This should give a new schedule, 2h charging, 06-08
    assert coordinator.scheduler.charging_number_of_hours == 2
    assert coordinator.scheduler.charging_start_time.hour == 6

    # Unload the entry and verify that the data has been removed
    assert await async_unload_entry(hass, config_entry)
    await hass.async_block_till_done()
    assert config_entry.entry_id not in hass.data[DOMAIN]
