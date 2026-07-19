# rainfall — layer documentation

**Map**: CONUS annual rainfall map (ArcGIS Pro project: Rainfall)
**Script**: `main.py` (branch `rainfall`, not yet committed as of 2026-07-18)
**Overview**: Annual precipitation classes for the contiguous US, drawn as smooth polygon bands over a shaded-relief backdrop, with state boundaries and major cities for reference. Two relief backdrops were produced to compare in ArcGIS: Tom Patterson's Natural Earth manual shaded relief vs a multi-directional hillshade of the Copernicus GLO-90 DEM. The map frame is EPSG:5070 (CONUS Albers); the relief raster bounds (-140, 16.5, -56, 57) are the frame extent transformed to lat/lon and rounded out, so the reprojected rasters cover the whole layout rather than just CONUS.

> Entries were reconstructed from `main.py` and the `mapprep` package on 2026-07-18, after the layers were created. Rationale marked *(reconstructed)* is inferred from code and comments, not a firsthand record of the decisions.

## rainfall.gpkg

### rainfall_classes
- **Role**: The thematic layer — annual precipitation bands to symbolize and label as discrete classes.
- **Source**: PRISM 30-year (1991–2020) annual precipitation normals, 2.5 arc-minute (~4 km), in mm. `$PRISM_DIR/prism_ppt_us_25m_2020_avg_30y/prism_ppt_us_25m_2020_avg_30y.tif` (PRISM Climate Group, Oregon State University).
- **Processing**: mm → inches via `mapprep/prism.py` `ppt_annual_normals_inches` (also writes the intermediate `prism_ppt_annual_inches.tif`), then classified and vectorized by `mapprep/raster.py` `classify_to_polygons` with breaks `[5, 10, 15, 20, 30, 40, 60, 80, 100]` inches, `smooth_sigma=2` (gaussian pre-smoothing of values — the main smooth-lines knob), `upsample=4` (removes the pixel staircase at class edges), `sieve_pixels=64` (merges patches smaller than 64 upsampled pixels into their largest neighbor — the de-speckling knob), `simplify_tolerance=0.02`° (coverage simplification; shared class boundaries stay aligned). One dissolved multipolygon per class with `lower`/`upper`/`label` fields ("< 5", "5-10", …, "> 100").
- **Rationale** *(reconstructed)*: Classified polygons rather than a continuous raster so the bands can be symbolized, labeled, and outlined discretely in ArcGIS; the breaks are conventional annual-precipitation classes in inches.
- **Facts** *(extracted 2026-07-18)*: EPSG:4269, MultiPolygon, 10 features, fields [class, lower, upper, label]

### us_states
- **Role**: State boundary linework / reference layer.
- **Source**: Natural Earth 50m admin-1 states & provinces (lakes version), `$NATURAL_EARTH_DIR/StatesProvinces/ne_50m_admin_1_states_provinces_lakes`.
- **Processing**: `mapprep/natural_earth.py` `us_states(contiguous=True)` — filtered to `iso_a2 == 'US'`, excluding Alaska, Hawaii, Puerto Rico. 49 features = 48 states + DC.
- **Rationale** *(reconstructed)*: 50m scale matches a CONUS-extent map; the lakes version keeps Great Lakes shorelines out of the state polygons.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, MultiPolygon, 49 features, fields [featurecla, scalerank, adm1_code, diss_me, iso_3166_2, wikipedia, iso_a2, adm0_sr, … (121 total)]

### populated_places
- **Role**: Major-city points for labeling.
- **Source**: Natural Earth 50m populated places (simple), `$NATURAL_EARTH_DIR/PopulatedPlaces/ne_50m_populated_places_simple`.
- **Processing**: `mapprep/natural_earth.py` `us_populated_places(min_population=500_000, contiguous=True)` — US places with `pop_max >= 500,000`, excluding Alaska, Hawaii, Puerto Rico.
- **Rationale** *(reconstructed)*: 500k threshold keeps the city count manageable (57 points) at CONUS scale; `pop_max` is metro-area population, so this reads as "major metros".
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Point, 57 features, fields [scalerank, natscale, labelrank, featurecla, name, namepar, namealt, nameascii, … (31 total)]

