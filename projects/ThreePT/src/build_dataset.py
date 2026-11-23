"""Build the model-ready dataset: label, features, and time split.

Usage (run from the project folder, after clean.py):
    python src/build_dataset.py

Input:
    data/processed/requests.parquet
Output:
    data/processed/dataset.parquet
    docs/dataset_summary.md

Settings (types, long-delay rule, split, window) are in src/config.py.
Every feature uses only information known when the request was created.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import (DATA_COLLECTED_ON, DOCS_DIR, DROP_SAME_SECOND, LONG_DELAY_HOURS,
                    LONG_DELAY_QUANTILE, MODEL_TYPES, NEARBY_METERS, PROCESSED_DIR,
                    RECENT_DAYS, SPLITS)

WINDOW = RECENT_DAYS * 24 * 3600   # seconds

ID_COLS = ["unique_key", "case_id", "split", "created_date"]
FEATURE_COLS = [
    "complaint_type", "descriptor", "agency", "borough", "zip", "location_type", "channel",
    "latitude", "longitude", "hour", "dayofweek", "month", "is_weekend",
    "recent_same_type_zip", "recent_same_type_nearby", "open_same_type_zip",
]
LABEL_COL = "long_delay"
EVAL_ONLY_COLS = ["closed_date", "resolution_hours", "is_open"]


def count_in_window(groups, times, q_groups, q_start, q_end, span):
    """For each query, count events with the same group and q_start <= time < q_end."""
    keys = np.sort(groups * span + times)
    lo = np.searchsorted(keys, q_groups * span + q_start, side="left")
    hi = np.searchsorted(keys, q_groups * span + q_end, side="left")
    return hi - lo


def add_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    df["zip"] = df["incident_zip"].where(df["incident_zip"].str.fullmatch(r"1[01]\d{3}", na=False))
    df["channel"] = df["open_data_channel_type"]
    created = df["created_date"]
    df["hour"] = created.dt.hour
    df["dayofweek"] = created.dt.day_of_week        # 0 = Monday
    df["month"] = created.dt.month
    df["is_weekend"] = df["dayofweek"] >= 5
    return df


def add_report_features(df: pd.DataFrame) -> pd.DataFrame:
    """Recent reports, open backlog, and repeated-report cases. Uses all cleaned rows."""
    base = df["created_date"].min().floor("D") - pd.Timedelta(days=RECENT_DAYS + 1)
    t = (df["created_date"] - base).dt.total_seconds().to_numpy().astype(np.int64)
    t_closed = (df["closed_date"] - base).dt.total_seconds().to_numpy()
    span = int(max(t.max(), np.nanmax(t_closed))) + 1
    type_idx = pd.factorize(df["complaint_type"])[0].astype(np.int64)

    # Same type, same zip: reports in the last RECENT_DAYS, and requests still open right now.
    has_zip = df["zip"].notna().to_numpy()
    zip_idx = pd.factorize(df["zip"])[0].astype(np.int64)
    g = type_idx * (zip_idx.max() + 1) + zip_idx
    gz, tz = g[has_zip], t[has_zip]
    recent_zip = count_in_window(gz, tz, gz, tz - WINDOW, tz, span)
    closed_z = has_zip & ~np.isnan(t_closed)
    created_before = count_in_window(gz, tz, gz, np.zeros_like(tz), tz, span)
    closed_before = count_in_window(g[closed_z], t_closed[closed_z].astype(np.int64),
                                    gz, np.zeros_like(tz), tz, span)
    df["recent_same_type_zip"] = pd.Series(pd.NA, index=df.index, dtype="Int64")
    df["open_same_type_zip"] = pd.Series(pd.NA, index=df.index, dtype="Int64")
    df.loc[has_zip, "recent_same_type_zip"] = recent_zip
    df.loc[has_zip, "open_same_type_zip"] = created_before - closed_before

    # Same type, nearby: 3x3 block of NEARBY_METERS grid cells (every report within NEARBY_METERS,
    # plus some up to about 2.8 x NEARBY_METERS on the diagonal).
    has_loc = df["latitude"].notna().to_numpy() & df["longitude"].notna().to_numpy()
    x = df["longitude"].to_numpy()[has_loc] * 111_320 * np.cos(np.radians(40.7))
    y = df["latitude"].to_numpy()[has_loc] * 110_574
    cx = np.floor(x / NEARBY_METERS).astype(np.int64)
    cy = np.floor(y / NEARBY_METERS).astype(np.int64)
    cx, cy = cx - cx.min() + 1, cy - cy.min() + 1
    width = cy.max() + 2
    n_cells = (cx.max() + 2) * width
    tl, kl = t[has_loc], type_idx[has_loc]
    cell = cx * width + cy
    groups = kl * n_cells + cell
    nearby = np.zeros(len(tl), dtype=np.int64)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            q = kl * n_cells + (cx + dx) * width + (cy + dy)
            nearby += count_in_window(groups, tl, q, tl - WINDOW, tl, span)
    df["recent_same_type_nearby"] = pd.Series(pd.NA, index=df.index, dtype="Int64")
    df.loc[has_loc, "recent_same_type_nearby"] = nearby

    # Case: same type, same grid cell, each report within RECENT_DAYS of the previous one.
    # case_id = unique_key of the first report. Reports without a location are their own case.
    sub = pd.DataFrame({"key": df["unique_key"].to_numpy()[has_loc], "g": groups, "t": tl},
                       index=df.index[has_loc]).sort_values(["g", "t"])
    new_case = (sub["g"].diff() != 0) | (sub["t"].diff() > WINDOW)
    first_key = sub.groupby(new_case.cumsum())["key"].transform("first")
    df["case_id"] = df["unique_key"]
    df.loc[first_key.index, "case_id"] = first_key
    return df


def add_split(df: pd.DataFrame) -> pd.DataFrame:
    df["split"] = pd.Series(pd.NA, index=df.index, dtype="str")
    for name, (start, end) in SPLITS.items():
        in_range = (df["created_date"] >= start) & (df["created_date"] < end)
        df.loc[in_range, "split"] = name
    return df


def add_label(df: pd.DataFrame, log: dict) -> tuple[pd.DataFrame, dict]:
    """long_delay = 1 if time to close is above the type's limit. Open requests use time until collection."""
    collected = pd.Timestamp(DATA_COLLECTED_ON)
    hours = df["resolution_hours"].copy()
    open_hours = (collected - df["created_date"]).dt.total_seconds() / 3600
    limits = {}
    for t in df["complaint_type"].unique():
        if t in LONG_DELAY_HOURS:
            limits[t] = float(LONG_DELAY_HOURS[t])
            continue
        train = df[(df["complaint_type"] == t) & (df["split"] == "train")]
        r = train["resolution_hours"].where(~train["is_open"], np.inf)   # still open = longest
        limits[t] = float(np.quantile(r, LONG_DELAY_QUANTILE))
    limit = df["complaint_type"].map(limits)

    known_open = df["is_open"] & (open_hours > limit)
    unknown = df["is_open"] & ~known_open
    log["removed: still open but not yet past the limit"] = int(unknown.sum())
    df = df[~unknown].copy()
    df[LABEL_COL] = (df["is_open"] | (hours[df.index] > limit[df.index])).astype("int8")
    return df, limits


