# property-rainwater — layer documentation

**Map**: Property rainwater-harvest site plans (personal; planning brief in
`mapmaking/projects/property-rainwater-harvest/brief.md`)
**Script**: `main.py` + `lidar.py` (uncommitted, 2026-07-21). `lidar.py` needs the
PDAL CLI from conda (`conda create -n pdal -c conda-forge pdal`; env `PDAL_EXE`
overrides discovery) and runs after `main.py` (it stamps heights onto its
`buildings` layer).
**Overview**: Reusable property-scale water-flow analysis for planning Brad
Lancaster-style rainwater-harvesting earthworks (basins, berms on contour, overflow
routes). Site location comes from CLI flags or `SITE_*` variables in the untracked
repo-root `.env`; **street addresses, coordinates, and raster bounds are deliberately
kept out of this file and all tracked files** — resolve them from `.env` or the local
outputs. Each site's layers land in `output/<SITE_SLUG>/` (gitignored). The analysis
extent should be a box much larger than the parcel (~1 km for a lot-sized site) so flow
accumulation captures run-on from uphill. Draw order in ArcGIS: hillshade backdrop →
flow_accum_log (transparent-to-blue ramp) → contours faint → flowpaths bold → address
point. CRS per site: NAD83 UTM zone derived from the bbox (meters; NAVD88 meters
vertical). Facts below are from the first site's run (a ~1.1 × 1.1 km Tucson-area
foothills extent); regenerate per site.

## <slug>/dem_1m.tif
- **Role**: Base elevation surface every other layer derives from; sample it when
  checking basin depths and berm heights.
- **Source**: USGS 3DEP 1 m DEM tiles fetched keyless from The National Map products
  API (`fetch_tnm_dem_1m` in `main.py`), cached in `cache/tnm/`. Public domain. For the
  first site: project AZ_PimaCounty_2021_B21, derived from Sep–Nov 2021 lidar
  (20.6 pts/m²).
- **Processing**: Tiles from the newest-acquisition project mosaicked and warped to the
  site's NAD83 UTM zone at 1 m (bilinear), clipped to the site bbox.
- **Rationale**: OpenTopography's `/API/usgsdem` rejects non-academic API keys (401),
  so TNM is the access path. Where lidar projects overlap, newest acquisition year
  (parsed from the project name) wins — publication date is misleading (a 2018
  acquisition here was published in 2025, after the 2021 one). 1 m 3DEP is sufficient
  for flow planning; a finer DTM gridded from the source point cloud (EPT on
  `usgs-lidar-public` S3) is a per-site phase 2. 2026-07-21: switched output CRS from
  hardcoded EPSG:6341 to per-site NAD83 UTM (26900+zone) when the project became a
  reusable tool; NAD83 keeps the datum of the source tiles.
- **Facts** *(extracted 2026-07-21, first site; bounds redacted — site privacy)*:
  EPSG:26912, 1131x1110 px @ 1 m, float32, nodata=-999999.0, overviews none, deflate,
  3.4 MB. ~54 m of relief across the extent.

## <slug>/hillshade.tif
- **Role**: Backdrop for reading terrain under the hydrology layers.
- **Source**: Derived from `dem_1m.tif`.
- **Processing**: `mapprep/hillshade.py` `from_dem`, multi-directional, z_factor 1
  (projected meters over NAVD88 meters — no exaggeration needed at lot-scale relief).
- **Rationale**: Multi-directional over single-azimuth so shadow-side rills don't
  vanish; drainage detail is the whole point.
- **Facts** *(extracted 2026-07-21, first site; bounds redacted)*: EPSG:26912,
  1131x1110 px @ 1 m, uint8, nodata=0.0, overviews none, deflate, 0.9 MB.

## <slug>/slope_degrees.tif
- **Role**: Constraint layer for earthworks: Lancaster's berm-and-basin guidance is
  slope-banded (roughly: sheet mulch <2°, basins to ~8°, terraces/check dams above).
