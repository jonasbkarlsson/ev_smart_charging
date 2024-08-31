"""SolarCharging class"""

import logging
import math

from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt

from custom_components.ev_smart_charging.const import (
    CHARGING_STATUS_DISCONNECTED,
    CHARGING_STATUS_NOT_ACTIVE,
    CONF_GRID_VOLTAGE,
    SOLAR_CHARGING_STATUS_CHARGING,
    SOLAR_CHARGING_STATUS_CHARGING_COMPLETED,
    SOLAR_CHARGING_STATUS_NOT_ACTIVATED,
    SOLAR_CHARGING_STATUS_WAITING,
)
from custom_components.ev_smart_charging.helpers.general import get_parameter
from custom_components.ev_smart_charging.sensor import (
    EVSmartChargingSensorChargingCurrent,
    EVSmartChargingSensorSolarStatus,
)


_LOGGER = logging.getLogger(__name__)


class SolarCharging:
    """SolarCharging class"""

    def __init__(
        self,
        config_entry: ConfigEntry,
    ) -> None:
        self.grid_usage = 0
        self.grid_usage_timestamp = dt.now().timestamp()
        self.grid_voltage = float(get_parameter(config_entry, CONF_GRID_VOLTAGE))
        self.charging_activated = False
        self.solar_charging_activated = False
        self.ev_connected = False
        self.number_of_phases = 1
        self.min_charging_current = 6
        self.max_charging_current = 16
        self.solar_charging_off_delay = 5
        self.current_charging_amps = 0
        self.low_power_timestamp = dt.now().timestamp() - 100000  # Long time ago
        self.sensor_charging_current = None
        self.sensor_solar_status = None
        self.pacing_time = 10
        self.ev_soc = 0
        self.target_ev_soc = 100
        self.solar_charging = False

    def set_charging_current_sensor(
        self, sensor_charging_current: EVSmartChargingSensorChargingCurrent
    ) -> None:
        """Store sensor."""
        self.sensor_charging_current = sensor_charging_current

    def set_solar_status_sensor(
        self, sensor_solar_status: EVSmartChargingSensorSolarStatus
    ) -> None:
        """Store sensor."""
        self.sensor_solar_status = sensor_solar_status
        self.sensor_solar_status.set_status(SOLAR_CHARGING_STATUS_WAITING)

    def update_solar_status(self) -> None:
        """Update solar charging status"""
        if self.sensor_solar_status and self.sensor_charging_current:
            current_solar_status = self.sensor_solar_status.state
            new_solar_status = current_solar_status
            if not self.charging_activated:
                new_solar_status = CHARGING_STATUS_NOT_ACTIVE
            else:
                if not self.solar_charging_activated:
                    new_solar_status = SOLAR_CHARGING_STATUS_NOT_ACTIVATED
                else:
                    if not self.ev_connected:
                        new_solar_status = CHARGING_STATUS_DISCONNECTED
                    else:
                        if self.ev_soc >= self.target_ev_soc:
                            new_solar_status = SOLAR_CHARGING_STATUS_CHARGING_COMPLETED
                        else:
                            if self.solar_charging:
                                new_solar_status = SOLAR_CHARGING_STATUS_CHARGING
                            else:
                                new_solar_status = SOLAR_CHARGING_STATUS_WAITING

            if new_solar_status != current_solar_status:
                if new_solar_status in [
                    SOLAR_CHARGING_STATUS_NOT_ACTIVATED,
                    CHARGING_STATUS_DISCONNECTED,
                    SOLAR_CHARGING_STATUS_CHARGING_COMPLETED,
                    CHARGING_STATUS_NOT_ACTIVE,
                ]:
                    new_charging_amps = 0.0
                    self.sensor_charging_current.set_charging_current(new_charging_amps)
                    self.current_charging_amps = new_charging_amps
                    self.solar_charging = False
                self.sensor_solar_status.set_status(new_solar_status)

    def update_configuration(
        self,
        charging_activated: bool,
        solar_charging_activated: bool,
        ev_connected: bool,
        number_of_phases: int,
        min_charging_current: float,
        max_charging_current: float,
        solar_charging_off_delay: float,
    ) -> None:
        """Update configuration"""
        _LOGGER.debug(
            "update_configuration().= %s %s %s %s %s %s %s",
            str(charging_activated),
            str(solar_charging_activated),
            str(ev_connected),
            str(number_of_phases),
            str(min_charging_current),
            str(max_charging_current),
            str(solar_charging_off_delay),
        )
        self.charging_activated = charging_activated
        self.solar_charging_activated = solar_charging_activated
        self.ev_connected = ev_connected
        self.number_of_phases = number_of_phases
        self.min_charging_current = min_charging_current
        self.max_charging_current = max_charging_current
        self.solar_charging_off_delay = solar_charging_off_delay
        self.update_solar_status()

    def update_ev_soc(self, ev_soc: float) -> None:
        """Update EV SOC"""
        self.ev_soc = ev_soc
        self.update_solar_status()

    def update_target_ev_soc(self, target_ev_soc: float) -> None:
        """Update target EV SOC"""
        self.target_ev_soc = target_ev_soc
        self.update_solar_status()

    def update_grid_usage(self, grid_usage: float) -> None:
        """New value of grid usage received"""
        timestamp = dt.now().timestamp()
        # Don't update charging current more than once per 10 seconds
        if (
            self.charging_activated
            and self.solar_charging_activated
            and self.ev_connected
            and self.sensor_charging_current
            and self.sensor_solar_status
            and (timestamp - self.grid_usage_timestamp) >= self.pacing_time
            and self.ev_soc < self.target_ev_soc
        ):

            self.pacing_time = 10
            self.grid_usage_timestamp = timestamp
            self.grid_usage = grid_usage

            available_amps = (
                -self.grid_usage / self.grid_voltage
            ) / self.number_of_phases
            proposed_charging_amps = available_amps + self.current_charging_amps
            new_charging_amps = math.floor(
                min(
                    max(proposed_charging_amps, self.min_charging_current),
                    self.max_charging_current,
                )
            )

            if proposed_charging_amps >= self.min_charging_current:
                self.low_power_timestamp = None

            if proposed_charging_amps < self.min_charging_current:
                timestamp = dt.now().timestamp()
                if not self.low_power_timestamp:
                    self.low_power_timestamp = timestamp
                if (timestamp - self.low_power_timestamp) > (
                    60 * self.solar_charging_off_delay
                ):
                    # Too low solar power for too long time
                    _LOGGER.debug("Too low solar power for too long time.")
                    new_charging_amps = 0

            if new_charging_amps != self.current_charging_amps:
                _LOGGER.debug(
                    "set_charging_current(new_charging_amps) = %s",
                    new_charging_amps,
                )
                self.sensor_charging_current.set_charging_current(new_charging_amps)
                if new_charging_amps == 0:
                    self.solar_charging = False
                else:
                    self.solar_charging = True
                    if self.current_charging_amps == 0:
                        # Wait longer to update after turning on charger.
                        self.pacing_time = 30
                self.current_charging_amps = new_charging_amps
                self.update_solar_status()
