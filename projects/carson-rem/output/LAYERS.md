# carson-rem — layer documentation

**Map**: Carson River relative elevation model map (ArcGIS Pro project name unknown; the geopackage follows the `output/<project>.gpkg` convention)
**Script**: `main.py` (commit 773ccee on `main`; project first committed 2024-10-05 as "Add Carson River prep", 57e3bd5)
**Overview**: A river relative-elevation-model (REM) map of the Carson River. The script writes two Natural Earth reference layers into `carson-rem.gpkg`, then runs RiverREM's `REMMaker` on a pre-merged DEM (`input/merged-dem.tif`) to detrend elevations relative to the river's water surface and render a color visualization (`mako_r` colormap) into `output/rem-maker/`. The DEM input and all REM outputs are absent locally — only the geopackage remains on disk (last written 2024-10-02).

> Entries were reconstructed from `main.py`, `pyproject.toml`, the `mapprep` package, and git history on 2026-07-18, long after the layers were created. Rationale marked *(reconstructed)* is inferred from code and commit messages, not a firsthand record of the decisions.

## carson-rem.gpkg

### us_states
- **Role**: State boundary reference layer.
- **Source**: Natural Earth 50m admin-1 states & provinces (lakes version), `$NATURAL_EARTH_DIR/StatesProvinces/ne_50m_admin_1_states_provinces_lakes`.
- **Processing**: `mapprep/natural_earth.py` `us_states(contiguous=True)` — filtered to `iso_a2 == 'US'`, excluding Alaska, Hawaii, Puerto Rico; written unmodified via GeoPandas. 49 features = 48 states + DC. (The file on disk predates the uv-workspace refactor; it was written by the original script's equivalent `us_states_50m_contiguous()` helper, same underlying dataset and filter.)
- **Rationale** *(reconstructed)*: Standard locator/reference linework; why a full contiguous-US layer for a single-river map is not recorded — likely a locator inset or overview frame, but unknown.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Unknown, 49 features, fields [featurecla, scalerank, adm1_code, diss_me, iso_3166_2, wikipedia, iso_a2, adm0_sr, ... (121 total)]

### us_country
- **Role**: Country boundary reference layer. Despite the layer name, it contains all North American countries, not just the US.
- **Source**: Natural Earth 50m admin-0 countries, `$NATURAL_EARTH_DIR/Countries/ne_50m_admin_0_countries`.
- **Processing**: `mapprep/natural_earth.py` `countries(continent='North America')` — filtered to `CONTINENT == 'North America'`; written unmodified. 38 features.
- **Rationale** *(reconstructed)*: Unknown; presumably context/neatline fill around the US states layer.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Unknown, 38 features, fields [featurecla, scalerank, LABELRANK, SOVEREIGNT, SOV_A3, ADM0_DIF, LEVEL, TYPE, ... (168 total)]

## rem-maker/ — declared by the script, not present locally
- **Role**: The thematic core of the map — the REM raster and its color visualization. The directory exists but is empty; the outputs were either never regenerated here or deleted.
- **Source**: `input/merged-dem.tif` (also missing locally). The name implies a DEM mosaic merged before this script runs; the source dataset and merge step are not in this repo — unknown. River centerline comes from OpenStreetMap, queried by RiverREM via osmnx (the project's `.osm_cache/` directory is its cache location, now empty).
- **Processing**: `riverrem.REMMaker` (installed from the OpenTopography GitHub repo — PyPI's `riverrem` is a dead stub; see `pyproject.toml`). `REMMaker(dem='input/merged-dem.tif', out_dir='output/rem-maker')`, then `make_rem()` — samples DEM elevations along the OSM river centerline, interpolates a water-surface trend, and subtracts it from the DEM to produce the REM GeoTIFF — and `make_rem_viz(cmap='mako_r')`, which renders a hillshade-blended color visualization of the REM. All other REMMaker parameters left at defaults.
- **Rationale** *(reconstructed)*: REMs are the standard technique for revealing floodplain features (meander scars, oxbows, terraces) invisible in absolute elevation; `mako_r` is a perceptually-uniform blue-dominant colormap conventional for water-themed REM renders. No parameter tuning is recorded.
- **Facts**: not extracted (directory is empty).

## Other notes
- `willie/` contains only empty directories (`big/`, `in/`, `out/`); its purpose is not recorded anywhere in code or git history — unknown.
- `.cache/` and `.osm_cache/` are empty cache directories left behind by RiverREM/osmnx runs.
