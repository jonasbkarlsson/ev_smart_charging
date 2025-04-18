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
    get_platform,
)
from custom_components.ev_smart_charging.const import (
    BUTTON,
    DOMAIN,
    NAME,
    PLATFORM_ENERGIDATASERVICE,
    PLATFORM_GESPOT,
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
    MockPriceEntityGESpot,
    MockSOCEntity,
    MockTargetSOCEntity,
)


async def test_find_entity(hass: HomeAssistant):
    """Test the FindEntity."""

    entity_registry: EntityRegistry = async_entity_registry_get(hass)

    # First create a couple of entities
    assert FindEntity.find_nordpool_sensor(hass) == ""
    MockPriceEntity.create(hass, entity_registry)
    assert FindEntity.find_energidataservice_sensor(hass) == ""
    MockPriceEntityEnergiDataService.create(hass, entity_registry)
    assert FindEntity.find_gespot_sensor(hass) == ""
    MockPriceEntityGESpot.create(hass, entity_registry)
    assert FindEntity.find_vw_soc_sensor(hass) == ""
    MockSOCEntity.create(hass, entity_registry)
    assert FindEntity.find_vw_target_soc_sensor(hass) == ""
    MockTargetSOCEntity.create(hass, entity_registry)
    assert FindEntity.find_ocpp_device(hass) == ""
    MockChargerEntity.create(hass, entity_registry)

    # Now test and confirm that all can be found
    assert FindEntity.find_nordpool_sensor(hass) != ""
    assert FindEntity.find_energidataservice_sensor(hass) != ""
    assert FindEntity.find_gespot_sensor(hass) != ""
    assert FindEntity.find_vw_soc_sensor(hass) != ""
    assert FindEntity.find_vw_target_soc_sensor(hass) != ""
    assert FindEntity.find_ocpp_device(hass) != ""


async def test_get_platform(hass: HomeAssistant):
    """Test the get_platform."""

    entity_registry: EntityRegistry = async_entity_registry_get(hass)

    # First create a couple of entities
    MockPriceEntity.create(hass, entity_registry)
    MockPriceEntityEnergiDataService.create(hass, entity_registry)
    MockPriceEntityGESpot.create(hass, entity_registry)

    assert get_platform(hass, None) is None
    assert (
        get_platform(hass, FindEntity.find_nordpool_sensor(hass)) == PLATFORM_NORDPOOL
    )
    assert (
        get_platform(hass, FindEntity.find_energidataservice_sensor(hass))
        == PLATFORM_ENERGIDATASERVICE
    )
    assert (
        get_platform(hass, FindEntity.find_gespot_sensor(hass))
        == PLATFORM_GESPOT
    )
    assert get_platform(hass, "Non existant entity") is None
