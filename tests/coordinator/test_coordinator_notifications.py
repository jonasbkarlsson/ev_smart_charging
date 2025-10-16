"""Tests for persistent notifications in coordinator."""

from unittest.mock import AsyncMock, MagicMock
import sys
import pytest
from custom_components.ev_smart_charging.coordinator import EVSmartChargingCoordinator


@pytest.mark.asyncio
async def test_switch_apply_limit_update_turns_off_keep_on_and_notifies(
    monkeypatch,
):
    """Test switch_apply_limit_update turns off keep_on and notifies if max_price is 0"""

    # Setup
    coordinator = MagicMock()
    coordinator.switch_apply_limit = False
    coordinator.switch_keep_on = True
    coordinator.switch_keep_on_entity_id = "switch.keep_on"
    coordinator.switch_opportunistic = False
    coordinator.switch_opportunistic_entity_id = None
    coordinator.max_price = 0
    coordinator.get_all_entity_ids = MagicMock()
    coordinator.update_configuration = AsyncMock()
    coordinator.hass = MagicMock()
    coordinator.hass.services.async_call = AsyncMock()

    # Patch SWITCH and SERVICE_TURN_OFF
    module = sys.modules["custom_components.ev_smart_charging.coordinator"]
    monkeypatch.setattr(module, "SWITCH", "switch")
    monkeypatch.setattr(module, "SERVICE_TURN_OFF", "turn_off")

    # Call
    # We need to call the real method, not a MagicMock
    # Patch _LOGGER to avoid logging errors
    monkeypatch.setattr(module, "_LOGGER", MagicMock())
    # Patch get_all_entity_ids to do nothing
    coordinator.get_all_entity_ids = MagicMock()
    # Patch update_configuration to do nothing
    coordinator.update_configuration = AsyncMock()

    # Create a real instance for method binding
    real_coordinator = EVSmartChargingCoordinator.__new__(EVSmartChargingCoordinator)
    real_coordinator.switch_apply_limit = False
    real_coordinator.switch_keep_on = True
    real_coordinator.switch_keep_on_entity_id = "switch.keep_on"
    real_coordinator.switch_opportunistic = False
    real_coordinator.switch_opportunistic_entity_id = None
    real_coordinator.max_price = 0
    real_coordinator.get_all_entity_ids = MagicMock()
    real_coordinator.update_configuration = AsyncMock()
    real_coordinator.hass = MagicMock()
    real_coordinator.hass.services.async_call = AsyncMock()

    # Call method
    await real_coordinator.switch_apply_limit_update(True)

    # Assert keep_on turned off
    real_coordinator.hass.services.async_call.assert_any_call(
        domain="switch",
        service="turn_off",
        target={"entity_id": "switch.keep_on"},
    )
    # Assert notification sent
    real_coordinator.hass.services.async_call.assert_any_call(
        "persistent_notification",
        "create",
        {
            "message": "Apply price limit is turn on, but the price limit is set to zero.",
            "title": "EV Smart Charging",
        },
    )
    # Assert update_configuration called
    real_coordinator.update_configuration.assert_awaited()


@pytest.mark.asyncio
async def test_switch_apply_limit_update_turns_off_opportunistic(monkeypatch):
    """Test switch_apply_limit_update turns off opportunistic if state is False"""

    # Setup
    module = sys.modules["custom_components.ev_smart_charging.coordinator"]
    monkeypatch.setattr(module, "SWITCH", "switch")
    monkeypatch.setattr(module, "SERVICE_TURN_OFF", "turn_off")
    monkeypatch.setattr(module, "_LOGGER", MagicMock())

    real_coordinator = EVSmartChargingCoordinator.__new__(EVSmartChargingCoordinator)
    real_coordinator.switch_apply_limit = True
    real_coordinator.switch_keep_on = False
    real_coordinator.switch_keep_on_entity_id = None
    real_coordinator.switch_opportunistic = True
    real_coordinator.switch_opportunistic_entity_id = "switch.opportunistic"
    real_coordinator.max_price = 10
    real_coordinator.get_all_entity_ids = MagicMock()
    real_coordinator.update_configuration = AsyncMock()
    real_coordinator.hass = MagicMock()
    real_coordinator.hass.services.async_call = AsyncMock()

    await real_coordinator.switch_apply_limit_update(False)

    real_coordinator.hass.services.async_call.assert_any_call(
        domain="switch",
        service="turn_off",
        target={"entity_id": "switch.opportunistic"},
    )
    real_coordinator.update_configuration.assert_awaited()


@pytest.mark.asyncio
async def test_switch_apply_limit_update_no_actions(monkeypatch):
    """Test switch_apply_limit_update does nothing if no conditions are met"""

    module = sys.modules["custom_components.ev_smart_charging.coordinator"]
    monkeypatch.setattr(module, "SWITCH", "switch")
    monkeypatch.setattr(module, "SERVICE_TURN_OFF", "turn_off")
    monkeypatch.setattr(module, "_LOGGER", MagicMock())

    real_coordinator = EVSmartChargingCoordinator.__new__(EVSmartChargingCoordinator)
    real_coordinator.switch_apply_limit = False
    real_coordinator.switch_keep_on = False
    real_coordinator.switch_keep_on_entity_id = None
    real_coordinator.switch_opportunistic = False
    real_coordinator.switch_opportunistic_entity_id = None
    real_coordinator.max_price = 10
    real_coordinator.get_all_entity_ids = MagicMock()
    real_coordinator.update_configuration = AsyncMock()
    real_coordinator.hass = MagicMock()
    real_coordinator.hass.services.async_call = AsyncMock()

    await real_coordinator.switch_apply_limit_update(True)

    # Should not call any service except update_configuration
    real_coordinator.hass.services.async_call.assert_not_called()
    real_coordinator.update_configuration.assert_awaited()


