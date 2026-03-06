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

Total Action Cost = SUM(CustomerValue[intervention_cost])

Cost per Saved Customer =
DIVIDE(
    [Total Action Cost],
    CALCULATE(
        DISTINCTCOUNT(CustomerValue[customer_id]),
        CustomerValue[expected_net_value] > 0
    ),
    0
)

High Confidence Net Value =
CALCULATE(
    [Expected Net Value],
    CustomerValue[score_confidence] = "High"
)

Critical Share % =
DIVIDE(
    [Critical Customers],
    [Total Customers],
    0
)

At Risk Share % =
DIVIDE(
    [At Risk Customers],
    [Total Customers],
    0
)

Top 10% Priority Net Value =
VAR NTop =
    INT(0.1 * COUNTROWS(ALLSELECTED(CustomerActions[customer_id])))
VAR TopRows =
    TOPN(
        NTop,
        ALLSELECTED(CustomerActions),
        CustomerActions[priority_score],
        DESC
    )
RETURN
    SUMX(TopRows, CustomerActions[expected_net_value])

Best Scenario Net Value =
MAX(CampaignScenarios[expected_net_value])

Best Scenario Label =
VAR BestValue = [Best Scenario Net Value]
RETURN
    CALCULATE(
        SELECTEDVALUE(CampaignScenarios[scenario]),
        FILTER(
            ALL(CampaignScenarios),
            CampaignScenarios[expected_net_value] = BestValue
        )
    )
```

## 4) Optional What-If parameter
For a budget slider in reports:
1. `Modeling` -> `New parameter` -> `Numeric range`.
2. Name: `Budget Param`, Min: `5000`, Max: `100000`, Increment: `5000`.
3. Create this measure:

```DAX
Budget Targeted Net Value =
VAR Budget = SELECTEDVALUE('Budget Param'[Budget Param Value], 25000)
VAR Ranked =
    ADDCOLUMNS(
        ALLSELECTED(CustomerActions),
        "_rank", RANKX(ALLSELECTED(CustomerActions), CustomerActions[priority_score], , DESC),
        "_cost", CustomerActions[final_action_cost]
    )
VAR WithCumCost =
    ADDCOLUMNS(
        Ranked,
        "_cum_cost",
            SUMX(
                FILTER(Ranked, [_rank] <= EARLIER([_rank])),
                [_cost]
            )
    )
VAR SelectedRows = FILTER(WithCumCost, [_cum_cost] <= Budget)
RETURN
    SUMX(SelectedRows, CustomerActions[expected_net_value])
```

## 5) Build dashboard pages (exact blueprint)

Use a 16:9 canvas and keep visual titles enabled for executive readability.

### Page A: Executive Summary
- Top row cards (left to right):
  - `Total Customers`
  - `Avg Health Score`
  - `Expected Net Value`
  - `Campaign ROI`
  - `High Confidence Net Value`
- Left panel visual: donut with `HealthScores[health_segment]` by distinct `customer_id`.
- Center panel visual: clustered column by `CampaignScenarios[scenario]` with:
  - `expected_net_value`
  - `total_action_cost`
- Right panel visual: KPI card pair:
  - `Best Scenario Label`
  - `Best Scenario Net Value`
- Bottom strip slicers:
  - `HealthScores[health_segment]`
  - `CustomerValue[score_confidence]`
  - `CustomerActions[next_best_action]`

### Page B: Intervention Planner
- Main table (full width):
  - `customer_id`
  - `health_segment`
  - `score_confidence`
  - `churn_probability`
  - `next_best_action`
  - `top_driver`
  - `expected_net_value`
  - `priority_score`
  - Sort by `priority_score` descending.
- Left chart: bar chart by `next_best_action` with `SUM(expected_net_value)`.
- Right chart: scatter from `CustomerActions`:
  - X: `final_action_cost`
  - Y: `expected_net_value`
  - Size: `clv`
  - Legend: `health_segment`
- Cards above table:
  - `Top 10% Priority Net Value`
  - `Cost per Saved Customer`

### Page C: Risk and Explainability
- Left: histogram of `HealthScores[health_score]`.
- Center: decomposition tree:
  - Analyze: `SUM(CustomerActions[expected_net_value])`
  - Explain by: `health_segment`, `score_confidence`, `next_best_action`, `top_driver`.
- Right top cards:
  - `Critical Customers`
  - `Critical Share %`
  - `At Risk Share %`
- Right bottom: matrix
  - Rows: `health_segment`
  - Columns: `score_confidence`
  - Values: `AVG(expected_net_value)`

### Page D: Budget Simulator (optional but differentiator)
- Add slicer with `Budget Param`.
- Cards:
  - `Budget Param Value`
  - `Budget Targeted Net Value`
  - `Campaign ROI`
- Line chart:
  - Axis: `CampaignScenarios[scenario]`
  - Values: `expected_net_value`
- Supporting table from `CampaignScenarios`:
  - `scenario`, `customers_targeted`, `total_action_cost`, `expected_clv_saved`, `expected_net_value`, `avg_expected_roi`

## 6) What a good result looks like
- High `Expected Net Value` while keeping action cost controlled.
- `Top 5%` scenario should usually have strongest ROI.
- Action table should show clear business reasons (`top_driver`) for prioritization.
- High-confidence bucket should retain a meaningful share of total net value.
- Budget simulator should show monotonic gains with diminishing returns (not random oscillation).

## 7) Refresh flow
After running pipeline again:
1. In Power BI: `Home` -> `Refresh`.
2. Verify row counts in `CustomerActions` and `CampaignScenarios` changed accordingly.
