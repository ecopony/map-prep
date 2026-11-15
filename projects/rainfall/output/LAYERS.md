# rainfall — layer documentation

**Map**: CONUS annual rainfall map (ArcGIS Pro project: Rainfall)
**Script**: `main.py` (branch `rainfall`, not yet committed as of 2026-07-19)
**Overview**: Annual precipitation classes for the contiguous US, drawn as smooth polygon bands (two smoothness variants to compare) over a shaded-relief backdrop, with state boundaries, major cities, and major lakes (split into US/foreign layers for separate styling). Context layers frame CONUS as the subject: surrounding-country polygons styled as neutral land, an ocean polygon with two bathymetry-coloring candidates (stepped NE bands vs continuous SRTM15+), a woodland tree-cover tint spanning all land in the frame, and a dissolved CONUS outline for a layout vignette. Two relief backdrops were produced to compare in ArcGIS: Tom Patterson's Natural Earth manual shaded relief vs a multi-directional hillshade of the Copernicus GLO-90 DEM (hillshade blended over the rainfall bands with Soft Light in the Pro project). The map frame is EPSG:5070 (CONUS Albers); the raster bounds (-140, 16.5, -56, 57) are the frame extent transformed to lat/lon and rounded out, so clipped rasters cover the whole layout rather than just CONUS. The four `legend_rainfall_*.png` files are layout graphics (pre-rendered legends dropped in as Picture elements), not map layers.

> Entries were reconstructed from `main.py` and the `mapprep` package on 2026-07-18, after the layers were created. Rationale marked *(reconstructed)* is inferred from code and comments, not a firsthand record of the decisions.

## rainfall.gpkg

### rainfall_classes
- **Role**: The thematic layer — annual precipitation bands to symbolize and label as discrete classes.
- **Source**: PRISM 30-year (1991–2020) annual precipitation normals, 2.5 arc-minute (~4 km), in mm. `$PRISM_DIR/prism_ppt_us_25m_2020_avg_30y/prism_ppt_us_25m_2020_avg_30y.tif` (PRISM Climate Group, Oregon State University).
- **Processing**: mm → inches via `mapprep/prism.py` `ppt_annual_normals_inches` (also writes the intermediate `prism_ppt_annual_inches.tif`), then classified and vectorized by `mapprep/raster.py` `classify_to_polygons` with breaks `[5, 10, 15, 20, 30, 40, 60, 80, 100]` inches, `smooth_sigma=2` (gaussian pre-smoothing of values — the main smooth-lines knob), `upsample=4` (removes the pixel staircase at class edges), `sieve_pixels=64` (merges patches smaller than 64 upsampled pixels into their largest neighbor — the de-speckling knob), `simplify_tolerance=0.02`° (coverage simplification; shared class boundaries stay aligned). Then clipped to the `us_states` layer (geopandas `clip`, states reprojected EPSG:4326→4269, `keep_geom_type=True`). One dissolved multipolygon per class with `lower`/`upper`/`label` fields ("< 5", "5-10", …, "> 100").
- **Rationale** *(reconstructed)*: Classified polygons rather than a continuous raster so the bands can be symbolized, labeled, and outlined discretely in ArcGIS; the breaks are conventional annual-precipitation classes in inches. *(2026-07-18)* Clipped to the state outlines because smoothing/simplification pushed class edges past the coastline and the raw PRISM footprint doesn't match the Natural Earth shoreline; clipping makes the bands nest cleanly inside the state linework.
- **Facts** *(extracted 2026-07-18)*: EPSG:4269, MultiPolygon, 10 features, fields [class, lower, upper, label]

### rainfall_classes_smooth
- **Role**: Smoother, more generalized variant of `rainfall_classes` — same breaks and fields, kept alongside it so the two can be compared in ArcGIS before picking one.
- **Source**: Same PRISM normals raster as `rainfall_classes`.
- **Processing**: Same chain as `rainfall_classes` (`mapprep/raster.py` `classify_to_polygons`, breaks `[5, 10, 15, 20, 30, 40, 60, 80, 100]` inches, then clipped to `us_states`) but with `smooth_sigma=5` (vs 2 — gaussian pre-smoothing of ~4 km pixels, so ~20 km-scale smoothing vs ~8 km) and `sieve_pixels=256` (vs 64 — drops class patches smaller than 256 upsampled pixels, removing most small islands/enclaves); `upsample=4` and `simplify_tolerance=0.02`° unchanged.
- **Rationale**: Added 2026-07-18 because the default layer's band edges felt too busy at layout scale; sigma 5 generalizes the boundaries and sieve 256 clears the residual speckle that stronger smoothing alone leaves behind. The original layer is retained as the more detail-faithful alternative. *(2026-07-18)* Clipped to the state outlines along with `rainfall_classes` — see its rationale.
- **Facts** *(extracted 2026-07-18)*: EPSG:4269, MultiPolygon, 10 features, fields [class, lower, upper, label]

### rainfall_classes_cadillac
- **Role**: Three-class aridity view of the same precipitation surface — "< 7", "7-20", "> 20" inches — an alternative thematic layer to the ten-class bands, framing the map around habitability/farmability thresholds instead of a full ramp.
- **Source**: Same PRISM normals raster as `rainfall_classes`.
- **Processing**: Same chain and generalization recipe as `rainfall_classes_smooth` (`mapprep/raster.py` `classify_to_polygons`, `smooth_sigma=5`, `upsample=4`, `sieve_pixels=256`, `simplify_tolerance=0.02`°, clipped to `us_states`) but with breaks `[7, 20]` inches.
- **Rationale**: Added 2026-07-24. The thresholds are Marc Reisner's from *Cadillac Desert*: land under 20 in/yr is "hostile terrain to a farmer," and places at 7 in or less (Phoenix, El Paso, Reno) are "arguably no place to inhabit at all." Reuses the smooth-variant parameters because the ten-class comparison showed sigma 5 + sieve 256 reads better at layout scale; with only three classes the boundaries carry the whole story, so the generalized lines matter even more.
- **Facts** *(extracted 2026-07-24)*: EPSG:4269, MultiPolygon, 3 features, fields [class, lower, upper, label]

### us_states
- **Role**: State boundary linework / reference layer.
- **Source**: Natural Earth 50m admin-1 states & provinces (lakes version), `$NATURAL_EARTH_DIR/StatesProvinces/ne_50m_admin_1_states_provinces_lakes`.
- **Processing**: `mapprep/natural_earth.py` `us_states(contiguous=True)` — filtered to `iso_a2 == 'US'`, excluding Alaska, Hawaii, Puerto Rico. 49 features = 48 states + DC.
- **Rationale** *(reconstructed)*: 50m scale matches a CONUS-extent map; the lakes version keeps Great Lakes shorelines out of the state polygons.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, MultiPolygon, 49 features, fields [featurecla, scalerank, adm1_code, diss_me, iso_3166_2, wikipedia, iso_a2, adm0_sr, … (121 total)]

