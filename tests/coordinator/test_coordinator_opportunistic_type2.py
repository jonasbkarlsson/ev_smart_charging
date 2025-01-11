"""Test ev_smart_charging coordinator."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_OFF, MAJOR_VERSION, MINOR_VERSION

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
from tests.const import MOCK_CONFIG_ALL


# pylint: disable=unused-argument
async def test_coordinator_opportunistic_type2_switches(
    hass: HomeAssistant, set_cet_timezone, freezer
):
    """Test Coordinator."""

    # Test additional rules due to adding opportunistic type2
    #
    # switch_opportunistic_type2
    # if ON turn OFF switch_keep_on
    # if ON turn OFF switch_opportunistic
    #
    # switch_opportunistic_type
    # if ON turn OFF switch_opportunistic_type2
    #
    # switch_keep_on
    # if ON turn OFF switch_opportunistic_type2

    freezer.move_to("2022-09-30T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    if MAJOR_VERSION > 2024 or (MAJOR_VERSION == 2024 and MINOR_VERSION >= 7):
        config_entry.mock_state(hass=hass, state=ConfigEntryState.LOADED)
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
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(True)
    await coordinator.switch_opportunistic_update(False)
    await coordinator.switch_opportunistic_type2_update(False)
    await hass.async_block_till_done()

    assert coordinator.switch_apply_limit is False
    assert coordinator.switch_keep_on is True
    assert coordinator.switch_opportunistic is False
    assert coordinator.switch_opportunistic_type2 is False

    # Turn on switch_opportunistic_type2
    await coordinator.switch_opportunistic_type2_update(True)
    await hass.async_block_till_done()

    assert coordinator.switch_apply_limit is False
    assert coordinator.switch_keep_on is False
    assert coordinator.switch_opportunistic is False
    assert coordinator.switch_opportunistic_type2 is True

    # Turn on switch_opportunistic
    await coordinator.switch_opportunistic_update(True)
    await hass.async_block_till_done()

    assert coordinator.switch_apply_limit is True
    assert coordinator.switch_keep_on is False
    assert coordinator.switch_opportunistic is True
    assert coordinator.switch_opportunistic_type2 is False

    # Turn on switch_opportunistic_type2
    await coordinator.switch_opportunistic_type2_update(True)
    await hass.async_block_till_done()

    assert coordinator.switch_apply_limit is True
    assert coordinator.switch_keep_on is False
    assert coordinator.switch_opportunistic is False
    assert coordinator.switch_opportunistic_type2 is True

    # Turn on switch_keep_on
    await coordinator.switch_keep_on_update(True)
    await hass.async_block_till_done()

    assert coordinator.switch_apply_limit is False
    assert coordinator.switch_keep_on is True
    assert coordinator.switch_opportunistic is False
    assert coordinator.switch_opportunistic_type2 is False

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()
