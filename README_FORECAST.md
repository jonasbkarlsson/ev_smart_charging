# Incorporating Forecasted/Predicted Price Data into EV Smart Charging

This guide explains how to enhance the [EV Smart Charging](https://github.com/hesmisch/ev_smart_charging) integration to support multi-day price forecasts using the EPEX Predictor service.

## 1. Prerequisites (Updated Integration)

You must use a version of the `ev_smart_charging` integration that supports raw data processing with custom attributes. 

**Key changes required in the integration code:**
- **`helpers/raw.py`**: The `convert_raw_item` function must be updated to preserve all dictionary attributes (like a `predicted: true/false` flag) instead of only extracting `start` and `value`.
- **`coordinator.py`**: The price ingestion logic must be capable of handling dates beyond tomorrow if the price sensor provides them.

## 2. Create the Forecast Sensor (Sensor YYY)

Add a REST sensor to fetch data from the EPEX Predictor API. This service provides 5-day forecasts for various European regions.

### Configuration (`configuration.yaml`)

```yaml
sensor:
  - platform: rest
    resource: "https://epexpredictor.batzill.com/prices_short?country=NL&fixedPrice=11.207&taxPercent=21&unit=EUR_PER_KWH&hours=120"
    method: GET
    unique_id: epex_price_prediction
    name: "EPEX Price Prediction"
    unit_of_measurement: €/kWh
    value_template: "{{ value_json.t[0] }}" # Current price
    json_attributes:
      - s # Timestamps (UNIX)
      - t # Prices
```

### URL Parameter Details:
- **`country`**: Your region (e.g., `NL`, `DE`, `BE`, `FR`).
- **`fixedPrice`**: Fixed costs or transport fees in your region (in the unit specified).
- **`taxPercent`**: VAT percentage to be added to the market price.
- **`unit`**: The price unit (e.g., `EUR_PER_KWH`, `CT_PER_KWH`).
- **`hours`**: How many hours of forecast to retrieve (e.g., `120` for 5 days).

## 3. Create the Combined Chart Sensor (Sensor XXX)

Create a template sensor that merges your actual EPEX Spot data with the forecasted data. This sensor ensures a seamless transition from real-time prices to predictions.

### Configuration (`configuration.yaml`)

```yaml
template:
  - sensor:
      - name: EPEX Chart Data
        unique_id: epex_chart_data
        unit_of_measurement: "ct/kWh"
        state: >-
          {%- set actual_data = state_attr('sensor.epex_spot_data_total_price', 'data') | default([], true) -%}
          {%- set pred_timestamps = state_attr('sensor.epex_price_prediction', 's') | default([], true) -%}
          {{ (actual_data | length) + (pred_timestamps | length) }}
        attributes:
          data: >-
            {# Merges all historical and future data for the main chart #}
            {%- set actual_data = state_attr('sensor.epex_spot_data_total_price', 'data') | default([], true) -%}
            {%- set pred_timestamps = state_attr('sensor.epex_price_prediction', 's') | default([], true) -%}
            {%- set pred_prices = state_attr('sensor.epex_price_prediction', 't') | default([], true) -%}
            {%- set ns = namespace(entries=[], result=[]) -%}
            {%- for item in actual_data -%}
              {%- set start = as_datetime(item['start_time']) -%}
              {%- if start -%}
                {%- set price = (item | dictsort | selectattr('0', 'ne', 'start_time') | selectattr('0', 'ne', 'end_time') | map(attribute='1') | reject('none') | map('float') | list | first) -%}
                {%- set ns.entries = ns.entries + [{'ts': as_timestamp(start) | int, 'price': (price * 100) | round(2), 'predicted': false}] -%}
              {%- endif -%}
            {%- endfor -%}
            {%- set actual_ts = ns.entries | map(attribute='ts') | list -%}
            {%- for i in range(pred_timestamps | length) -%}
              {%- set ts = pred_timestamps[i] | int -%}
              {%- if ts not in actual_ts -%}
                {%- set ns.entries = ns.entries + [{'ts': ts, 'price': (pred_prices[i] * 100) | round(2), 'predicted': true}] -%}
              {%- endif -%}
            {%- endfor -%}
            {%- for entry in ns.entries | sort(attribute='ts') -%}
              {%- set ns.result = ns.result + [{'x': entry.ts * 1000, 'y': entry.price, 'time': (entry.ts | timestamp_custom('%Y-%m-%dT%H:%M:%S%z', true)), 'price': entry.price, 'predicted': entry.predicted}] -%}
            {%- endfor -%}
            {{- ns.result -}}
          prices_today: >-
            {# Provides the full today's list (actual + predicted if epex is missing) #}
            {# Implementation details similar to 'data' but filtered for today.date() #}
          prices_tomorrow: >-
            {# Provides all future data for the scheduler (not limited to tomorrow) #}
            {# Filtered for start.date() >= (now() + timedelta(days=1)).date() #}
```

## 4. Update EV Smart Charging Configuration

Finally, inform the integration to use your new combined sensor as its price source.

1. Go to **Settings** -> **Devices & Services**.
2. Find the **EV Smart Charging** integration.
3. Click **Configure**.
4. Change the **Price sensor** key to `sensor.epex_chart_data`.
5. Ensure the **Price unit** matches what your sensor provides (e.g., `ct/kWh`).

## 5. (Optional) Visualizing in ApexCharts

To see the difference between actual and predicted prices, use a configuration that splits the series:

```yaml
type: custom:apexcharts-card
series:
  - entity: sensor.ev_smart_charging_charging
    name: Actual Price
    data_generator: >
      return entity.attributes.raw_two_days.filter(e => !e.predicted).map(e => [new Date(e.start), e.value]);
  - entity: sensor.ev_smart_charging_charging
    name: Predicted Price
    data_generator: >
      const all = entity.attributes.raw_two_days;
      const actuals = all.filter(e => !e.predicted);
      const preds = all.filter(e => e.predicted);
      if (actuals.length > 0 && preds.length > 0) preds.unshift(actuals[actuals.length - 1]);
      return preds.map(e => [new Date(e.start), e.value]);
    stroke:
      dashArray: 5
```