### populated_places
- **Role**: Major-city points for labeling.
- **Source**: Natural Earth 50m populated places (simple), `$NATURAL_EARTH_DIR/PopulatedPlaces/ne_50m_populated_places_simple`.
- **Processing**: `mapprep/natural_earth.py` `us_populated_places(max_scalerank=2, contiguous=True)` — US places with NE `scalerank <= 2`, excluding Alaska, Hawaii, Puerto Rico. No population threshold and no exclusion list.
- **Rationale** *(reconstructed)*: 500k threshold keeps the city count manageable at CONUS scale; `pop_max` is metro-area population, so this reads as "major metros". *(2026-07-18)* Dropped 9 clutter labels rather than raising the threshold (raising it to ~800k was considered and rejected because it also removed regionally important solo labels like New Orleans and Oklahoma City). *(2026-08-11)* Replaced the population cutoff + hand-picked exclusion list with NE's curated `scalerank <= 2` (48 → 20 cities): with text labels planned, 48 was too dense, and scalerank encodes label-worthiness rather than size — it keeps New Orleans (0.8M) while already excluding every city on the old exclusion list (all rank 4). `scalerank <= 3` (45 cities, adds small state capitals like Boise/Santa Fe/Cheyenne) was considered and rejected as too dense in the east.
- **Facts** *(extracted 2026-08-11)*: EPSG:4326, Point, 20 features, fields [scalerank, natscale, labelrank, featurecla, name, namepar, namealt, nameascii, … (31 total)]

### conus_outline
- **Role**: Single dissolved outline of the contiguous US, for the layout vignette effect (e.g. an outer glow / feathered mask around the country).
- **Source**: Derived from the `us_states` layer (Natural Earth 50m admin-1, lakes version).
- **Processing**: `us_states.dissolve()` in `main.py`, geometry only — no attribute fields.
- **Rationale**: Added 2026-07-19. Dissolved from `us_states` rather than taken from the NE admin-0 country polygon so the outline coincides exactly with the state linework (the country polygon would need Alaska/Hawaii removed and can differ in island/shoreline detail from the lakes-version states).
- **Facts** *(extracted 2026-07-19)*: EPSG:4326, MultiPolygon, 1 features, fields []

### lakes
- **Role**: Major-lake water bodies — fills the Great Lakes (absent from the lakes-version state/country polygons) and adds Winnipeg, Great Salt Lake, etc.
- **Source**: Natural Earth 50m lakes, `$NATURAL_EARTH_DIR/Lakes/ne_50m_lakes`.
- **Processing**: `mapprep/natural_earth.py` `lakes(min_area_km2=1000)` — filtered by polygon area in equal-area EPSG:6933 (NE `scalerank` is not a reliable size proxy: rank 0 spans Superior down to the Finger Lakes), then `.cx` bbox intersection with the map bounds. 41 features.
- **Rationale**: Added 2026-07-19. The ~1000 km² floor keeps the asked-for majors (Great Lakes, Winnipeg, Great Salt Lake) plus map-prominent lakes like Champlain, Okeechobee, Mead, Powell without Finger Lakes-scale clutter. Quirk: NE 50m carries a few duplicate features (e.g. Lake Mead twice) — harmless under an opaque fill. *(2026-07-19)* Dropped the Montana/Dakotas Missouri River reservoirs (Fort Peck ×2 duplicate features, Sakakawea, Oahe) via `excluded_lakes` in `main.py` as a visual distraction; 41 → 37 features.
- **Facts** *(extracted 2026-07-19)*: EPSG:4326, Polygon, 37 features, fields [scalerank, featurecla, name, name_alt, note, admin, namepar, min_zoom, … (39 total)]

### lakes_us
- **Role**: The US share of the `lakes` layer, to style differently from foreign water (draw above `lakes`; the base layer shows through only outside the US).
- **Source**: Derived from `lakes` (NE 50m) and the NE 50m admin-0 United States polygon.
- **Processing**: `lakes.clip(...)` in `main.py` against `countries(include='United States of America')`, `keep_geom_type=True`. Splits the Great Lakes, Lake of the Woods, and Rainy Lake at the international border. 14 features.
- **Rationale**: Added 2026-07-19, deliberately accepting the border split. Clipped with the **regular** admin-0 country polygon, not `us_states`/`conus_outline` — those are lakes-version polygons with the Great Lakes carved out as holes, which would delete the Great Lakes from the clip instead of halving them. Inherits the `excluded_lakes` drop (Fort Peck, Sakakawea, Oahe); 18 → 14 features.
- **Facts** *(extracted 2026-07-19)*: EPSG:4326, MultiPolygon, 14 features, fields [scalerank, featurecla, name, name_alt, note, admin, namepar, min_zoom, … (39 total)]

### surrounding_countries
- **Role**: All non-US land in the map frame (Canada, Mexico, Cuba, Bahamas, Central America, Caribbean, Bermuda, …) so every foreign country styles uniformly — outlines only, no internal state/province divisions.
- **Source**: Natural Earth 50m admin-0 countries, `$NATURAL_EARTH_DIR/Countries/ne_50m_admin_0_countries`.
- **Processing**: `mapprep/natural_earth.py` `countries(exclude='United States of America')`, then geopandas `.cx` bbox intersection with the map bounds (-140, 16.5, -56, 57). Whole country polygons, not clipped. 26 features.
- **Rationale**: Replaced the earlier `neighboring_countries` layer (Canada + Mexico only, added 2026-07-18) on 2026-07-19: Cuba, the Bahamas, and other Caribbean land appear in the frame and stuck out unstyled. Admin-0 chosen over admin-1 so neighbors show no internal divisions; 50m matches `us_states` so shared borders align. Quirks to know: France and the Netherlands are included because their admin-0 multipolygons contain Caribbean territories (their European parts fall outside the frame); Puerto Rico and the U.S. Virgin Islands are separate NE admin-0 units, so they are in this layer despite being US territories — appropriate here since they're outside the CONUS study area and should style as surrounding land.
- **Facts** *(extracted 2026-07-19)*: EPSG:4326, MultiPolygon, 26 features, fields [featurecla, scalerank, LABELRANK, SOVEREIGNT, SOV_A3, ADM0_DIF, LEVEL, TYPE, … (168 total)]

### ocean
- **Role**: Ocean polygon for water styling (fill/tint under or over the relief backdrop).
- **Source**: Natural Earth 50m ocean, `$NATURAL_EARTH_DIR/Ocean/ne_50m_ocean`.
- **Processing**: `mapprep/natural_earth.py` `ocean()`, clipped (geopandas `clip`) to the map bounds (-140, 16.5, -56, 57) shared with the relief rasters.
- **Rationale**: Added 2026-07-18. A polygon (rather than styling the map background) so the ocean can take its own fill/effects independent of land nodata areas; clipped to the frame bounds because the source polygon is global. 50m shoreline matches `us_states` and `neighboring_countries`, so the coastline nests with the land layers.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, MultiPolygon, 1 features, fields [scalerank, featurecla, min_zoom]

