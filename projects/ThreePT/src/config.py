"""Settings for collecting NYC 311 data.

Change the values here, not inside the scripts.
"""
from pathlib import Path

# NYC 311 Service Requests from 2020 to Present (Socrata dataset id: erm2-nwe9)
DATASET_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9"

# Period to collect: START_DATE is included, END_DATE is excluded.
START_DATE = "2023-01-01"
END_DATE = "2025-01-01"

# Exact complaint_type values as they appear in the data.
# Check the real names first with:  python src/collect.py --list-types
# then edit this list.
COMPLAINT_TYPES = [
    "HEAT/HOT WATER",
    "Noise - Residential",
    "Street Condition",
]

# Columns to download (smaller download, faster).
FIELDS = [
    "unique_key",
    "created_date",
    "closed_date",
    "agency",
    "agency_name",
    "complaint_type",
    "descriptor",
    "location_type",
    "incident_zip",
    "borough",
    "latitude",
    "longitude",
    "open_data_channel_type",
    "status",
]

# Rows per request. Socrata allows up to 50,000 per page.
PAGE_SIZE = 50_000

# ---- Model dataset (src/build_dataset.py) ----

# Date the raw data was downloaded. Requests still open on this date are judged against it.
DATA_COLLECTED_ON = "2026-11-24"

# Complaint types kept in the model dataset (team decision pending: drop "Noise - Residential"?).
MODEL_TYPES = [
    "HEAT/HOT WATER",
    "Noise - Residential",
    "Street Condition",
]

# Long delay = time to close above this quantile of its type, computed on the train period only.
LONG_DELAY_QUANTILE = 0.9

# Fixed limit in hours per type, e.g. {"HEAT/HOT WATER": 72}. A type listed here ignores the quantile.
LONG_DELAY_HOURS: dict[str, float] = {}

# Requests closed in the same second as created (mostly Street Condition) are left out.
DROP_SAME_SECOND = True

# Time split by created_date: start included, end excluded.
SPLITS = {
    "train": ("2023-01-01", "2024-01-01"),
    "valid": ("2024-01-01", "2024-07-01"),
    "test": ("2024-07-01", "2025-01-01"),
}

# Repeated reports: same type, within NEARBY_METERS (grid), within RECENT_DAYS.
NEARBY_METERS = 100
RECENT_DAYS = 7

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
DOCS_DIR = ROOT / "docs"
