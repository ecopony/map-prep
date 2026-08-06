# wind-turbines — layer documentation

**Map**: Three related US wind-turbine maps — turbine counts by state, installed-vs-potential capacity by state, and a turbine-density heat map. Exact ArcGIS Pro project name(s) unknown; the finished layouts are exported here as `WindTurbineCountLayout.png`, `WindTurbineCapacityLayout.png`, and `WindTurbineHeatMapLayout.png`.
**Script**: `wind-turbine-counts.ipynb`, `wind-turbine-capacity.ipynb`, `wind-turbine-heatmap.ipynb` (committed 2338186, 2024-01-19; `WindTurbineCountLayout.png` re-exported in 4594964, 2024-04-28)
**Overview**: Each notebook writes one geopackage for its own map. All three build on the USGS United States Wind Turbine Database (USWTDB) v6.1 (2023-11-28) and/or WINDExchange state capacity tables, with Natural Earth 50m countries and states as the basemap reference. The counts map classifies states by whether they contain any turbines and how many; the capacity map carries installed capacity, potential capacity, and percent-installed per state for choropleth symbolization; the heat map ships the raw turbine points for density (heat-map) rendering in ArcGIS. Everything is EPSG:4326.

> Entries were reconstructed from the notebooks and git history on 2026-07-18, well after the layers were created. Rationale marked *(reconstructed)* is inferred from code, comments, and commit messages, not a firsthand record of the decisions.

## wind-turbines.gpkg

Produced by `wind-turbine-counts.ipynb`.