### bathymetry_bands
- **Role**: Ocean styling option A — stepped depth-band polygons to tint progressively darker with depth (classic NE/atlas look, matches the banded aesthetic of the rainfall classes). Compare against `bathy_srtm15plus.tif` (option B).
- **Source**: Natural Earth 10m bathymetry (`ne_10m_bathymetry_all`, one shapefile per depth: 0, 200, 1000, … 10000 m), downloaded 2026-07-19 into `$NATURAL_EARTH_DIR/Ocean/`.
- **Processing**: `mapprep/natural_earth.py` `bathymetry()` — reads all 12 band shapefiles, concatenates sorted shallow-to-deep (so deeper bands draw on top; the polygons are nested, each band covering everything deeper than it) — then geopandas `clip` to the map bounds. Depths ≥ 9000 m don't occur in the frame, so 10 depth values remain. Symbolize on `depth` (meters, positive-down).
- **Rationale**: Added 2026-07-19 to give the ocean bathymetry-based coloration; vector bands chosen as one of two candidates because stepped tints match the classified rainfall bands. 10m scale used because NE only publishes bathymetry at 10m; its shoreline is finer than the 50m `ocean`/`us_states` shoreline, so keep the `ocean` polygon (or land layers) on top to hide the mismatch at the coast.
- **Facts** *(extracted 2026-07-19)*: EPSG:4326, MultiPolygon, 213 features, fields [scalerank, featurecla, depth]

### meridian_100
- **Role**: Powell's 100th meridian — the 1878 "supposed" arid-humid divide — as a reference line, to contrast with `arid_humid_divide` (the shifting-meridian story from the Water in the West series; Seager et al. 2018, "Whither the 100th Meridian?", *Earth Interactions* 22).
- **Source**: Constructed in `main.py`.
- **Processing**: A vertical line at 100°W spanning the map-bounds latitudes (16.5–57°N), segmentized every 0.5° so it curves correctly when projected (a two-point line would stay straight in EPSG:5070).
- **Rationale**: Added 2026-08-11. Spans the whole frame rather than clipping to CONUS so it reads as a graticule-like reference; clip against `conus_outline` in Pro if a US-only line looks better.
- **Facts** *(extracted 2026-08-11)*: EPSG:4326, LineString, 1 features, fields [label]

### meridian_100_faded
- **Role**: Layout variant of `meridian_100` for the Water in the West premise sheets (rainfall, Cadillac thresholds, surplus/deficit): the same line pre-cut into dashes that are solid across the US and fade out beyond the Canadian and Mexican borders, so the line stops short of the title block instead of running through it. Symbolize with a plain **solid** stroke (butt caps, no dash effect — the dashes are the features) and drive transparency from the `transparency` field (Symbology pane → Vary symbology by attribute → Transparency); `opacity` is the same value inverted, for whichever direction the control wants. Use instead of `meridian_100`, not on top of it.
- **Source**: Derived from `meridian_100` and `us_states` in `main.py`.
- **Processing**: `mapprep/lines.py` `faded_dashes(meridian_100, us_states, 'EPSG:5070', fade=300_000)` with defaults `dash=40_000`, `gap=25_000` (metres). The line and states are projected to EPSG:5070; the solid stretch runs between the outermost points where the line crosses the states (dash midpoints 27.96–48.72°N); dashes are laid from 300 km before it to 300 km after, each a separate feature. A dash's opacity comes from its midpoint's distance beyond the solid stretch, eased with a smoothstep to zero at 300 km; dashes rounding to 0 are dropped. Result: 36 solid dashes, 5 fading south (99, 80, 50, 20, 1 %) and 4 fading north (92, 67, 35, 9 %), spanning 25.3–51.4°N. `zone` is `before` (south) / `inside` / `after` (north), following the line's south-to-north drawing direction.
- **Rationale**: Added 2026-11-10 after the first layout drafts, where the dashed meridian ran through the title and subtitle. ArcGIS Pro cannot run a gradient along a line — its gradient stroke only runs across the width (Esri blog "Gradients along lines, rather than across", Feb 2025; the Esri Community idea has been open since 2020) — so the fade is carried in the data. One feature per dash rather than short segments under a Pro dash effect, because a dash effect restarts on every feature. The documented Pro-side alternative (a fill layer with a Buffer effect and a linear gradient fill) was not used: it is unconfirmed with dashes and would have to be rebuilt in each of the three maps. Stored in EPSG:5070 (the map frame's CRS), unlike the geographic layers around it, so dash lengths are exact on the page. Dash 40 km / gap 25 km approximate the dash rhythm of the draft's Pro symbol at layout scale; all three lengths are arguments to `faded_dashes` if the layout changes. Written by running only this block, not a full `main.py` rerun. *(2026-11-10, same day)* Fade shortened 400 → 300 km (48 → 45 features): on the rainfall sheet the 400 km tail's last faint dashes reached to just under the title lettering.
- **Facts** *(extracted 2026-11-10)*: EPSG:5070, LineString, 45 features, fields [zone, opacity, transparency]

### arid_humid_divide
- **Role**: The *effective* arid-humid divide — where Powell's line actually sits under the 1991–2020 climate. The bold moving line of the shifting-meridian story, drawn against `meridian_100`; also a companion overlay for the Cadillac Desert classes.
- **Source**: Derived from `aridity_index.tif` (P/PET; see below). Concept: Seager et al. 2018's "effective 100th meridian," which they define by an aridity level rather than a fixed longitude without committing to a value (Part I's one passing reference is AI ≈ 1; neither paper extracts an explicit divide line — they read the gradient off AI maps and latitude-band Hovmöller plots). The 0.65 threshold is the UNEP drylands boundary (World Atlas of Desertification, 1992), not from Seager.
- **Processing**: `mapprep/aridity.py` `effective_divide(threshold=0.65, smooth_sigma=5, latitude_smooth_sigma=10)` — per raster row, the east edge of the easternmost arid (P/PET < 0.65) pixel on the sigma-5-smoothed surface, i.e. the point east of which the country is contiguously humid; the longitude series is then gaussian-smoothed over rows (sigma 10 rows ≈ 40 km). Rows with no humid data east of the last arid pixel (south Florida) are dropped. Single line, Rio Grande (~25.8°N) to the Canadian border.
- **Rationale**: Added 2026-08-11. A raw 0.65 contour was tried first and rejected: the humid Rocky Mountain high country connects to the humid East, so the iso-line detours deep into Colorado (and at smooth_sigma ≥ 10 merges with the inland-Northwest drylands boundary). The easternmost-arid-pixel formulation matches the single-divide concept in Seager et al. and yields one clean north-south line. *(2026-08-11, same day)* Switched PET from Thornthwaite to Hargreaves: the Thornthwaite divide bowed to ~105°W in the north (its cool-climate PET underestimate), so most of the line sat *west* of the 100th meridian and visually contradicted the migrated-east story. With Hargreaves the divide runs near-vertically at ~97–99°W — east of Powell's line for its entire Gulf-to-Canada run, matching the ~98°W placement associated with the papers (Part I: "a case might be made that Webb (1931) was correct that the 98th meridian" better marks the divide). Credit "after Seager et al. 2018". `threshold` field carries the 0.65 for labeling.
- **Facts** *(extracted 2026-08-11)*: EPSG:4269, LineString, 1 features, fields [threshold]

