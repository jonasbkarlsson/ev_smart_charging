"""EV Smart Charging Entity class"""
import logging
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, NAME, VERSION

_LOGGER = logging.getLogger(__name__)


class EVSmartChargingEntity(Entity):
    """Entity class."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self.config_entry.entry_id

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": NAME,
            "model": VERSION,
            "manufacturer": NAME,
        }
