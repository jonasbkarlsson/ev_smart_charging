"""Test ev_smart_charging coordinator with calculated SOC."""

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache_with_extra_data,
)

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, State
from homeassistant.const import STATE_OFF, STATE_ON, MAJOR_VERSION, MINOR_VERSION
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.ev_smart_charging import async_setup_entry, async_unload_entry
from custom_components.ev_smart_charging.const import DOMAIN

from tests.helpers.helpers import (
    MockChargerEntity,
    MockPriceEntity,
    MockSOCEntity,
    MockTargetSOCEntity,
)
from tests.price import PRICE_20220930
from tests.const import MOCK_CONFIG_ALL, MOCK_CONFIG_CALCULATED_SOC

CHARGING_STATE = "binary_sensor.ocpp_charging_state"
LAST_REPORTED = "sensor.volkswagen_we_connect_id_last_reported"
CALCULATED_SOC = "sensor.ev_smart_charging_calculated_soc"


async def setup_coordinator(hass: HomeAssistant, config: dict):
    """Set up the integration and return the coordinator."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=config, entry_id="test")
    if MAJOR_VERSION > 2024 or (MAJOR_VERSION == 2024 and MINOR_VERSION >= 7):
        config_entry.mock_state(hass=hass, state=ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)
    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()
    return config_entry, hass.data[DOMAIN][config_entry.entry_id]


# pylint: disable=unused-argument
async def test_coordinator_calculated_soc(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test the calculated SOC."""

    freezer.move_to("2022-09-30T10:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockPriceEntity.set_state(hass, PRICE_20220930, None)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)
    hass.states.async_set(CHARGING_STATE, STATE_OFF)
    # A timestamp without time zone is in local time
    hass.states.async_set(LAST_REPORTED, "2022-09-30T09:30:00")

    config_entry, coordinator = await setup_coordinator(
        hass, MOCK_CONFIG_CALCULATED_SOC
    )
    assert coordinator.ev_soc == 40.0
    state = hass.states.get(CALCULATED_SOC)
    assert state.state == "40.0"
    assert state.attributes["reported_at"] == "2022-09-30T09:30:00+02:00"

    # Charge for one hour at 6 %/h
    hass.states.async_set(CHARGING_STATE, STATE_ON)
    await hass.async_block_till_done()
    freezer.move_to("2022-09-30T11:00:00+02:00")
    await coordinator.update_calculated_soc()
    await hass.async_block_till_done()
    assert coordinator.ev_soc == 46.0
    state = hass.states.get(CALCULATED_SOC)
    assert state.state == "46.0"
    assert state.attributes["reported_soc"] == 40.0
    assert state.attributes["charging_hours"] == 1.0
    assert coordinator.sensor.ev_soc == 46.0

    # The EV reports at 10:30, which includes 30 minutes of charging
    MockSOCEntity.set_state(hass, "43")
    hass.states.async_set(LAST_REPORTED, "2022-09-30T10:30:00+02:00")
    await hass.async_block_till_done()
    assert coordinator.ev_soc == 46.0

    # Charging stops. The SOC is not changed while not charging.
    hass.states.async_set(CHARGING_STATE, STATE_OFF)
    await hass.async_block_till_done()
    freezer.move_to("2022-09-30T12:00:00+02:00")
    await coordinator.update_calculated_soc()
    await coordinator.update_sensors()
    await hass.async_block_till_done()
    assert coordinator.ev_soc == 46.0

    # Capped at the Target SOC
    MockTargetSOCEntity.set_state(hass, "45")
    await hass.async_block_till_done()
    assert coordinator.ev_soc == 45.0

    assert await async_unload_entry(hass, config_entry)
    await hass.async_block_till_done()


async def test_coordinator_calculated_soc_restore(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test that charging before a restart is kept."""

    freezer.move_to("2022-09-30T10:00:00+02:00")
    mock_restore_cache_with_extra_data(
        hass,
        [
            (
                State(CALCULATED_SOC, "43.0"),
                {
                    "reported_soc": 40.0,
                    "reported_at": "2022-09-30T09:00:00+02:00",
                    "charging_periods": [["2022-09-30T09:00:00+02:00", None]],
                    "saved_at": "2022-09-30T09:30:00+02:00",
                },
            )
        ],
    )

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockPriceEntity.set_state(hass, PRICE_20220930, None)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)
    hass.states.async_set(CHARGING_STATE, STATE_OFF)
    hass.states.async_set(LAST_REPORTED, "2022-09-30T09:00:00+02:00")

    config_entry, coordinator = await setup_coordinator(
        hass, MOCK_CONFIG_CALCULATED_SOC
    )
    # 30 minutes of charging at 6 %/h before the restart
    assert coordinator.ev_soc == 43.0
    assert hass.states.get(CALCULATED_SOC).state == "43.0"

    # The state to be stored
    sensor = coordinator.sensor_calculated_soc
    stored = sensor.extra_restore_state_data.as_dict()
    assert stored["reported_soc"] == 40.0
    assert stored["saved_at"] == "2022-09-30T10:00:00+02:00"

    # Restore when the coordinator is already set up
    await sensor.async_added_to_hass()
    await hass.async_block_till_done()
    assert coordinator.ev_soc == 43.0

    assert await async_unload_entry(hass, config_entry)
    await hass.async_block_till_done()


async def test_coordinator_calculated_soc_own_charging_state(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test the calculated SOC using the integration's own charging state."""

    freezer.move_to("2022-09-30T10:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockPriceEntity.set_state(hass, PRICE_20220930, None)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)
    hass.states.async_set(LAST_REPORTED, "invalid")

    config = MOCK_CONFIG_CALCULATED_SOC | {"charging_state_entity": ""}
    config_entry, coordinator = await setup_coordinator(hass, config)
    assert coordinator.ev_soc == 40.0

    await coordinator.turn_on_charging()
    freezer.move_to("2022-09-30T10:30:00+02:00")
    await coordinator.update_calculated_soc()
    await hass.async_block_till_done()
    assert coordinator.ev_soc == 43.0

    await coordinator.turn_off_charging()
    freezer.move_to("2022-09-30T11:00:00+02:00")
    await coordinator.update_sensors()
    assert coordinator.ev_soc == 43.0

    # A timestamp that cannot be parsed is ignored
    hass.states.async_set(LAST_REPORTED, "2022-13-45T10:00:00")
    await hass.async_block_till_done()
    assert coordinator.ev_soc == 43.0

    assert await async_unload_entry(hass, config_entry)
    await hass.async_block_till_done()


async def test_coordinator_no_calculated_soc(
    hass: HomeAssistant, skip_service_calls, set_cet_timezone, freezer
):
    """Test that the calculated SOC is not used without a timestamp entity."""

    freezer.move_to("2022-09-30T10:00:00+02:00")

    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    MockSOCEntity.create(hass, entity_registry, "40")
    MockTargetSOCEntity.create(hass, entity_registry, "80")
    MockPriceEntity.create(hass, entity_registry, 123)
    MockPriceEntity.set_state(hass, PRICE_20220930, None)
    MockChargerEntity.create(hass, entity_registry, STATE_OFF)

    config_entry, coordinator = await setup_coordinator(hass, MOCK_CONFIG_ALL)
    assert coordinator.soc_estimator is None
    assert hass.states.get(CALCULATED_SOC) is None

    await coordinator.turn_on_charging()
    freezer.move_to("2022-09-30T11:00:00+02:00")
    await coordinator.update_sensors()
    assert coordinator.ev_soc == 40.0

    assert await async_unload_entry(hass, config_entry)
    await hass.async_block_till_done()
