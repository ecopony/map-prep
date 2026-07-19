# ca-suicides — layer documentation

**Map**: California suicide rates by county, choropleth (final layout titled "California Suicide Rates"; ArcGIS Pro project name unknown)
**Script**: `suicides.ipynb` (commit `ce7c55f`, 2024-01-19)
**Overview**: County polygons for a choropleth of age-adjusted suicide death rates, from California Bureau of Public Health "Data on Suicide and Self Harm" 2018–2020 (suicide rates by county table, prepared as `suicides.csv`). CDPH aggregates several low-population counties into three groups, so the notebook dissolves Natural Earth county polygons into matching groups; `all_counties_with_merged` (44 features) matches the 44 rows of `suicides.csv` one-to-one on `NAME` and is the layer the choropleth symbolizes. The notebook only builds geometry — the CSV join, classification (5 classes, 5.8–24.9 per 100k), and symbology were done in ArcGIS (not in code).

> Entries were reconstructed from `suicides.ipynb`, `suicides.csv`, and the finished layout export on 2026-07-18, after the layers were created. Rationale marked *(reconstructed)* is inferred from code and comments, not a firsthand record of the decisions.

## california_suicides.gpkg

### california_counties
- **Role**: All 58 California counties, undissolved — the base county geometry the other layers are derived from.
- **Source**: Natural Earth 10m admin-2 counties, `.../GeospatialResources/NaturalEarth/Counties/ne_10m_admin_2_counties/ne_10m_admin_2_counties.shp` (hardcoded macOS-style path in the notebook, predating the `$NATURAL_EARTH_DIR` convention).
- **Processing**: Filtered to `REGION == 'CA'`, kept only `NAME` and geometry.
- **Rationale** *(reconstructed)*: Kept alongside the merged layers, presumably as a reference/backup of the unmodified county set; why 10m Natural Earth counties over, e.g., Census TIGER is not recorded — unknown.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Unknown, 58 features, fields [NAME]

### merged_counties
- **Role**: The three dissolved county groups matching CDPH's aggregated reporting units.
- **Source**: Derived from `california_counties`.
- **Processing**: `dissolve_counties` — GeoPandas `dissolve()` over three fixed lists: northern (Del Norte, Lassen, Modoc, Plumas, Sierra, Siskiyou, Trinity), north-central (Colusa, Glenn, Tehama), southern (Alpine, Amador, Calaveras, Inyo, Mariposa, Mono, Tuolumne). Each group's `NAME` is set to the comma-joined county list, e.g. "Colusa, Glenn, Tehama".
- **Rationale** *(reconstructed)*: CDPH suppresses/aggregates small-county rates, so geometry must be dissolved to the same units before joining; the comma-joined `NAME` exactly matches the `Name` strings in `suicides.csv`, enabling an attribute join. The layout notes "Data for several counties are aggregated."
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Polygon, 3 features, fields [NAME]

### all_counties_with_merged
- **Role**: The join/choropleth layer — 41 individual counties plus the 3 dissolved groups, matching `suicides.csv` row-for-row (44 each) on `NAME`.
- **Source**: Derived from `california_counties`.
- **Processing**: `pd.concat` of `unmerged_counties` and `merged_counties`.
- **Rationale** *(reconstructed)*: One polygon per CSV row so the CDPH table joins cleanly with no unmatched records. The join itself is not in the notebook — done in ArcGIS.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Unknown, 44 features, fields [NAME]

### original_counties_that_were_merged
- **Role**: The 17 individual counties that went into the three dissolved groups, undissolved.
- **Source**: Derived from `california_counties`.
- **Processing**: Filter to the union of the three merge lists.
- **Rationale** *(reconstructed)*: Unknown — likely kept so the internal boundaries of the aggregated groups could still be drawn as linework (the final layout draws boundaries within the merged purple regions in the north).
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Polygon, 17 features, fields [NAME]

### unmerged_counties
- **Role**: The 41 counties reported individually by CDPH.
- **Source**: Derived from `california_counties`.
- **Processing**: Filter excluding the 17 merged counties.
- **Rationale** *(reconstructed)*: Intermediate kept as its own layer; also a component of `all_counties_with_merged`. Why it was written separately is unknown.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Unknown, 41 features, fields [NAME]

## SuicideLayout.png
Final map export of the finished ArcGIS layout "California Suicide Rates" — 5-class choropleth of age-adjusted suicide rate by county (5.8–24.9 per 100k), CDPH 2018–2020, with CDC statewide/national comparison callouts. Not a layer. 2550x3300 px (extracted 2026-07-18).

## suicide-data.png
Screenshot of a styled table render of the first rows of `suicides.csv` (columns Name, Number of Deaths, Death Rate, Rank) — a data preview, not a layer; how it was produced is not in the notebook. 1581x469 px (extracted 2026-07-18).
