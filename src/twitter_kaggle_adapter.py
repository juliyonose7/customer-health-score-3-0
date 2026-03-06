from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"

DEFAULT_TWCS_PATH = ROOT.parent / "DS" / "twcs" / "twcs.csv"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Adapt Kaggle TWCS dataset to project raw schema."
    )
    parser.add_argument(
        "--source",
        type=str,
        default=str(DEFAULT_TWCS_PATH),
        help="Path to twcs.csv file.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=300000,
        help="Limit rows for faster local processing.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for synthetic transactions creation.",
    )
    return parser.parse_args()


def _load_twcs(path: Path, max_rows: int) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"TWCS file not found: {path}")

    usecols = [
        "tweet_id",
        "author_id",
        "inbound",
        "created_at",
        "text",
        "in_response_to_tweet_id",
    ]
    df = pd.read_csv(path, usecols=usecols, nrows=max_rows)
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    df = df.dropna(subset=["created_at", "author_id", "text"])
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"] != ""]

    # inbound=False/True can be parsed as bool or string depending on csv engine/version.
    df["inbound"] = df["inbound"].astype(str).str.lower().map({"true": True, "false": False})
    return df.dropna(subset=["inbound"])


def _build_support_and_social(inbound_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    mapped = inbound_df.copy()
    mapped["customer_id"] = "TW-" + mapped["author_id"].astype(str)
    mapped["date"] = mapped["created_at"].dt.tz_convert(None).dt.strftime("%Y-%m-%d")

    support = mapped[["customer_id", "date", "text"]].copy()
    support["channel"] = "twitter"
    support["resolution_time_hours"] = 24.0
    support["author"] = mapped["author_id"].astype(str)

    social = mapped[["customer_id", "date", "text"]].copy()
    social["platform"] = "twitter"
    social = social[["customer_id", "date", "platform", "text"]]

    return support, social


def _build_transactions(inbound_df: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    mapped = inbound_df.copy()
    mapped["customer_id"] = "TW-" + mapped["author_id"].astype(str)
    mapped["date_ts"] = mapped["created_at"].dt.tz_convert(None)

    per_customer = mapped.groupby("customer_id", as_index=False).agg(
        interactions=("tweet_id", "count"),
        first_date=("date_ts", "min"),
        last_date=("date_ts", "max"),
    )

    rows: list[dict] = []
    products = ["Core", "Plus", "Premium", "AddOn"]

    for row in per_customer.itertuples(index=False):
        interactions = int(row.interactions)
        tx_count = int(max(1, min(18, interactions // 3 + int(rng.integers(1, 5)))))
        base = float(30 + min(240, interactions * 1.8))

        days_span = max(1, (row.last_date - row.first_date).days)
        for _ in range(tx_count):
            offset = int(rng.integers(0, days_span + 1))
            tx_date = row.first_date + pd.to_timedelta(offset, unit="D")
            amount = round(base * float(rng.uniform(0.55, 1.25)), 2)
            rows.append(
                {
                    "customer_id": row.customer_id,
                    "date": tx_date.strftime("%Y-%m-%d"),
                    "amount": amount,
                    "product": str(rng.choice(products)),
                    "purchase_freq_hint": round(float(rng.uniform(0.05, 1.0)), 3),
                }
            )

    return pd.DataFrame(rows)


def adapt_twitter_dataset(source_path: Path, max_rows: int, seed: int) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    twcs = _load_twcs(source_path, max_rows=max_rows)
    inbound = twcs[twcs["inbound"] == True].copy()

    if inbound.empty:
        raise ValueError("No inbound tweets found in source data")

    support_tickets, social_mentions = _build_support_and_social(inbound)
    transactions = _build_transactions(inbound, seed=seed)

    transactions.to_csv(RAW_DIR / "transactions.csv", index=False)
    support_tickets.to_csv(RAW_DIR / "support_tickets.csv", index=False)
    social_mentions.to_csv(RAW_DIR / "social_mentions.csv", index=False)

    print(f"Source rows loaded: {len(twcs)}")
    print(f"Inbound rows used: {len(inbound)}")
    print(f"transactions.csv rows: {len(transactions)}")
    print(f"support_tickets.csv rows: {len(support_tickets)}")
    print(f"social_mentions.csv rows: {len(social_mentions)}")


if __name__ == "__main__":
    args = _parse_args()
    adapt_twitter_dataset(Path(args.source), max_rows=args.max_rows, seed=args.seed)
