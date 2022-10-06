"""Test ev_smart_charging coordinator."""
from datetime import datetime
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.util import dt as dt_util

from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.const import DOMAIN
from custom_components.ev_smart_charging.helpers.coordinator import Raw
from custom_components.ev_smart_charging.sensor import EVSmartChargingSensor

from tests.helpers.helpers import (
    MockChargerEntity,
    MockPriceEntity,
    MockSOCEntity,
    MockTargetSOCEntity,
)
from tests.price import PRICE_20220326, PRICE_20220327, PRICE_20221001
from .const import MOCK_CONFIG_ALL

# pylint: disable=unused-argument
async def test_to_daylight_saving_time(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator when going to daylight saving time"""

    freezer.move_to("2022-03-26T14:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "11")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 10)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator

    sensor: EVSmartChargingSensor = EVSmartChargingSensor(config_entry)
    assert sensor is not None
    await coordinator.add_sensor(sensor)
    await coordinator.switch_active_update(True)
    await coordinator.switch_apply_limit_update(True)

    # Provide price
    MockPriceEntity.set_state(hass, PRICE_20220326, PRICE_20220327)

    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid

    # pylint: disable=protected-access
    raw_schedule: Raw = Raw(coordinator._charging_schedule)
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 3, 27, 3, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        != 0
    )
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 3, 27, 4, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        == 0
    )
    assert raw_schedule.number_of_nonzero() == 12

    return

    # Move time to just before scheduled charging time
    freezer.move_to("2022-10-01T02:50:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF

    # Move time to scheduled charging time
    freezer.move_to("2022-10-01T03:00:00+02:00")
    MockPriceEntity.set_state(hass, PRICE_20221001, None)
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_ON
    assert coordinator.sensor.state == STATE_ON

    # Min SOC reached
    MockSOCEntity.set_state(hass, "40")
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.auto_charging_state == STATE_OFF
    assert coordinator.sensor.state == STATE_OFF