## prism_ppt_annual_inches.tif
- **Role**: Intermediate — PRISM annual normals converted from mm to inches. Kept on disk so the continuous surface can be inspected or rendered directly as an alternative to the classified polygons.
- **Source**: Same PRISM normals raster as `rainfall_classes` above.
- **Processing**: `mapprep/raster.py` `scale_values` with factor 1/25.4; nodata preserved.
- **Rationale** *(reconstructed)*: Converted to inches up front so the class breaks and any map labels are in the US-customary units the map uses.
- **Facts** *(extracted 2026-07-18)*: EPSG:4269, 1405x621 px @ 0.0416667 deg (2.5 arcmin), bounds (-125.0208, 24.0625, -66.4792, 49.9375), float32, nodata=-9999.0, overviews none, uncompressed, 3.5 MB

## relief_ne_msr.tif
- **Role**: Relief backdrop candidate A — Tom Patterson's manual shaded relief of the US (hand-tuned, painterly).
- **Source**: Natural Earth `US_MSR_10M` raster, `$NATURAL_EARTH_DIR/Raster/US_MSR_10M/US_MSR_10M/US_MSR.tif`.
- **Processing**: `mapprep/raster.py` `clip` to the map bounds (given in EPSG:4326; native EPSG:3857 kept), `dst_nodata=0` so area beyond the source extent is transparent-able.
- **Rationale** *(reconstructed)*: Produced alongside the COP90 hillshade specifically to compare the two backdrops in ArcGIS (per the comment in `main.py`). Note the MSR only covers the US, so bounds areas outside it are nodata.
- **Facts** *(extracted 2026-07-18)*: EPSG:3857, 12879x8122 px @ 726.053 units, bounds (-15584728.7111, 1862698.8722, -6233891.4844, 7760118.6729), uint8, nodata=0.0, overviews [2, 4, 8, 16, 32], deflate, 18.2 MB

## conus_cop90_dem.tif
- **Role**: Intermediate — elevation mosaic used to derive `relief_cop90_hillshade.tif`.
- **Source**: Copernicus GLO-90 DEM via the OpenTopography global DEM API (requires `OPEN_TOPOGRAPHY_API_KEY`); raw slabs cached in `cache/opentopography/`.
- **Processing**: `mapprep/dem.py` `fetch` — the bbox exceeds the API's per-request area limit, so it is fetched as 10 longitudinal slabs (0.02° overlap to avoid seams) and mosaicked with `gdal.Warp`, resampled to `resolution_arcsec=9` (~270 m) with average resampling.
- **Rationale** *(reconstructed)*: 9 arcsec is plenty for a CONUS-scale backdrop and keeps the mosaic ~1.2 GB instead of far larger at native 90 m; average resampling smooths rather than aliases.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, 33600x16200 px @ 0.0025 deg (9 arcsec), bounds (-140.0004, 16.5004, -56.0004, 57.0004), float32, nodata=None, overviews [2, 4, 8, 16, 32], deflate, 1206.7 MB

## relief_cop90_hillshade.tif
- **Role**: Relief backdrop candidate B — algorithmic hillshade covering the whole frame (including Canada/Mexico, which the NE MSR lacks).
- **Source**: Derived from `conus_cop90_dem.tif` above.
- **Processing**: `mapprep/hillshade.py` `from_dem` — GDAL DEMProcessing hillshade, `multi_directional=True`, `z_factor=3`, `scale=111120` (degrees-to-meters for the geographic DEM), `computeEdges`. Overviews built for fast display.
- **Rationale** *(reconstructed)*: Multi-directional avoids the flat look of single-azimuth shading on a continental extent; z_factor 3 exaggerates terrain that would otherwise read as flat at this scale. Produced to compare against the NE manual shaded relief.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, 33600x16200 px @ 0.0025 deg (9 arcsec), bounds (-140.0004, 16.5004, -56.0004, 57.0004), uint8, nodata=0.0, overviews [2, 4, 8, 16, 32], deflate, 233.4 MB