- **Source**: Derived from `dem_1m.tif`.
- **Processing**: `gdal.DEMProcessing` slope, degrees.
- **Rationale**: Degrees not percent to match the permaculture literature's bands.
- **Facts** *(extracted 2026-07-21, first site; bounds redacted)*: EPSG:26912,
  1131x1110 px @ 1 m, float32, nodata=-9999.0, overviews none, deflate, 4.5 MB.

## <slug>/flow_accum_log.tif
- **Role**: The "where does water concentrate" display surface — style with a
  transparent-to-blue ramp over the hillshade.
- **Source**: Derived from `dem_1m.tif` via WhiteboxTools.
- **Processing**: `breach_depressions_least_cost` (dist=100, fill=True) →
  `d_inf_flow_accumulation`, out_type=catchment area, log-transformed. Conditioned DEM
  and D8 intermediates cached in `cache/wbt/<slug>/`.
- **Rationale**: **Breach, not fill**: filling depressions would erase exactly the
  natural basins rainwater harvesting wants to find and enlarge; breaching only carves
  through digital dams. D-infinity for display because it disperses realistically on
  hillslopes instead of D8's parallel-line artifacts; log-scaled because the raw range
  spans ~6 orders of magnitude and would symbolize as all-or-nothing.
- **Facts** *(extracted 2026-07-21, first site; bounds redacted)*: EPSG:26912,
  1131x1110 px @ 1 m, float64, nodata=-999999.0, overviews none, uncompressed, 10.1 MB.

## <slug>/dtm_50cm.tif
- **Role**: Bare-earth surface at design resolution — finer basin/berm geometry than
  the 1 m DEM; the surface to contour for construction drawings.
- **Source**: Source lidar point cloud via EPT (`SITE_EPT_URL`; here the 2021 PAG/USGS
  collection on the `usgs-lidar-public` S3 bucket, 20.6 pts/m²).
- **Processing**: `lidar.py`: one EPT fetch of the site bbox → reproject to site UTM →
  cached LAZ (`cache/lidar/<slug>/`) → PDAL `writers.gdal` IDW of class-2 (ground)
  returns at 0.5 m, `window_size=6` to interpolate small gaps under canopy. Explicit
  `bounds` pin DTM/DSM to an identical grid.
- **Rationale**: 0.5 m is justified by the collection's density (≥8 pts/m² needed;
  this one has ~20). IDW-of-ground is the standard bare-earth grid. Range check:
  matches the 1 m 3DEP DEM's min/max exactly (same source lidar) — good cross-check.
- **Facts** *(extracted 2026-07-21, first site; bounds redacted)*: EPSG:26912,
  2263x2220 px @ 0.5 m, float32, nodata=-9999.0, deflate, 13.4 MB.

## <slug>/dsm_50cm.tif
- **Role**: Highest-surface model (roofs, tree canopy) — input to the nDSM; also
  useful for shade studies.
- **Source**: Same cached LAZ as the DTM.
- **Processing**: PDAL `writers.gdal` max of first returns (`ReturnNumber[1:1]`),
  noise classes 7/18 excluded, same 0.5 m pinned grid.
- **Rationale**: First-return max is the conventional DSM; median would eat narrow
  roof ridges at 0.5 m.
- **Facts** *(extracted 2026-07-21, first site; bounds redacted)*: EPSG:26912,
  2263x2220 px @ 0.5 m, float32, nodata=-9999.0, deflate, 7.3 MB.

## <slug>/ndsm_50cm.tif
- **Role**: Height-above-ground of everything (roofs, trees) — the "roof height"
  answer, and a canopy map for planning shade/planting.
- **Source**: Derived: DSM − DTM.
- **Processing**: `lidar.py` rasterio subtraction on the shared grid; negatives
  clamped to 0.
- **Rationale**: Identical pinned grids mean no resampling error. First site: values
  0–~35 m (tallest = trees, not buildings; building medians run 1.7–9.6 m).
- **Facts** *(extracted 2026-07-21, first site; bounds redacted)*: EPSG:26912,
  2263x2220 px @ 0.5 m, float32, nodata=-9999.0, deflate, 13.4 MB.

## <slug>/site.gpkg

