"""Test ev_smart_charging coordinator."""

from datetime import datetime
import asyncio
from pytest_homeassistant_custom_component.common import MockConfigEntry
from freezegun import freeze_time

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF, MAJOR_VERSION, MINOR_VERSION
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.util import dt as dt_util

from custom_components.ev_smart_charging import async_setup_entry
from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.const import (
    DOMAIN,
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
@freeze_time("2022-09-30T05:59:50+02:00", tick=True)
async def test_coordinator_reschedule(
    hass: HomeAssistant,
    skip_service_calls,
    set_cet_timezone,
    freezer,
    skip_update_quarterly,
):
    """Test Coordinator reschedule."""

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "79")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)
    MockPriceEntity.set_state(hass, PRICE_20220930, PRICE_20221001)
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
    assert coordinator is not None
    coordinator.ready_quarter_local = 8 * 4
    await hass.async_block_till_done()
    await coordinator.switch_active_update(True)
    await coordinator.switch_active_price_charging_update(True)
    await coordinator.switch_apply_limit_update(False)
    await coordinator.switch_continuous_update(True)
    await coordinator.switch_ev_connected_update(True)
    await coordinator.switch_keep_on_update(False)
    await hass.async_block_till_done()

    # Schedule 05:45-06:00
    await coordinator.update_configuration()
    await asyncio.sleep(5)
    assert coordinator.sensor.state == STATE_ON
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 9, 30, 5, 45, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 9, 30, 6, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_quarters == 1

    # Schedule 06:00-06:15
    await asyncio.sleep(5)
    await coordinator.update_sensors()
    await asyncio.sleep(5)
    assert coordinator.sensor.state == STATE_ON
    assert coordinator.sensor.charging_is_planned is True
    assert coordinator.sensor.charging_start_time == datetime(
        2022, 9, 30, 6, 0, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_stop_time == datetime(
        2022, 9, 30, 6, 15, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
    )
    assert coordinator.sensor.charging_number_of_quarters == 1

    # No schedule
    MockSOCEntity.set_state(hass, "80")
    await coordinator.update_sensors()
    await asyncio.sleep(5)
    assert coordinator.sensor.state == STATE_OFF
    assert coordinator.sensor.charging_is_planned is False

    await asyncio.sleep(2)

    # Unsubscribe to listeners
    coordinator.unsubscribe_listeners()
