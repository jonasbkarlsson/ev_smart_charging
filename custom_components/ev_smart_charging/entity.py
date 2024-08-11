"""EV Smart Charging Entity class"""
import logging
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, ICON, NAME, VERSION

_LOGGER = logging.getLogger(__name__)


class EVSmartChargingEntity(Entity):
    """Entity class."""

    _attr_icon = ICON
    _attr_has_entity_name = True

    _entity_key: str

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self._attr_translation_key = self._entity_key

    def set_entity_id(self, platform_str, key):
        """Set the entity id"""
        entity_id = str(platform_str) + "." + DOMAIN + "_" + key
        _LOGGER.debug("entity_id = %s", entity_id)
        self.entity_id = entity_id


    def update_ha_state(self):
        """Update the HA state"""
        if self.entity_id is not None and self.hass is not None:
            self.async_schedule_update_ha_state()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": self.config_entry.title,
            "model": VERSION,
            "manufacturer": NAME,
        }
