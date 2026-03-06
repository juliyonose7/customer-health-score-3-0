from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"


def _minmax(series: pd.Series) -> pd.Series:
    s_min = float(series.min())
    s_max = float(series.max())
    if s_max == s_min:
        return pd.Series(0.5, index=series.index)
    return (series - s_min) / (s_max - s_min)


def build_health_score() -> pd.DataFrame:
    features = pd.read_csv(PROCESSED_DIR / "features.csv")
    predictions = pd.read_csv(PROCESSED_DIR / "model_predictions.csv")

    df = features.merge(predictions[["customer_id", "churn_probability"]], on="customer_id", how="left")

    churn_component = 1.0 - df["churn_probability"].fillna(df["churned"])

    sentiment_component = _minmax(df["sentiment_mean"].fillna(0))
    recency_component = 1.0 - _minmax(df["recency_days"].fillna(df["recency_days"].median()))
    frequency_component = _minmax(df["frequency"].fillna(0))
    monetary_component = _minmax(df["monetary_avg"].fillna(0))

    rfm_component = 0.4 * recency_component + 0.3 * frequency_component + 0.3 * monetary_component

    df["health_score"] = (100.0 * (0.4 * churn_component + 0.3 * sentiment_component + 0.3 * rfm_component)).round(2)

    def segment(score: float) -> str:
        if score >= 70:
            return "Healthy"
        if score >= 40:
            return "At Risk"
        return "Critical"

    df["health_segment"] = df["health_score"].map(segment)

    output_cols = [
        "customer_id",
        "health_score",
        "health_segment",
        "churn_probability",
        "sentiment_mean",
        "recency_days",
        "frequency",
        "monetary_avg",
        "clv",
    ]

    out = df[output_cols].sort_values("health_score", ascending=False)
    out.to_csv(PROCESSED_DIR / "health_scores.csv", index=False)
    print(f"Saved health_scores.csv with {len(out)} customers")
    print(out["health_segment"].value_counts().to_string())
    return out


if __name__ == "__main__":
    build_health_score()
