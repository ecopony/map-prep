# conferences — layer documentation

**Map**: unknown — no matching ArcGIS Pro project is named in the code; presumably an ACC conference-realignment map.
**Script**: `acc.py` (commit 42d8980 "Add ACC dataset creation", 2024-06-13)
**Overview**: A small one-off project charting the geographic footprint of the ACC athletic conference at three points in time (1984, 2024, 2025) as school-location point layers, with US state boundaries for reference. It is only partly a map-layer project: the script writes `output/acc.gpkg` (the layers below), but its second half renders an interactive Plotly figure — convex hulls of each snapshot's schools over an Albers USA basemap, titled "ACC Conference Footprints for 1984, 2024, and 2025" — via `fig.show()` only; nothing from that figure is saved to disk. Three throwaway `GeoDataFrame.plot()` calls are likewise never saved. The school data (names, cities, join/leave years) and city coordinates are hardcoded in the script, not fetched from any dataset. Note the project predates the uv workspace and has no `pyproject.toml`; it also imports `plotly`, which the workspace does not declare, so it may not run under the root `.venv` as-is.

> Entries were reconstructed from `acc.py` and git history on 2026-07-18, long after the script was written. The `output/` directory is empty — every file below is declared by the script but not present locally, so no Facts could be extracted. Rationale marked *(reconstructed)* is inferred from code, not a firsthand record of the decisions.

## acc.gpkg
Declared by the script, not present locally. All four layers are written in EPSG:4326.

### us_states_50m
- **Role**: State boundary reference layer under the school points.
- **Source**: Natural Earth 50m admin-1 states & provinces (lakes version), `$NATURAL_EARTH_DIR/StatesProvinces/ne_50m_admin_1_states_provinces_lakes` (env var loaded from the repo-root `.env`).
- **Processing**: Read with geopandas, filtered to `iso_a2 == 'US'` — unlike later projects there is no contiguous-US filter, so Alaska, Hawaii, and territories flagged `US` are included. Predates the `mapprep/natural_earth.py` helpers; the filter is inline in `acc.py`.
- **Rationale** *(reconstructed)*: unknown beyond needing state outlines for context; keeping all US admin-1 units is plausibly deliberate since the Plotly figure uses an `albers usa` projection (which handles AK/HI), but the code doesn't say.
- **Facts**: not extracted (file not present)

### acc_schools_1984
- **Role**: ACC member-school locations as of 1984 — the "before realignment" snapshot.
- **Source**: Hardcoded dicts in `acc.py`: 19 schools with city, `Year_Joined`, `Year_Left`, and hand-entered lat/lon per city (approximate campus/city coordinates; provenance of the coordinates is not recorded).
- **Processing**: pandas DataFrame → geopandas points from the lat/lon columns (EPSG:4326), then filtered to `Year_Joined <= 1984` and (`Year_Left` null or `> 1984`). Yields the 7 remaining 1953 charter members plus Georgia Tech (1979) — 8 schools, including Maryland (which left in 2014).
- **Rationale** *(reconstructed)*: 1984 as the "classic ACC" snapshot year — why 1984 specifically rather than another pre-expansion year is unknown.
- **Facts**: not extracted (file not present)

### acc_schools_2024
- **Role**: ACC member-school locations for the 2024 snapshot — the conference just before the 2024 West Coast/SMU expansion.
- **Source**: Same hardcoded data as `acc_schools_1984`.
- **Processing**: Same point GeoDataFrame, filtered to `Year_Joined <= 2023` and (`Year_Left` null or `> 2024`) — 15 schools: excludes Maryland (left 2014) and the three 2024 joiners (Cal, SMU, Stanford).
- **Rationale** *(reconstructed)*: The `<= 2023` cutoff (rather than `<= 2024`) makes this layer represent membership *before* the 2024 additions, so the 2024 vs 2025 pair contrasts pre- and post-expansion footprints. That reading is inferred from the filter values; the script has no comment explaining it.
- **Facts**: not extracted (file not present)

### acc_schools_2025
- **Role**: ACC member-school locations for the 2025 snapshot — the post-expansion, coast-to-coast footprint.
- **Source**: Same hardcoded data as above.
- **Processing**: Filtered to `Year_Joined <= 2024` and (`Year_Left` null or `> 2025`) — 18 schools: everyone except Maryland, now including Cal, SMU, and Stanford.
- **Rationale** *(reconstructed)*: Captures the dramatic westward stretch of the convex-hull footprint after the 2024 realignment, which is the point of the Plotly comparison figure.
- **Facts**: not extracted (file not present)