### arid_humid_divide_epochs
- **Role**: The divide's migration over the instrumental record — the same effective arid-humid divide computed for three 30-year windows (1901–1930, 1946–1975, 1991–2020), to be drawn as a small-multiple or ghosted-line sequence behind `arid_humid_divide`. The `epoch` field labels each line.
- **Source**: DIY climatologies from the PRISM monthly time series, AN ("all networks") 4 km variant, auto-downloaded to `$PRISM_DIR/time_series/` by `mapprep/prism.py` `monthly_path` (~2.2 GB total for tmin/tmax/ppt × 3 epochs; cached climatologies in `cache/climatology/`).
- **Processing**: Per epoch: `prism.monthly_climatology_paths` averages each calendar month over the 30 years; then the identical chain to `arid_humid_divide` — `aridity.hargreaves_pet_annual` → `raster.total` (annual ppt) → `aridity.aridity_index` → `aridity.effective_divide` (threshold 0.65, smooth_sigma 5, latitude_smooth_sigma 10). All epochs share the same series, grid, and method, so the lines are directly comparable; the normals-based `arid_humid_divide` stays canonical for the present line, and its DIY 1991–2020 twin here matches it almost exactly (mean lon −97.83 vs −97.80).
- **Rationale**: Added 2026-08-11. Windows chosen to be non-overlapping, evenly spread, and to end at the current normals period. Finding: the divide migrated *west*, not east — mean longitude −96.7 (1901–1930) → −96.7 (1946–1975) → −97.8 (1991–2020), consistent at every latitude and strongest in the north (46–49°N: −96.0 → −98.4). The observed 20th-century precipitation increase in the Plains has so far outrun rising PET, which matches Seager et al. 2018's own nuance (the eastward march is largely model-projected; observed wetting has masked it). If the map narrates "the meridian is moving," it must be framed as humid-side expansion to date with eastward migration projected — the data won't support an observed eastward crawl. This is *consistent with* Seager et al., not a disproof: their two claims are that the divide *today* sits near 98°W (confirmed here) and that it *will* move east under continued warming (a model projection, untested by the historical record); they themselves note observed precipitation increases have so far offset rising PET. The popularized "meridian marching east" version is what the epoch lines contradict, not the paper. Physical drivers of the westward drift: the documented 20th-century wetting of the central/eastern Plains, the central-US "warming hole" muting PET rise, and irrigation/Corn Belt intensification boosting moisture recycling while suppressing daytime highs. Suggested caption framing: divide near 98°W, east of Powell's line; held steady or nudged west over the observed record as wetting outran PET; projected to march east as warming eventually wins. Caveats that may exaggerate the westward signal: (1) Hargreaves scales PET with √(tmax−tmin), and the diurnal range shrank over the century (tmin rose faster than tmax), so our PET trend is likely understated relative to Penman-Monteith — some drift may be method, not climate; (2) PRISM's AN series is not network-consistent over a century (PRISM recommends the 800 m LT series for trend work; AN was used because LT has no 4 km release), so the early-epoch positions carry station-coverage uncertainty.
- **Facts** *(extracted 2026-08-11)*: EPSG:4269, LineString, 3 features, fields [threshold, epoch]

