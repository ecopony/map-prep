# vintage-topo — layer documentation

> **Structural note**: this project deviates from the usual one-`output/`-per-project layout. It has no processing script and no `output/` of its own — it is split into two sub-area directories, `crater-lake/` and `nehalem/`, each holding only exported ArcGIS layout images. This single `LAYERS.md` (in a created `output/` directory) covers both sub-areas; file paths below are relative to `vintage-topo/`.

**Map**: Vintage USGS topographic sheets restyled with shaded relief (and one 3D scene); ArcGIS Pro project name unknown.
**Script**: none — no processing script exists in the repo. All composition was done in ArcGIS Pro; only the layout exports were committed (`9cfa25d` "Add vintage topo layouts", 2024-09-17).
**Overview**: Two small map projects built on scanned historical USGS topographic maps of Oregon: the 1891 1:250,000 "Ashland Sheet" (which includes Crater Lake) and the 1985 provisional-edition 1:24,000 Nehalem quadrangle. Per the credit lines printed on the exports, each scan was combined with a DEM (NASA DEM for Ashland/Crater Lake, ESRI Living Atlas DEM for Nehalem) — the visible result is the vintage sheet shaded/draped with modern relief, plus a 3D perspective render of the Ashland sheet. There are no intermediate layers on disk; the finished exports are all that exists.

> Entries were reconstructed from the exported images and git history on 2026-07-18, long after the layouts were created (September 2024). No source script or ArcGIS project is in the repo, so rationale marked *(reconstructed)* is inferred from what is visible in the images themselves; where the "why" is unknowable it is marked unknown.

## crater-lake/

Source sheet (visible in the export): USGS "Ashland Sheet", Oregon, 1:250,000, edition of Oct. 1891, contour interval 200 ft, surveyed 1886–7; covers Jackson/Douglas/Klamath counties with Crater Lake in the northeast corner. Credit line on the export: "Original image USGS. DEM NASA. Created by Edward Copony."

### crater-lake/Layout72.png
Final map export (not a layer): the 1891 Ashland Sheet scan with modern DEM-derived shaded relief applied, exported flat from an ArcGIS layout. Filename suggests a 72-DPI export *(reconstructed)*.
**Facts** *(extracted 2026-07-18, PIL)*: 1440x1872 px, RGB, 5.6 MB. No georeferencing (plain PNG).

### crater-lake/Layout3d.png
Final map export (not a layer): 3D perspective scene of the same vintage sheet draped over a DEM and rendered as an extruded terrain block (view over the sheet's southeast corner — Pelican Bay / Aspen Lake area).
**Facts** *(extracted 2026-07-18, PIL)*: 3300x2550 px, RGB, 10.3 MB. No georeferencing (plain PNG).

## nehalem/

Source sheet (visible in the export): USGS Nehalem quadrangle, Oregon — Tillamook Co., 7.5-minute series, Provisional Edition 1985, 1:24,000, contour interval 40 ft; covers Nehalem Bay, Manzanita, Wheeler, and the surrounding coast. Credit line on the export: "Source image USGS. DEM ESRI Living Atlas. Map created by Edward Copony."

### nehalem/Layout72.png
Final map export (not a layer): the 1985 Nehalem quad scan with modern DEM-derived shaded relief applied to the terrain, exported flat from an ArcGIS layout. Filename suggests a 72-DPI export *(reconstructed)*.
**Facts** *(extracted 2026-07-18, PIL)*: 1584x2016 px, RGB, 3.7 MB. No georeferencing (plain PNG).

## Notes for reuse
- **Rationale** *(reconstructed)*: the project pairs historical USGS scans with modern DEM relief for an aged, hand-drawn look with realistic depth; why these two particular sheets were chosen is unknown.
- The underlying inputs (the USGS scan GeoTIFFs, the DEMs, and the ArcGIS Pro project/scene) are not in the repo; regenerating or modifying these maps would require recreating the ArcGIS work from scratch.
