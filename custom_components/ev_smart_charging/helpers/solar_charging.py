"""SolarCharging class"""

import logging
import math

from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt

from custom_components.ev_smart_charging.const import (
    CONF_GRID_VOLTAGE,
    SOLAR_CHARGING_STATUS_CHARGING,
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
        number_of_phases: int,
        min_charging_current: float,
        max_charging_current: float,
        solar_charging_off_delay: float,
    ) -> None:
        self.grid_usage = 0
        self.grid_usage_timestamp = dt.now().timestamp()
        self.grid_voltage = float(get_parameter(config_entry, CONF_GRID_VOLTAGE))
        self.number_of_phases = number_of_phases
        self.min_charging_current = min_charging_current
        self.max_charging_current = max_charging_current
        self.solar_charging_off_delay = solar_charging_off_delay
        self.current_charging_amps = 0
        self.low_power_timestamp = dt.now().timestamp() - 100000  # Long time ago
        self.sensor_charging_current = None
        self.sensor_solar_status = None

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

    def update_configuration(
        self,
        number_of_phases: int,
        min_charging_current: float,
        max_charging_current: float,
        solar_charging_off_delay: float,
    ) -> None:
        """Update configuration"""
        _LOGGER.debug(
            "update_configuration().number_of_phases = %s", str(number_of_phases)
        )
        self.number_of_phases = number_of_phases
        self.min_charging_current = min_charging_current
        self.max_charging_current = max_charging_current
        self.solar_charging_off_delay = solar_charging_off_delay

    def update_grid_usage(self, grid_usage: float) -> None:
        """New value of grid usage received"""
        timestamp = dt.now().timestamp()
        # Don't update charging current more than once per 10 seconds
        if (timestamp - self.grid_usage_timestamp) >= 10:
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
                if self.sensor_charging_current:
                    _LOGGER.debug(
                        "set_charging_current(new_charging_amps) = %s",
                        new_charging_amps,
                    )
                    self.sensor_charging_current.set_charging_current(new_charging_amps)
                    if self.sensor_solar_status:
                        if new_charging_amps == 0:
                            self.sensor_solar_status.set_status(
                                SOLAR_CHARGING_STATUS_WAITING
                            )
                        else:
                            self.sensor_solar_status.set_status(
                                SOLAR_CHARGING_STATUS_CHARGING
                            )
                self.current_charging_amps = new_charging_amps
