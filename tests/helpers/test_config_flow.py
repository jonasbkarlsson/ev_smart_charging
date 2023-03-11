"""Test ev_smart_charging/helpers/config_flow.py"""

from copy import deepcopy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import async_get as async_device_registry_get
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ev_smart_charging.helpers.config_flow import (
    DeviceNameCreator,
    FindEntity,
    FlowValidator,
)
from custom_components.ev_smart_charging.const import (
    BUTTON,
    DOMAIN,
    NAME,
    PLATFORM_NORDPOOL,
    PLATFORM_OCPP,
    PLATFORM_VW,
    SENSOR,
    SWITCH,
)

from tests.const import (
    MOCK_CONFIG_ALL,
    MOCK_CONFIG_USER_NO_CHARGER,
    MOCK_CONFIG_USER,
    MOCK_CONFIG_USER_WRONG_CHARGER,
    MOCK_CONFIG_USER_WRONG_PRICE,
)
from tests.helpers.helpers import (
    MockChargerEntity,
    MockPriceEntity,
    MockPriceEntityEnergiDataService,
    MockPriceEntityEntsoe,
    MockSOCEntity,
    MockTargetSOCEntity,
)


async def test_validate_step_user_price(hass: HomeAssistant):
    """Test the price entity in test_validate_step_user."""

    entity_registry: EntityRegistry = async_entity_registry_get(hass)

    # Check with no price entity
    assert FlowValidator.validate_step_user(hass, MOCK_CONFIG_USER) == (
        "base",
        "price_not_found",
    )

    # Check with wrong domain
    entity_registry.async_get_or_create(
        domain=BUTTON,
        platform=PLATFORM_NORDPOOL,
        unique_id="kwh_se3_sek_2_10_0",
    )
    assert entity_registry.async_is_registered("button.nordpool_kwh_se3_sek_2_10_0")
    hass.states.async_set("button.nordpool_kwh_se3_sek_2_10_0", "123")
    assert FlowValidator.validate_step_user(hass, MOCK_CONFIG_USER_WRONG_PRICE) == (
        "base",
        "price_not_sensor",
    )

    # Check with price entity without attributes
    entity_registry.async_get_or_create(
        domain=SENSOR,
        platform=PLATFORM_NORDPOOL,
        unique_id="kwh_se3_sek_2_10_0",
    )
    assert entity_registry.async_is_registered("sensor.nordpool_kwh_se3_sek_2_10_0")
    hass.states.async_set("sensor.nordpool_kwh_se3_sek_2_10_0", "123")
    assert FlowValidator.validate_step_user(hass, MOCK_CONFIG_USER) == (
        "base",
        "sensor_is_not_price",
    )

    # Check with price entity with current_price
    hass.states.async_set(
        "sensor.nordpool_kwh_se3_sek_2_10_0", "123", {"current_price": 123}
    )
    assert FlowValidator.validate_step_user(hass, MOCK_CONFIG_USER) == (
        "base",
        "sensor_is_not_price",
    )

    # Check with price entity with current_price and raw_today
    hass.states.async_set(
        "sensor.nordpool_kwh_se3_sek_2_10_0",
        "123",
        {"current_price": 123, "raw_today": None},
    )
    assert FlowValidator.validate_step_user(hass, MOCK_CONFIG_USER) == (
        "base",
        "sensor_is_not_price",
    )

    # Check with price entity with current_price, raw_today and raw_tomorrow
    hass.states.async_set(
        "sensor.nordpool_kwh_se3_sek_2_10_0",
        "123",
        {"current_price": 123, "raw_today": None, "raw_tomorrow": None},
    )
    assert FlowValidator.validate_step_user(hass, MOCK_CONFIG_USER) == (
        "base",
        "ev_soc_not_found",
    )


