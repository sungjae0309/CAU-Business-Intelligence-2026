"""Merge the monthly raw files, clean them, and write a summary.

Usage (run from the project folder):
    python src/clean.py

Output:
    data/processed/requests.parquet   (or .csv if pyarrow is missing)
    docs/data_summary.md
"""
from __future__ import annotations

import pandas as pd

from config import DOCS_DIR, PROCESSED_DIR, RAW_DIR


def load_raw() -> pd.DataFrame:
    files = sorted(RAW_DIR.glob("20[0-9][0-9]-[0-9][0-9].csv"))
    if not files:
        raise SystemExit("No monthly files in data/raw. Run: python src/collect.py")
    print(f"Reading {len(files)} monthly files...")
    return pd.concat((pd.read_csv(f, dtype=str) for f in files), ignore_index=True)


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    log = {"raw rows": len(df)}

    df = df.drop_duplicates("unique_key")
    log["after removing duplicate unique_key"] = len(df)

    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
    df["closed_date"] = pd.to_datetime(df["closed_date"], errors="coerce")
    df = df[df["created_date"].notna()].copy()
    log["after removing rows with no created_date"] = len(df)

    df["resolution_hours"] = (df["closed_date"] - df["created_date"]).dt.total_seconds() / 3600
    df["is_open"] = df["closed_date"].isna()

    bad = df["resolution_hours"] < 0
    log["removed: closed before created"] = int(bad.sum())
    df = df[~bad].copy()

    df["closed_same_second"] = df["resolution_hours"] == 0
    for col in ("latitude", "longitude"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["created_month"] = df["created_date"].dt.to_period("M").astype(str)
    log["final rows"] = len(df)
    return df, log


def summary(df: pd.DataFrame, log: dict) -> str:
    closed = df[~df["is_open"]]
    by_type = closed.groupby("complaint_type")["resolution_hours"]
    stats = pd.DataFrame({
        "requests": df.groupby("complaint_type").size(),
        "still open": df.groupby("complaint_type")["is_open"].sum(),
        "median hours": by_type.median().round(1),
        "p90 hours (top 10% line)": by_type.quantile(0.9).round(1),
    }).fillna(0)
    monthly = df.groupby(["created_month", "complaint_type"]).size().unstack(fill_value=0)

    lines = ["# Data summary", "", "## Cleaning steps", ""]
    lines += [f"- {k}: {v:,}" for k, v in log.items()]
    lines += ["", f"- closed in the same second as created: {int(df['closed_same_second'].sum()):,}",
              f"- missing latitude/longitude: {int(df['latitude'].isna().sum()):,}",
              "", "## By complaint type", "", stats.to_markdown(),
              "", "## Requests per month", "", monthly.to_markdown(), ""]
    return "\n".join(lines)


def main() -> None:
    df, log = clean(load_raw())
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    try:
        out = PROCESSED_DIR / "requests.parquet"
        df.to_parquet(out, index=False)
    except ImportError:
        out = PROCESSED_DIR / "requests.csv"
        df.to_csv(out, index=False)
    print(f"Saved {len(df):,} rows -> {out}")

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "data_summary.md").write_text(summary(df, log), encoding="utf-8")
    print("Wrote docs/data_summary.md")


if __name__ == "__main__":
    main()
