"""Switch platform for EV Smart Charging."""

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    ENTITY_KEY_ACTIVE_PRICE_SWITCH,
    ENTITY_KEY_ACTIVE_SOLAR_SWITCH,
    ENTITY_KEY_ACTIVE_SWITCH,
    ENTITY_KEY_APPLY_LIMIT_SWITCH,
    ENTITY_KEY_CONF_THREE_PHASE_CHARGING,
    ENTITY_KEY_CONTINUOUS_SWITCH,
    ENTITY_KEY_EV_CONNECTED_SWITCH,
    ENTITY_KEY_LOW_PRICE_CHARGING_SWITCH,
    ENTITY_KEY_KEEP_ON_SWITCH,
    ENTITY_KEY_LOW_SOC_CHARGING_SWITCH,
    ENTITY_KEY_OPPORTUNISTIC_SWITCH,
    ICON_CONNECTION,
    SWITCH,
)
from .coordinator import EVSmartChargingCoordinator
from .entity import EVSmartChargingEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_devices
):  # pylint: disable=unused-argument
    """Setup switch platform."""
    _LOGGER.debug("EVSmartCharging.switch.py")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    switches = []
    switches.append(EVSmartChargingSwitchActive(entry, coordinator))
    switches.append(EVSmartChargingSwitchApplyLimit(entry, coordinator))
    switches.append(EVSmartChargingSwitchContinuous(entry, coordinator))
    switches.append(EVSmartChargingSwitchEVConnected(entry, coordinator))
    switches.append(EVSmartChargingSwitchKeepOn(entry, coordinator))
    switches.append(EVSmartChargingSwitchOpportunistic(entry, coordinator))
    switches.append(EVSmartChargingSwitchLowPriceCharging(entry, coordinator))
    switches.append(EVSmartChargingSwitchLowSocCharging(entry, coordinator))
    switches.append(EVSmartChargingSwitchThreePhaseCharging(entry, coordinator))
    switches.append(EVSmartChargingSwitchActivePriceCharging(entry, coordinator))
    switches.append(EVSmartChargingSwitchActiveSolarCharging(entry, coordinator))
    async_add_devices(switches)


# pylint: disable=abstract-method
class EVSmartChargingSwitch(EVSmartChargingEntity, SwitchEntity, RestoreEntity):
    """EV Smart Charging switch class."""

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSwitch.__init__()")
        super().__init__(entry)
        self.coordinator = coordinator
        id_name = self._entity_key.replace("_", "").lower()
        self._attr_unique_id = ".".join([entry.entry_id, SWITCH, id_name])
        self.set_entity_id(SWITCH, self._entity_key)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        self._attr_is_on = True

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        restored: State = await self.async_get_last_state()
        if restored is not None:
            if restored.state == STATE_ON:
                await self.async_turn_on()
            else:
                await self.async_turn_off()