async def test_validate_step_user_soc(hass: HomeAssistant):
    """Test the soc entities in test_validate_step_user."""

    entity_registry: EntityRegistry = async_entity_registry_get(hass)

    # First create a price entity
    MockPriceEntity.create(hass, entity_registry)

    # Check with no soc entity
    assert FlowValidator.validate_step_user(hass, MOCK_CONFIG_USER) == (
        "base",
        "ev_soc_not_found",
    )

    # Check with non-float soc entity
    entity_registry.async_get_or_create(
        domain=SENSOR,
        platform=PLATFORM_VW,
        unique_id="state_of_charge",
    )
    assert entity_registry.async_is_registered(
        "sensor.volkswagen_we_connect_id_state_of_charge"
    )
    hass.states.async_set(
        "sensor.volkswagen_we_connect_id_state_of_charge",
        "abc",
    )
    assert FlowValidator.validate_step_user(hass, MOCK_CONFIG_USER) == (
        "base",
        "ev_soc_invalid_data",
    )

    # Check with out-of-range float soc entity
    hass.states.async_set(
        "sensor.volkswagen_we_connect_id_state_of_charge",
        "100.1",
    )
    assert FlowValidator.validate_step_user(hass, MOCK_CONFIG_USER) == (
        "base",
        "ev_soc_invalid_data",
    )

    # Check with out-of-range float soc entity
    hass.states.async_set(
        "sensor.volkswagen_we_connect_id_state_of_charge",
        "-0.1",
    )
    assert FlowValidator.validate_step_user(hass, MOCK_CONFIG_USER) == (
        "base",
        "ev_soc_invalid_data",
    )

    # Check with correct soc entity
    hass.states.async_set(
        "sensor.volkswagen_we_connect_id_state_of_charge",
        "55",
    )
    assert FlowValidator.validate_step_user(hass, deepcopy(MOCK_CONFIG_USER)) == (
        "base",
        "ev_target_soc_not_found",
    )


async def test_validate_step_user_target_soc(hass: HomeAssistant):
    """Test the target soc entities in test_validate_step_user."""

    entity_registry: EntityRegistry = async_entity_registry_get(hass)

    # First create a price and soc entities
    MockPriceEntity.create(hass, entity_registry)
    MockSOCEntity.create(hass, entity_registry)

    # Check with no target soc entity
    assert FlowValidator.validate_step_user(hass, deepcopy(MOCK_CONFIG_USER)) == (
        "base",
        "ev_target_soc_not_found",
    )

    # Check with non-float target soc entity
    entity_registry.async_get_or_create(
        domain=SENSOR,
        platform=PLATFORM_VW,
        unique_id="target_state_of_charge",
    )
    assert entity_registry.async_is_registered(
        "sensor.volkswagen_we_connect_id_target_state_of_charge"
    )
    hass.states.async_set(
        "sensor.volkswagen_we_connect_id_target_state_of_charge",
        "abc",
    )
    assert FlowValidator.validate_step_user(hass, deepcopy(MOCK_CONFIG_USER)) == (
        "base",
        "ev_target_soc_invalid_data",
    )

    # Check with out-of-range float target soc entity
    hass.states.async_set(
        "sensor.volkswagen_we_connect_id_target_state_of_charge",
        "100.1",
    )
    assert FlowValidator.validate_step_user(hass, deepcopy(MOCK_CONFIG_USER)) == (
        "base",
        "ev_target_soc_invalid_data",
    )

    # Check with out-of-range float target soc entity
    hass.states.async_set(
        "sensor.volkswagen_we_connect_id_target_state_of_charge",
        "-0.1",
    )
    assert FlowValidator.validate_step_user(hass, deepcopy(MOCK_CONFIG_USER)) == (
        "base",
        "ev_target_soc_invalid_data",
    )

    # Check with correct target soc entity
    hass.states.async_set(
        "sensor.volkswagen_we_connect_id_target_state_of_charge",
        "55",
    )
    assert FlowValidator.validate_step_user(hass, deepcopy(MOCK_CONFIG_USER)) == (
        "base",
        "charger_control_switch_not_found",
    )


