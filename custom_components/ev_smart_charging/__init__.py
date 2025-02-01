"""EV Smart Charging integration"""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MAJOR_VERSION, MINOR_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import async_get as async_device_registry_get
from homeassistant.helpers.device_registry import DeviceRegistry, DeviceEntry
from homeassistant.helpers.entity_registry import async_get as async_entity_registry_get
from homeassistant.helpers.entity_registry import (
    EntityRegistry,
    async_entries_for_config_entry,
)
from homeassistant.util import dt

from .coordinator import EVSmartChargingCoordinator
from .const import (
    CONF_EV_CONTROLLED,
    CONF_GRID_USAGE_SENSOR,
    CONF_GRID_VOLTAGE,
    CONF_LOW_PRICE_CHARGING_LEVEL,
    CONF_LOW_SOC_CHARGING_LEVEL,
    CONF_OPPORTUNISTIC_LEVEL,
    CONF_SOLAR_CHARGING_CONFIGURED,
    CONF_START_QUARTER,
    DOMAIN,
    STARTUP_MESSAGE,
    PLATFORMS,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    _LOGGER.debug("async_setup_entry")

    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.debug(STARTUP_MESSAGE)

    coordinator = EVSmartChargingCoordinator(hass, entry)
    validation_error = coordinator.validate_input_sensors()
    if not validation_error:
        validation_error = coordinator.validate_control_entities()
    if validation_error is not None:
        _LOGGER.debug("%s", validation_error)
        for unsub in coordinator.listeners:
            unsub()
        raise ConfigEntryNotReady(validation_error)

    hass.data[DOMAIN][entry.entry_id] = coordinator
    coordinator.setup_timestamp = dt.now().timestamp()

    for platform in PLATFORMS:
        coordinator.platforms.append(platform)
    if MAJOR_VERSION > 2024 or (MAJOR_VERSION == 2024 and MINOR_VERSION >= 7):
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    else:
        for platform in PLATFORMS:
            hass.async_create_task(
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


# Global lock
ev_smart_charging_lock = asyncio.Lock()


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    _LOGGER.debug("async_reload_entry")
    # Make sure setup is completed before next unload is started.
    async with ev_smart_charging_lock:
        await async_unload_entry(hass, entry)
        await async_setup_entry(hass, entry)


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    new = {**config_entry.data}
    migration = False
    version = config_entry.version

    if version == 1:
        # Set default values for new configuration parameters
        new[CONF_START_QUARTER] = "None"
        version = 2
        migration = True

    if version == 2:
        # Set default values for new configuration parameters
        new[CONF_OPPORTUNISTIC_LEVEL] = 50.0
        version = 3
        migration = True

    if version == 3:
        version = 4
        migration = True

    if version == 4:
        version = 5
        new[CONF_EV_CONTROLLED] = False
        migration = True

    if version == 5:
        version = 6
        new[CONF_LOW_PRICE_CHARGING_LEVEL] = 0.0
        new[CONF_LOW_SOC_CHARGING_LEVEL] = 20.0
        migration = True

    if version == 6:
        version = 7
        new[CONF_SOLAR_CHARGING_CONFIGURED] = False
        new[CONF_GRID_USAGE_SENSOR] = ""
        new[CONF_GRID_VOLTAGE] = 230  # [V]
        migration = True

    if version > 7:
        _LOGGER.error(
            "Migration from version %s to a lower version is not possible",
            version,
        )
        return False

    if migration:
        if MAJOR_VERSION > 2024 or (MAJOR_VERSION == 2024 and MINOR_VERSION >= 4):
            # New argument to set version from HA 2024.4.
            hass.config_entries.async_update_entry(
                config_entry, data=new, version=version
            )
        else:  # pragma: no cover
            # Old way to set new version. Used up to HA 2024.3.
            config_entry.version = version
            hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.info("Migration to version %s successful", version)

    return True
