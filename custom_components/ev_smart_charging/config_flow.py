"""Adds config flow for EV Smart Charging."""
import logging
from typing import Any, Optional
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CHARGER_TYPE_NONE,
    CHARGER_TYPE_OCPP,
    CONF_CHARGER_TYPE,
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
    PLATFORM_NORDPOOL,
    PLATFORM_OCPP,
    PLATFORM_VW,
)

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
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            # process user_input
            self.user_input = user_input
            # return self.async_create_entry(title=NAME, data=self.user_input)
            return await self.async_step_charger()

        user_input = {}
        # Provide defaults for form
        user_input[CONF_NORDPOOL_SENSOR] = self._get_nordpool_sensor()
        user_input[CONF_EV_SOC_SENSOR] = self._get_vw_soc_sensor()
        user_input[CONF_EV_TARGET_SOC_SENSOR] = self._get_vw_target_soc_sensor()
        user_input[CONF_CHARGER_TYPE] = CHARGER_TYPE_NONE
        user_input[CONF_CHARGER_ENTITY] = None

        chargers = [CHARGER_TYPE_NONE]
        ocpp = self._get_ocpp_device()
        if ocpp is not None:
            chargers.append(CHARGER_TYPE_OCPP)
            user_input[CONF_CHARGER_TYPE] = CHARGER_TYPE_OCPP
            user_input[CONF_CHARGER_ENTITY] = ocpp

        return await self._show_config_form_user(user_input, chargers)

    async def _show_config_form_user(self, user_input, chargers):
        """Show the configuration form."""

        user_schema = {
            vol.Required(
                CONF_NORDPOOL_SENSOR, default=user_input[CONF_NORDPOOL_SENSOR]
            ): cv.string,
            vol.Required(
                CONF_EV_SOC_SENSOR, default=user_input[CONF_EV_SOC_SENSOR]
            ): cv.string,
            vol.Required(
                CONF_EV_TARGET_SOC_SENSOR, default=user_input[CONF_EV_TARGET_SOC_SENSOR]
            ): cv.string,
            vol.Required(
                CONF_CHARGER_TYPE, default=user_input[CONF_CHARGER_TYPE]
            ): vol.In(chargers),
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

    def _get_ocpp_device(self):
        registry_entries = self.hass.data["entity_registry"].entities.data
        for entry in registry_entries:
            if registry_entries[entry].platform == PLATFORM_OCPP:
                entity_id = registry_entries[entry].entity_id
                if entity_id.startswith("switch"):
                    if entity_id.endswith("charge_control"):
                        return registry_entries[entry].entity_id
        return "Not found"

    def _get_nordpool_sensor(self):
        """Search for Nordpool sensor"""
        registry_entries = self.hass.data["entity_registry"].entities.data
        for entry in registry_entries:
            if registry_entries[entry].platform == PLATFORM_NORDPOOL:
                return registry_entries[entry].entity_id
        return "Not found"

    def _get_vw_soc_sensor(self):
        """Search for Volkswagen SOC sensor"""
        registry_entries = self.hass.data["entity_registry"].entities.data
        for entry in registry_entries:
            if registry_entries[entry].platform == PLATFORM_VW:
                entity_id = registry_entries[entry].entity_id
                if entity_id.endswith("state_of_charge"):
                    if not entity_id.endswith("target_state_of_charge"):
                        return registry_entries[entry].entity_id
        return "Not found"

    def _get_vw_target_soc_sensor(self):
        """Search for Volkswagen Target SOC sensor"""
        registry_entries = self.hass.data["entity_registry"].entities.data
        for entry in registry_entries:
            if registry_entries[entry].platform == PLATFORM_VW:
                entity_id = registry_entries[entry].entity_id
                if entity_id.endswith("target_state_of_charge"):
                    return registry_entries[entry].entity_id
        return "Not found"


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow handler"""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def _get_existing_param(self, parameter: str, default_val: any = None):
        if parameter in self.config_entry.options.keys():
            return self.config_entry.options.get(parameter)
        if parameter in self.config_entry.data.keys():
            return self.config_entry.data.get(parameter)
        return default_val

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
                        default=await self._get_existing_param(CONF_PCT_PER_HOUR),
                    ): cv.positive_float,
                    vol.Required(
                        CONF_READY_HOUR,
                        default=await self._get_existing_param(CONF_READY_HOUR),
                    ): vol.In(HOURS),
                    vol.Required(
                        CONF_MAX_PRICE,
                        default=await self._get_existing_param(CONF_MAX_PRICE),
                    ): cv.positive_float,
                }
            ),
        )
