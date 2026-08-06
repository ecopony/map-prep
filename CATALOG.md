# Layer Catalog

Index of map-prep projects and their layer documentation. Each documented project keeps an `output/LAYERS.md` describing every layer it produces — cartographic role, source data, processing chain, and the rationale behind the choices. **Read a project's LAYERS.md before using its layers in a map**; the files alone don't tell you why they exist or how they were made.

Maintained by the `make-layer` skill (`.claude/skills/make-layer/`). Entries before 2026-07-18 were backfilled from code and git history — their rationale is marked *(reconstructed)* rather than a firsthand record.

## Documented projects

- [ambient-occlusion](ambient-occlusion/output/LAYERS.md) — Ambient-occlusion-style relief components per area (multi-scale blurred DEMs, their hillshades and slopes, and a slope-hillshade); all declared outputs currently absent locally
- [ca-poverty](ca-poverty/output/LAYERS.md) — California county poverty-rate choropleth (2022 ACS) comparing the Far North region with the rest of the state; notebook computes the statistics, outputs are final PNG exports only
- [ca-suicides](ca-suicides/output/LAYERS.md) — California county polygons (with CDPH-matching dissolved county groups) for a choropleth of 2018–2020 suicide rates by county
- [carson-rem](carson-rem/output/LAYERS.md) — Carson River relative elevation model: RiverREM detrends a merged DEM along the OSM river centerline, plus Natural Earth US states/countries reference layers in carson-rem.gpkg
- [census-poverty](census-poverty/output/LAYERS.md) — Census ACS 5-year county poverty rates (100/150/200% thresholds) fetched via API and written as CSVs keyed to join Natural Earth county polygons in ArcGIS Pro
- [chehalis-rem](chehalis-rem/output/LAYERS.md) — Empty riverrem REM working directory (likely REMMaker runs for Colorado, Deschutes, Rogue, Shenandoah, and Snake reaches, per subdirectory names); no script, data, or layers survive to document
- [conferences](conferences/output/LAYERS.md) — ACC conference membership snapshots (1984/2024/2025) as hardcoded school points plus NE 50m US states in acc.gpkg; also renders an unsaved Plotly footprint-comparison figure
- [crater-lake-hillshade](crater-lake-hillshade/output/LAYERS.md) — Finished poster exports only: a John Nelson-style tinted hillshade of Crater Lake, Oregon (SRTM DEM) plus a valley-mist relief variant; no script or reproducible layers exist
- [cropland](cropland/output/LAYERS.md) — Tabulates 2023 USDA Cropland Data Layer fruit-crop area (apples, cherries, melons, oranges, strawberries) in hectares per contiguous US state to a CSV; no spatial layers
- [forest-loss](forest-loss/output/LAYERS.md) — Oregon forest-loss map layers: SRTM 30 m hillshade backdrop, a mosaicked forest-loss raster from input tiles, and Natural Earth vectors splitting Oregon from surrounding states, plus Oregon cities; only the final layout PNG survives locally
- [hillshade](hillshade/output/LAYERS.md) — Experimental stylized terrain render: 15 numbered PNG stages compositing an elevation tint, traditional/multi-directional/low-light hillshades, valley mist, and slope shading over a DEM, ending in a final blended relief image
- [lighthouses](lighthouses/output/LAYERS.md) — Two finished poster-style ArcGIS layout exports (Washington and US West Coast lighthouses as glowing points on a dark basemap); no data layers or generating script
- [property-rainwater](property-rainwater/output/LAYERS.md) — Reusable property-scale water-flow analysis for planning Lancaster-style rainwater-harvesting earthworks: per-site 1 m 3DEP DEM, hillshade, slope, D∞ flow accumulation, 25 cm contours, extracted flowpaths, lidar 0.5 m DTM/DSM/nDSM (PDAL + EPT), and county parcels + building footprints stamped with lidar heights, under `output/<slug>/`; site locations live in untracked `.env` (`SITE_*`), never in tracked files
- [rainfall](rainfall/output/LAYERS.md) — CONUS annual precipitation classes (PRISM normals vectorized to smooth polygon bands) over shaded-relief backdrops, with states and major cities; includes two relief candidates to compare (Natural Earth manual shaded relief vs Copernicus GLO-90 hillshade)
- [ridge-maps](ridge-maps/output/LAYERS.md) — Ridgeline art print of Crater Lake, OR: 50 stacked SRTM elevation profiles rendered as a green line plot (crater-lake-green.png), not a georeferenced layer
- [stylized-pdx](stylized-pdx/output/LAYERS.md) — Circular poster map of Portland: city boundary, 25 km frame circle, and clipped OR+WA TNM roads in stylized-pdx.gpkg; water and mask render-only via matplotlib
- [topo-blocks](topo-blocks/output/LAYERS.md) — Artistic three-panel PNG block designs cut from mountain contour shapefiles (16 print-friendly color schemes); apparel art, not ArcGIS layers
- [vintage-topo](vintage-topo/output/LAYERS.md) — Vintage USGS topo sheets (1891 Ashland/Crater Lake 1:250k, 1985 Nehalem 7.5-minute quad) restyled with modern DEM shaded relief; final layout exports only, including a 3D perspective render of the Ashland sheet
- [wind-turbines](wind-turbines/output/LAYERS.md) — US wind-turbine maps from USWTDB v6.1 and WINDExchange data: per-state turbine counts, installed-vs-potential capacity choropleth, and turbine-point heat map, each as an EPSG:4326 geopackage with Natural Earth 50m basemap layers

## Not documented

- joyplot — empty directory, nothing to document