### aridity_classes
- **Role**: The UNEP drylands classification as clean vector bands — the thematic layer for the aridity-ratio map (`west-water-aridity-ratio` brief): hyper-arid < 0.05, arid 0.05–0.2, semi-arid 0.2–0.5, dry subhumid 0.5–0.65, humid ≥ 0.65. The 0.65 class edge is the same drylands boundary behind `arid_humid_divide`.
- **Source**: `aridity_index.tif` (P/PET, Hargreaves PET; see below). Breaks: UNEP World Atlas of Desertification (1992).
- **Processing**: `mapprep/raster.py` `classify_to_polygons` at breaks [0.05, 0.2, 0.5, 0.65], smooth_sigma=5, upsample=4, sieve_pixels=256, simplify 0.02°; clipped to `us_states`. Same generalization recipe as `rainfall_classes_cadillac` — few classes carry the story, so the heavier smoothing wins.
- **Rationale**: Added 2026-08-12. Legend intent is dual labeling: the P/PET value *and* the inverted plain-language ratio ("0.2 — the sky could take back 5× what it gives — Tucson"), per the aridity-ratio brief. Hargreaves PET runs ~5–10% low in hot arid cities vs Penman, nudging AI up in the hyper-arid/arid zones; check whether the 0.05 and 0.2 boundaries look right before final symbology (the brief's remaining open question — gridMET Penman ETo is the upgrade path if not).
- **Facts** *(extracted 2026-08-12)*: EPSG:4269, MultiPolygon, 5 features, fields [class, lower, upper, label]

### water_balance_classes
- **Role**: The water-balance surface as classed vector bands for the `west-water-surplus-deficit` map — ten classes hinged at zero, five per side. The boundary between the `-5-0` and `0-5` classes *is* the break-even line; style it as an explicit thin dark line (series line motif, and the colorblind backstop for the hinge).
- **Source**: `water_balance_in.tif` (see below).
- **Processing**: `classify_to_polygons` at breaks [−40, −20, −10, −5, 0, 5, 10, 20, 40], smooth_sigma=5, upsample=4, sieve_pixels=256, simplify 0.02°; clipped to `us_states`. Same generalization recipe as the other few-class band layers.
- **Rationale**: Added 2026-08-19. Breaks are symmetric per-inch so equal magnitudes get equal color depth — the deficit/surplus asymmetry then shows honestly through *area* (11% of pixels < −40″, 1.2% > +40″; raster max +199″ in the Olympics is absorbed by the open `> 40` class). Symbology (mirrored in `legend_water_balance_*`): BrBG-derived brown→teal, deficit side #543005 #8c510a #bf812d #dfc27d #f9f0da, surplus side #7fcbbd #38a493 #0d8172 #03604f #003c30. The hinge pair (#f9f0da/#7fcbbd) is deliberately lightness-offset rather than stock BrBG's mirrored pales: the stock center pair measures ΔE 4.9 under protanopia (the zero edge — the map's argument — would vanish for red-green colorblind readers); the offset pair measures 13.7. Validated with the dataviz skill's palette checker; worst adjacent pair anywhere is 10.4 (two deep teals covering 1.2% of pixels).
- **Facts** *(extracted 2026-08-19)*: EPSG:4269, MultiPolygon, 10 features, fields [class, lower, upper, label]

### water_balance_break_even
- **Role**: The break-even line (P = PET) for the surplus & deficit sheet — a single line from the Texas Gulf coast (near 95.2°W, 29.0°N) north through Arkansas, Missouri and Illinois to Lake Michigan (87.5°W, 44.3°N). Drawn as a thin solid dark line over `water_balance_classes` and labeled, as the counterpart to the dashed 100th meridian: it sits near 94°W in the south and 87–88°W in the north, roughly 500–1,100 km east of Powell's line.
- **Source**: Derived from `water_balance_classes` (no new data).
- **Processing**: `mapprep/lines.py` `shared_boundary` — the boundary shared by the union of the deficit classes (0–4) and the union of the surplus classes (5–9), line-merged into connected pieces; `main.py` keeps the longest piece lying wholly east of 100°W.
- **Rationale**: Added 2026-11-12. The zero edge is not one line: 32 pieces in all, including surplus islands on the Plains (a 970 km ring in Iowa/Minnesota), a separate 2,034 km edge around the Southeast's deficit area (Carolinas–Georgia–Florida), and the Pacific and northern-Rockies edges. Outlining all of them clutters the sheet, so only the main Plains-side edge is drawn (2,732 km). Taken from the class polygons rather than contoured from the raster so the line sits exactly on the cream/teal color edge. `aridity.effective_divide` was not usable here: its easternmost-arid-pixel scan fails once deficit pockets appear far east of the Plains, which is the case at P = PET. The piece is chosen by a length rule, so re-check it if the classes are re-smoothed — the pieces could join or split differently.
  *(Same day)* Drawn on the layout this exact edge looked ragged, so it is now the **source** for `water_balance_break_even_faded` rather than a layer to draw.
- **Facts** *(extracted 2026-11-12)*: EPSG:4269, LineString, 1 features, fields [length_km, closed, label]

### water_balance_break_even_faded
- **Role**: Not on any layout yet — built for the surplus & deficit sheet, left off it (2026-11-12: the color hinge already shows break-even), and kept as a candidate third line for the shifting-100th-meridian map beside `meridian_100` and `arid_humid_divide`. The break-even line as one smooth north-south curve, pre-cut into dashes that fade out beyond its ends, the same construction as `meridian_100_faded`. Symbolize with a plain solid stroke and drive transparency from the `transparency` field. Runs from the Texas Gulf coast (about 94.9°W) through Arkansas and Missouri to Lake Michigan's west shore (about 87.7°W).
- **Source**: Derived from `water_balance_break_even` (no new data).
- **Processing**: `mapprep/lines.py` `north_south_average(break_even, smooth=2.5, extend=4)` — the exact edge's crossings averaged to one longitude per 0.05° of latitude, gaussian-smoothed along latitude (sigma 2.5°), and continued 9° past each end in a straight line; then `faded_dashes(..., dash=70_000, fade=300_000)` in EPSG:5070 with the solid area set to the latitude band the 100th meridian spans inside the US (28.0°N–49.0°N), so the line is solid over the same latitudes as `meridian_100_faded` and fades out over 300 km level with it (ends near 25.4°N and 51.7°N).
- **Rationale**: Added 2026-11-12, replacing the exact edge on the layout: a line that follows every bend of the class boundary reads as an outline, not as a divide. Averaged and smoothed, it reads like a second meridian and can be compared with the 100th at a glance. It is a generalization — it departs from the cream/teal edge by up to a couple of hundred kilometres where the edge bulges (the Ozarks, southern Illinois), and north of Chicago it runs along the lakeshore because that is where the edge is. Dashes are 70 km against the meridian's 40 km (same 25 km gap) so the two lines differ. sigma 2.5° was chosen by eye over 1.0° and 1.5°, which kept an S-bend through Arkansas.
  *(Same day)* First built to stop where the real edge does (Gulf coast to Lake Michigan); extended to match the meridian's span so the two lines read as a pair on the sheet. **Only the stretch between 29.0°N and 44.3°N is data.** South of that the line is a straight continuation over the Gulf; north of it, a straight continuation up Lake Michigan and across the Upper Peninsula and Lake Superior — where the true zero edge is not (the UP is in surplus, and the edge resumes farther west in Wisconsin and Minnesota).
- **Facts** *(extracted 2026-11-12)*: EPSG:5070, LineString, 33 features (26 solid, 3 fading south, 4 fading north), fields [zone, opacity, transparency, label]

## bathy_srtm15plus.tif
- **Role**: Ocean styling option B — continuous topo-bathymetry raster for smooth depth-graded water (symbolize with a light-to-dark blue ramp; can also be hillshaded for seafloor texture). Compare against `bathymetry_bands` (option A).
- **Source**: SRTM15+ (global 15 arc-second topo-bathymetry) via the OpenTopography global DEM API; raw fetch cached at `cache/bathy_srtm15plus_raw.tif`.
- **Processing**: `mapprep/dem.py` `fetch(demtype='SRTM15Plus')` at native 15 arcsec (single request — SRTM15+ has a 125M km² per-request limit), then `mapprep/raster.py` `clip` with `cutline` = the `ocean` layer in `rainfall.gpkg` (land → nodata −9999) and overviews built.
- **Rationale**: Added 2026-07-19. Masked to the NE 50m ocean polygon rather than thresholding at elevation 0 so the water edge coincides exactly with the vector shoreline used by the other layers (elevation-thresholding would misalign at the coast and expose below-sea-level land like Death Valley). Values are meters, negative below sea level; symbolize roughly −9000..0.
- **Facts** *(extracted 2026-07-19)*: EPSG:4326, 20160x9720 px @ 0.00416667 deg (15 arcsec), bounds (-140.0000, 16.5000, -56.0000, 57.0000), float32, nodata=-9999.0, overviews [2, 4, 8, 16, 32], deflate, 405.5 MB

## woodland_treecover.tif
- **Role**: Woodland tint for all land in the frame (US and surrounding countries alike) — percent tree cover 0–100 to render as a subtle green wash over the relief.
- **Source**: EarthEnv 1-km consensus land cover (Tuanmu & Jetz 2014), full version with DISCover; the four global tree-class prevalence rasters (evergreen/deciduous needleleaf, evergreen broadleaf, deciduous broadleaf, mixed/other trees), downloaded 2026-07-19 to `$EARTHENV_DIR/consensus_landcover/` (`EARTHENV_DIR` added to `.env`).
- **Processing**: `mapprep/earthenv.py` `treecover` — windows the four global class rasters to the map bounds and sums them (the 12 EarthEnv classes sum to 100, so the tree subset is percent tree cover; a few pixels hit 102 from per-class rounding). uint8, nodata 255 (ocean).
- **Rationale**: Added 2026-07-19. Chosen over local options because none cover the whole frame (NLCD is CONUS-only, Hansen tiles on disk are PNW-only) and over MODIS VCF because EarthEnv needs no Earthdata auth; 1 km is ample at CONUS scale and the four ~50 MB global class files are cached for reuse. Style suggestion: transparent below ~15–20% cover, then a low-opacity green ramp.
- **Facts** *(extracted 2026-07-19)*: EPSG:4326, 10080x4860 px @ 0.00833333 deg (30 arcsec), bounds (-140.0000, 16.5000, -56.0000, 57.0000), uint8, nodata=255.0, overviews none, deflate, 13.5 MB

## pet_annual_mm.tif
- **Role**: Intermediate — annual potential evapotranspiration (mm), the denominator of `aridity_index.tif`. Kept on disk for inspection and for the planned aridity-ratio (P:PET) map in the Water in the West series.
- **Source**: Computed from the twenty-four PRISM 1991–2020 monthly tmin/tmax normals (`prism_tmin_us_25m_2020MM_avg_30y`, `prism_tmax_...`), auto-downloaded to `$PRISM_DIR` by `mapprep/prism.py` `monthly_normals_paths` from `data.prism.oregonstate.edu` (2026-08-11).
- **Processing**: `mapprep/aridity.py` `hargreaves_pet_annual` — Hargreaves-Samani (1985) monthly PET from min/max temperature and FAO-56 extraterrestrial radiation (computed from latitude and mid-month solar geometry), summed over the year.
- **Rationale**: Added 2026-08-11 for the shifting-meridian layers. A temperature-only method is required (PRISM has no radiation/wind/humidity normals for Penman-Monteith). Thornthwaite was implemented first and rejected: its cool-climate PET underestimate pulled the northern arid-humid divide ~5° too far west; Hargreaves tracks Penman closely enough to reproduce Seager et al.'s ~98°W divide.
- **Facts** *(extracted 2026-08-11)*: EPSG:4269, 1405x621 px @ 0.0416667 deg, bounds (-125.0208, 24.0625, -66.4792, 49.9375), float32, nodata=-9999.0, overviews none, deflate, 1.7 MB

## aridity_index.tif
- **Role**: UNEP aridity index (annual P / annual PET) — the continuous surface behind `arid_humid_divide` (0.65 = drylands threshold), and the candidate mid-ground surface for a dedicated shifting-meridian or aridity-ratio map (dry = warm/brown below 0.65, humid = pale above).
- **Source**: PRISM annual precipitation normals (numerator; same grid as `prism_ppt_annual_inches.tif`, in mm) over `pet_annual_mm.tif` (denominator).
- **Processing**: `mapprep/aridity.py` `aridity_index` — pixelwise P/PET on the shared PRISM 4-km grid; nodata where either input is missing or PET ≤ 0.
- **Rationale**: Added 2026-08-11. Sanity-checked against known climates (Hargreaves PET): Phoenix 0.12, Denver 0.32, Bismarck 0.52, Dallas 0.73, Wichita 0.74, Omaha 0.80, St. Louis 0.99, Seattle 1.19 — the 0.65 divide falls between Bismarck and Omaha, just east of the 100th meridian. *(2026-08-12)* `aridity.aridity_index` now delegates to the generic `raster.ratio`; output verified bit-identical.
- **Facts** *(extracted 2026-08-11)*: EPSG:4269, 1405x621 px @ 0.0416667 deg, bounds (-125.0208, 24.0625, -66.4792, 49.9375), float32, nodata=-9999.0, overviews none, deflate, 1.7 MB

## water_balance_in.tif
- **Role**: Annual water balance (P − PET) in inches — the absolute-terms twin of `aridity_index.tif` for the `west-water-surplus-deficit` map. Negative = deficit, positive = surplus; the zero line is another flavor of the arid–humid divide. Symbolize diverging around 0.
- **Source**: PRISM annual precipitation normals (mm) minus `pet_annual_mm.tif`, converted to inches (÷25.4).
- **Processing**: `raster.difference` → `raster.scale_values`; intermediate mm surface in `cache/water_balance_mm.tif`.
- **Rationale**: Added 2026-08-12. City checks: Tucson −56″, Phoenix −59″, Albuquerque −49″, Bismarck −18″, St. Louis ≈0″ (its AI is 0.99 — the break-even eastern foil), Portland +6″, Miami +14″, Mobile +16″. Hargreaves PET runs low in hot deserts, so desert deficits are slightly *understated* — conservative in the right direction. *(2026-08-19)* Integrated over CONUS (latitude-weighted pixel areas): **72% of the lower 48 by area runs an annual deficit**, and total deficit volume is **~6× total surplus** (~3,300 vs ~560 km³/yr) — legend-callout material; the asymmetry is the series thesis in one statistic. Deficit here = atmospheric demand unmet by local rain (PET − P where positive), not streamflow.
- **Facts** *(extracted 2026-08-12)*: EPSG:4269, 1405x621 px @ 0.0416667 deg, bounds (-125.0208, 24.0625, -66.4792, 49.9375), float32, nodata=-9999.0, overviews none, uncompressed, 3.5 MB

## summer_rain_fraction.tif
- **Role**: July–September share of annual precipitation (0–1) — the rain-regime / North American Monsoon surface for the `west-water-summer-rain` map. Near 0 on the winter-wet Pacific coast, ~0.25 where rain is even, approaching 0.5 in the monsoon Southwest.
- **Source**: PRISM 1991–2020 monthly precipitation normals (twelve grids, auto-downloaded by `prism.monthly_normals_paths('ppt')`).
- **Processing**: `raster.total` of JAS ÷ `raster.total` of all twelve months via `raster.ratio`. Denominator is the sum of the same monthlies (not the official annual grid) so the fraction is self-consistent; JAS chosen over JJA because the North American Monsoon onsets late June–early July — JAS reads the monsoon signal cleanly.
- **Rationale**: Added 2026-08-12. City checks give textbook regimes: Tucson 0.49 and Albuquerque 0.45 (monsoonal), Portland 0.06 (winter-wet), St. Louis 0.26 (even), Bismarck 0.38 (summer-peaked Plains). Framing from *A Natural History of the Sonoran Desert* (biseasonal rainfall); note PRISM stops at the border — a Sonora inset would need TerraClimate.
- **Facts** *(extracted 2026-08-12)*: EPSG:4269, 1405x621 px @ 0.0416667 deg, bounds (-125.0208, 24.0625, -66.4792, 49.9375), float32, nodata=-9999.0, overviews none, deflate, 1.7 MB

## surplus_months.tif
- **Role**: Count of months (0–12) where monthly P ≥ monthly PET — "how many months a year does the sky run a profit," for the `west-water-surplus-months` map. Inherently banded; symbolize as classed integers or collapsed regime bands.
- **Source**: PRISM monthly precipitation normals vs. monthly Hargreaves PET (`aridity.hargreaves_pet_monthly` from the tmin/tmax normals; twelve grids cached in `cache/pet_monthly/`).
- **Processing**: `mapprep/aridity.py` `surplus_months` — pixelwise count of months with P ≥ PET; nodata where any month is.
- **Rationale**: Added 2026-08-12, alongside a refactor splitting `_hargreaves_monthly` out of the annual function (annual output verified bit-identical). Monthly Hargreaves is noisier than the annual sum, but the count needs only the *sign* of P − PET, so it's robust. City checks: Tucson/Phoenix/Albuquerque 0, Bismarck 2, Portland 7 (all winter — the Mediterranean-climate trap: rain arrives when plants can't use it), St. Louis 7, Miami 8, Mobile 11.
- **Facts** *(extracted 2026-08-12)*: EPSG:4269, 1405x621 px @ 0.0416667 deg, bounds (-125.0208, 24.0625, -66.4792, 49.9375), uint8, nodata=255.0, overviews none, deflate, 0.1 MB