@pytest.mark.asyncio
async def test_switch_low_price_charging_update_notification_sent(monkeypatch):
    """Test notification is sent when low_price_charging is 0 and switch is turned on."""
    module = sys.modules["custom_components.ev_smart_charging.coordinator"]
    monkeypatch.setattr(module, "_LOGGER", MagicMock())

    real_coordinator = EVSmartChargingCoordinator.__new__(EVSmartChargingCoordinator)
    real_coordinator.switch_low_price_charging = False
    real_coordinator.low_price_charging = 0
    real_coordinator.hass = MagicMock()
    real_coordinator.hass.services.async_call = AsyncMock()
    real_coordinator.update_configuration = AsyncMock()

    await real_coordinator.switch_low_price_charging_update(True)

    real_coordinator.hass.services.async_call.assert_any_call(
        "persistent_notification",
        "create",
        {
            "message": "Low price charging is turn on, "
            "but the low price charging level is set to zero.",
            "title": "EV Smart Charging",
        },
    )
    real_coordinator.update_configuration.assert_awaited()
    assert real_coordinator.switch_low_price_charging is True


@pytest.mark.asyncio
async def test_switch_low_price_charging_update_no_notification_when_level_nonzero(
    monkeypatch,
):
    """Test notification is not sent when low_price_charging is not 0."""
    module = sys.modules["custom_components.ev_smart_charging.coordinator"]
    monkeypatch.setattr(module, "_LOGGER", MagicMock())

    real_coordinator = EVSmartChargingCoordinator.__new__(EVSmartChargingCoordinator)
    real_coordinator.switch_low_price_charging = False
    real_coordinator.low_price_charging = 5
    real_coordinator.hass = MagicMock()
    real_coordinator.hass.services.async_call = AsyncMock()
    real_coordinator.update_configuration = AsyncMock()

    await real_coordinator.switch_low_price_charging_update(True)

    # Should not call any service except update_configuration
    real_coordinator.hass.services.async_call.assert_not_called()
    real_coordinator.update_configuration.assert_awaited()
    assert real_coordinator.switch_low_price_charging is True


@pytest.mark.asyncio
async def test_switch_low_price_charging_update_off(monkeypatch):
    """Test turning off the switch does not send notification."""
    module = sys.modules["custom_components.ev_smart_charging.coordinator"]
    monkeypatch.setattr(module, "_LOGGER", MagicMock())

    real_coordinator = EVSmartChargingCoordinator.__new__(EVSmartChargingCoordinator)
    real_coordinator.switch_low_price_charging = True
    real_coordinator.low_price_charging = 0
    real_coordinator.hass = MagicMock()
    real_coordinator.hass.services.async_call = AsyncMock()
    real_coordinator.update_configuration = AsyncMock()

    await real_coordinator.switch_low_price_charging_update(False)

    # Should not call any service except update_configuration
    real_coordinator.hass.services.async_call.assert_not_called()
    real_coordinator.update_configuration.assert_awaited()
    assert real_coordinator.switch_low_price_charging is False


@pytest.mark.asyncio
async def test_switch_low_soc_charging_update_notification_sent(monkeypatch):
    """Test notification is sent when low_soc_charging is 0 and switch is turned on."""
    module = sys.modules["custom_components.ev_smart_charging.coordinator"]
    monkeypatch.setattr(module, "_LOGGER", MagicMock())

    real_coordinator = EVSmartChargingCoordinator.__new__(EVSmartChargingCoordinator)
    real_coordinator.switch_low_soc_charging = False
    real_coordinator.low_soc_charging = 0
    real_coordinator.hass = MagicMock()
    real_coordinator.hass.services.async_call = AsyncMock()
    real_coordinator.update_configuration = AsyncMock()

    await real_coordinator.switch_low_soc_charging_update(True)

    real_coordinator.hass.services.async_call.assert_any_call(
        "persistent_notification",
        "create",
        {
            "message": "Low SOC charging is turn on, "
            "but the low SOC charging level is set to zero.",
            "title": "EV Smart Charging",
        },
    )
    real_coordinator.update_configuration.assert_awaited()
    assert real_coordinator.switch_low_soc_charging is True


@pytest.mark.asyncio
async def test_switch_low_soc_charging_update_no_notification(monkeypatch):
    """Test notification is not sent when low_soc_charging is not 0 or switch is turned off."""
    module = sys.modules["custom_components.ev_smart_charging.coordinator"]
    monkeypatch.setattr(module, "_LOGGER", MagicMock())

    real_coordinator = EVSmartChargingCoordinator.__new__(EVSmartChargingCoordinator)
    real_coordinator.switch_low_soc_charging = False
    real_coordinator.low_soc_charging = 10
    real_coordinator.hass = MagicMock()
    real_coordinator.hass.services.async_call = AsyncMock()
    real_coordinator.update_configuration = AsyncMock()

    await real_coordinator.switch_low_soc_charging_update(True)
    real_coordinator.hass.services.async_call.assert_not_called()
    real_coordinator.update_configuration.assert_awaited()
    assert real_coordinator.switch_low_soc_charging is True

    # Now test with state=False and low_soc_charging=0
    real_coordinator.low_soc_charging = 0
    real_coordinator.hass.services.async_call.reset_mock()
    real_coordinator.update_configuration.reset_mock()
    await real_coordinator.switch_low_soc_charging_update(False)
    real_coordinator.hass.services.async_call.assert_not_called()
    real_coordinator.update_configuration.assert_awaited()
    assert real_coordinator.switch_low_soc_charging is False
