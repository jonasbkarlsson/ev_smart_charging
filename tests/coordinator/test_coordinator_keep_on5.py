"""Test that Keep charger on respects Smart charging activated."""

from unittest.mock import MagicMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF, MAJOR_VERSION, MINOR_VERSION
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.ev_smart_charging import async_setup_entry
from custom_components.ev_smart_charging.const import (
    CHARGING_STATUS_NOT_ACTIVE,
    DOMAIN,
)
from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.helpers.coordinator import (
    get_charging_value,
)

from tests.helpers.helpers import (
    MockChargerEntity,
    MockPriceEntity,
    MockSOCEntity,
    MockTargetSOCEntity,
)
from tests.price import PRICE_20220930, PRICE_20221001, PRICE_20221002
from tests.const import (
    MOCK_CONFIG_KEEP_ON1,
)


def charger_turned_on(mock_async_call: MagicMock) -> bool:
    """Check if switch.turn_on was called for the charger."""
    for call in mock_async_call.call_args_list:
        if (
            call.kwargs.get("domain") == "switch"
            and call.kwargs.get("service") == "turn_on"
            and call.kwargs.get("target") == {"entity_id": "switch.ocpp_charge_control"}
        ):
            return True
    return False


async def setup_keep_on(hass: HomeAssistant) -> EVSmartChargingCoordinator:
    """Set up the integration with Keep charger on and an EV connected."""

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "38")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_KEEP_ON1, entry_id="test"
    )
    if MAJOR_VERSION > 2024 or (MAJOR_VERSION == 2024 and MINOR_VERSION >= 7):
        config_entry.mock_state(hass=hass, state=ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)
    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    assert isinstance(coordinator, EVSmartChargingCoordinator)

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

    return coordinator


# pylint: disable=unused-argument
async def test_keep_on_after_completion_time_smart_charging_not_active(
    hass: HomeAssistant, set_cet_timezone, freezer
):
    """Keep charger on must not turn on charging after the completion time
    if smart charging has been deactivated during the charging session."""

    freezer.move_to("2022-09-30T14:00:00+02:00")
    with patch("homeassistant.core.ServiceRegistry.async_call") as mock_async_call:
        coordinator = await setup_keep_on(hass)

        # Charging starts according to schedule, 02:00-09:00
        freezer.move_to("2022-10-01T02:00:00+02:00")
        MockPriceEntity.set_state(hass, PRICE_20221001, None)
        await coordinator.update_sensors()
        await hass.async_block_till_done()
        assert coordinator.auto_charging_state == STATE_ON
        assert coordinator.switch_keep_on_completion_time is not None

        # Deactivate smart charging during the charging session
        freezer.move_to("2022-10-01T03:00:00+02:00")
        await coordinator.switch_active_update(False)
        await hass.async_block_till_done()
        assert coordinator.auto_charging_state == STATE_OFF

        # Move time to after the completion time
        mock_async_call.reset_mock()
        freezer.move_to("2022-10-01T09:15:00+02:00")
        await coordinator.update_sensors()
        await hass.async_block_till_done()
        assert coordinator.auto_charging_state == STATE_OFF
        assert coordinator.sensor.state == STATE_OFF
        assert coordinator.sensor_status.native_value == CHARGING_STATUS_NOT_ACTIVE
        assert not charger_turned_on(mock_async_call)

        coordinator.unsubscribe_listeners()


async def test_keep_on_target_soc_reached_smart_charging_not_active(
    hass: HomeAssistant, set_cet_timezone, freezer
):
    """Keep charger on must not turn on charging when the target SOC is reached
    if smart charging is not active."""

    freezer.move_to("2022-09-30T14:00:00+02:00")
    with patch("homeassistant.core.ServiceRegistry.async_call") as mock_async_call:
        coordinator = await setup_keep_on(hass)

        await coordinator.switch_active_update(False)
        await hass.async_block_till_done()
        assert coordinator.auto_charging_state == STATE_OFF

        # SOC reaches target SOC
        mock_async_call.reset_mock()
        freezer.move_to("2022-09-30T15:00:00+02:00")
        MockSOCEntity.set_state(hass, "80")
        await coordinator.update_sensors()
        await hass.async_block_till_done()
        assert coordinator.auto_charging_state == STATE_OFF
        assert coordinator.sensor.state == STATE_OFF
        assert coordinator.sensor_status.native_value == CHARGING_STATUS_NOT_ACTIVE
        assert not charger_turned_on(mock_async_call)

        coordinator.unsubscribe_listeners()


async def test_keep_on_completion_time_from_previous_day_smart_charging_not_active(
    hass: HomeAssistant, set_cet_timezone, freezer
):
    """Keep charger on must not turn on charging due to a completion time left
    from the previous day's charging session if smart charging is not active.
    The EV stays connected, so the completion time is not reset."""

    freezer.move_to("2022-09-30T14:00:00+02:00")
    with patch("homeassistant.core.ServiceRegistry.async_call") as mock_async_call:
        coordinator = await setup_keep_on(hass)

        # Charging starts according to schedule, 02:00-09:00
        freezer.move_to("2022-10-01T02:00:00+02:00")
        MockPriceEntity.set_state(hass, PRICE_20221001, None)
        await coordinator.update_sensors()
        await hass.async_block_till_done()
        assert coordinator.auto_charging_state == STATE_ON

        # Target SOC reached, and Keep charger on is turned off
        freezer.move_to("2022-10-01T08:00:00+02:00")
        MockSOCEntity.set_state(hass, "80")
        await coordinator.update_sensors()
        await coordinator.switch_keep_on_update(False)
        await hass.async_block_till_done()
        assert coordinator.auto_charging_state == STATE_OFF

        # Next day, after the ready time and without prices for tomorrow.
        # The SOC has dropped and smart charging is deactivated.
        freezer.move_to("2022-10-02T18:00:00+02:00")
        MockPriceEntity.set_state(hass, PRICE_20221002, None)
        MockSOCEntity.set_state(hass, "70")
        await coordinator.update_sensors()
        await coordinator.switch_active_update(False)
        await hass.async_block_till_done()
        assert coordinator.auto_charging_state == STATE_OFF
        assert not coordinator.tomorrow_valid
        assert not get_charging_value(coordinator._charging_schedule)
        assert coordinator.switch_keep_on_completion_time is not None
        assert (
            coordinator.switch_keep_on_completion_time.date().isoformat()
            == "2022-10-01"
        )

        # Keep charger on is turned on again
        mock_async_call.reset_mock()
        freezer.move_to("2022-10-02T18:15:00+02:00")
        await coordinator.switch_keep_on_update(True)
        await hass.async_block_till_done()
        assert coordinator.auto_charging_state == STATE_OFF
        assert coordinator.sensor.state == STATE_OFF
        assert coordinator.sensor_status.native_value == CHARGING_STATUS_NOT_ACTIVE
        assert not charger_turned_on(mock_async_call)

        coordinator.unsubscribe_listeners()
