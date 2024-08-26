"""SolarCharging class"""

import logging
import math

from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt

from custom_components.ev_smart_charging.const import (
    CHARGING_STATUS_DISCONNECTED,
    CONF_GRID_VOLTAGE,
    SOLAR_CHARGING_STATUS_CHARGING,
    SOLAR_CHARGING_STATUS_CHARGING_COMPLETED,
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

    def update_configuration(
        self,
        ev_connected: bool,
        number_of_phases: int,
        min_charging_current: float,
        max_charging_current: float,
        solar_charging_off_delay: float,
    ) -> None:
        """Update configuration"""
        _LOGGER.debug(
            "update_configuration().= %s %s %s %s %s",
            str(ev_connected),
            str(number_of_phases),
            str(min_charging_current),
            str(max_charging_current),
            str(solar_charging_off_delay),
        )
        self.ev_connected = ev_connected
        self.number_of_phases = number_of_phases
        self.min_charging_current = min_charging_current
        self.max_charging_current = max_charging_current
        self.solar_charging_off_delay = solar_charging_off_delay
        if self.sensor_solar_status and self.sensor_charging_current:
            if (
                self.ev_connected
                and self.sensor_solar_status.state == CHARGING_STATUS_DISCONNECTED
            ):
                if self.ev_soc >= self.target_ev_soc:
                    self.sensor_solar_status.set_status(
                        SOLAR_CHARGING_STATUS_CHARGING_COMPLETED
                    )
                else:
                    self.sensor_solar_status.set_status(SOLAR_CHARGING_STATUS_WAITING)

            if (
                not self.ev_connected
                and self.sensor_solar_status.state != CHARGING_STATUS_DISCONNECTED
            ):
                self.sensor_solar_status.set_status(CHARGING_STATUS_DISCONNECTED)
                new_charging_amps = 0.0
                self.sensor_charging_current.set_charging_current(new_charging_amps)
                self.current_charging_amps = new_charging_amps
                self.solar_charging = False

    def check_if_charging_completed(self) -> None:
        """Check if target EV SOC has been reached"""
        if self.ev_soc >= self.target_ev_soc and self.solar_charging:
            new_charging_amps = 0.0
            self.sensor_charging_current.set_charging_current(new_charging_amps)
            self.current_charging_amps = new_charging_amps
            self.solar_charging = False
            self.sensor_solar_status.set_status(
                SOLAR_CHARGING_STATUS_CHARGING_COMPLETED
            )

    def update_ev_soc(self, ev_soc: float) -> None:
        """Update EV SOC"""
        self.ev_soc = ev_soc
        self.check_if_charging_completed()

    def update_target_ev_soc(self, target_ev_soc: float) -> None:
        """Update target EV SOC"""
        self.target_ev_soc = target_ev_soc
        self.check_if_charging_completed()

    def update_grid_usage(self, grid_usage: float) -> None:
        """New value of grid usage received"""
        timestamp = dt.now().timestamp()
        # Don't update charging current more than once per 10 seconds
        if (
            timestamp - self.grid_usage_timestamp
        ) >= self.pacing_time and self.ev_soc < self.target_ev_soc:
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
            if not self.ev_connected:
                new_charging_amps = 0

            if new_charging_amps != self.current_charging_amps:
                if self.sensor_charging_current:
                    _LOGGER.debug(
                        "set_charging_current(new_charging_amps) = %s",
                        new_charging_amps,
                    )
                    self.sensor_charging_current.set_charging_current(new_charging_amps)
                    if self.sensor_solar_status:
                        if new_charging_amps == 0:
                            self.solar_charging = False
                            if self.ev_connected:
                                self.sensor_solar_status.set_status(
                                    SOLAR_CHARGING_STATUS_WAITING
                                )
                            else:
                                self.sensor_solar_status.set_status(
                                    CHARGING_STATUS_DISCONNECTED
                                )
                        else:
                            self.solar_charging = True
                            self.sensor_solar_status.set_status(
                                SOLAR_CHARGING_STATUS_CHARGING
                            )
                            if self.current_charging_amps == 0:
                                # Wait longer to update after turning on charger.
                                self.pacing_time = 30
                self.current_charging_amps = new_charging_amps
