## v2.5.2-beta-01

## Changes
- Integrated built-in EPEX Predictor support into EV Smart Charging scheduling and dashboard data flow.
- Added automatic unit-scale normalization for predicted prices when live and predicted magnitudes differ (for example EUR/kWh vs ct/kWh), to avoid 100x chart mismatches.
- Improved dynamic dashboard examples and chart range behavior based on available `raw_two_days` data.
- Updated README with predictor-specific config flow/options parameters: EPEX Predictor country code, fixed price, tax percent, and unit.
- Clarified that predictor parameters are used when `switch.ev_smart_charging_use_predicted_epex_data` is enabled.
- Added a reference to EpexPredictor for model/input details: https://github.com/b3nn0/EpexPredictor.
- Thanks to [b3nn0](https://github.com/b3nn0) for EpexPredictor.
