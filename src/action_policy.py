from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"


def _next_best_action(row: pd.Series) -> tuple[str, str]:
    if row["health_segment"] == "Critical" and row["clv"] >= row["clv_p75"]:
        return "Executive retention outreach", "High value account with critical risk"
    if row["health_segment"] == "Critical":
        return "Priority support callback", "Critical health segment"
    if row["health_segment"] == "At Risk" and row["sentiment_mean"] < -0.2:
        return "Proactive issue resolution", "Negative sentiment trend"
    if row["health_segment"] == "At Risk" and row["recency_days"] > 90:
        return "Targeted retention offer", "High recency and declining activity"
    if row["health_segment"] == "Healthy" and row["clv"] >= row["clv_p75"]:
        return "Upsell premium plan", "High value healthy customer"
    return "Automated check-in email", "Maintain engagement"


def _action_cost(action: str) -> float:
    costs = {
        "Executive retention outreach": 55.0,
        "Priority support callback": 25.0,
        "Proactive issue resolution": 22.0,
        "Targeted retention offer": 18.0,
        "Upsell premium plan": 12.0,
        "Automated check-in email": 3.0,
    }
    return costs.get(action, 10.0)


def _top_reason(row: pd.Series) -> str:
    reasons: list[str] = []
    if row["churn_probability"] >= 0.60:
        reasons.append("High churn probability")
    if row["sentiment_mean"] <= -0.2:
        reasons.append("Negative sentiment")
    if row["recency_days"] >= 90:
        reasons.append("Low purchase recency")
    if row["ticket_volume"] >= 6:
        reasons.append("High ticket volume")
    if row["social_mentions_count"] >= 6:
        reasons.append("High social complaint activity")
    return "; ".join(reasons[:3]) if reasons else "Stable behavior"


def _build_campaign_scenarios(actions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    valid = actions[actions["expected_net_value"] > 0].copy()

    for fraction in [0.05, 0.10, 0.20]:
        n = max(1, int(len(valid) * fraction))
        chunk = valid.nlargest(n, "priority_score")

        total_cost = float(chunk["final_action_cost"].sum())
        total_saved = float(chunk["expected_clv_saved"].sum())
        total_net = float(chunk["expected_net_value"].sum())

        rows.append(
            {
                "scenario": f"Top {int(fraction * 100)}%",
                "customers_targeted": int(len(chunk)),
                "total_action_cost": round(total_cost, 2),
                "expected_clv_saved": round(total_saved, 2),
                "expected_net_value": round(total_net, 2),
                "avg_expected_roi": round(float(chunk["expected_roi"].mean()), 4),
                "avg_churn_probability": round(float(chunk["churn_probability"].mean()), 4),
            }
        )

    return pd.DataFrame(rows)


def build_action_policy() -> tuple[pd.DataFrame, pd.DataFrame]:
    value = pd.read_csv(PROCESSED_DIR / "customer_value.csv")
    features = pd.read_csv(PROCESSED_DIR / "features.csv")

    df = value.merge(
        features[
            [
                "customer_id",
                "recency_days",
                "ticket_volume",
                "social_mentions_count",
                "sentiment_mean",
            ]
        ],
        on="customer_id",
        how="left",
    )

    df["clv_p75"] = float(df["clv"].quantile(0.75))

    actions = df.apply(_next_best_action, axis=1, result_type="expand")
    df["next_best_action"] = actions[0]
    df["action_reason"] = actions[1]

    df["final_action_cost"] = df["next_best_action"].map(_action_cost)
    # Priority balances risk, value, and confidence while penalizing very costly actions.
    confidence_weight = df["score_confidence"].map({"High": 1.0, "Medium": 0.85, "Low": 0.7}).fillna(0.8)
    df["priority_score"] = (
        (df["churn_probability"] * 0.45)
        + (df["expected_net_value"].clip(lower=0) / max(float(df["expected_net_value"].max()), 1.0) * 0.35)
        + (confidence_weight * 0.20)
        - (df["final_action_cost"] / max(float(df["final_action_cost"].max()), 1.0) * 0.10)
    )

    df["top_driver"] = df.apply(_top_reason, axis=1)

    customer_actions = df[
        [
            "customer_id",
            "health_segment",
            "health_score",
            "churn_probability",
            "clv",
            "expected_clv_saved",
            "expected_net_value",
            "expected_roi",
            "score_confidence",
            "next_best_action",
            "action_reason",
            "top_driver",
            "final_action_cost",
            "priority_score",
        ]
    ].sort_values("priority_score", ascending=False)

    campaign_scenarios = _build_campaign_scenarios(customer_actions)

    customer_actions.to_csv(PROCESSED_DIR / "customer_actions.csv", index=False)
    campaign_scenarios.to_csv(PROCESSED_DIR / "campaign_scenarios.csv", index=False)

    print(f"Saved customer_actions.csv with {len(customer_actions)} customers")
    print(f"Saved campaign_scenarios.csv with {len(campaign_scenarios)} scenarios")

    return customer_actions, campaign_scenarios


if __name__ == "__main__":
    build_action_policy()
