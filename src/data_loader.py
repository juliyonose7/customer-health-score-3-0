from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
EXTERNAL_DIR = ROOT / "data" / "external"

REQUIRED_FILES = {
    "transactions.csv": ["customer_id", "date", "amount"],
    "support_tickets.csv": ["customer_id", "date", "text"],
    "social_mentions.csv": ["customer_id", "date", "text"],
}


def _validate_columns(file_name: str, df: pd.DataFrame) -> None:
    required = REQUIRED_FILES[file_name]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{file_name} is missing required columns: {missing}")


def load_external_data() -> None:
    """Copy and validate user-provided CSV files from data/external into data/raw."""
    EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for file_name in REQUIRED_FILES:
        source = EXTERNAL_DIR / file_name
        if not source.exists():
            raise FileNotFoundError(
                f"Expected file not found: {source}. Add this CSV and run again."
            )

        df = pd.read_csv(source)
        _validate_columns(file_name, df)

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            if df["date"].isna().any():
                raise ValueError(f"{file_name} contains invalid date values")
            df["date"] = df["date"].dt.strftime("%Y-%m-%d")

        out_path = RAW_DIR / file_name
        df.to_csv(out_path, index=False)
        print(f"Loaded {file_name} -> {out_path} ({len(df)} rows)")


if __name__ == "__main__":
    load_external_data()
