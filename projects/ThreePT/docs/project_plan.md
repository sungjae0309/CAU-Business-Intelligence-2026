# ThreePT · Project plan (from the Week 12 proposal)

This file is the single source of truth for what we decided in the proposal.
Update it when a decision changes, and note the date.

## One-line summary

Not the most complaints, but the most likely to be left behind:
we predict which NYC 311 requests will take much longer than usual to be closed,
so the staff in charge can look at them first.

## Problem

- NYC 311 gets over 3 million requests a year. Each request goes to a city department
  (for example housing, sanitation, transportation).
- The staff in charge cannot handle everything at once, so every week they decide what to look at first.
- Common ways: most complaints first, or oldest requests first.
  - Most complaints first misses areas with few complaints that stay open for a long time.
  - Oldest first finds those requests only after they are already late.
- Example used in the proposal (made-up numbers): Area A has 100 noise complaints, most closed in 1 day.
  Area B has 10 heating complaints, 5 still open after 1 month. Area B needs help more.

## BI decision

| | |
| --- | --- |
| Who | Staff in charge at city departments |
| Decision | Which requests and areas to check first each week, and where to send staff |
| Action | Rank by long-delay risk, not only by complaint count |

## Social computing angle

- The data comes from citizens reporting problems online, by phone, or with a mobile app.
- The same problem reported again and again is a social signal. We use it as a model input.

## Data

- Source: NYC 311 Service Requests from 2020 to Present (NYC Open Data, `erm2-nwe9`)
- Period: 2023-01-01 to 2024-12-31
- Complaint types: `HEAT/HOT WATER`, `Noise - Residential`, `Street Condition`
- No personal information about the reporter. Data files are not committed (see `.gitignore`).
- Fallback if data is too large: one department, six months.

## Method

1. **Define a long delay**: time to close in the top 10% of its complaint type
   (alternative: over the city's official time limit / SLA for that type).
2. **Predict** with information known when the request is created only
   (type, location, time, recent similar reports). No future information.
   - Simple model: logistic regression
   - Main model: LightGBM
3. **Group repeated reports**: same type, within 100 m, within 7 days = one case.
4. **Split by time**: train 2023 → validate 2024 H1 → test 2024 H2.

## Evaluation (the professor marked this as important)

- Baselines: (1) most complaints first, (2) oldest requests first
- Each week, each method picks its top 50 requests.
- Metric: Recall@50 per week = share of real long delays caught in the top 50.
- Success: at least +10 percentage points over the best baseline.
- These numbers are an initial plan and can be adjusted after we see the real data.

## Demo (Week 15, Dec 8)

- Streamlit map dashboard: pick a week and an area → top 50 risky requests on a map, with reasons.
- Option if time allows: hotspot clustering (areas where delays keep happening).

## Hypotheses and limits

- H1: high-count areas and high-risk areas are different.
- H2: our model beats both baselines.
- Limits: "closed" does not always mean fixed; some areas report more than others;
  the data cannot tell us why a delay happens.

## Team

| Name | Role |
| --- | --- |
| 이성재 (Lead) | Schedule and meetings, data collection, presentation |
| 정민교 | Implementation: models and demo |
| 윤하울 | Analysis: evaluation and results |
| All | Report, weekly cross-review |

## Schedule

| Week | Task |
| --- | --- |
| Week 1 | Data, baselines, evaluation setup |
| Week 2 | Our model and experiments |
| Week 3 | Finish the demo |
| Week 4 (Dec 8) | Final presentation and demo |
| Week 16 | Submit source code, demo video, report (PR: `[ThreePT] Project Deliverables`) |

## Status log

- 2026-11-24: Data collection started. Type counts for 2023–2024:
  HEAT/HOT WATER 494,259 · Noise - Residential 677,749 · Street Condition 135,251.
  Sample check: missing values are mostly in Street Condition
  (location_type 65.3%, latitude/longitude 28.5%, closed_date 1.2%).
- 2026-11-24: Data collection done. 1,307,259 rows in 24 monthly files.
  After `clean.py`: 1,307,128 rows (131 closed before created removed). Details in `docs/data_summary.md`.
  Noise - Residential: no open requests, median 0.8 h; monthly count rises from about 25k to 45k from 2024-09.

## Open questions

- Long-delay label: top 10% per type, or the city's time limit?
- How to handle requests that are still open (no closed_date)?
- How to handle Street Condition rows without a location?
