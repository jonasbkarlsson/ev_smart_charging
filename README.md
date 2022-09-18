# EV Smart Charging

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

The EV Smart Charging integration will automatically charge the EV when the electricity price is the lowest. The integration requires the [Nordpool](https://github.com/custom-components/nordpool) integration, and can automatically detect the integrations [Volkswagen We Connect ID](https://github.com/mitch-dc/volkswagen_we_connect_id) and [OCPP](https://github.com/lbbrhzn/ocpp). Integrations for other car makers and charger makers can be used with manual configurations.

## Installation

### HACS
1. In Home Assistant go to "HACS" -> "Integrations". Click on the three dots in the upper-right corner and select "Custom repositories". Paste [ev_smart_charging] into the Repository field. In "Category" select "Integration". Click on "ADD".
2. In Home Assistant go to "HACS" -> "Integrations". Click on "+ Explore & Download Repositories" and search for "EV Smart Charging".
3. In Home Assistant go to "Settings" -> "Devices & Services" -> "Integrations" click "+ Add integration" and search for "EV Smart Charging".

### Manual

1. Using the tool of choice open the directory (folder) for your Home Assistant configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `ev_smart_charging`.
4. Download _all_ the files from the `custom_components/ev_smart_charging/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant.
7. In Home Assistant go to "Settings" -> "Devices & Services" -> "Integrations" click "+ Add integration" and search for "EV Smart Charging".

## Configuration

The configuration is done in the Home Assistant user interface.

The first form contains the entities that the integration is interacting with.
Parameter | Required | Description
-- | -- | --
Nordpool entity | Yes | Sensor entity to the Nordpool integration.
EV SOC entity | Yes | Sensor entity with the car's State-of-Charge. A value between 0 and 100.
EV target SOC entity | No | Entity with the target value for the State-of-Charge. A value between 0 and 100. If not provided, 100 is assumed.
Charger entity | No | If provided, the integration will set the state of this entity to 'on' and 'off'.

The second form contain parameters that affects how the charging will be done.
Parameter | Required | Description
-- | -- | --
Percent per hour | Yes | The charging speed expressed as percent per hour.
Departure time | Yes | The lastest time tomorrow for the charging to reach the target State-of-Charge.
Electricity price limit | No | If provided, charging will not be performed during hours when the electricity price is above this limit. NOTE that this might lead to the car not being charged to the target State-of-Charge.

![Setup](images/setup.png)

## Sensor

![Sensor](images/sensor.png)

[ev_smart_charging]: https://github.com/jonasbkarlsson/ev_smart_charging
[releases-shield]: https://img.shields.io/github/v/release/jonasbkarlsson/ev_smart_charging?style=for-the-badge
[releases]: https://github.com/jonasbkarlsson/ev_smart_charging/releases
[license-shield]: https://img.shields.io/github/license/jonasbkarlsson/ev_smart_charging?style=for-the-badge
[license]: https://github.com/jonasbkarlsson/ev_smart_charging/blob/main/LICENSE
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Jonas%20Karlsson%20@jonasbkarlsson-41BDF5.svg?style=for-the-badge
[user_profile]: https://github.com/jonasbkarlsson
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[buymecoffee]: https://www.buymeacoffee.com/jonasbkarlsson