## aridity_change.tif
- **Role**: A century of aridity change — ΔAI = AI(1991–2020) − AI(1901–1930) from the epoch climatologies behind `arid_humid_divide_epochs`. Positive = wetter. The full-surface companion to the epoch divide lines for the `west-water-aridity-change` map; symbolize diverging around 0 (suggest muting tails beyond ~±0.2 so the Plains signal isn't drowned by noisy mountain pixels).
- **Source**: `cache/climatology/aridity_index_{1991-2020,1901-1930}.tif` (PRISM AN 4 km monthly series, DIY 30-yr climatologies, Hargreaves PET — see `arid_humid_divide_epochs`).
- **Processing**: `raster.difference` of the two endpoint epoch AI surfaces.
- **Rationale**: Added 2026-08-12. Distribution skews wet — mean +0.067, 5th percentile −0.029, 95th +0.185 — the geography of the Plains wetting that pulled the divide west. Magnitude caveats are load-bearing (pattern is robust, magnitude less so): the AN series is not network-consistent over a century, and the Hargreaves PET trend is likely understated because the diurnal temperature range shrank — real drying may be somewhat stronger than shown. State both on any map made from this.
- **Facts** *(extracted 2026-08-12)*: EPSG:4269, 1405x621 px @ 0.0416667 deg, bounds (-125.0208, 24.0625, -66.4792, 49.9375), float32, nodata=-9999.0, overviews none, deflate, 1.8 MB

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

## legend_rainfall_stacked.png
- **Role**: Layout legend graphic (not a map layer) — classic vertical swatch list with range labels ("< 5", "5–10", …, "> 100"). One of four style candidates; only the chosen one goes on the layout, inserted as a Picture element at 100% scale.
- **Source**: No external data. Colors are the `rainfall_classes` symbology in the Pro project, sampled programmatically from a symbology screenshot on 2026-07-20 (first color `#c2523c` = the `<Null>` class, i.e. "< 5"); class breaks are `rainfall_breaks` in `main.py`.
- **Processing**: `mapprep/legend.py` `options` (called from `main.py`) — transparent-background RGBA PNG at 300 dpi with sizes in real inches, Kumbh Sans labels in neutral ink `#3d3d3d`, hairline swatch outlines so pale colors hold shape on any backdrop. Range labels are generated from the breaks.
- **Rationale**: Added 2026-07-20. ArcGIS Pro's Legend element is tedious to style; a pre-rendered transparent PNG gives full typographic control and drops in as a Picture. The colors are mirrored from the symbology, not linked to it — re-run `main.py` (or the legend block) whenever the ramp or breaks change. Kumbh Sans matches the map's typography. *(2026-11-10)* Four classes respaced after the first layout draft, where the East read as one wall of green (30–40 and 40–60 were the same pure green hue ~10 L* apart): 30–40 `#32e300` → `#6fd41a`, 40–60 `#0ec546` → `#2aa83c`, 60–80 `#1ea088` → `#167f6c`, 80–100 `#166c8b` → `#165f8a`; the other six are unchanged. Lightness now steps 91 → 76 → 61 → 48 → 38 → 21 from 20–30 to > 100 (was 91 → 79 → 70 → 59 → 42 → 21). For these four the direction is reversed: they originate in `main.py`, so set the Pro symbology **from** them. Not yet seen under the Soft Light hillshade blend. All four style PNGs regenerated (legend block only); pixel sizes unchanged.
- **Facts** *(measured 2026-07-20; `extract_facts.py` doesn't read PNGs)*: 579x762 px @ 300 dpi (1.93 × 2.54 in), RGBA, 27 KB

## legend_rainfall_ramp.png
- **Role**: Legend style candidate — contiguous vertical color column with tick labels at the class boundaries (traditional isarithmic/precipitation-map look). See `legend_rainfall_stacked.png` for source, processing, and rationale shared by all four.
- **Facts** *(measured 2026-07-20)*: 579x627 px @ 300 dpi (1.93 × 2.09 in), RGBA, 20 KB

## legend_rainfall_bar.png
- **Role**: Legend style candidate — horizontal contiguous bar with break values under the seams. See `legend_rainfall_stacked.png` for shared details.
- **Facts** *(measured 2026-07-20)*: 744x233 px @ 300 dpi (2.48 × 0.78 in), RGBA, 15 KB

## legend_rainfall_blocks.png
- **Role**: Legend style candidate — separated horizontal blocks, each range-labeled beneath (blocks auto-widen to fit their labels). See `legend_rainfall_stacked.png` for shared details.
- **Facts** *(measured 2026-07-20)*: 1489x224 px @ 300 dpi (4.96 × 0.75 in), RGBA, 23 KB

## legend_water_balance_{stacked,ramp,bar,blocks}.png
- **Role**: Layout legend graphics for `water_balance_classes`, four style candidates (same treatment as the `legend_rainfall_*` set; only the chosen one goes on the layout). Unlike the rainfall legends, these colors originate *here* (chosen and CVD-validated in code, 2026-08-19) — set the Pro symbology **from** these hexes, not the reverse. See `water_balance_classes` for the palette and its rationale.
- **Processing**: `mapprep/legend.py` `options` from `main.py` — 300 dpi transparent RGBA, Kumbh Sans, breaks [−40 … 40].
- **Facts** *(measured 2026-08-19)*: stacked 612x762 px (2.04 × 2.54 in) 25 KB; ramp 612x627 px (2.09 in) 18 KB; bar 744x233 px (0.78 in) 13 KB; blocks 1708x224 px (5.69 × 0.75 in) 21 KB — all 300 dpi RGBA

## legend_water_balance_blocks_breaks.png
- **Role**: Layout legend graphic for `water_balance_classes` — the blocks form with the break values (−40, −20, −10, −5, 0, 5, 10, 20, 40) under the gaps between blocks instead of a range under each block. Intended replacement for `legend_water_balance_blocks.png` on the surplus & deficit sheet.
- **Source**: No external data; same colors and breaks as the `legend_water_balance_*` set.
- **Processing**: `mapprep/legend.py` `render(..., style='blocks', label_gaps=True, swatch_w=0.443)` from `main.py` — 300 dpi transparent RGBA, Kumbh Sans, true minus signs.
- **Rationale**: Added 2026-11-11. Range labels on signed classes ("-40--20", "-10--5") run the range dash into the minus signs and are hard to read, and the range form made the legend 5.69 in wide. Labeling the gaps reads cleanly, shows the zero hinge as a number, and with `swatch_w=0.443` (the rainfall blocks legend's label-driven block width) the legend is the same overall width as `legend_rainfall_blocks.png`, so it drops into the same spot on the shared layout.
- **Facts** *(measured 2026-11-11)*: 1488x224 px @ 300 dpi (4.96 × 0.75 in), RGBA, 16 KB

## legend_break_even.png
- **Role**: Layout legend graphic (not a map layer), currently unused along with its layer — a line entry for `water_balance_break_even_faded`: a short long-dashed stroke labeled "Break-even". Meant to sit with `legend_meridian_100.png` under the water balance legend, left edges aligned, at 100% scale.
- **Source**: No external data. Stroke is meant to mirror the layer's symbology in the Pro project.
- **Processing**: `mapprep/legend.py` `line_item('Break-even', ..., color='#323232cc', linewidth=0.8, dashes=(7.9, 2.8), length=0.6, font='Kumbh Sans')` from `main.py` — grey `#323232` at 80% opacity, 0.8 pt, dashes 7.9 pt on / 2.8 pt off (the layer's 70 km : 25 km at the meridian entry's scale), four whole dashes, 8.5 pt label, 300 dpi transparent RGBA.
- **Rationale**: Added 2026-11-12; first rendered solid for the exact edge, re-rendered dashed the same day when the line became a smoothed, meridian-style one. Longer dashes and a darker, slightly heavier stroke than the meridian entry so the two lines read as different things. The stroke is the **recommended** style, not read from a Pro symbol — pass the real color and weight and re-run if it is drawn differently.
- **Facts** *(measured 2026-11-12)*: 420x67 px @ 300 dpi (1.40 × 0.22 in), RGBA, 4 KB

## legend_cadillac_{stacked,ramp,bar,blocks}.png
- **Role**: Layout legend graphics for `rainfall_classes_cadillac` (the "No Place to Inhabit at All" sheet), four style candidates in the same treatment as the `legend_rainfall_*` set; the blocks version is the intended one, to match the rainfall sheet. Range labels "< 7", "7–20", "> 20" under the title "Annual precipitation (inches)". `legend_meridian_100.png` sits under it as on the rainfall sheet (the Cadillac sheet uses the same quiet meridian line; a heavier variant and its own legend entry were tried and dropped 2026-11-11 once the palette was lightened).
- **Source**: No external data. Colors are meant to mirror the `rainfall_classes_cadillac` symbology in the Pro project.
- **Processing**: `mapprep/legend.py` `options` from `main.py` — colors `#a8321e` (brick red) / `#cf9a3a` (ochre) / `#c9d9c3` (pale sage), breaks [7, 20], 300 dpi transparent RGBA, Kumbh Sans.
- **Rationale**: Added 2026-11-11. *(Same day)* Palette changed from the first draft's pure red / brown / saturated green (below) to brick red / ochre / pale sage: the two dry classes are the verdicts and carry the color, the > 20″ class recedes, and the classes step dark → mid → light with a warm/cool split at the 20″ line rather than relying on red vs green (reasoned from lightness and hue, **not** run through a CVD simulation). Unlike the first set, these colors originate *here* — set the Pro symbology from these hexes. History of the first set: The three hexes were first estimated from a layout export (median fills `#c10000`, `#916100`, `#339800`, darkened by the hillshade, matched to the nearest ArcGIS palette colors) and then confirmed against the Pro symbols the same day — they match exactly. Update `cadillac_colors` and re-run when the palette is revised (the thresholds brief flags the draft red/brown/green as harsh and weak for red-green colorblind readers). Blocks are 0.33 in wide against 0.44 in on the rainfall legend, because blocks size to their widest label; swatch height, gap and type size are identical.
- **Facts** *(measured 2026-11-11)*: stacked 579x300 px (1.93 × 1.00 in) 12 KB; ramp 579x270 px (0.90 in) 10 KB; bar 579x233 px (0.78 in) 10 KB; blocks 579x224 px (1.93 × 0.75 in) 11 KB — all 300 dpi RGBA

## legend_meridian_100.png
- **Role**: Layout legend graphic (not a map layer) — a single line entry for `meridian_100_faded`: a short dashed stroke with the label "100th meridian". Sits under whichever class legend a sheet uses, inserted as a Picture element at 100% scale; align its left edge with the class legend's and the stroke starts flush with the first swatch.
- **Source**: No external data. Stroke is meant to mirror the `meridian_100_faded` symbology in the Pro project.
- **Processing**: `mapprep/legend.py` `line_item('100th meridian', ..., color='#32323254', linewidth=0.7, font='Kumbh Sans')` from `main.py` — stroke grey `#323232` at 33% opacity, 0.7 pt, dashes 4.5 pt on / 2.8 pt off (the layer's 40 km : 25 km ratio), sample snapped to five whole dashes (0.47 in, from a 0.53 in default), label 8.5 pt in ink `#3d3d3d`, 300 dpi transparent RGBA, same 0.04 in crop padding as `render`.
- **Rationale**: Added 2026-11-10 so the rainfall sheet's legend explains the meridian. Label set at 8.5 pt to match the class labels of the `legend_rainfall_*` set (not the 10 pt legend title). The stroke color is the default recommended for the line, **not** sampled from the Pro symbol — pass `color=` to `line_item` and re-run if the layer is styled differently. *(2026-11-10, same day)* Weight set to 0.7 pt, the width used for the line in Pro; sample now ends on a whole dash instead of a clipped stub. Label glyphs measured the same pixel height as the `legend_rainfall_blocks.png` labels (26–27 px digits at 300 dpi), so the two match only when both Pictures sit at the same scale on the layout. Stroke changed from solid `#3d3d3d` to `#323232` at 33% opacity: on the rainfall sheet the line reads as a translucent darkening of the fill, not a flat grey, and a solid dark dash in the legend looked like a different line. The grey and opacity are a least-squares estimate from 60 line-vs-background pixel pairs in a layout export (rough: RMSE ~21 levels), **not** read from the Pro symbol — replace with the real color and layer transparency when known.
- **Facts** *(measured 2026-11-10; `extract_facts.py` doesn't read PNGs)*: 429x67 px @ 300 dpi (1.43 × 0.22 in), RGBA, 4 KB

## legend_meridian_100_water_balance.png
- **Role**: Layout legend graphic (not a map layer) — the "100th meridian" line entry for the Water Surplus and Deficit sheet, where `meridian_100_faded` is drawn darker and heavier than on the rainfall sheets. Same size and placement as `legend_meridian_100.png`, so it swaps in at the same position.
- **Source**: No external data. Stroke is meant to mirror the meridian's symbology on that layout.
- **Processing**: `mapprep/legend.py` `line_item('100th meridian', ..., color='#1a1a1ab8', linewidth=1.0, font='Kumbh Sans')` from `main.py` — near-black `#1a1a1a` at 72% opacity, 1.0 pt, default dashes 4.5 pt on / 2.8 pt off, five whole dashes, 8.5 pt label, 300 dpi transparent RGBA.
- **Rationale**: Added 2026-11-12. The original 33%-grey meridian disappears against the dark brown deficit fills, so the line was restyled on this sheet and the legend entry has to match. The stroke is **estimated from a layout export**, not read from the Pro symbol — pass the real color, weight and transparency and re-run if they differ.
- **Facts** *(measured 2026-11-12)*: 429x67 px @ 300 dpi (1.43 × 0.22 in), RGBA, 4 KB
