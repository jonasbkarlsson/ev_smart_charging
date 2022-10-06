"""Global fixtures for ev_smart_charging integration."""
# Fixtures allow you to replace functions with a Mock object. You can perform
# many options via the Mock to reflect a particular behavior from the original
# function that you want to see without going through the function's actual logic.
# Fixtures can either be passed into tests as parameters, or if autouse=True, they
# will automatically be used across all tests.
#
# Fixtures that are defined in conftest.py are available across all tests. You can also
# define fixtures within a particular test file to scope them locally.
#
# pytest_homeassistant_custom_component provides some fixtures that are provided by
# Home Assistant core. You can find those fixture definitions here:
# https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/blob/master/pytest_homeassistant_custom_component/common.py
#
# See here for more info: https://docs.pytest.org/en/latest/fixture.html (note that
# pytest includes fixtures OOB which you can use as defined on this page)
from unittest.mock import patch
from homeassistant.util import dt as dt_util

import pytest

# pylint: disable=invalid-name
pytest_plugins = "pytest_homeassistant_custom_component"


# This fixture enables loading custom integrations in all tests.
# Remove to enable selective use of this fixture
# pylint: disable=unused-argument
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enables loading of custom integration"""
    yield


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss persistent
# notifications. These calls would fail without this fixture since the persistent_notification
# integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield


# This fixture, when used, will result in calls to validate_input_sensors to return None. To have
# the call return a value, we would add the `return_value=<VALUE_TO_RETURN>` parameter to the
# patch call.
# pylint: disable=line-too-long
@pytest.fixture(name="bypass_validate_input_sensors")
def bypass_validate_input_sensors_fixture():
    """Skip calls to validate input sensors."""
    with patch(
        "custom_components.ev_smart_charging.coordinator.EVSmartChargingCoordinator.validate_input_sensors",
        return_value=None,
    ):
        yield


# This fixture, when used, will result in calls to validate_input_sensors to return None. To have
# the call return a value, we would add the `return_value=<VALUE_TO_RETURN>` parameter to the
# patch call.
@pytest.fixture(name="bypass_validate_step_user")
def bypass_validate_step_user_fixture():
    """Skip calls to validate step user."""
    with patch(
        "custom_components.ev_smart_charging.helpers.config_flow.FlowValidator.validate_step_user",
        return_value=None,
    ):
        yield


# This fixture is used to set CET time zone.
@pytest.fixture(name="set_cet_timezone")
def set_cet_timezone_fixture():
    """Set CET timezone."""
    with patch(
        "homeassistant.util.dt.DEFAULT_TIME_ZONE",
        dt_util.get_time_zone("Europe/Stockholm"),
    ):
        yield


# This fixture is used to prevent HomeAssistant from doing Service Calls.
@pytest.fixture(name="skip_service_calls")
def skip_service_calls_fixture():
    """Skip service calls."""
    with patch("homeassistant.core.ServiceRegistry.async_call"):
        yield
