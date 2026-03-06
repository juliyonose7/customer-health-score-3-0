# Power BI Setup Guide

This guide turns the exported workbook into a decision-oriented dashboard.

## 1) Open data source
1. Open Power BI Desktop.
2. `Get data` -> `Excel workbook`.
3. Select `data/processed/power_bi_export.xlsx`.
4. Load these sheets:
   - `HealthScores`
   - `ModelMetrics`
   - `CustomerValue`
   - `CustomerActions`
   - `CampaignScenarios`
   - `TransactionsSummary`

## 2) Model relationships
Create relationships (single direction is enough):
- `HealthScores[customer_id]` -> `CustomerValue[customer_id]`
- `HealthScores[customer_id]` -> `CustomerActions[customer_id]`
- `HealthScores[customer_id]` -> `TransactionsSummary[customer_id]`

## 3) Create DAX measures
Add these measures in Power BI:

```DAX
Total Customers = DISTINCTCOUNT(HealthScores[customer_id])

Avg Health Score = AVERAGE(HealthScores[health_score])

At Risk Customers =
CALCULATE(
    DISTINCTCOUNT(HealthScores[customer_id]),
    HealthScores[health_segment] = "At Risk"
)

Critical Customers =
CALCULATE(
    DISTINCTCOUNT(HealthScores[customer_id]),
    HealthScores[health_segment] = "Critical"
)

Expected Net Value = SUM(CustomerValue[expected_net_value])

Expected CLV Saved = SUM(CustomerValue[expected_clv_saved])

Campaign ROI =
DIVIDE(
    SUM(CustomerValue[expected_net_value]),
    SUM(CustomerValue[intervention_cost]),
    0
)
```

## 4) Build dashboard pages

### Page A: Health & Risk Overview
- Card: `Total Customers`
- Card: `Avg Health Score`
- Card: `At Risk Customers`
- Card: `Critical Customers`
- Donut: `health_segment` by count of `customer_id`
- Histogram/column: health score distribution

### Page B: Action Center
- Table visual from `CustomerActions`:
  - `customer_id`, `health_segment`, `churn_probability`, `next_best_action`, `top_driver`, `expected_net_value`, `priority_score`
- Sort by `priority_score` desc.
- Add slicers: `health_segment`, `score_confidence`, `next_best_action`.

### Page C: Economic Impact
- Cards:
  - `Expected CLV Saved`
  - `Expected Net Value`
  - `Campaign ROI`
- Clustered column chart from `CampaignScenarios`:
  - Axis: `scenario`
  - Values: `expected_net_value`, `total_action_cost`
- Scatter plot from `CustomerValue`:
  - X: `intervention_cost`
  - Y: `expected_net_value`
  - Size: `clv`
  - Legend: `health_segment`

## 5) What a good result looks like
- High `Expected Net Value` while keeping action cost controlled.
- `Top 5%` scenario should usually have strongest ROI.
- Action table should show clear business reasons (`top_driver`) for prioritization.

## 6) Refresh flow
After running pipeline again:
1. In Power BI: `Home` -> `Refresh`.
2. Verify row counts in `CustomerActions` and `CampaignScenarios` changed accordingly.
