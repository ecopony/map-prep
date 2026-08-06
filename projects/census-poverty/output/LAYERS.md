# census-poverty — layer documentation

**Map**: County-level poverty choropleths, joined to Natural Earth county polygons in ArcGIS Pro (specific ArcGIS project name unknown; the README says the NM-vs-OR comparison recreates an analysis "from the blog post")
**Script**: `main.py` (commit `b945ee5` "Add poverty data script", 2025-09-28)
**Overview**: Tabular project, not raster/vector: fetches county poverty counts from the Census Bureau ACS 5-year API (table C17002, ratio of income to poverty level) and writes join-ready CSVs. Each CSV carries a `Geography` key in `USA-SSFFF` format intended to join against the Natural Earth county `ADM2_CODE` field in ArcGIS Pro, plus a computed poverty rate to symbolize. `main.py` is a demo driver that runs several state combinations; the real interface is `census_poverty.py` (`fetch_poverty_comparison` / `CensusPovertyData`), so the set of CSVs in `output/` depends on which calls have been run. Raw API responses are cached per state/year/threshold in `cache/*.json`.

> Entries were reconstructed from `main.py`, `census_poverty.py`, `README.md`, and `cache/` contents on 2026-07-18, long after the project was built (no output files exist locally). Rationale marked *(reconstructed)* is inferred from code and comments, not a firsthand record of the decisions.

All five CSVs below are **declared by the script, not present locally** — they are what `uv run main.py` would write today (filenames follow `{threshold}-percent-poverty-{states}-{year}.csv`; the year defaults to 2023 in `fetch_poverty_comparison`). They share one schema and processing chain, described once here:

- **Source**: U.S. Census Bureau API, ACS 5-Year Estimates (`https://api.census.gov/data/{year}/acs/acs5`), table C17002 "Ratio of Income to Poverty Level in the Past 12 Months", queried per county within each state. No API key used. Responses cached as `cache/poverty_{year}_{state_fips}_{threshold}.json` with no expiration.
- **Processing**: `census_poverty.py` `CensusPovertyData.fetch_poverty_data` → `_fetch_state_poverty_data` sums the C17002 bins for the requested threshold (100%: `_002E`–`_003E`; 150%: `_002E`–`_005E`; 200%: `_002E`–`_007E`) against total `C17002_001E`; `_process_poverty_data` strips " County, State" from names, computes `PovertyRate{t} = Below{t}Percent / TotalPopulation * 100` (rounded to 2 dp), rewrites `Geography` from `0500000USSSFFF` to `USA-SSFFF`, and sorts by rate descending. Written by `export_for_gis` (plain `df.to_csv`, no index).
- **Columns**: `Geography`, `Name`, `State`, `County`, `TotalPopulation`, `Below{t}Percent`, `PovertyRate{t}` (the README's column list omits `County` and cites table B06012 — the code uses C17002; the code is authoritative).
- **Rationale** *(reconstructed)*: The module docstring and README frame the project as replacing manual CSV downloads from the Census website with reproducible API calls. The `USA-` Geography prefix exists specifically to match Natural Earth `ADM2_CODE` for ArcGIS joins (per README "GIS Integration"). Why C17002 rather than a direct poverty table: unknown, though C17002's cumulative income-ratio bins are what make the 100/150/200% thresholds possible from one table.

## 200-percent-poverty-new-mexico-oregon-2023.csv
- **Role**: The original two-state comparison — counties of New Mexico and Oregon with share of population below 200% of the federal poverty level, for a side-by-side choropleth. `main.py` labels it a recreation of the blog-post analysis.
- **Facts**: not extracted (file not present). Cache shows real fetches exist for NM and OR at 2023/200% (`poverty_2023_35_200.json`, `poverty_2023_41_200.json`).

## 200-percent-poverty-california-2023.csv
- **Role**: Single-state example — all California counties at the 200% threshold.
- **Facts**: not extracted (file not present). No California cache file exists, so this run has not been made with the current cache.

## 150-percent-poverty-oregon-washington-idaho-2023.csv
- **Role**: Multi-state example — OR/WA/ID counties at the 150% threshold, demonstrating a non-default threshold.
- **Facts**: not extracted (file not present). No matching cache files exist.

## 100-percent-poverty-new-mexico-2023.csv
- **Role**: Half of a threshold-sensitivity comparison — New Mexico at the strict 100% federal poverty line; `main.py` prints its mean rate against the 200% run.
- **Facts**: not extracted (file not present). Cache holds NM at 100% only for year 2022 (`poverty_2022_35_100.json`), not 2023, so a fresh run would hit the API.

## 200-percent-poverty-new-mexico-2023.csv
- **Role**: Other half of the threshold comparison — New Mexico at 200%, same data as the NM side of the two-state CSV above.
- **Facts**: not extracted (file not present). Backed by cache `poverty_2023_35_200.json`.
