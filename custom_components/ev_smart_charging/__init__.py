"""EV Smart Charging integration"""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import async_get as async_device_registry_get
from homeassistant.helpers.device_registry import DeviceRegistry, DeviceEntry
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import (
    EntityRegistry,
    async_entries_for_config_entry,
)

from .coordinator import EVSmartChargingCoordinator
from .const import (
    CONF_EV_CONTROLLED,
    CONF_LOW_PRICE_CHARGING_LEVEL,
    CONF_LOW_SOC_CHARGING_LEVEL,
    CONF_OPPORTUNISTIC_LEVEL,
    CONF_START_HOUR,
    DOMAIN,
    STARTUP_MESSAGE,
    PLATFORMS,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""

    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.debug(STARTUP_MESSAGE)

    coordinator = EVSmartChargingCoordinator(hass, entry)
    validation_error = coordinator.validate_input_sensors()
    if validation_error is not None:
        _LOGGER.debug("%s", validation_error)
        for unsub in coordinator.listeners:
            unsub()
        raise ConfigEntryNotReady(validation_error)

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # If the name of the integration (config_entry.title) has changed,
    # update the device name.
    entity_registry: EntityRegistry = async_entity_registry_get(hass)
    all_entities = async_entries_for_config_entry(entity_registry, entry.entry_id)
    if all_entities:
        device_id = all_entities[0].device_id
        device_registry: DeviceRegistry = async_device_registry_get(hass)
        device: DeviceEntry = device_registry.async_get(device_id)
        if device:
            if device.name_by_user is not None:
                if entry.title != device.name_by_user:
                    device_registry.async_update_device(
                        device.id, name_by_user=entry.title
                    )
            else:
                if entry.title != device.name:
                    device_registry.async_update_device(
                        device.id, name_by_user=entry.title
                    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    _LOGGER.debug("async_unload_entry")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        for unsub in coordinator.listeners:
            unsub()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    new = {**config_entry.data}
    migration = False

    if config_entry.version == 1:
        # Set default values for new configuration parameters
        new[CONF_START_HOUR] = "None"
        config_entry.version = 2
        migration = True

    if config_entry.version == 2:
        # Set default values for new configuration parameters
        new[CONF_OPPORTUNISTIC_LEVEL] = 50.0
        config_entry.version = 3
        migration = True

    if config_entry.version == 3:
        config_entry.version = 4
        migration = True

    if config_entry.version == 4:
        config_entry.version = 5
        new[CONF_EV_CONTROLLED] = False
        migration = True

    if config_entry.version == 5:
        config_entry.version = 6
        new[CONF_LOW_PRICE_CHARGING_LEVEL] = 0.0
        new[CONF_LOW_SOC_CHARGING_LEVEL] = 20.0
        migration = True

    if config_entry.version > 6:
        _LOGGER.error(
            "Migration from version %s to a lower version is not possible",
            config_entry.version,
        )
        return False

    if migration:
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True
