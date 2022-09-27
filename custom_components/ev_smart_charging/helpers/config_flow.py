"""Helpers for config_flow"""

from collections import UserDict
import logging
from typing import Any, List
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import async_get as async_device_registry_get
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import (
    EntityRegistry,
    RegistryEntry,
)

# pylint: disable=relative-beyond-top-level
from ..const import (
    CONF_CHARGER_ENTITY,
    CONF_EV_SOC_SENSOR,
    CONF_EV_TARGET_SOC_SENSOR,
    CONF_PRICE_SENSOR,
    DOMAIN,
    NAME,
    PLATFORM_NORDPOOL,
    PLATFORM_OCPP,
    PLATFORM_VW,
    SENSOR,
    SWITCH,
)
from .general import Validator

_LOGGER = logging.getLogger(__name__)


class FlowValidator:
    """Validator of flows"""

    @staticmethod
    def validate_step_user(
        hass: HomeAssistant, user_input: dict[str, Any]
    ) -> List[str]:
        """Validate step_user"""

        entity_registry: EntityRegistry = async_entity_registry_get(hass)
        entities = entity_registry.entities

        # Validate Price entity
        price_state = hass.states.get(user_input[CONF_PRICE_SENSOR])
        if price_state is None:
            return ("base", "price_not_found")
        entry: RegistryEntry = entities.get(user_input[CONF_PRICE_SENSOR])
        if entry.domain != SENSOR:
            return ("base", "price_not_sensor")
        if not "current_price" in price_state.attributes.keys():
            _LOGGER.debug("No attribute current_price in price sensor")
            return ("base", "sensor_is_not_price")
        if not "raw_today" in price_state.attributes.keys():
            _LOGGER.debug("No attribute raw_today in price sensor")
            return ("base", "sensor_is_not_price")
        if not "raw_tomorrow" in price_state.attributes.keys():
            _LOGGER.debug("No attribute raw_tomorrow in price sensor")
            return ("base", "sensor_is_not_price")

        # Validate EV SOC entity
        entity = hass.states.get(user_input[CONF_EV_SOC_SENSOR])
        if entity is None:
            return ("base", "ev_soc_not_found")
        if not Validator.is_float(entity.state):
            _LOGGER.debug("EV SOC state is not float")
            return ("base", "ev_soc_invalid_data")
        if not 0.0 <= float(entity.state) <= 100.0:
            _LOGGER.debug("EV SOC state is between 0 and 100")
            return ("base", "ev_soc_invalid_data")

        # Validate EV Target SOC entity
        # If the set value is only whitespaces, the value will be set to ""
        user_input[CONF_EV_TARGET_SOC_SENSOR] = user_input[
            CONF_EV_TARGET_SOC_SENSOR
        ].strip()
        if len(user_input[CONF_EV_TARGET_SOC_SENSOR]) > 0:
            entity = hass.states.get(user_input[CONF_EV_TARGET_SOC_SENSOR])
            if entity is None:
                return ("base", "ev_target_soc_not_found")
            if not Validator.is_float(entity.state):
                _LOGGER.debug("EV Target SOC state is not float")
                return ("base", "ev_soc_target_invalid_data")
            if not 0.0 <= float(entity.state) <= 100.0:
                _LOGGER.debug("EV Target SOC state is between 0 and 100")
                return ("base", "ev_soc_target_invalid_data")

        # Validate Charger control switch entity
        # If the set value is only whitespaces, the value will be set to ""
        user_input[CONF_CHARGER_ENTITY] = user_input[CONF_CHARGER_ENTITY].strip()
        if len(user_input[CONF_CHARGER_ENTITY]) > 0:
            entity = hass.states.get(user_input[CONF_CHARGER_ENTITY])
            if entity is None:
                return ("base", "charger_control_switch_not_found")
            entry: RegistryEntry = entities.get(user_input[CONF_CHARGER_ENTITY])
            if entry.domain != SWITCH:
                return ("base", "charger_control_switch_not_switch")

        return None


class FindEntity:
    """Find entities"""

    @staticmethod
    def find_nordpool_sensor(hass: HomeAssistant) -> str:
        """Find Nordpool sensor"""
        entity_registry: EntityRegistry = async_entity_registry_get(hass)
        registry_entries: UserDict[
            str, RegistryEntry
        ] = entity_registry.entities.items()
        for entry in registry_entries:
            if entry[1].platform == PLATFORM_NORDPOOL:
                return entry[1].entity_id
        return ""

    @staticmethod
    def find_vw_soc_sensor(hass: HomeAssistant) -> str:
        """Search for Volkswagen SOC sensor"""
        entity_registry: EntityRegistry = async_entity_registry_get(hass)
        registry_entries: UserDict[
            str, RegistryEntry
        ] = entity_registry.entities.items()
        for entry in registry_entries:
            if entry[1].platform == PLATFORM_VW:
                entity_id = entry[1].entity_id
                if "state_of_charge" in entity_id:
                    if not "target_state_of_charge" in entity_id:
                        return entity_id
        return ""

    @staticmethod
    def find_vw_target_soc_sensor(hass: HomeAssistant) -> str:
        """Search for Volkswagen Target SOC sensor"""
        entity_registry: EntityRegistry = async_entity_registry_get(hass)
        registry_entries: UserDict[
            str, RegistryEntry
        ] = entity_registry.entities.items()
        for entry in registry_entries:
            if entry[1].platform == PLATFORM_VW:
                entity_id = entry[1].entity_id
                if "target_state_of_charge" in entity_id:
                    return entity_id
        return ""

    @staticmethod
    def find_ocpp_device(hass: HomeAssistant) -> str:
        """Find OCPP entity"""
        entity_registry: EntityRegistry = async_entity_registry_get(hass)
        registry_entries: UserDict[
            str, RegistryEntry
        ] = entity_registry.entities.items()
        for entry in registry_entries:
            if entry[1].platform == PLATFORM_OCPP:
                entity_id = entry[1].entity_id
                if entity_id.startswith("switch"):
                    if "charge_control" in entity_id:
                        return entity_id
        return ""


class DeviceNameCreator:
    """Class that creates the name of the new device"""

    @staticmethod
    def create(hass: HomeAssistant) -> str:
        """Create device name"""
        device_registry: DeviceRegistry = async_device_registry_get(hass)
        devices = device_registry.devices
        # Find existing EV Smart Charging devices
        ev_devices = []
        for device in devices:
            for item in devices[device].identifiers:
                if item[0] == DOMAIN:
                    ev_devices.append(device)
        # If this is the first device. just return NAME
        if len(ev_devices) == 0:
            return NAME
        # Find the highest number at the end of the name
        higest = 1
        for device in ev_devices:
            device_name: str = devices[device].name
            if device_name == NAME:
                pass
            else:
                try:
                    device_number = int(device_name[len(NAME) :])
                    if device_number > higest:
                        higest = device_number
                except ValueError:
                    pass
        # Add ONE to the highest value and append after NAME
        return f"{NAME} {higest+1}"
