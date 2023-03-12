"""Test ev_smart_charging config flow."""
from typing import Any, Dict
from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ev_smart_charging.const import DOMAIN

from .const import (
    MOCK_CONFIG_ALL,
    MOCK_CONFIG_CHARGER_EXTRA,
    MOCK_CONFIG_CHARGER_NEW,
    MOCK_CONFIG_USER,
)


# This fixture bypasses the actual setup of the integration
# since we only want to test the config flow. We test the
# actual functionality of the integration in other test modules.
@pytest.fixture(autouse=True)
def bypass_setup_fixture():
    """Prevent setup."""
    with patch(
        "custom_components.ev_smart_charging.async_setup",
        return_value=True,
    ), patch(
        "custom_components.ev_smart_charging.async_setup_entry",
        return_value=True,
    ):
        yield


# Simiulate a successful config flow.
# Note that we use the `bypass_validate_step_user` fixture here because
# we want the config flow validation to succeed during the test.
# pylint: disable=unused-argument
async def test_successful_config_flow(hass: HomeAssistant, bypass_validate_step_user):
    """Test a successful config flow."""
    # Initialize a config flow
    result: Dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG_USER
    )

    # Check that the config flow is complete and a new entry is created with
    # the input data
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "EV Smart Charging"
    assert result["data"] == MOCK_CONFIG_CHARGER_EXTRA
    if "errors" in result.keys():
        assert len(result["errors"]) == 0
    assert result["result"]


# Simiulate an unsuccessful config flow
async def test_unsuccessful_config_flow(hass: HomeAssistant):
    """Test an usuccessful config flow."""

    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG_USER
    )

    # Check that the config flow is not complete and that there are errors
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert len(result["errors"]) > 0


# Simulate a successful option flow
async def test_successful_config_flow_option(
    hass: HomeAssistant, bypass_validate_step_user
):
    """Test a option flow."""

    config_entry: config_entries.ConfigEntry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test"
    )
    config_entry.add_to_hass(hass)

    # Initialize a option flow
    result = await hass.config_entries.options.async_init(
        handler="test", context={"source": "init"}
    )

    # Check that the option flow shows the init form
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG_USER
    )

    # Check that the option flow is complete and a new entry is created with
    # the input data
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["data"] == MOCK_CONFIG_USER
    if "errors" in result.keys():
        assert len(result["errors"]) == 0
    assert result["result"]


# Simulate an unsuccessful option flow
async def test_unsuccessful_config_flow_option(hass: HomeAssistant):
    """Test a option flow."""

    config_entry: config_entries.ConfigEntry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ALL, entry_id="test"
    )
    config_entry.add_to_hass(hass)

    # Initialize a option flow
    result = await hass.config_entries.options.async_init(
        handler="test", context={"source": "init"}
    )

    # Check that the option flow shows the init form
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG_USER
    )

    # Check that the config flow is not complete and that there are errors
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"
    assert len(result["errors"]) > 0
