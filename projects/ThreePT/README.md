# ThreePT · NYC 311 Long-Delay Prediction

Business Intelligence — Fall 2026 · Chung-Ang University

## Project overview

We predict which NYC 311 requests are likely to take much longer than usual to be closed,
so the staff in charge can look at them first.

### Team

| Name | Role |
| --- | --- |
| 이성재 (Lead) | Schedule, data collection, presentation |
| 정민교 | Implementation: models and demo |
| 윤하울 | Analysis: evaluation and results |
| All | Report, weekly cross-review |

## Code and reproducibility

### Folder structure

```
src/
  config.py     settings: period, complaint types, columns
  collect.py    download NYC 311 data month by month
  clean.py      merge, clean, and write a summary
notebooks/      analysis and modeling notebooks
docs/           data spec and data summary
data/raw/       monthly CSV files (not on GitHub)
data/processed/ cleaned data (not on GitHub)
```

### Setup

Run all commands from this folder (`projects/ThreePT`).

```bash
cd projects/ThreePT
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional: get a free app token at NYC Open Data and set it for higher rate limits.

```bash
export NYC_APP_TOKEN=your_token
```

### Data collection

```bash
python src/collect.py --list-types   # 1. check exact complaint_type names, then edit src/config.py
python src/collect.py --sample 1000  # 2. small test download -> data/raw/sample.csv
python src/collect.py                # 3. full download, month by month (safe to stop and rerun)
python src/clean.py                  # 4. clean -> data/processed/requests.parquet + docs/data_summary.md
```

## Deliverables

- Proposal
- Source code / notebooks
- Presentation
- Final report

## Data and licensing

Only include data and materials that may be shared in this repository. Do not commit credentials or sensitive personal information.

- Source: NYC 311 Service Requests from 2020 to Present (NYC Open Data, dataset id `erm2-nwe9`)
- Data files are not stored on GitHub. Share `data/processed/requests.parquet` on Google Drive.

## Schedule

| Week | Task |
| --- | --- |
| Week 1 | Data, baselines, evaluation setup |
| Week 2 | Our model and experiments |
| Week 3 | Finish the demo |
| Week 4 (Dec 8) | Final presentation and demo |
