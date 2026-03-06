from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"


def build_rfm_base(reference_date: str = "2026-03-01") -> pd.DataFrame:
    transactions = pd.read_csv(RAW_DIR / "transactions.csv", parse_dates=["date"])
    support_tickets = pd.read_csv(RAW_DIR / "support_tickets.csv", parse_dates=["date"])
    social_mentions = pd.read_csv(RAW_DIR / "social_mentions.csv", parse_dates=["date"])

    ref_date = pd.Timestamp(reference_date)

    rfm = (
        transactions.groupby("customer_id", as_index=False)
        .agg(
            last_purchase=("date", "max"),
            frequency=("amount", "count"),
            monetary_total=("amount", "sum"),
            monetary_avg=("amount", "mean"),
        )
    )
    rfm["recency_days"] = (ref_date - rfm["last_purchase"]).dt.days

    ticket_agg = (
        support_tickets.groupby("customer_id", as_index=False)
        .agg(
            ticket_volume=("text", "count"),
            resolution_time_avg=("resolution_time_hours", "mean"),
        )
    )

    social_agg = social_mentions.groupby("customer_id", as_index=False).agg(
        social_mentions_count=("text", "count")
    )

    merged = rfm.merge(ticket_agg, on="customer_id", how="left").merge(
        social_agg, on="customer_id", how="left"
    )

    for col in ["ticket_volume", "resolution_time_avg", "social_mentions_count"]:
        merged[col] = merged[col].fillna(0)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    merged.to_csv(PROCESSED_DIR / "rfm_base.csv", index=False)
    print(f"Saved rfm_base.csv with {len(merged)} customers")
    return merged


if __name__ == "__main__":
    build_rfm_base()
