"""Test ev_smart_charging/helpers/general.py"""

from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.core import State

from custom_components.ev_smart_charging.const import (
    CONF_MIN_SOC,
    CONF_PCT_PER_HOUR,
    CONF_READY_QUARTER,
)
from custom_components.ev_smart_charging.helpers.general import (
    Validator,
    get_parameter,
    get_quarter_index,
)

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
    assert get_parameter(config_entry, CONF_READY_QUARTER) is None
    assert get_parameter(config_entry, CONF_READY_QUARTER, 12) == 12


async def test_get_quarter_index(hass):
    """Test get_quarter_index"""

    assert get_quarter_index("None") is None
    assert get_quarter_index("00:00") is 0
    assert get_quarter_index("00:15") is 1
    assert get_quarter_index("23:45") is 95
    assert get_quarter_index("12:34") is None
