"""Test ev_smart_charging coordinator."""
from datetime import datetime
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_OFF
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.util import dt as dt_util

from custom_components.ev_smart_charging.coordinator import (
    EVSmartChargingCoordinator,
)
from custom_components.ev_smart_charging.const import DOMAIN
from custom_components.ev_smart_charging.helpers.coordinator import Raw
from custom_components.ev_smart_charging.sensor import EVSmartChargingSensorCharging

from tests.helpers.helpers import (
    MockChargerEntity,
    MockPriceEntity,
    MockSOCEntity,
    MockTargetSOCEntity,
)
from tests.price_daylight_saving import (
    PRICE_20220326,
    PRICE_20220327,
    PRICE_20220328,
    PRICE_20221029,
    PRICE_20221030,
    PRICE_20221031,
)
from .const import MOCK_CONFIG_ALL


# pylint: disable=unused-argument
async def test_to_daylight_saving_time(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator when going to daylight saving time"""

    freezer.move_to("2022-03-26T14:00:00+01:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "11")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 10)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator

    sensor: EVSmartChargingSensorCharging = EVSmartChargingSensorCharging(config_entry)
    assert sensor is not None
    await coordinator.add_sensor([sensor])
    await coordinator.switch_active_update(True)
    await coordinator.switch_apply_limit_update(True)
    await coordinator.switch_continuous_update(True)

    # Provide price
    MockPriceEntity.set_state(hass, PRICE_20220326, PRICE_20220327)

    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid

    # This should give 12 hours of charging
    # From UTC 2022-03-26 16:00 (17:00 CET)
    # To UTC 2022-03-27 04:00 (06:00 CEST)

    # pylint: disable=protected-access
    raw_schedule: Raw = Raw(coordinator._charging_schedule)
    assert raw_schedule.number_of_nonzero() == 12
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 3, 26, 16, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        == 0
    )
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 3, 26, 17, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        != 0
    )
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 3, 27, 5, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        != 0
    )
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 3, 27, 6, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        == 0
    )

    freezer.move_to("2022-03-27T14:00:00+02:00")

    # Provide price
    MockPriceEntity.set_state(hass, PRICE_20220327, PRICE_20220328)

    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid

    # This should give 12 hours of charging
    # From UTC 2022-03-27 16:00 (18:00 CET)
    # To UTC 2022-03-28 04:00 (06:00 CEST)

    # pylint: disable=protected-access
    raw_schedule: Raw = Raw(coordinator._charging_schedule)
    assert raw_schedule.number_of_nonzero() == 12
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 3, 27, 17, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        == 0
    )
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 3, 27, 18, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        != 0
    )
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 3, 28, 5, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        != 0
    )
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 3, 28, 6, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        == 0
    )


async def test_from_daylight_saving_time(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test Coordinator when going to daylight saving time"""

    freezer.move_to("2022-10-29T14:00:00+02:00")  # Daylight saving time

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "11")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 10)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    coordinator = EVSmartChargingCoordinator(hass, config_entry)
    assert coordinator

    sensor: EVSmartChargingSensorCharging = EVSmartChargingSensorCharging(config_entry)
    assert sensor is not None
    await coordinator.add_sensor([sensor])
    await coordinator.switch_active_update(True)
    await coordinator.switch_apply_limit_update(True)
    await coordinator.switch_continuous_update(True)

    # Provide price
    MockPriceEntity.set_state(hass, PRICE_20221029, PRICE_20221030)

    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid

    # This should give 12 hours of charging
    # From UTC 2022-10-29 17:00 (19:00 CEST)
    # To UTC 2022-10-30 05:00 (06:00 CET)

    # pylint: disable=protected-access
    raw_schedule: Raw = Raw(coordinator._charging_schedule)
    assert raw_schedule.number_of_nonzero() == 12
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 10, 29, 18, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        == 0
    )
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 10, 29, 19, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        != 0
    )
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 10, 30, 5, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        != 0
    )
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 10, 30, 6, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        == 0
    )

    freezer.move_to("2022-10-30T14:00:00+01:00")  # Normal time

    # Provide price
    MockPriceEntity.set_state(hass, PRICE_20221030, PRICE_20221031)

    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.tomorrow_valid

    # This should give 12 hours of charging
    # From UTC 2022-10-30 17:00 (18:00 CET)
    # To UTC 2022-10-31 05:00 (06:00 CEST)

    # pylint: disable=protected-access
    raw_schedule: Raw = Raw(coordinator._charging_schedule)
    assert raw_schedule.number_of_nonzero() == 12
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 10, 30, 17, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        == 0
    )
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 10, 30, 18, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        != 0
    )
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 10, 31, 5, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        != 0
    )
    assert (
        raw_schedule.get_value(
            datetime(
                2022, 10, 31, 6, 30, tzinfo=dt_util.get_time_zone("Europe/Stockholm")
            )
        )
        == 0
    )
