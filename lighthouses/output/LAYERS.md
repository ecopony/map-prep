# lighthouses — layer documentation

**Map**: Lighthouse poster maps (ArcGIS Pro project name unknown; the `*Layout.png` filenames indicate ArcGIS Pro layout exports)
**Script**: none — no generating script exists in the repo, and git history shows none was ever committed (the only commits touching this project, `6931c9c` "Add West Coast Lighthouse output" and `f2cb575` "Add Washington lighthouses output", both 2024-04-29, each add a single PNG)
**Overview**: Two finished poster-style maps of lighthouse locations, exported from ArcGIS Pro layouts. Both use the same visual treatment: a near-black basemap with lighthouse point locations rendered as glowing yellow points and a large yellow title along the bottom edge. There are no data layers here — the PNGs are final map exports, and the source lighthouse data and ArcGIS project are not in the repo.

> Entries were reconstructed on 2026-07-18, long after the files were created (2024-04-29). The author of this documentation was not present when the maps were made; everything below comes from the files themselves and git commit messages. Rationale marked *(reconstructed)* is inferred, not a firsthand record.

## LighthousesOfWashingtonLayout.png
- **Role**: Final map export, not a layer — a landscape poster titled "LIGHTHOUSES OF WASHINGTON" showing lighthouse locations along the Washington coast, Strait of Juan de Fuca, and Puget Sound as glowing yellow points on a dark basemap.
- **Source**: Unknown — no source data in the repo. The attribution line visible in the export credits "WA State Parks GIS, Esri, TomTom, Garmin, FAO, NOAA, USGS, Bureau of Land Management, EPA, NPS, USFWS", suggesting a WA State Parks GIS lighthouse layer over an Esri basemap.
- **Processing**: Unknown — designed and exported from an ArcGIS Pro layout; no processing script exists in the repo.
- **Rationale** *(reconstructed)*: unknown. The glow-on-dark styling evokes lighthouse beacons at night, but this is inferred from the visual design only.
- **Facts** *(extracted 2026-07-18, PIL)*: 3300x2550 px, RGBA, 300 dpi (11 x 8.5 in), 1.8 MB

## WestCoastLighthousesLayout.png
- **Role**: Final map export, not a layer — a portrait poster titled "WEST COAST LIGHTHOUSES" showing lighthouse locations along the US Pacific coast (Washington through Southern California) as glowing yellow points on a dark basemap, same styling as the Washington poster.
- **Source**: Unknown — no source data in the repo. The attribution line visible in the export credits Esri basemap contributors (Esri, TomTom, Garmin, FAO, NOAA, USGS, EPA, USFWS) plus a "Map created by ..." credit.
- **Processing**: Unknown — designed and exported from an ArcGIS Pro layout; no processing script exists in the repo.
- **Rationale** *(reconstructed)*: unknown. Committed one day-order before the Washington poster (`6931c9c` precedes `f2cb575`); the Washington map appears to be a state-level companion to this coast-wide one, but that sequencing is the only evidence.
- **Facts** *(extracted 2026-07-18, PIL)*: 2550x3300 px, RGBA, 300 dpi (8.5 x 11 in), 0.3 MB
