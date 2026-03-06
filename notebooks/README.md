# Notebooks Guide

Use these notebooks as analysis layers on top of the reusable modules in `src/`.

## Suggested notebook sequence
1. `01_data_generation.ipynb` - run synthetic generation and inspect schema.
2. `02_eda.ipynb` - profile transactions and support/social volumes.
3. `03_sentiment.ipynb` - inspect sentiment distributions and edge cases.
4. `04_features.ipynb` - validate engineered features and churn label logic.
5. `05_modeling.ipynb` - compare model metrics and inspect feature importance.
6. `06_health_score.ipynb` - segment customers and prepare BI extracts.

## CLI alternatives
- Full synthetic run: `python -m src.run_pipeline`
- Use real data in `data/external`: `python -m src.data_loader` then `python -m src.run_pipeline --skip-generate`
