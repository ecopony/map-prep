# stylized-pdx — layer documentation

**Map**: Stylized circular map of Portland, Oregon. Unlike most projects here, `main.py` renders the final composition itself with matplotlib (`plt.show()`, never saved to disk); no ArcGIS Pro project is referenced in code or git history, so whether the geopackage also feeds ArcGIS is unknown.
**Script**: `main.py` (commit `852e8b9` "Add stylized PDX map", 2024-07-29)
**Overview**: A poster-style map: a 25 km circle centered on Portland's centroid frames city-limits fill, TNM road linework in three weight classes (freeways, arterials, collectors), NHD water polygons, and a semi-transparent white mask over everything outside the city boundary and water. Only three of these layers are persisted to `output/stylized-pdx.gpkg` (`pdx_boundary`, `pdx_circle`, `all_roads`); the water layers (`NHDArea`, `NHDWaterbody`) and the derived mask exist only in memory for the matplotlib render. The project predates the uv workspace (no `pyproject.toml`) and reads source data from `$TNM_DIR` and `$NHD_DIR` via the repo-root `.env`.

> Entries were reconstructed from `main.py` and git history on 2026-07-18, long after the script was written (2024-07-29). The `output/` directory is empty — every file below is declared by the script but not present locally, so no facts were extracted. Rationale marked *(reconstructed)* is inferred from code and comments, not a firsthand record of the decisions.

## stylized-pdx.gpkg
Declared by the script, not present locally. Written incrementally as the script runs — each layer's `to_file(..., driver='GPKG')` call happens at a different point in the flow, which matters for `pdx_boundary` (see below).

### pdx_boundary
- **Role**: Portland city limits — the light-gray fill of the map and the shape the outside-the-city mask is cut against.
- **Source**: USGS The National Map (TNM) governmental-unit geopackage, `$TNM_DIR/OR/GOVTUNIT_Oregon_State_GPKG/GOVTUNIT_Oregon_State_GPKG.gpkg`, layer `GU_IncorporatedPlace`.
- **Processing**: SQL-filtered to `place_name = 'Portland' or place_name = 'Maywood Park'`, reprojected to EPSG:4326, dissolved to a single feature, then written to the geopackage. **Note**: the write happens *before* the simplification step — the script then simplifies the in-memory geometry (`simplify_coords`, tolerance 0.0025°, exterior rings only, so any holes are dropped) and uses that simplified version for the centroid, the mask, and the render. The persisted layer is the unsimplified dissolve.
- **Rationale** *(reconstructed)*: Maywood Park is a separate incorporated city fully enclosed by Portland; including it in the dissolve avoids a donut hole in the city fill. Why the simplified geometry is used downstream but never persisted is unknown — possibly notebook-style exploratory code (the script plots nearly every intermediate).
- **Facts**: not extracted (file not present)

### pdx_circle
- **Role**: The circular layout frame — white disc with black edge drawn at the bottom of the stack, and the clip/mask boundary for every other layer.
- **Source**: Derived; no external dataset.
- **Processing**: Centroid of the (simplified) city boundary computed in EPSG:3857, buffered by `pdx_radius = 25000`, then reprojected back to EPSG:4326 and written.
- **Rationale** *(reconstructed)*: A fixed-radius circle around the city centroid gives the poster its circular composition. Why 25 km specifically is unknown. Note the buffer distance is 25,000 EPSG:3857 (Web Mercator) meters; at Portland's latitude (~45.5°N) that corresponds to roughly 17.5 km on the ground, not 25 km — the code gives no indication whether this was intended.
- **Facts**: not extracted (file not present)

### all_roads
- **Role**: Road linework, symbolized by functional class in the render — `tnmfrc` 1/8 as freeways (1.0 pt, `#828282`), 2/3 as arterials (0.6 pt, `#828282`), 4/5 as collectors (0.3 pt, `#B2B2B2`).
- **Source**: TNM transportation geopackages for both states, `$TNM_DIR/OR/TRAN_Oregon_State_GPKG/...` and `$TNM_DIR/WA/TRAN_Washington_State_GPKG/...`, layer `Trans_RoadSegment` in each.
- **Processing**: Each state's segments read with the circle as a read `mask`, reprojected to EPSG:4326, `gpd.clip` to the circle, then the OR and WA frames concatenated (`pd.concat`, index reset) and written as one layer. No functional-class filter is applied at write time — the full clipped segment set is stored; class filtering happens only at render time.
- **Rationale** *(reconstructed)*: The circle spans the Columbia River, so Washington roads (Vancouver, WA) are needed to fill the frame's northern half — hence two state files merged. Keeping all classes in the layer and filtering on `tnmfrc` at render time leaves symbology choices open.
- **Facts**: not extracted (file not present)

## Not persisted (render-only)
For completeness — these are built and plotted by `main.py` but never written to `output/`:

- **NHD water** — `NHDArea` (river/stream polygons, unfiltered) and `NHDWaterbody` (filtered to `FType = 390` lakes/ponds with `AREASQKM > 0.248`) from `$NHD_DIR/OR/NHD_H_Oregon_State_GDB/NHD_H_Oregon_State_GDB.gdb`, clipped to the circle, drawn in `#004C73`. Only the Oregon NHD file is read, so Washington-side water beyond what the OR file carries (the NHD Oregon state extract does include the Columbia mainstem) may be incomplete — the code gives no indication this was considered. *(reconstructed)*: the area threshold presumably drops pond speckle; why 0.248 sq km exactly is unknown.
- **pdx_mask** — circle minus city boundary minus both water layers, drawn as 80%-opacity white on top (zorder 4), dimming everything outside Portland while leaving water visible.
- **The figure itself** — 10x12 in, titled "portland, oregon", shown with `plt.show()` and never saved; there is no PNG in `output/` and the script has no `savefig`.
