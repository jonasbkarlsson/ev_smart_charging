# EV Smart Charger

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

The EV Smart Charinger integration TBD.

## Installation

### HACS
1. In HA UI go to "HACS" -> "Integrations". Click on the three dots in the upper-right corner and select "Custom repositories". Paste [ev_smart_charging] into the Repository field. In "Category" select "Integration". Click on "ADD".
2. In HA UI go to "HACS" -> "Integrations". Click on "+ Explore & Download Repositories" and search for "EV Smart Charging".
3. In the HA UI go to "Settings" -> "Devices & Services" -> "Integrations" click "+ Add integration" and search for "EV Smart Charging".

### Manual

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `ev_smart_charging`.
4. Download _all_ the files from the `custom_components/ev_smart_charging/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Settings" -> "Devices & Services" -> "Integrations" click "+ Add integration" and search for "EV Smart Charging".

## Configuration

The configuration is done in the UI.

![Setup](images/setup.png)

## Sensor

![Sensor](images/sensor.png)

## Contributions

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

[ev_smart_charging]: https://github.com/jonasbkarlsson/ev_smart_charging
[releases-shield]: https://img.shields.io/github/v/release/jonasbkarlsson/ev_smart_charging?style=for-the-badge
[releases]: https://github.com/jonasbkarlsson/ev_smart_charging/releases
[license-shield]: https://img.shields.io/github/license/jonasbkarlsson/ev_smart_charging?style=for-the-badge
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Jonas%20Karlsson%20@jonasbkarlsson-blue.svg?style=for-the-badge
[user_profile]: https://github.com/jonasbkarlsson
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[buymecoffee]: https://www.buymeacoffee.com/jonasbkarlsson
