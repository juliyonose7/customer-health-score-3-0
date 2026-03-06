# Customer Health Score 3.0

Hybrid data analytics project to predict churn early by combining transactional behavior with NLP sentiment analysis.

## Project Goals
- Generate synthetic but realistic customer data.
- Build churn features (RFM + support/social sentiment).
- Train churn models and compare metrics.
- Compute a 0-100 Customer Health Score.
- Export curated outputs for Power BI.

## Project Structure
- `data/raw`: generated source CSV files.
- `data/processed`: feature tables and final health scores.
- `src`: reusable Python modules.
- `dashboard`: Power BI export tooling.
- `notebooks`: EDA and model notebooks.

## Phase Execution
1. Generate data: `python -m src.data_generation`
2. Build RFM base: `python -m src.preprocessing`
3. Run sentiment: `python -m src.sentiment`
4. Build features: `python -m src.features`
5. Train models: `python -m src.model`
6. Calculate health score: `python -m src.health_score`
7. Export for Power BI: `python -m dashboard.power_bi_export`

## One-command execution
- Synthetic data end-to-end: `python -m src.run_pipeline`
- Real data end-to-end:
	- Add CSV files to `data/external`: `transactions.csv`, `support_tickets.csv`, `social_mentions.csv`
	- Load and validate files: `python -m src.data_loader`
	- Run pipeline without synthetic generation: `python -m src.run_pipeline --skip-generate`

## Quality Checks
- Run tests: `pytest -q`
- Run pipeline + tests in one script (PowerShell): `./scripts/run_all.ps1`
- CI runs on `push` and `pull_request` using `.github/workflows/ci.yml`

## Docker
- Build lightweight image: `docker build -t customer-health-score:latest .`
- Run synthetic pipeline in container: `docker run --rm -v ${PWD}:/app customer-health-score:latest`
- Optional full NLP dependencies during build:
	- `docker build --build-arg INSTALL_FULL_NLP=1 -t customer-health-score:latest .`
- PowerShell helper script: `./scripts/docker_run.ps1`

## Suggested Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
