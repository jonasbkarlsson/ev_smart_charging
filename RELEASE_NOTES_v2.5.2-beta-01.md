## v2.5.2-beta-01

### Highlights
- Integrated built-in EPEX Predictor support into EV Smart Charging scheduling and dashboard data flow.
- Added automatic unit-scale normalization for predicted prices when live and predicted magnitudes differ (for example EUR/kWh vs ct/kWh), to avoid 100x chart mismatches.
- Improved dynamic dashboard examples and chart range behavior based on available `raw_two_days` data.

### Configuration & Docs
- Updated README with predictor-specific config flow/options parameters:
  - EPEX Predictor country code
  - EPEX Predictor fixed price
  - EPEX Predictor tax percent
  - EPEX Predictor unit
- Clarified that predictor parameters are used when `switch.ev_smart_charging_use_predicted_epex_data` is enabled.
- Added a reference to the EpexPredictor project for model/input details.

### Thanks
- Thanks to [b3nn0](https://github.com/b3nn0) for EpexPredictor.
- EpexPredictor project: https://github.com/b3nn0/EpexPredictor
