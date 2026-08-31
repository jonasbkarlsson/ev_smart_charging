"""Test that low_price/low_soc charging is visible in charging_schedule."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF, MAJOR_VERSION, MINOR_VERSION
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.ev_smart_charging import async_setup_entry
from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.const import DOMAIN
from custom_components.ev_smart_charging.helpers.coordinator import get_charging_value

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
async def test_low_price_charging_visible_in_schedule(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """low_price_charging should light up the current quarter in charging_schedule,
    even when there is no optimized plan, and clear it again when switched off."""

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_LOW_PRICE_CHARGING, entry_id="test"
    )
    if MAJOR_VERSION > 2024 or (MAJOR_VERSION == 2024 and MINOR_VERSION >= 7):
        config_entry.mock_state(hass=hass, state=ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)
    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()
    coordinator: EVSmartChargingCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    assert coordinator is not None

    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
    await coordinator.update_sensors()
    await hass.async_block_till_done()

    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(False)
    await coordinator.switch_low_price_charging_update(True)
    await hass.async_block_till_done()

    # Get into a "no optimized plan" state: past the ready_quarter with no valid
    # tomorrow prices, so the Scheduler removes the schedule.
    freezer.move_to("2022-09-30T18:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20220930, None)
    await coordinator.switch_active_update(True)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.scheduler.get_charging_is_planned() is False
    assert coordinator.auto_charging_state == STATE_OFF
    # Nothing is charging -> current quarter is empty in the schedule.
    assert not get_charging_value(coordinator.sensor.charging_schedule)

    # Move to a quarter where the price is below the low-price threshold. There
    # is still no optimized plan, but low_price_charging turns the charger on.
    freezer.move_to("2022-09-30T19:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20220930, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.scheduler.get_charging_is_planned() is False
    assert coordinator.low_price_charging_state == STATE_ON
    assert coordinator.auto_charging_state == STATE_ON
    # The current quarter is now visible in the schedule attribute. Before this
    # change it stayed at 0 and the graph was blind to low-price charging.
    assert get_charging_value(coordinator.sensor.charging_schedule)

    # Turn low-price charging off -> current quarter must clear again.
    await coordinator.switch_low_price_charging_update(False)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.low_price_charging_state == STATE_OFF
    assert coordinator.auto_charging_state == STATE_OFF
    assert not get_charging_value(coordinator.sensor.charging_schedule)

    coordinator.unsubscribe_listeners()
