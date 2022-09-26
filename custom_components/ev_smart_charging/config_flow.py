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
    CONF_EV_SOC_SENSOR,
    CONF_EV_TARGET_SOC_SENSOR,
    CONF_MAX_PRICE,
    CONF_NORDPOOL_SENSOR,
    CONF_CHARGER_ENTITY,
    CONF_PCT_PER_HOUR,
    CONF_READY_HOUR,
    DOMAIN,
    HOURS,
    NAME,
)
from .helpers.config_flow import DeviceNameCreator, FindEntity, FlowValidator
from .helpers.general import get_parameter

_LOGGER = logging.getLogger(__name__)


class EVSmartChargingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow."""

    VERSION = 1
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
            user_input[CONF_NORDPOOL_SENSOR] = FindEntity.find_nordpool_sensor(
                self.hass
            )
            user_input[CONF_EV_SOC_SENSOR] = FindEntity.find_vw_soc_sensor(self.hass)
            user_input[
                CONF_EV_TARGET_SOC_SENSOR
            ] = FindEntity.find_vw_target_soc_sensor(self.hass)
            user_input[CONF_CHARGER_ENTITY] = FindEntity.find_ocpp_device(self.hass)

        else:
            # process user_input
            error = FlowValidator.validate_step_user(self.hass, user_input)
            if error is not None:
                self._errors[error[0]] = error[1]

            if not self._errors:
                self.user_input = user_input
                return await self.async_step_charger()

        return await self._show_config_form_user(user_input)

    async def _show_config_form_user(self, user_input):
        """Show the configuration form."""

        user_schema = {
            vol.Required(
                CONF_NORDPOOL_SENSOR, default=user_input[CONF_NORDPOOL_SENSOR]
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
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(user_schema),
            errors=self._errors,
            last_step=False,
        )

    async def async_step_charger(self, user_input=None):
        """UI configuration of charger"""

        _LOGGER.debug("EVChargingControlConfigFlow.async_step_charger")
        self._errors = {}

        if user_input is not None:
            # process user_input
            user_input[CONF_DEVICE_NAME] = DeviceNameCreator.create(
                self.hass
            )  # Add device name
            self.user_input.update(user_input)
            return self.async_create_entry(title=NAME, data=self.user_input)

        user_input = {}
        # Provide defaults for form
        user_input[CONF_PCT_PER_HOUR] = 6.0
        user_input[CONF_READY_HOUR] = "08:00"
        user_input[CONF_MAX_PRICE] = 0.0

        return await self._show_config_form_charger(user_input)

    async def _show_config_form_charger(self, user_input):
        """Show the configuration form."""

        charger_schema = {
            vol.Required(
                CONF_PCT_PER_HOUR, default=user_input[CONF_PCT_PER_HOUR]
            ): cv.positive_float,
            vol.Required(CONF_READY_HOUR, default=user_input[CONF_READY_HOUR]): vol.In(
                HOURS
            ),
            vol.Required(
                CONF_MAX_PRICE, default=user_input[CONF_MAX_PRICE]
            ): cv.positive_float,
        }

        return self.async_show_form(
            step_id="charger",
            data_schema=vol.Schema(charger_schema),
            errors=self._errors,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow handler"""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""

        if user_input is not None:
            return self.async_create_entry(title=NAME, data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PCT_PER_HOUR,
                        default=get_parameter(self.config_entry, CONF_PCT_PER_HOUR),
                    ): cv.positive_float,
                    vol.Required(
                        CONF_READY_HOUR,
                        default=get_parameter(self.config_entry, CONF_READY_HOUR),
                    ): vol.In(HOURS),
                    vol.Required(
                        CONF_MAX_PRICE,
                        default=get_parameter(self.config_entry, CONF_MAX_PRICE),
                    ): cv.positive_float,
                }
            ),
        )