def build() -> tuple[pd.DataFrame, dict, dict]:
    df = pd.read_parquet(PROCESSED_DIR / "requests.parquet")
    log = {"cleaned rows (all types)": len(df)}

    df = add_basic_features(df)
    df = add_report_features(df)     # counts use every cleaned row, before any row is removed
    df = add_split(df)

    df = df[df["complaint_type"].isin(MODEL_TYPES)].copy()
    log["after keeping MODEL_TYPES"] = len(df)

    bad_open = df["is_open"] & (df["status"] == "Closed")
    log["removed: status Closed but no closed_date"] = int(bad_open.sum())
    df = df[~bad_open]

    if DROP_SAME_SECOND:
        log["removed: closed in the same second as created"] = int(df["closed_same_second"].sum())
        df = df[~df["closed_same_second"]]

    no_split = df["split"].isna()
    log["removed: outside the split periods"] = int(no_split.sum())
    df = df[~no_split].copy()

    df, limits = add_label(df, log)
    log["final rows"] = len(df)
    df = df[ID_COLS + FEATURE_COLS + [LABEL_COL] + EVAL_ONLY_COLS].reset_index(drop=True)
    return df, log, limits


def summary(df: pd.DataFrame, log: dict, limits: dict) -> str:
    split_order = list(SPLITS)
    tab = (df.groupby(["split", "complaint_type"])[LABEL_COL]
             .agg(rows="size", long_delay="sum", rate="mean")
             .reset_index())
    tab["split"] = pd.Categorical(tab["split"], split_order, ordered=True)
    tab = tab.sort_values(["split", "complaint_type"])
    tab["rate"] = (tab["rate"] * 100).round(1).astype(str) + "%"

    lim = pd.DataFrame({"limit hours": {k: round(v, 1) for k, v in limits.items()}})
    lim["rule"] = [("fixed" if k in LONG_DELAY_HOURS else f"train quantile {LONG_DELAY_QUANTILE}")
                   for k in lim.index]

    roles = ([(c, "id / grouping") for c in ID_COLS] + [(c, "feature") for c in FEATURE_COLS]
             + [(LABEL_COL, "label")] + [(c, "evaluation only, not a feature") for c in EVAL_ONLY_COLS])

    lines = ["# Dataset summary", "",
             "Built by `src/build_dataset.py` from `data/processed/requests.parquet`.", "",
             "## Settings", "",
             f"- Types: {', '.join(MODEL_TYPES)}",
             f"- Split: " + "; ".join(f"{k} {a} to {b} (end excluded)" for k, (a, b) in SPLITS.items()),
             f"- Recent window: {RECENT_DAYS} days; nearby grid: {NEARBY_METERS} m",
             f"- Open requests judged at collection date {DATA_COLLECTED_ON}",
             f"- Same-second closes removed: {DROP_SAME_SECOND}",
             "", "## Long-delay limit", "", lim.to_markdown(),
             "", "## Row filtering", ""]
    lines += [f"- {k}: {v:,}" for k, v in log.items()]
    lines += ["", "## Rows and long-delay rate", "", tab.to_markdown(index=False),
              "", "## Columns", "", "| Column | Role |", "| --- | --- |"]
    lines += [f"| {c} | {r} |" for c, r in roles]
    lines += ["", "## Feature notes", "",
              f"- `recent_same_type_zip`: same type, same zip, created in the {RECENT_DAYS} days before",
              f"- `recent_same_type_nearby`: same type, 3x3 block of {NEARBY_METERS} m grid cells, "
              f"created in the {RECENT_DAYS} days before (empty if no location)",
              "- `open_same_type_zip`: same type, same zip, created before and not closed yet at creation time "
              "(lower in early 2023 because 2022 requests are not collected)",
              f"- `case_id`: same type, same {NEARBY_METERS} m grid cell, each report within {RECENT_DAYS} days "
              "of the previous one; id of the first report",
              "- Counts use all cleaned requests of the type, including rows removed from this table",
              ""]
    return "\n".join(lines)


def main() -> None:
    df, log, limits = build()
    out = PROCESSED_DIR / "dataset.parquet"
    df.to_parquet(out, index=False)
    print(f"Saved {len(df):,} rows -> {out}")
    for k, v in log.items():
        print(f"  {k}: {v:,}")
    print("Long-delay limits (hours):", {k: round(v, 1) for k, v in limits.items()})
    (DOCS_DIR / "dataset_summary.md").write_text(summary(df, log, limits), encoding="utf-8")
    print("Wrote docs/dataset_summary.md")


if __name__ == "__main__":
    main()