### wind_turbines
- **Role**: All US wind turbine locations as points — the raw data behind the per-state counts.
- **Source**: USGS United States Wind Turbine Database (USWTDB) v6.1, shapefile `uswtdb_v6_1_20231128.shp` at `$DATA_DIR/WindTurbines/uswtdbSHP/` (https://eerscmap.usgs.gov/uswtdb/data/).
- **Processing**: Read with geopandas, reprojected to EPSG:4326, written unmodified otherwise.
- **Rationale** *(reconstructed)*: Unknown beyond standardizing on EPSG:4326 for all layers in the project.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Point, 73352 features, fields [case_id, faa_ors, faa_asn, usgs_pr_id, eia_id, t_state, t_county, t_fips, ... (27 total)]

### united_states_50m
- **Role**: Single US country outline for the basemap.
- **Source**: Natural Earth 50m admin-0 countries, `$NATURAL_EARTH_DIR/Countries/ne_50m_admin_0_countries`.
- **Processing**: Filtered to `ADMIN == 'United States of America'`.
- **Rationale** *(reconstructed)*: Unknown.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, MultiPolygon, 1 features, fields [featurecla, scalerank, LABELRANK, SOVEREIGNT, SOV_A3, ADM0_DIF, LEVEL, TYPE, ... (168 total)]

### us_states_50m
- **Role**: All US states/territories with a per-state turbine count attribute (`wind_turbine_join_count`) for labeling or choropleth.
- **Source**: Natural Earth 50m admin-1 states & provinces (non-lakes version), `$NATURAL_EARTH_DIR/StatesProvinces/ne_50m_admin_1_states_provinces`. Note the other two notebooks use the *lakes* version; this one uses the plain version and adds the Great Lakes as a separate layer instead.
- **Processing**: Filtered to `iso_a2 == 'US'` (51 features: 50 states + DC), then a geopandas `sjoin` with the turbine points, grouped by state index; the size of each group becomes `wind_turbine_join_count` (0 where no turbines join).
- **Rationale** *(reconstructed)*: Spatial join rather than the USWTDB `t_state` attribute — why is unknown. Turbines not intersecting a state polygon (e.g. offshore points) are not counted.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Unknown, 51 features, fields [featurecla, scalerank, adm1_code, diss_me, iso_3166_2, wikipedia, iso_a2, adm0_sr, ... (122 total)]

### great_lakes_50m
- **Role**: Great Lakes water polygons, drawn over the non-lakes state polygons.
- **Source**: Natural Earth 50m lakes, `$NATURAL_EARTH_DIR/Lakes/ne_50m_lakes`.
- **Processing**: Filtered by name to the five Great Lakes (Superior, Michigan, Huron, Erie, Ontario).
- **Rationale** *(reconstructed)*: Since the state layer here is the non-lakes version, the lakes are supplied as their own layer so they can be symbolized as water on top; why this was preferred over the lakes version of the states layer is unknown.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Polygon, 5 features, fields [scalerank, featurecla, name, name_alt, note, admin, namepar, min_zoom, ... (39 total)]

### states_with_no_wind_turbines_50m
- **Role**: The subset of states with zero joined turbines, split out so they can be symbolized distinctly (e.g. greyed out).
- **Source**: Derived from `us_states_50m` above.
- **Processing**: `wind_turbine_join_count == 0`.
- **Rationale** *(reconstructed)*: Pre-splitting the two classes into separate layers avoids attribute-driven symbology in ArcGIS; not stated in code, inferred from the layer names.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Unknown, 8 features, fields [featurecla, scalerank, adm1_code, diss_me, iso_3166_2, wikipedia, iso_a2, adm0_sr, ... (122 total)]

### states_with_at_least_one_wind_turbine_50m
- **Role**: Complement of the layer above — states with one or more joined turbines.
- **Source**: Derived from `us_states_50m` above.
- **Processing**: `wind_turbine_join_count > 0`.
- **Rationale** *(reconstructed)*: See `states_with_no_wind_turbines_50m`.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Unknown, 43 features, fields [featurecla, scalerank, adm1_code, diss_me, iso_3166_2, wikipedia, iso_a2, adm0_sr, ... (122 total)]

## wind-turbines-capacity.gpkg

Produced by `wind-turbine-capacity.ipynb`.

### na_countries_50m
- **Role**: North American country polygons as basemap context around the US.
- **Source**: Natural Earth 50m admin-0 countries, `$NATURAL_EARTH_DIR/Countries/ne_50m_admin_0_countries`.
- **Processing**: Filtered to `CONTINENT == 'North America'`.
- **Rationale** *(reconstructed)*: Unknown.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Unknown, 38 features, fields [featurecla, scalerank, LABELRANK, SOVEREIGNT, SOV_A3, ADM0_DIF, LEVEL, TYPE, ... (168 total)]

### us_states_50m
- **Role**: The thematic layer — states carrying installed capacity, potential capacity, and percent-installed for choropleth symbolization.
- **Source**: Geometry from Natural Earth 50m admin-1 states & provinces (lakes version), `$NATURAL_EARTH_DIR/StatesProvinces/ne_50m_admin_1_states_provinces_lakes`. Attributes from two CSVs prepared from the U.S. Office of Energy Efficiency and Renewable Energy's WINDExchange (https://windexchange.energy.gov/maps-data/321): `$DATA_DIR/WindTurbines/capacity/installed-capacity.csv` and `potential-capacity.csv`.
- **Processing**: States filtered to `iso_a2 == 'US'` and trimmed to [iso_3166_2, name, geometry]; `state_abr` derived from `iso_3166_2`. Left-merged with `potential_capacity` on `state_abr` and `installed_capacity` on state name (installed NaN filled with 0 before merge); `percent_installed = installed / potential * 100`; rows with any remaining NaN dropped, leaving 48 of the 51 US features — states with no potential-capacity match are silently excluded from the layer.
- **Rationale** *(reconstructed)*: Filling missing installed capacity with 0 treats "no data" as "no installed turbines"; dropping rows lacking potential capacity removes them from the map entirely. Whether either was a deliberate cartographic choice is unknown.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Unknown, 48 features, fields [iso_3166_2, name, state_abr, potential_capacity, installed_capacity, percent_installed]

## wind-turbines-heatmap.gpkg

Produced by `wind-turbine-heatmap.ipynb`.

### wind_turbines
- **Role**: Turbine points for heat-map (density) rendering. The density surface itself is not computed here — *(reconstructed)* it was presumably produced with heat-map symbology in ArcGIS Pro, since the geopackage carries only the raw points.
- **Source**: USWTDB v6.1 (2023-11-28), same shapefile as `wind-turbines.gpkg` above; per the notebook's markdown cell, "Wind turbine data from the USGS United States Wind Turbine Database (USWTDB), 2023."
- **Processing**: Read, reprojected to EPSG:4326, written as-is.
- **Rationale** *(reconstructed)*: Unknown.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Point, 73352 features, fields [case_id, faa_ors, faa_asn, usgs_pr_id, eia_id, t_state, t_county, t_fips, ... (27 total)]

### na_countries_50m
- **Role**: North American country polygons as basemap context.
- **Source/Processing**: Identical to `na_countries_50m` in `wind-turbines-capacity.gpkg` (Natural Earth 50m admin-0, `CONTINENT == 'North America'`).
- **Rationale** *(reconstructed)*: Unknown.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Unknown, 38 features, fields [featurecla, scalerank, LABELRANK, SOVEREIGNT, SOV_A3, ADM0_DIF, LEVEL, TYPE, ... (168 total)]

### us_states_50m
- **Role**: State boundary reference layer.
- **Source**: Natural Earth 50m admin-1 states & provinces (lakes version), `$NATURAL_EARTH_DIR/StatesProvinces/ne_50m_admin_1_states_provinces_lakes`.
- **Processing**: Filtered to `iso_a2 == 'US'`; no attribute work.
- **Rationale** *(reconstructed)*: Unknown.
- **Facts** *(extracted 2026-07-18)*: EPSG:4326, Unknown, 51 features, fields [featurecla, scalerank, adm1_code, diss_me, iso_3166_2, wikipedia, iso_a2, adm0_sr, ... (121 total)]

## installed-capacity.png / potential-capacity.png
- **Role**: Chart images (717x406 and 617x436 px) of state capacity data, associated with `wind-turbine-capacity.ipynb`.
- **Processing/Rationale**: The code that saved them is not present — the current notebook renders only a percent-installed seaborn bar chart and has no `savefig` call (nor does its checkpoint). Presumably exported from earlier chart cells; specifics unknown.
- **Facts** *(extracted 2026-07-18)*: installed-capacity.png 717x406 px; potential-capacity.png 617x436 px.

## WindTurbineCountLayout.png, WindTurbineCapacityLayout.png, WindTurbineHeatMapLayout.png
Final map exports of the finished ArcGIS Pro layouts, not layers — 4200x2550, 3300x2550, and 3300x2550 px respectively *(extracted 2026-07-18)*. The count layout was re-exported on 2024-04-28 (commit 4594964, "Update wind turbine count output"); the heat-map layout on 2024-01-21 (9ec6bc5).
