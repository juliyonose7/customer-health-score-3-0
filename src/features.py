from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"


def build_features() -> pd.DataFrame:
    rfm = pd.read_csv(PROCESSED_DIR / "rfm_base.csv")
    sentiment = pd.read_csv(PROCESSED_DIR / "sentiment_customer.csv")

    data = rfm.merge(sentiment, on="customer_id", how="left")
    for col in ["sentiment_mean", "sentiment_min", "sentiment_max", "sentiment_recent_mean", "sentiment_trend"]:
        data[col] = data[col].fillna(0.0)

    preliminary_churn = ((data["recency_days"] > 90) & (data["sentiment_mean"] < -0.15)).astype(int)
    churn_rate_global = max(float(preliminary_churn.mean()), 0.03)

    data["avg_purchase_value"] = data["monetary_avg"].clip(lower=1.0)
    data["purchase_frequency"] = data["frequency"].clip(lower=1)
    data["clv"] = (data["avg_purchase_value"] * data["purchase_frequency"]) / churn_rate_global

    data["churned"] = (
        ((data["recency_days"] > 90) & (data["sentiment_mean"] < -0.10))
        | ((data["recency_days"] > 110) & (data["ticket_volume"] > 5))
    ).astype(int)

    data = data.replace([np.inf, -np.inf], np.nan).fillna(0)
    data.to_csv(PROCESSED_DIR / "features.csv", index=False)
    print(f"Saved features.csv with {len(data)} customers")
    return data


if __name__ == "__main__":
    build_features()
