from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from faker import Faker


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"


@dataclass(frozen=True)
class GenerationConfig:
    n_customers: int = 800
    seed: int = 42


def _customer_ids(n_customers: int) -> list[str]:
    return [f"CUST-{idx:05d}" for idx in range(1, n_customers + 1)]


def _build_transactions(customer_ids: Iterable[str], rng: np.random.Generator) -> pd.DataFrame:
    rows: list[dict] = []
    products = ["Core", "Plus", "Premium", "AddOn"]

    for customer_id in customer_ids:
        purchase_count = int(rng.integers(3, 21))
        base_amount = float(rng.uniform(20, 350))
        for _ in range(purchase_count):
            rows.append(
                {
                    "customer_id": customer_id,
                    "date": pd.Timestamp("2025-01-01") + pd.to_timedelta(int(rng.integers(0, 430)), unit="D"),
                    "amount": round(base_amount * float(rng.uniform(0.7, 1.4)), 2),
                    "product": str(rng.choice(products)),
                    "purchase_freq_hint": round(float(rng.uniform(0.05, 1.0)), 3),
                }
            )
    return pd.DataFrame(rows)


def _build_text_rows(customer_ids: Iterable[str], rng: np.random.Generator, fake: Faker, source: str) -> pd.DataFrame:
    pos_templates = [
        "Great service and fast support response.",
        "Very satisfied with product quality.",
        "Team solved my issue quickly."
    ]
    neg_templates = [
        "Terrible experience, issue still unresolved.",
        "Support is slow and not helpful.",
        "I am disappointed with recurring bugs."
    ]
    neu_templates = [
        "Requesting more information about pricing.",
        "Question about product features.",
        "Need an update on my support ticket."
    ]

    rows: list[dict] = []
    for customer_id in customer_ids:
        events = int(rng.integers(0, 9))
        for _ in range(events):
            mood = str(rng.choice(["pos", "neg", "neu"], p=[0.45, 0.30, 0.25]))
            if mood == "pos":
                text = str(rng.choice(pos_templates))
            elif mood == "neg":
                text = str(rng.choice(neg_templates))
            else:
                text = str(rng.choice(neu_templates))

            rows.append(
                {
                    "customer_id": customer_id,
                    "date": pd.Timestamp("2025-01-01") + pd.to_timedelta(int(rng.integers(0, 430)), unit="D"),
                    "text": text,
                    "platform": source,
                    "resolution_time_hours": round(float(rng.uniform(2, 96)), 2),
                    "author": fake.name(),
                }
            )
    return pd.DataFrame(rows)


def generate_data(config: GenerationConfig = GenerationConfig()) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(config.seed)
    fake = Faker()
    Faker.seed(config.seed)

    customer_ids = _customer_ids(config.n_customers)

    transactions = _build_transactions(customer_ids, rng).sort_values(["customer_id", "date"])
    support_tickets = _build_text_rows(customer_ids, rng, fake, source="support").rename(
        columns={"platform": "channel"}
    )
    social_mentions = _build_text_rows(customer_ids, rng, fake, source="social")[["customer_id", "date", "platform", "text"]]

    transactions.to_csv(RAW_DIR / "transactions.csv", index=False)
    support_tickets.to_csv(RAW_DIR / "support_tickets.csv", index=False)
    social_mentions.to_csv(RAW_DIR / "social_mentions.csv", index=False)

    print(f"Generated {len(customer_ids)} customers")
    print(f"transactions.csv rows: {len(transactions)}")
    print(f"support_tickets.csv rows: {len(support_tickets)}")
    print(f"social_mentions.csv rows: {len(social_mentions)}")


if __name__ == "__main__":
    generate_data()
