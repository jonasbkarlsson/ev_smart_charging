"""Test ev_smart_charging/helpers/general.py"""


from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.ev_smart_charging.const import (
    CONF_MIN_SOC,
    CONF_PCT_PER_HOUR,
    CONF_READY_HOUR,
    PLATFORM_ENERGIDATASERVICE,
    PLATFORM_NORDPOOL,
)
from custom_components.ev_smart_charging.helpers.config_flow import FindEntity
from custom_components.ev_smart_charging.helpers.general import (
    Validator,
    get_parameter,
    get_platform,
)
from tests.helpers.helpers import MockPriceEntity, MockPriceEntityEnergiDataService

from .const import MOCK_CONFIG_DATA, MOCK_CONFIG_OPTIONS

# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
# side of the assertion matches with the right side.


# pylint: disable=unused-argument
async def test_is_float(hass):
    """Test is_float"""

    assert isinstance(Validator.is_float("0"), bool)
    assert Validator.is_float("0") is True
    assert Validator.is_float("56.4") is True
    assert Validator.is_float("-34.3") is True
    assert Validator.is_float("a") is False
    assert Validator.is_float(None) is False
    assert Validator.is_float("") is False


async def test_is_soc_state(hass):
    """Test is_soc_state"""

    assert Validator.is_soc_state(None) is False
    soc_state = State(entity_id="sensor.test", state="unavailable")
    assert Validator.is_soc_state(soc_state) is False
    soc_state = State(entity_id="sensor.test", state="")
    assert Validator.is_soc_state(soc_state) is False
    soc_state = State(entity_id="sensor.test", state="0.0")
    assert Validator.is_soc_state(soc_state) is True
    soc_state = State(entity_id="sensor.test", state="100.0")
    assert Validator.is_soc_state(soc_state) is True
    soc_state = State(entity_id="sensor.test", state="-0.1")
    assert Validator.is_soc_state(soc_state) is False
    soc_state = State(entity_id="sensor.test", state="100.1")
    assert Validator.is_soc_state(soc_state) is False


async def test_get_parameter(hass):
    """Test get_parameter"""

    config_entry = MockConfigEntry(data=MOCK_CONFIG_DATA, options=MOCK_CONFIG_OPTIONS)
    config_entry.add_to_hass(hass)
    assert get_parameter(config_entry, CONF_PCT_PER_HOUR) == 8.0
    assert get_parameter(config_entry, CONF_MIN_SOC) == 30.0
    assert get_parameter(config_entry, CONF_READY_HOUR) is None
    assert get_parameter(config_entry, CONF_READY_HOUR, 12) == 12


async def test_get_platform(hass: HomeAssistant):
    """Test the get_platform."""

    entity_registry: EntityRegistry = async_entity_registry_get(hass)

    # First create a couple of entities
    MockPriceEntity.create(hass, entity_registry)
    MockPriceEntityEnergiDataService.create(hass, entity_registry)

    assert get_platform(hass, None) is None
    assert (
        get_platform(hass, FindEntity.find_nordpool_sensor(hass)) == PLATFORM_NORDPOOL
    )
    assert (
        get_platform(hass, FindEntity.find_energidataservice_sensor(hass))
        == PLATFORM_ENERGIDATASERVICE
    )
    assert get_platform(hass, "Non existant entity") is None
