from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"


def export_for_power_bi() -> Path:
    health = pd.read_csv(PROCESSED_DIR / "health_scores.csv")
    features = pd.read_csv(PROCESSED_DIR / "features.csv")
    metrics = pd.read_csv(PROCESSED_DIR / "model_metrics.csv")
    transactions = pd.read_csv(RAW_DIR / "transactions.csv")

    tx_summary = (
        transactions.groupby("customer_id", as_index=False)
        .agg(total_spend=("amount", "sum"), purchases=("amount", "count"))
    )

    export_path = PROCESSED_DIR / "power_bi_export.xlsx"
    with pd.ExcelWriter(export_path, engine="openpyxl") as writer:
        health.to_excel(writer, sheet_name="HealthScores", index=False)
        features.to_excel(writer, sheet_name="Features", index=False)
        metrics.to_excel(writer, sheet_name="ModelMetrics", index=False)
        tx_summary.to_excel(writer, sheet_name="TransactionsSummary", index=False)

    print(f"Exported Power BI workbook: {export_path}")
    return export_path


if __name__ == "__main__":
    export_for_power_bi()
