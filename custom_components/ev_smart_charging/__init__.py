"""EV Smart Charging integration"""

import asyncio
import logging

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigEntryChange,
    SIGNAL_CONFIG_ENTRY_CHANGED,
)
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.ev_smart_charging.helpers.general import get_parameter

from .coordinator import EVSmartChargingCoordinator
from .const import (
    CONF_DEVICE_NAME,
    DOMAIN,
    STARTUP_MESSAGE,
    PLATFORMS,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup(
    hass: HomeAssistant, config: Config
):  # pylint: disable=unused-argument
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""

    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.debug(STARTUP_MESSAGE)

    # Make sure the Integration name is the same as the Device name
    # This is currently needed since
    # homeassistant.config_entries.OptionsFlowManager.async_finish_flow()
    # does not pass "title" to self.hass.config_entries.async_update_entry()
    # Don't bother to test code copied from async_update_entry()
    if entry.title != get_parameter(entry, CONF_DEVICE_NAME):
        entry.title = get_parameter(entry, CONF_DEVICE_NAME)
        for listener_ref in entry.update_listeners:
            if (listener := listener_ref()) is not None:  # pragma: no cover
                hass.async_create_task(listener(hass, entry))  # pragma: no cover
        async_dispatcher_send(
            hass, SIGNAL_CONFIG_ENTRY_CHANGED, ConfigEntryChange.UPDATED, entry
        )

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
        new["start_hour"] = "None"
        config_entry.version = 2
        migration = True

    if config_entry.version == 2:
        # Set default values for new configuration parameters
        new["opportunistic_level"] = 50.0
        config_entry.version = 3
        migration = True

    if config_entry.version == 3:
        config_entry.version = 4
        migration = True

    if config_entry.version > 4:
        _LOGGER.error(
            "Migration from version %s to a lower version is not possible",
            config_entry.version,
        )
        return False

    if migration:
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True
