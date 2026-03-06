# Notebooks Guide

The project now uses only 2 notebooks.

## Notebook list
1. `01_end_to_end_pipeline.ipynb`
- Runs the complete pipeline in one place.
- Supports public TWCS dataset if available locally.
- Produces all artifacts, including Power BI export.

2. `02_analysis_visuals.ipynb`
- Focused on analysis and storytelling.
- Includes charts for health distribution, economic impact, and action prioritization.

## CLI alternatives
- Full synthetic run: `python -m src.run_pipeline`
- Public TWCS run: `python -m src.twitter_kaggle_adapter --max-rows 120000` then `python -m src.run_pipeline --skip-generate`
