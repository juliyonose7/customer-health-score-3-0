from __future__ import annotations

import argparse

from dashboard.power_bi_export import export_for_power_bi
from src.action_policy import build_action_policy
from src.data_generation import generate_data
from src.expected_value import build_expected_value
from src.features import build_features
from src.health_score import build_health_score
from src.model import train_and_score
from src.preprocessing import build_rfm_base
from src.sentiment import build_customer_sentiment


def run_pipeline(generate: bool) -> None:
    if generate:
        print("[1/9] Generating synthetic data")
        generate_data()
    else:
        print("[1/9] Skipping data generation (using existing raw files)")

    print("[2/9] Building RFM base")
    build_rfm_base()

    print("[3/9] Running sentiment")
    build_customer_sentiment()

    print("[4/9] Building features")
    build_features()

    print("[5/9] Training model")
    train_and_score()

    print("[6/9] Building health score")
    build_health_score()

    print("[7/9] Calculating expected value")
    build_expected_value()

    print("[8/9] Building action policy")
    build_action_policy()

    print("[9/9] Exporting Power BI workbook")
    export_for_power_bi()

    print("Pipeline finished")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Customer Health Score pipeline")
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Skip synthetic data generation and use existing files in data/raw",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(generate=not args.skip_generate)
