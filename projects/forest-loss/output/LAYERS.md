# forest-loss — layer documentation

**Map**: Oregon forest loss map (ArcGIS Pro; the finished layout was exported as `ForestLossLayout.png`, so the Pro project is presumably named ForestLoss — not confirmed)
**Script**: `main.py` (committed 2024-09-03 as "Add forest loss processing", 713704c; current form reflects the 2026-07 uv-workspace and natural_earth kwarg refactors, 773ccee)
**Overview**: Reference and terrain layers for a map of forest loss centered on Oregon: a shaded-relief backdrop from SRTM 30 m tiles, a mosaicked forest-loss raster merged from tiles in `input/`, and Natural Earth vector layers that split Oregon from the rest of the US for figure/ground styling, plus Oregon cities for labeling. The finished layout PNG predates the committed script (2024-02-12 vs 2024-09-03), so the script is a cleaned-up record of processing that had already produced the map.

> Entries were reconstructed from `main.py`, the `mapprep` package, and git history on 2026-07-18, after the layers were created. Rationale marked *(reconstructed)* is inferred from code and commit messages, not a firsthand record of the decisions. Only `ForestLossLayout.png` exists locally; every other output is declared by the script but not present locally, so no facts could be extracted for them.

## ForestLossLayout.png
Final map export of the finished ArcGIS layout (committed 2024-02-12, "Add finished forest loss"), not a layer. 3300x2550 px, RGBA.

## forest-loss.gpkg — declared by the script, not present locally

### us_states
- **Role**: US state boundary reference layer.
- **Source**: Natural Earth 50m admin-1 states & provinces (lakes version), `$NATURAL_EARTH_DIR/StatesProvinces/ne_50m_admin_1_states_provinces_lakes`.
- **Processing**: `mapprep/natural_earth.py` `us_states(contiguous=True)` — filtered to `iso_a2 == 'US'`, excluding Alaska, Hawaii, Puerto Rico.
- **Rationale** *(reconstructed)*: unknown; presumably basemap context around Oregon. Why both this and the oregon/other_states split are exported is not recorded.
- **Facts**: not extracted — file not present locally.

### us_country
- **Role**: Country-polygon backdrop.
- **Source**: Natural Earth 50m admin-0 countries, `$NATURAL_EARTH_DIR/Countries/ne_50m_admin_0_countries`.
- **Processing**: `mapprep/natural_earth.py` `countries(continent='North America')` — all North American countries, not just the US (the layer name `us_country` understates it).
- **Rationale** *(reconstructed)*: unknown; the continent-wide filter suggests neighboring-country context (Canada/Mexico) at the map edges.
- **Facts**: not extracted — file not present locally.

### oregon
- **Role**: The focal state polygon, exported separately so it can be styled apart from the rest.
- **Source**: Natural Earth 50m admin-1 states & provinces (lakes version), as above.
- **Processing**: `mapprep/natural_earth.py` `states_provinces(include="Oregon")` — single feature matched on `name`.
- **Rationale** *(reconstructed)*: Splitting Oregon from `other_states` lets ArcGIS give the subject state and its surroundings different symbology (figure/ground); this intent is inferred from the include/exclude pairing in the code.
- **Facts**: not extracted — file not present locally.

### other_states
- **Role**: All non-Oregon states/provinces, the complement of `oregon` for muted surrounding-area styling.
- **Source**: Natural Earth 50m admin-1 states & provinces (lakes version), as above. Note this is the full global admin-1 dataset minus Oregon, not just US states.
- **Processing**: `mapprep/natural_earth.py` `states_provinces(exclude="Oregon")`.
- **Rationale** *(reconstructed)*: Complement of the `oregon` layer; see above.
- **Facts**: not extracted — file not present locally.

### us_populated_places
- **Role**: Oregon city points for labeling.
- **Source**: Natural Earth 10m populated places, `$NATURAL_EARTH_DIR/PopulatedPlaces/ne_10m_populated_places`.
- **Processing**: `mapprep/natural_earth.py` `us_populated_places(scale='10m', min_population=70000)` — US places with `POP_MAX >= 70,000` — then filtered in `main.py` to `ADM1NAME == 'Oregon'`.
- **Rationale** *(reconstructed)*: The 10m dataset and low 70k threshold fit a single-state map where mid-size cities matter; exact reasoning for 70,000 is unknown.
- **Facts**: not extracted — file not present locally.

## combined_forest_loss.tif — declared by the script, not present locally
- **Role**: The thematic raster — forest-loss tiles mosaicked into one GeoTIFF. Written to the project directory root, not `output/`.
- **Source**: unknown — merged from whatever `.tif` tiles sit in `forest-loss/input/`, which is not present locally and is not identified in code or commit messages.
- **Processing**: `mapprep/hillshade.py` `combine_tif_files('input', 'combined_forest_loss.tif')` — rasterio `merge` of all `input/*.tif`, metadata copied from the first tile. No reprojection, classification, or compression.
- **Rationale** *(reconstructed)*: unknown beyond needing the tiled source as a single raster for ArcGIS.
- **Facts**: not extracted — file not present locally.

## combined_raster.tif and hillshade_raster.tif — declared by the script, not present locally
- **Role**: Terrain intermediates/backdrop: an SRTM elevation mosaic and its hillshade. Written to the project directory root (hardcoded filenames in `generate_hillshade_raster`), not `output/`.
- **Source**: NASA SRTM 30 m `.hgt` tiles, distributed as zips in `$NASA_DIR/SRTM_30` and extracted to `$NASA_DIR/SRTM_30/output` by `mapprep/hillshade.py` `extract_zip_files`.
- **Processing**: `mapprep/hillshade.py` `generate_hillshade_raster` — rasterio `merge` of all extracted `.hgt` tiles into `combined_raster.tif`, then GDAL `DEMProcessing(..., 'hillshade')` with all-default parameters (single azimuth 315, z-factor 1, no scale correction for the geographic CRS) into `hillshade_raster.tif`.
- **Rationale** *(reconstructed)*: unknown; this predates the tuned `from_dem` hillshade helper used by later projects, and no parameter choices are recorded.
- **Facts**: not extracted — files not present locally.
