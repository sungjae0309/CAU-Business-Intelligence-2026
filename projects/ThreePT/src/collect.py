"""Download NYC 311 service requests month by month.

Usage (run from the project folder):
    python src/collect.py --list-types        # see exact complaint_type names
    python src/collect.py --sample 1000       # small test download
    python src/collect.py                     # full download (resumes where it stopped)
    python src/collect.py --force             # download every month again

Optional: set a free Socrata app token for higher rate limits
    export NYC_APP_TOKEN=your_token
"""
from __future__ import annotations

import argparse
import io
import os
import sys
import time
from datetime import date

import pandas as pd
import requests

from config import (COMPLAINT_TYPES, DATASET_URL, END_DATE, FIELDS,
                    PAGE_SIZE, RAW_DIR, START_DATE)


def make_session() -> requests.Session:
    s = requests.Session()
    token = os.environ.get("NYC_APP_TOKEN")
    if token:
        s.headers["X-App-Token"] = token
    else:
        print("[info] NYC_APP_TOKEN not set. It still works, but may be slower.")
    return s


def get(s: requests.Session, url: str, params: dict, retries: int = 6) -> requests.Response:
    """GET with retries for rate limits and server errors."""
    last_error = None
    for attempt in range(retries):
        try:
            r = s.get(url, params=params, timeout=180)
            if r.status_code == 200:
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                last_error = f"HTTP {r.status_code}"
            else:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
        except requests.RequestException as e:
            last_error = str(e)
        wait = 5 * (2 ** attempt)
        print(f"  [retry {attempt + 1}/{retries}] {last_error} -> waiting {wait}s")
        time.sleep(wait)
    raise RuntimeError(f"Request failed after {retries} tries: {last_error}")


def quote_list(values) -> str:
    return ", ".join("'" + v.replace("'", "''") + "'" for v in values)


def month_starts(start: str, end: str):
    y, m = map(int, start[:7].split("-"))
    end_d = date.fromisoformat(end)
    while date(y, m, 1) < end_d:
        nxt = (y + (m == 12), m % 12 + 1)
        yield date(y, m, 1), min(date(*nxt, 1), end_d)
        y, m = nxt


def where_clause(a: date, b: date, types) -> str:
    return (f"created_date >= '{a.isoformat()}T00:00:00' "
            f"AND created_date < '{b.isoformat()}T00:00:00' "
            f"AND complaint_type IN ({quote_list(types)})")


def list_types(s: requests.Session) -> None:
    params = {
        "$select": "complaint_type, count(*) AS n",
        "$where": f"created_date >= '{START_DATE}T00:00:00' AND created_date < '{END_DATE}T00:00:00'",
        "$group": "complaint_type",
        "$order": "n DESC",
        "$limit": 300,
    }
    rows = get(s, DATASET_URL + ".json", params).json()
    print(f"complaint_type counts, {START_DATE} to {END_DATE} (top {len(rows)}):\n")
    for row in rows:
        print(f"{int(row['n']):>12,}  {row['complaint_type']}")


def fetch(s: requests.Session, where: str, limit: int | None = None) -> pd.DataFrame:
    """Download all rows that match `where`, page by page."""
    frames, offset = [], 0
    while True:
        page_size = min(PAGE_SIZE, limit - offset) if limit else PAGE_SIZE
        params = {
            "$select": ", ".join(FIELDS),
            "$where": where,
            "$order": ":id",          # stable order, needed for paging
            "$limit": page_size,
            "$offset": offset,
        }
        text = get(s, DATASET_URL + ".csv", params).text
        if not text.strip():
            break
        page = pd.read_csv(io.StringIO(text), dtype=str)
        frames.append(page)
        offset += len(page)
        print(f"    page: {len(page):,} rows (total {offset:,})")
        if len(page) < page_size or (limit and offset >= limit):
            break
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=FIELDS)


def save(df: pd.DataFrame, path) -> None:
    tmp = path.with_suffix(".tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(path)          # write fully, then rename: no half files


def sample(s: requests.Session, n: int) -> None:
    a, b = next(month_starts(START_DATE, END_DATE))
    frames = []
    for t in COMPLAINT_TYPES:
        print(f"[sample] {t}")
        frames.append(fetch(s, where_clause(a, b, [t]), limit=n))
    df = pd.concat(frames, ignore_index=True)
    out = RAW_DIR / "sample.csv"
    save(df, out)
    print(f"\nSaved {len(df):,} rows -> {out}")
    print(df.groupby("complaint_type").size().to_string())
    print("\nMissing values (%):")
    print((df.isna().mean() * 100).round(1).to_string())


def collect_all(s: requests.Session, force: bool) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for a, b in month_starts(START_DATE, END_DATE):
        out = RAW_DIR / f"{a:%Y-%m}.csv"
        if out.exists() and not force:
            print(f"[skip] {out.name} already exists")
            continue
        print(f"[month] {a:%Y-%m}")
        df = fetch(s, where_clause(a, b, COMPLAINT_TYPES))
        save(df, out)
        total += len(df)
        print(f"  saved {len(df):,} rows -> {out.name}")
    print(f"\nDone. {total:,} new rows downloaded.")


def main() -> None:
    p = argparse.ArgumentParser(description="Download NYC 311 data")
    p.add_argument("--list-types", action="store_true", help="show complaint_type names and counts")
    p.add_argument("--sample", type=int, metavar="N", help="download N rows per type from the first month")
    p.add_argument("--force", action="store_true", help="download months again even if files exist")
    args = p.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    s = make_session()
    if args.list_types:
        list_types(s)
    elif args.sample:
        sample(s, args.sample)
    else:
        collect_all(s, args.force)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nStopped. Run again to continue from the next month.")
