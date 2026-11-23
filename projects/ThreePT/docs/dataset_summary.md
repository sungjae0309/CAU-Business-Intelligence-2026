# Dataset summary

Built by `src/build_dataset.py` from `data/processed/requests.parquet`.

## Settings

- Types: HEAT/HOT WATER, Street Condition
- Split: train 2023-01-01 to 2024-01-01 (end excluded); valid 2024-01-01 to 2024-07-01 (end excluded); test 2024-07-01 to 2025-01-01 (end excluded)
- Recent window: 7 days; nearby grid: 100 m
- Open requests judged at collection date 2026-11-24
- Same-second closes removed: True

## Long-delay limit

|                  |   limit hours | rule               |
|:-----------------|--------------:|:-------------------|
| Street Condition |         186.9 | train quantile 0.9 |
| HEAT/HOT WATER   |          81.5 | train quantile 0.9 |

## Row filtering

- cleaned rows (all types): 1,307,128
- after keeping MODEL_TYPES: 629,464
- removed: status Closed but no closed_date: 104
- removed: closed in the same second as created: 8,902
- removed: outside the split periods: 0
- removed: still open but not yet past the limit: 0
- final rows: 620,458

## Rows and long-delay rate

| split   | complaint_type   |   rows |   long_delay | rate   |
|:--------|:-----------------|-------:|-------------:|:-------|
| train   | HEAT/HOT WATER   | 229495 |        22950 | 10.0%  |
| train   | Street Condition |  59473 |         5948 | 10.0%  |
| valid   | HEAT/HOT WATER   | 132961 |         5307 | 4.0%   |
| valid   | Street Condition |  38055 |         4650 | 12.2%  |
| test    | HEAT/HOT WATER   | 131759 |        20015 | 15.2%  |
| test    | Street Condition |  28715 |         3575 | 12.4%  |

## Columns

| Column | Role |
| --- | --- |
| unique_key | id / grouping |
| case_id | id / grouping |
| split | id / grouping |
| created_date | id / grouping |
| complaint_type | feature |
| descriptor | feature |
| agency | feature |
| borough | feature |
| zip | feature |
| location_type | feature |
| channel | feature |
| latitude | feature |
| longitude | feature |
| hour | feature |
| dayofweek | feature |
| month | feature |
| is_weekend | feature |
| recent_same_type_zip | feature |
| recent_same_type_nearby | feature |
| open_same_type_zip | feature |
| long_delay | label |
| closed_date | evaluation only, not a feature |
| resolution_hours | evaluation only, not a feature |
| is_open | evaluation only, not a feature |

## Feature notes

- `recent_same_type_zip`: same type, same zip, created in the 7 days before
- `recent_same_type_nearby`: same type, 3x3 block of 100 m grid cells, created in the 7 days before (empty if no location)
- `open_same_type_zip`: same type, same zip, created before and not closed yet at creation time (lower in early 2023 because 2022 requests are not collected)
- `case_id`: same type, same 100 m grid cell, each report within 7 days of the previous one; id of the first report
- Counts use all cleaned requests of the type, including rows removed from this table