async def test_validate_step_user_charger(hass: HomeAssistant):
    """Test the charger entity in test_validate_step_user."""

    entity_registry: EntityRegistry = async_entity_registry_get(hass)

    # First create a price, soc and target soc entities
    MockPriceEntity.create(hass, entity_registry)
    MockSOCEntity.create(hass, entity_registry)
    MockTargetSOCEntity.create(hass, entity_registry)

    assert FlowValidator.validate_step_user(hass, MOCK_CONFIG_USER_NO_CHARGER) is None
    assert FlowValidator.validate_step_user(hass, deepcopy(MOCK_CONFIG_USER)) == (
        "base",
        "charger_control_switch_not_found",
    )

    # Check with wrong domain
    entity_registry.async_get_or_create(
        domain=BUTTON,
        platform=PLATFORM_OCPP,
        unique_id="charge_control",
    )
    assert entity_registry.async_is_registered("button.ocpp_charge_control")
    hass.states.async_set(
        "button.ocpp_charge_control",
        "55",
    )
    assert FlowValidator.validate_step_user(
        hass, deepcopy(MOCK_CONFIG_USER_WRONG_CHARGER)
    ) == (
        "base",
        "charger_control_switch_not_switch",
    )

    # Check with correct domain
    entity_registry.async_get_or_create(
        domain=SWITCH,
        platform=PLATFORM_OCPP,
        unique_id="charge_control",
    )
    assert entity_registry.async_is_registered("switch.ocpp_charge_control")
    hass.states.async_set(
        "switch.ocpp_charge_control",
        "55",
    )
    assert FlowValidator.validate_step_user(hass, MOCK_CONFIG_USER) is None


async def test_find_entity(hass: HomeAssistant):
    """Test the FindEntity."""

    entity_registry: EntityRegistry = async_entity_registry_get(hass)

    # First create a couple of entities
    assert FindEntity.find_price_sensor(hass) == ""

    assert FindEntity.find_entsoe_sensor(hass) == ""
    MockPriceEntityEntsoe.create(hass, entity_registry)
    assert FindEntity.find_price_sensor(hass).startswith("sensor.entsoe")

    assert FindEntity.find_energidataservice_sensor(hass) == ""
    MockPriceEntityEnergiDataService.create(hass, entity_registry)
    assert FindEntity.find_price_sensor(hass).startswith("sensor.energidataservice")

    assert FindEntity.find_nordpool_sensor(hass) == ""
    MockPriceEntity.create(hass, entity_registry)
    assert FindEntity.find_price_sensor(hass).startswith("sensor.nordpool")

    assert FindEntity.find_vw_soc_sensor(hass) == ""
    MockSOCEntity.create(hass, entity_registry)
    assert FindEntity.find_vw_target_soc_sensor(hass) == ""
    MockTargetSOCEntity.create(hass, entity_registry)
    assert FindEntity.find_ocpp_device(hass) == ""
    MockChargerEntity.create(hass, entity_registry)

    # Now test and confirm that all can be found
    assert FindEntity.find_nordpool_sensor(hass) != ""
    assert FindEntity.find_energidataservice_sensor(hass) != ""
    assert FindEntity.find_entsoe_sensor(hass) != ""
    assert FindEntity.find_vw_soc_sensor(hass) != ""
    assert FindEntity.find_vw_target_soc_sensor(hass) != ""
    assert FindEntity.find_ocpp_device(hass) != ""


async def test_device_name_creator(hass: HomeAssistant):
    """Test the FindEntity."""

    device_registry: DeviceRegistry = async_device_registry_get(hass)
    names = []

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test")
    assert (name := DeviceNameCreator.create(hass)) == NAME
    names.append(name)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        name=name,
        identifiers={(DOMAIN, config_entry.entry_id)},
    )

    config_entry2 = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test2"
    )
    assert (name2 := DeviceNameCreator.create(hass)) not in names
    names.append(name2)
    device_registry.async_get_or_create(
        config_entry_id=config_entry2.entry_id,
        name=name2,
        identifiers={(DOMAIN, config_entry2.entry_id)},
    )

    assert (name3 := DeviceNameCreator.create(hass)) not in names

    # Use incorrect device name to provoke ValueError
    name3 = f"{NAME} abc"
    config_entry3 = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test3"
    )
    device_registry.async_get_or_create(
        config_entry_id=config_entry3.entry_id,
        name=name3,
        identifiers={(DOMAIN, config_entry3.entry_id)},
    )
    assert (name4 := DeviceNameCreator.create(hass)) not in names
    assert NAME in name4
