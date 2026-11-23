# Data spec (draft)

## Source

- NYC 311 Service Requests from 2020 to Present (NYC Open Data, dataset id `erm2-nwe9`)
- Collected with `src/collect.py` on: (date)

## Scope

- Period: 2023-01-01 to 2024-12-31
- Complaint types: (fill in after `--list-types`)

## Columns

| Column | Meaning | Note |
| --- | --- | --- |
| unique_key | ID of one request | used to remove duplicates |
| created_date | when the request was made | |
| closed_date | when the request was closed | empty = still open |
| agency / agency_name | department in charge | |
| complaint_type / descriptor | type and detail of the problem | |
| location_type | e.g. residential building, street | |
| incident_zip / borough | area | |
| latitude / longitude | location | some are missing |
| open_data_channel_type | online, phone, mobile, other | |
| status | current status | |
| resolution_hours | closed_date − created_date in hours | added in `clean.py` |
| is_open | no closed_date yet | added in `clean.py` |

## Cleaning rules

- Remove duplicate `unique_key`
- Remove rows with no `created_date`
- Remove rows closed before they were created
- Keep open requests, but mark them with `is_open` (how to use them: decide with the team)

## Open questions

- Long delay label: top 10% of resolution time within each type, or the city's time limit?
- How to handle requests that are still open?
