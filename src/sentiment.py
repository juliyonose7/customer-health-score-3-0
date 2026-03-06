from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"


def _keyword_sentiment(text: str) -> float:
    text_lower = text.lower()
    positive = ["great", "satisfied", "quickly", "fast", "solved"]
    negative = ["terrible", "slow", "unresolved", "disappointed", "bugs"]

    pos_hits = sum(1 for token in positive if token in text_lower)
    neg_hits = sum(1 for token in negative if token in text_lower)

    if pos_hits == neg_hits:
        return 0.0
    score = (pos_hits - neg_hits) / max(pos_hits + neg_hits, 1)
    return float(max(-1.0, min(1.0, score)))


def _hf_sentiment_scores(texts: list[str]) -> list[float]:
    from transformers import pipeline

    clf = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english",
        truncation=True,
    )
    outputs = clf(texts)
    scores: list[float] = []
    for pred in outputs:
        label = str(pred["label"]).upper()
        score = float(pred["score"])
        signed = score if "POS" in label else -score
        scores.append(float(max(-1.0, min(1.0, signed))))
    return scores


def build_customer_sentiment() -> pd.DataFrame:
    support_tickets = pd.read_csv(RAW_DIR / "support_tickets.csv", parse_dates=["date"])
    social_mentions = pd.read_csv(RAW_DIR / "social_mentions.csv", parse_dates=["date"])

    combined = pd.concat(
        [
            support_tickets[["customer_id", "date", "text"]],
            social_mentions[["customer_id", "date", "text"]],
        ],
        ignore_index=True,
    )

    if combined.empty:
        raise ValueError("No text rows found in support_tickets.csv or social_mentions.csv")

    try:
        combined["sentiment_score"] = _hf_sentiment_scores(combined["text"].astype(str).tolist())
        engine = "huggingface"
    except Exception:
        combined["sentiment_score"] = combined["text"].astype(str).map(_keyword_sentiment)
        engine = "keyword_fallback"

    cutoff_date = combined["date"].max() - pd.Timedelta(days=30)
    recent = combined[combined["date"] >= cutoff_date]

    customer_sent = combined.groupby("customer_id", as_index=False).agg(
        sentiment_mean=("sentiment_score", "mean"),
        sentiment_min=("sentiment_score", "min"),
        sentiment_max=("sentiment_score", "max"),
    )

    recent_sent = recent.groupby("customer_id", as_index=False).agg(
        sentiment_recent_mean=("sentiment_score", "mean")
    )

    customer_sent = customer_sent.merge(recent_sent, on="customer_id", how="left")
    customer_sent["sentiment_recent_mean"] = customer_sent["sentiment_recent_mean"].fillna(
        customer_sent["sentiment_mean"]
    )
    customer_sent["sentiment_trend"] = customer_sent["sentiment_recent_mean"] - customer_sent["sentiment_mean"]

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    customer_sent.to_csv(PROCESSED_DIR / "sentiment_customer.csv", index=False)
    print(f"Saved sentiment_customer.csv with {len(customer_sent)} customers using {engine}")
    return customer_sent


if __name__ == "__main__":
    build_customer_sentiment()
