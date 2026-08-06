# cropland — layer documentation

**Map**: unknown — no ArcGIS Pro project is referenced by the script or git history; the only output is a CSV table, not a spatial layer.
**Script**: `main.py` (branch `rainfall` at commit `773ccee`, last touched 2026-07-15; originally added 2024-10-21 as "Add cropland processing")
**Overview**: A tabular analysis rather than a layer-producing project: it tallies the area (hectares) of five fruit-crop classes from the USDA Cropland Data Layer within each contiguous US state and writes the result as a CSV. It produces no rasters or geopackages. Note the script writes its output to the project directory (`cropland/`), not to `output/` — this directory exists only to hold this documentation.

> Entries were reconstructed from `main.py`, `pyproject.toml`, the `mapprep` package, and git history on 2026-07-18, after the fact. Rationale marked *(reconstructed)* is inferred from code and commit messages, not a firsthand record of the decisions. No output files exist locally, so each entry documents what the script declares.

## fruit_areas_by_state.csv
*(declared by the script, not present locally — written to the project directory, not `output/`)*

- **Role**: Summary table of fruit-crop area by state — one row per contiguous US state (48 states + DC), columns `state`, `Apples`, `Cherries`, `Melons`, `Oranges`, `Strawberries`, values in hectares.
- **Source**: USDA NASS Cropland Data Layer, 2023, 30 m (`2023_30m_cdls.tif`, expected in the project directory; not tracked in git and not present locally). State boundaries from Natural Earth 50m admin-1 states & provinces (lakes version) via `mapprep/natural_earth.py` `us_states(contiguous=True)` (`$NATURAL_EARTH_DIR/StatesProvinces/ne_50m_admin_1_states_provinces_lakes`), which filters to `iso_a2 == 'US'` excluding Alaska, Hawaii, Puerto Rico.
- **Processing**: States are reprojected to the CDL raster's CRS if they differ. For each state, `rasterio.mask.mask(..., crop=True)` clips the raster to the state geometry, then pixels equal to each CDL class code are counted: 68 (Apples), 66 (Cherries), 213 (Melons), 212 (Oranges), 221 (Strawberries) — the crop names come from the script's `fruit_name_map`. Pixel counts convert to hectares as `count * 900 / 10_000` (30 m × 30 m = 900 m² per pixel). Results assembled with pandas and written with `df.to_csv(..., index=False)`.
- **Rationale** *(reconstructed)*: Why these five fruit classes, and what map or analysis the table was for, is unknown — neither the code, comments, nor the commit message ("Add cropland processing") says. The pixel-count-times-cell-area approach is the standard way to get class areas from the CDL's 30 m grid.
- **Facts**: not extracted (file not present)
