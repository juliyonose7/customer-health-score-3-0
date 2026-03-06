from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"


def test_raw_files_exist_and_have_rows() -> None:
    raw_files = [
        RAW_DIR / "transactions.csv",
        RAW_DIR / "support_tickets.csv",
        RAW_DIR / "social_mentions.csv",
    ]
    for file_path in raw_files:
        assert file_path.exists(), f"Missing file: {file_path}"
        df = pd.read_csv(file_path)
        assert len(df) > 0, f"No rows in {file_path.name}"


def test_features_schema_and_no_null_customer_id() -> None:
    features = pd.read_csv(PROCESSED_DIR / "features.csv")
    required_columns = {
        "customer_id",
        "recency_days",
        "frequency",
        "monetary_avg",
        "sentiment_mean",
        "clv",
        "churned",
    }
    assert required_columns.issubset(features.columns)
    assert features["customer_id"].notna().all()


def test_model_metrics_minimum_quality() -> None:
    metrics = pd.read_csv(PROCESSED_DIR / "model_metrics.csv")
    assert "roc_auc" in metrics.columns
    best_auc = float(metrics["roc_auc"].max())
    assert best_auc >= 0.75


def test_health_score_ranges_and_segments() -> None:
    health = pd.read_csv(PROCESSED_DIR / "health_scores.csv")
    assert health["health_score"].between(0, 100).all()
    valid_segments = {"Healthy", "At Risk", "Critical"}
    assert set(health["health_segment"].unique()).issubset(valid_segments)
    assert len(health["health_segment"].unique()) >= 2
