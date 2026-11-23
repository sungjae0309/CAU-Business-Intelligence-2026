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

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
DOCS_DIR = ROOT / "docs"
