"""Test ev_smart_charging coordinator."""

from unittest.mock import AsyncMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_OFF, STATE_ON

from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.const import (
    DOMAIN,
)
from tests.const import MOCK_CONFIG_ALL


# pylint: disable=unused-argument
async def test_periodic_check_charging_state_retries_when_entity_is_off(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone
):
    """Test that periodic charging state checks retry charging when the entity is off."""

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    config_entry.add_to_hass(hass)
    coordinator = EVSmartChargingCoordinator(hass, config_entry)

    coordinator.charging_state_entity_id = "binary_sensor.ev_charging"
    coordinator.auto_charging_state = STATE_ON
    coordinator.turn_on_charging = AsyncMock()

    hass.states.async_set(coordinator.charging_state_entity_id, STATE_OFF)

    await coordinator.periodic_check_charging_state()

    coordinator.turn_on_charging.assert_awaited_once_with()

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_periodic_check_charging_state_does_not_retry_when_entity_is_on(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone
):
    """Test that periodic charging state checks do not retry when the entity is already on."""

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    config_entry.add_to_hass(hass)
    coordinator = EVSmartChargingCoordinator(hass, config_entry)

    coordinator.charging_state_entity_id = "binary_sensor.ev_charging"
    coordinator.auto_charging_state = STATE_ON
    coordinator.turn_on_charging = AsyncMock()

    hass.states.async_set(coordinator.charging_state_entity_id, STATE_ON)

    await coordinator.periodic_check_charging_state()

    coordinator.turn_on_charging.assert_not_awaited()

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_periodic_check_charging_state_does_not_retry_when_auto_charging_is_off(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone
):
    """Test that periodic charging state checks do not retry when charging should be off."""

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    config_entry.add_to_hass(hass)
    coordinator = EVSmartChargingCoordinator(hass, config_entry)

    coordinator.charging_state_entity_id = "binary_sensor.ev_charging"
    coordinator.auto_charging_state = STATE_OFF
    coordinator.turn_on_charging = AsyncMock()

    hass.states.async_set(coordinator.charging_state_entity_id, STATE_OFF)

    await coordinator.periodic_check_charging_state()

    coordinator.turn_on_charging.assert_not_awaited()

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()


async def test_periodic_check_charging_state_does_not_retry_when_state_is_missing(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone
):
    """Test that periodic charging state checks do not retry when the entity state is missing."""

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    config_entry.add_to_hass(hass)
    coordinator = EVSmartChargingCoordinator(hass, config_entry)

    coordinator.charging_state_entity_id = "binary_sensor.ev_charging"
    coordinator.auto_charging_state = STATE_ON
    coordinator.turn_on_charging = AsyncMock()

    await coordinator.periodic_check_charging_state()

    coordinator.turn_on_charging.assert_not_awaited()

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()
