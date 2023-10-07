"""Adds config flow for EV Smart Charging."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_COST_CALCULATION,
    CONF_COST_CURRENCY,
    CONF_COST_MULTIPLIER,
    CONF_COST_OFFSET,
    CONF_DEVICE_NAME,
    CONF_ENERGY_SENSOR,
    CONF_EV_CONTROLLED,
    CONF_EV_SOC_SENSOR,
    CONF_EV_TARGET_SOC_SENSOR,
    CONF_PRICE_SENSOR,
    CONF_CHARGER_ENTITY,
    DOMAIN,
)
from .helpers.config_flow import DeviceNameCreator, FindEntity, FlowValidator
from .helpers.general import get_parameter

_LOGGER = logging.getLogger(__name__)


class EVSmartChargingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow."""

    VERSION = 7

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
            user_input[
                CONF_EV_TARGET_SOC_SENSOR
            ] = FindEntity.find_vw_target_soc_sensor(self.hass)
            user_input[CONF_CHARGER_ENTITY] = FindEntity.find_ocpp_device(self.hass)
            user_input[CONF_EV_CONTROLLED] = False

        else:
            # process user_input
            error = FlowValidator.validate_step_user(self.hass, user_input)
            if error is not None:
                self._errors[error[0]] = error[1]

            if not self._errors:
                self.user_input = user_input
                return await self.async_step_cost()

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
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(user_schema),
            errors=self._errors,
            last_step=False,
        )

    async def async_step_cost(self, user_input=None):
        """UI configuration of charger"""

        _LOGGER.debug("EVChargingControlConfigFlow.async_step_cost")
        self._errors = {}

        if user_input is not None:
            # process user_input
            error = FlowValidator.validate_step_cost(self.hass, user_input)
            if error is not None:
                self._errors[error[0]] = error[1]

            if not self._errors:
                self.user_input.update(user_input)
                return self.async_create_entry(
                    title=self.user_input[CONF_DEVICE_NAME], data=self.user_input
                )

        user_input = {}
        # Provide defaults for form
        user_input[CONF_COST_CALCULATION] = False
        user_input[CONF_ENERGY_SENSOR] = ""
        user_input[CONF_COST_CURRENCY] = "EUR"
        user_input[CONF_COST_MULTIPLIER] = 1.0
        user_input[CONF_COST_OFFSET] = 0.0

        return await self._show_config_form_cost(user_input)

    async def _show_config_form_cost(self, user_input):
        """Show the configuration form."""

        cost_schema = {
            vol.Required(
                CONF_COST_CALCULATION, default=user_input[CONF_COST_CALCULATION]
            ): cv.boolean,
            vol.Optional(
                CONF_ENERGY_SENSOR, default=user_input[CONF_ENERGY_SENSOR]
            ): cv.string,
            vol.Optional(
                CONF_COST_CURRENCY, default=user_input[CONF_COST_CURRENCY]
            ): cv.string,
            vol.Optional(
                CONF_COST_MULTIPLIER, default=user_input[CONF_COST_MULTIPLIER]
            ): cv.positive_float,
            vol.Optional(
                CONF_COST_OFFSET, default=user_input[CONF_COST_OFFSET]
            ): vol.Coerce(float),
        }

        return self.async_show_form(
            step_id="cost",
            data_schema=vol.Schema(cost_schema),
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

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""

        self._errors = {}

        if user_input is not None:
            # process user_input
            error = FlowValidator.validate_step_user(self.hass, user_input)
            if error is not None:
                self._errors[error[0]] = error[1]

            if not self._errors:
                self.user_input = user_input
                return await self.async_step_cost()

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
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(user_schema),
            errors=self._errors,
            last_step=False,
        )

    async def async_step_cost(self, user_input=None) -> FlowResult:
        """UI configuration of charger"""

        self._errors = {}

        if user_input is not None:
            # process user_input
            error = FlowValidator.validate_step_cost(self.hass, user_input)
            if error is not None:
                self._errors[error[0]] = error[1]

            if not self._errors:
                self.user_input.update(user_input)
                return self.async_create_entry(
                    title=self.config_entry.title, data=self.user_input
                )

        cost_schema = {
            vol.Required(
                CONF_COST_CALCULATION,
                default=get_parameter(self.config_entry, CONF_COST_CALCULATION),
            ): cv.boolean,
            vol.Optional(
                CONF_ENERGY_SENSOR,
                default=get_parameter(self.config_entry, CONF_ENERGY_SENSOR),
            ): cv.string,
            vol.Optional(
                CONF_COST_CURRENCY,
                default=get_parameter(self.config_entry, CONF_COST_CURRENCY),
            ): cv.string,
            vol.Optional(
                CONF_COST_MULTIPLIER,
                default=get_parameter(self.config_entry, CONF_COST_MULTIPLIER),
            ): cv.positive_float,
            vol.Optional(
                CONF_COST_OFFSET,
                default=get_parameter(self.config_entry, CONF_COST_OFFSET),
            ): vol.Coerce(float),
        }

        return self.async_show_form(
            step_id="cost",
            data_schema=vol.Schema(cost_schema),
            errors=self._errors,
            last_step=True,
        )