class EVSmartChargingSwitchActive(EVSmartChargingSwitch):
    """EV Smart Charging active switch class."""

    _entity_key = ENTITY_KEY_ACTIVE_SWITCH

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSwitchActive.__init__()")
        super().__init__(entry, coordinator)
        if self.is_on is None:
            self._attr_is_on = True
            self.update_ha_state()
        self.coordinator.switch_active = self.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on(**kwargs)
        await self.coordinator.switch_active_update(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        await self.coordinator.switch_active_update(False)


class EVSmartChargingSwitchApplyLimit(EVSmartChargingSwitch):
    """EV Smart Charging apply limit switch class."""

    _entity_key = ENTITY_KEY_APPLY_LIMIT_SWITCH

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSwitchApplyLimit.__init__()")
        super().__init__(entry, coordinator)
        if self.is_on is None:
            self._attr_is_on = True
            self.update_ha_state()
        self.coordinator.switch_apply_limit = self.is_on
        self.coordinator.switch_apply_limit_unique_id = self._attr_unique_id

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on(**kwargs)
        await self.coordinator.switch_apply_limit_update(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        await self.coordinator.switch_apply_limit_update(False)


class EVSmartChargingSwitchContinuous(EVSmartChargingSwitch):
    """EV Smart Charging continuous switch class."""

    _entity_key = ENTITY_KEY_CONTINUOUS_SWITCH

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSwitchContinuous.__init__()")
        super().__init__(entry, coordinator)
        if self.is_on is None:
            self._attr_is_on = True
            self.update_ha_state()
        self.coordinator.switch_continuous = self.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on(**kwargs)
        await self.coordinator.switch_continuous_update(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        await self.coordinator.switch_continuous_update(False)


class EVSmartChargingSwitchEVConnected(EVSmartChargingSwitch):
    """EV Smart Charging continuous switch class."""

    _entity_key = ENTITY_KEY_EV_CONNECTED_SWITCH
    _attr_icon = ICON_CONNECTION

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSwitchEVConnected.__init__()")
        super().__init__(entry, coordinator)
        if self.is_on is None:
            self._attr_is_on = True
            self.update_ha_state()
        self.coordinator.switch_ev_connected = self.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on(**kwargs)
        await self.coordinator.switch_ev_connected_update(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        await self.coordinator.switch_ev_connected_update(False)


class EVSmartChargingSwitchKeepOn(EVSmartChargingSwitch):
    """EV Smart Charging keep charger on switch class."""

    _entity_key = ENTITY_KEY_KEEP_ON_SWITCH

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSwitchKeepOn.__init__()")
        super().__init__(entry, coordinator)
        if self.is_on is None:
            self._attr_is_on = False
            self.update_ha_state()
        self.coordinator.switch_keep_on = self.is_on
        self.coordinator.switch_keep_on_unique_id = self._attr_unique_id

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on(**kwargs)
        await self.coordinator.switch_keep_on_update(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        await self.coordinator.switch_keep_on_update(False)


class EVSmartChargingSwitchOpportunistic(EVSmartChargingSwitch):
    """EV Smart Charging opportunistic switch class."""

    _entity_key = ENTITY_KEY_OPPORTUNISTIC_SWITCH

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSwitchOpportunistic.__init__()")
        super().__init__(entry, coordinator)
        if self.is_on is None:
            self._attr_is_on = False
            self.update_ha_state()
        self.coordinator.switch_opportunistic = self.is_on
        self.coordinator.switch_opportunistic_unique_id = self._attr_unique_id

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on(**kwargs)
        await self.coordinator.switch_opportunistic_update(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        await self.coordinator.switch_opportunistic_update(False)


class EVSmartChargingSwitchLowPriceCharging(EVSmartChargingSwitch):
    """EV Smart Charging low price charging switch class."""

    _entity_key = ENTITY_KEY_LOW_PRICE_CHARGING_SWITCH

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSwitchLowPriceCharging.__init__()")
        super().__init__(entry, coordinator)
        if self.is_on is None:
            self._attr_is_on = False
            self.update_ha_state()
        self.coordinator.switch_low_price_charging = self.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on(**kwargs)
        await self.coordinator.switch_low_price_charging_update(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        await self.coordinator.switch_low_price_charging_update(False)


class EVSmartChargingSwitchLowSocCharging(EVSmartChargingSwitch):
    """EV Smart Charging low SOC charging switch class."""

    _entity_key = ENTITY_KEY_LOW_SOC_CHARGING_SWITCH

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSwitchLowSocCharging.__init__()")
        super().__init__(entry, coordinator)
        if self.is_on is None:
            self._attr_is_on = False
            self.update_ha_state()
        self.coordinator.switch_low_soc_charging = self.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on(**kwargs)
        await self.coordinator.switch_low_soc_charging_update(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        await self.coordinator.switch_low_soc_charging_update(False)


class EVSmartChargingSwitchThreePhaseCharging(EVSmartChargingSwitch):
    """EV Smart Charging three phase charging switch class."""

    _entity_key = ENTITY_KEY_CONF_THREE_PHASE_CHARGING
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSwitchThreePhaseCharging.__init__()")
        super().__init__(entry, coordinator)
        if self.is_on is None:
            self._attr_is_on = False
            self.update_ha_state()
        self.coordinator.switch_three_phase_charging = self.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on(**kwargs)
        await self.coordinator.switch_three_phase_charging_update(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        await self.coordinator.switch_three_phase_charging_update(False)


class EVSmartChargingSwitchActivePriceCharging(EVSmartChargingSwitch):
    """EV Smart Charging active price charging switch class."""

    _entity_key = ENTITY_KEY_ACTIVE_PRICE_SWITCH

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSwitchActivePriceCharging.__init__()")
        super().__init__(entry, coordinator)
        if self.is_on is None:
            self._attr_is_on = True
            self.update_ha_state()
        self.coordinator.switch_active_price_charging = self.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on(**kwargs)
        await self.coordinator.switch_active_price_charging_update(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        await self.coordinator.switch_active_price_charging_update(False)


class EVSmartChargingSwitchActiveSolarCharging(EVSmartChargingSwitch):
    """EV Smart Charging active solar charging switch class."""

    _entity_key = ENTITY_KEY_ACTIVE_SOLAR_SWITCH

    def __init__(self, entry, coordinator: EVSmartChargingCoordinator):
        _LOGGER.debug("EVSmartChargingSwitchActiveSolarCharging.__init__()")
        super().__init__(entry, coordinator)
        if self.is_on is None:
            self._attr_is_on = False
            self.update_ha_state()
        self.coordinator.switch_active_solar_charging = self.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on(**kwargs)
        await self.coordinator.switch_active_solar_charging_update(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        await self.coordinator.switch_active_solar_charging_update(False)
