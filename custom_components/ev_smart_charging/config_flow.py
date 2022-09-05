"""Adds config flow for EV Smart Charging."""
import logging
import voluptuous as vol

from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_EV_SOC_SENSOR,
    CONF_EV_TARGET_SOC_SENSOR,
    CONF_NORDPOOL_SENSOR,
    DOMAIN,
    NAME,
    PLATFORM_NORDPOOL,
    PLATFORM_VW,
)

_LOGGER = logging.getLogger(__name__)


class EVSmartChargingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        _LOGGER.debug("EVChargingControlConfigFlow.__init__")
        self._errors = {}

    async def async_step_user(self, user_input=None):

        _LOGGER.debug("EVChargingControlConfigFlow.async_step_user")
        self._errors = {}

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            # process user_input
            return self.async_create_entry(title=NAME, data=user_input)

        user_input = {}
        # Provide defaults for form
        user_input[CONF_NORDPOOL_SENSOR] = self._get_nordpool_sensor()
        user_input[CONF_EV_SOC_SENSOR] = self._get_vw_soc_sensor()
        user_input[CONF_EV_TARGET_SOC_SENSOR] = self._get_vw_target_soc_sensor()

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):
        """Show the configuration form."""

        data_schema = {
            vol.Required(
                CONF_NORDPOOL_SENSOR, default=user_input[CONF_NORDPOOL_SENSOR]
            ): cv.string,
            vol.Required(
                CONF_EV_SOC_SENSOR, default=user_input[CONF_EV_SOC_SENSOR]
            ): cv.string,
            vol.Required(
                CONF_EV_TARGET_SOC_SENSOR, default=user_input[CONF_EV_TARGET_SOC_SENSOR]
            ): cv.string,
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=self._errors,
        )

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