### flowpaths
- **Role**: Discrete concentrated-flow lines — the wash/rill network to design around
  (intercept, spread, or respect-and-overflow-into).
- **Source**: Derived from `dem_1m.tif` via WhiteboxTools D8 chain.
- **Processing**: `d8_flow_accumulation` (catchment area, m²) → `extract_streams` at
  `--stream-threshold` (default **1000 m²** upslope) → `raster_streams_to_vector`.
  `STRM_VAL` is the stream-link ID from extraction (not magnitude).
- **Rationale**: 1000 m² (0.1 ha) default is deliberately low — at lot scale the rills
  that matter drain fractions of a hectare; a conventional basin-scale threshold would
  show nothing on a residential parcel. First site: a flowpath passes within ~3 m of
  the geocoded address point — verify against the real parcel boundary.
- **Facts** *(extracted 2026-07-21, first site)*: EPSG:26912, LineString, 594 features,
  fields [STRM_VAL].

### contours_25cm
- **Role**: Layout layer for placing berms and basins *on contour*; field-checkable
  with an A-frame level.
- **Source**: Derived from `dem_1m.tif`.
- **Processing**: `gdal.ContourGenerate`, 0.25 m interval, `elev_m` in NAVD88 meters.
- **Rationale**: 0.25 m is fine enough to lay out lot-scale earthworks but coarse
  enough that a 1 m DEM isn't just contouring its own noise.
- **Facts** *(extracted 2026-07-21, first site)*: EPSG:26912, LineString, 2250
  features, fields [id, elev_m].

### buildings
- **Role**: Roof catchment polygons — the roof-area side of the water budget; with
  lidar heights, also the cistern/gutter planning layer.
- **Source**: ArcGIS REST layer from `--footprints-url` / `SITE_FOOTPRINTS_URL` (first
  site: Pima County `GISOpenData/LandRecords/MapServer/3`, Bing-derived footprints —
  found via the gisopendata.pima.gov Hub search API; the gisdata.pima.gov host allows
  scripted queries, gis.pima.gov 403s them).
- **Processing**: Bbox envelope query (`fetch_arcgis_layer` in `main.py`), reprojected
  to site UTM. `lidar.py` appends `height_med_m` (median nDSM inside the footprint —
  resists ground bleed at edges) and `height_max_m` (ridge line).
- **Rationale**: County footprints over OSM for completeness in low-OSM suburbs.
  First site: 198/203 stamped (the rest are slivers with no nDSM cells); nearest
  footprint sits ~11 m from the geocoded address point, median 2.9 m / ridge 4.1 m.
- **Facts** *(extracted 2026-07-21, first site)*: EPSG:26912, Polygon, 203 features,
  10 fields incl. height_med_m, height_max_m.

### parcels
- **Role**: Legal boundaries — replaces the geocoded point for any on-parcel /
  off-parcel judgment (which flowpaths actually cross the property).
- **Source**: ArcGIS REST layer from `--parcels-url` / `SITE_PARCELS_URL` (first site:
  Pima County `GISOpenData/LandRecords/MapServer/12`, Parcels - Regional).
- **Processing**: Same bbox envelope query, reprojected to site UTM. All source
  attributes kept (APN in `PARCEL`).
- **Rationale**: Assessor parcels are authoritative where geocoding is approximate.
- **Facts** *(extracted 2026-07-21, first site)*: EPSG:26912, Polygon, 201 features,
  50 fields.

### address_point
- **Role**: Reference marker for the property until the real parcel polygon is added.
- **Source**: Geocoded address from `--lon`/`--lat` (env `SITE_LON`/`SITE_LAT`); label
  from `SITE_ADDRESS`.
- **Processing**: Point reprojected from WGS84 to the site UTM.
- **Rationale**: Geocoder points land near the street centerline, not the lot
  centroid — replace with the assessor parcel (for Pima County:
  gisopendata.pima.gov) before trusting any on-parcel/off-parcel judgment.
- **Facts** *(extracted 2026-07-21, first site)*: EPSG:26912, Point, 1 features,
  fields [name].
