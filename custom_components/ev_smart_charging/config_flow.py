"""Adds config flow for EV Smart Charging."""

import logging
from typing import Any, Optional
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_DEVICE_NAME,
    CONF_EV_CONTROLLED,
    CONF_EV_SOC_SENSOR,
    CONF_EV_TARGET_SOC_SENSOR,
    CONF_GRID_USAGE_SENSOR,
    CONF_GRID_VOLTAGE,
    CONF_PRICE_SENSOR,
    CONF_CHARGER_ENTITY,
    CONF_SOLAR_CHARGING_CONFIGURED,
    DOMAIN,
)
from .helpers.config_flow import DeviceNameCreator, FindEntity, FlowValidator
from .helpers.general import get_parameter

_LOGGER = logging.getLogger(__name__)


class EVSmartChargingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow."""

    VERSION = 7
    user_input: Optional[dict[str, Any]]

    def __init__(self):
        """Initialize."""
        _LOGGER.debug("EVChargingControlConfigFlow.__init__")
        self._errors = {}
        self.user_input = {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        _LOGGER.debug("EVChargingControlConfigFlow.async_step_user")
        self._errors = {}

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        # if self._async_current_entries():
        #    return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            user_input = {}
            # Provide defaults for form
            user_input[CONF_DEVICE_NAME] = DeviceNameCreator.create(self.hass)
            user_input[CONF_PRICE_SENSOR] = FindEntity.find_price_sensor(self.hass)
            user_input[CONF_EV_SOC_SENSOR] = FindEntity.find_vw_soc_sensor(self.hass)
            user_input[CONF_EV_TARGET_SOC_SENSOR] = (
                FindEntity.find_vw_target_soc_sensor(self.hass)
            )
            user_input[CONF_CHARGER_ENTITY] = FindEntity.find_ocpp_device(self.hass)
            user_input[CONF_EV_CONTROLLED] = False
            user_input[CONF_SOLAR_CHARGING_CONFIGURED] = False

        else:
            # process user_input
            error = FlowValidator.validate_step_user(self.hass, user_input)
            if error is not None:
                self._errors[error[0]] = error[1]

            if not self._errors:
                self.user_input = user_input
                if user_input[CONF_SOLAR_CHARGING_CONFIGURED]:
                    return await self.async_step_solar()
                else:
                    return self.async_create_entry(
                        title=user_input[CONF_DEVICE_NAME], data=self.user_input
                    )

        return await self._show_config_form_user(user_input)

    async def _show_config_form_user(self, user_input):
        """Show the configuration form."""

        user_schema = {
            vol.Required(
                CONF_DEVICE_NAME, default=user_input[CONF_DEVICE_NAME]
            ): cv.string,
            vol.Required(
                CONF_PRICE_SENSOR, default=user_input[CONF_PRICE_SENSOR]
            ): cv.string,
            vol.Required(
                CONF_EV_SOC_SENSOR, default=user_input[CONF_EV_SOC_SENSOR]
            ): cv.string,
            vol.Optional(
                CONF_EV_TARGET_SOC_SENSOR, default=user_input[CONF_EV_TARGET_SOC_SENSOR]
            ): cv.string,
            vol.Optional(
                CONF_CHARGER_ENTITY, default=user_input[CONF_CHARGER_ENTITY]
            ): cv.string,
            vol.Optional(
                CONF_EV_CONTROLLED, default=user_input[CONF_EV_CONTROLLED]
            ): cv.boolean,
            vol.Optional(
                CONF_SOLAR_CHARGING_CONFIGURED,
                default=user_input[CONF_SOLAR_CHARGING_CONFIGURED],
            ): cv.boolean,
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(user_schema),
            errors=self._errors,
            last_step=False,
        )

    async def async_step_solar(self, user_input=None):
        """Configuraton of Solar charging"""
        _LOGGER.debug("EVChargingControlConfigFlow.async_step_solar")
        self._errors = {}

        if user_input is None:
            user_input = {}
            # Provide defaults for form
            user_input[CONF_GRID_USAGE_SENSOR] = ""
            user_input[CONF_GRID_VOLTAGE] = 230  # [V]

        else:
            # process user_input
            error = FlowValidator.validate_step_solar(self.hass, user_input)
            if error is not None:
                self._errors[error[0]] = error[1]

            if not self._errors:
                self.user_input = self.user_input | user_input
                return self.async_create_entry(
                    title=self.user_input[CONF_DEVICE_NAME], data=self.user_input
                )

        return await self._show_config_form_solar(user_input)

    async def _show_config_form_solar(self, user_input):
        """Show the configuration form."""

        positive_int = vol.All(vol.Coerce(int), vol.Range(min=1))

        user_schema = {
            vol.Required(
                CONF_GRID_USAGE_SENSOR, default=user_input[CONF_GRID_USAGE_SENSOR]
            ): cv.string,
            vol.Required(
                CONF_GRID_VOLTAGE, default=user_input[CONF_GRID_VOLTAGE]
            ): positive_int,
        }

        return self.async_show_form(
            step_id="solar",
            data_schema=vol.Schema(user_schema),
            errors=self._errors,
            last_step=True,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow handler"""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._errors = {}
        self.user_input = {}

    async def async_step_init(self, user_input) -> FlowResult:
        """Manage the options."""

        self._errors = {}

        if user_input is not None:
            # process user_input
            error = FlowValidator.validate_step_user(self.hass, user_input)

            if error is not None:
                self._errors[error[0]] = error[1]

            if not self._errors:
                self.user_input = user_input
                if user_input[CONF_SOLAR_CHARGING_CONFIGURED]:
                    return await self.async_step_solar()
                else:
                    return self.async_create_entry(
                        title=self.config_entry.title, data=self.user_input
                    )

        user_schema = {
            vol.Required(
                CONF_PRICE_SENSOR,
                default=get_parameter(self.config_entry, CONF_PRICE_SENSOR),
            ): cv.string,
            vol.Required(
                CONF_EV_SOC_SENSOR,
                default=get_parameter(self.config_entry, CONF_EV_SOC_SENSOR),
            ): cv.string,
            vol.Optional(
                CONF_EV_TARGET_SOC_SENSOR,
                default=get_parameter(self.config_entry, CONF_EV_TARGET_SOC_SENSOR),
            ): cv.string,
            vol.Optional(
                CONF_CHARGER_ENTITY,
                default=get_parameter(self.config_entry, CONF_CHARGER_ENTITY),
            ): cv.string,
            vol.Optional(
                CONF_EV_CONTROLLED,
                default=get_parameter(self.config_entry, CONF_EV_CONTROLLED),
            ): cv.boolean,
            vol.Optional(
                CONF_SOLAR_CHARGING_CONFIGURED,
                default=get_parameter(
                    self.config_entry, CONF_SOLAR_CHARGING_CONFIGURED
                ),
            ): cv.boolean,
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(user_schema),
            errors=self._errors,
            last_step=False,
        )

    async def async_step_solar(self, user_input=None) -> FlowResult:
        """Manage the options."""

        positive_int = vol.All(vol.Coerce(int), vol.Range(min=1))

        self._errors = {}

        if user_input is not None:
            # process user_input
            error = FlowValidator.validate_step_solar(self.hass, user_input)

            if error is not None:
                self._errors[error[0]] = error[1]

            if not self._errors:
                self.user_input = self.user_input | user_input
                return self.async_create_entry(
                    title=self.config_entry.title, data=self.user_input
                )

        user_schema = {
            vol.Required(
                CONF_GRID_USAGE_SENSOR,
                default=get_parameter(self.config_entry, CONF_GRID_USAGE_SENSOR),
            ): cv.string,
            vol.Required(
                CONF_GRID_VOLTAGE,
                default=get_parameter(self.config_entry, CONF_GRID_VOLTAGE),
            ): positive_int,
        }

        return self.async_show_form(
            step_id="solar",
            data_schema=vol.Schema(user_schema),
            errors=self._errors,
            last_step=True,
        )
