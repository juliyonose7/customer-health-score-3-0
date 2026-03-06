from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"


def _confidence_bucket(signal_volume: pd.Series) -> pd.Series:
    q1 = float(signal_volume.quantile(0.33))
    q2 = float(signal_volume.quantile(0.66))
    return pd.Series(
        np.where(signal_volume >= q2, "High", np.where(signal_volume >= q1, "Medium", "Low")),
        index=signal_volume.index,
    )


def build_expected_value() -> pd.DataFrame:
    health = pd.read_csv(PROCESSED_DIR / "health_scores.csv")
    features = pd.read_csv(PROCESSED_DIR / "features.csv")

    df = health.merge(
        features[["customer_id", "ticket_volume", "social_mentions_count"]],
        on="customer_id",
        how="left",
    )

    cost_map = {"Critical": 45.0, "At Risk": 20.0, "Healthy": 8.0}
    df["intervention_cost"] = df["health_segment"].map(cost_map).fillna(15.0)

    base_uplift = {
        "Critical": 0.22,
        "At Risk": 0.16,
        "Healthy": 0.06,
    }
    df["retention_uplift_prob"] = df["health_segment"].map(base_uplift).fillna(0.10)

    # Positive sentiment slightly lowers intervention gain and negative sentiment increases gain potential.
    sentiment_adjust = (-df["sentiment_mean"].fillna(0.0) * 0.10).clip(-0.05, 0.08)
    df["retention_uplift_prob"] = (df["retention_uplift_prob"] + sentiment_adjust).clip(0.02, 0.45)

    df["expected_clv_saved"] = (
        df["churn_probability"].fillna(0.0) * df["retention_uplift_prob"] * df["clv"].fillna(0.0)
    )
    df["expected_net_value"] = df["expected_clv_saved"] - df["intervention_cost"]
    df["expected_roi"] = np.where(
        df["intervention_cost"] > 0,
        df["expected_net_value"] / df["intervention_cost"],
        0.0,
    )

    signal_volume = (
        df["ticket_volume"].fillna(0.0)
        + df["social_mentions_count"].fillna(0.0)
        + df["frequency"].fillna(0.0)
    )
    df["score_confidence"] = _confidence_bucket(signal_volume)

    out_cols = [
        "customer_id",
        "health_segment",
        "health_score",
        "churn_probability",
        "clv",
        "intervention_cost",
        "retention_uplift_prob",
        "expected_clv_saved",
        "expected_net_value",
        "expected_roi",
        "score_confidence",
    ]

    out = df[out_cols].sort_values("expected_net_value", ascending=False)
    out.to_csv(PROCESSED_DIR / "customer_value.csv", index=False)
    print(f"Saved customer_value.csv with {len(out)} customers")
    return out


if __name__ == "__main__":
    build_expected_value()
