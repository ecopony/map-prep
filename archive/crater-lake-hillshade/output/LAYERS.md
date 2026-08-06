# crater-lake-hillshade — layer documentation

**Map**: Crater Lake, Oregon tinted-hillshade poster (ArcGIS Pro project name unknown)
**Script**: none — no generating script exists in the repo. Git history for this directory is a single commit (`deac3ff`, "Add Crater Lake hillshade output", 2024-06-02) that added only the two PNGs; no script was ever committed or deleted. The layers/DEM processing behind these exports is not reproducible from this repo.
**Overview**: An elevation-tinted hillshade of the Crater Lake region rendered in a John Nelson-inspired style (per the credit line printed on the layout itself: "DEM from NASA SRTM. Inspired by John Nelson. Map created by Edward Copony."). This directory contains only finished raster exports — no intermediate layers, geopackages, or GeoTIFFs.

> Entries were reconstructed on 2026-07-18, long after the files were created (May 2024) and without access to the sessions or tools that made them. Rationale marked *(reconstructed)* is inferred from the images themselves and the git commit message only.

## CraterLakeHillshadeLayout .png

Final map export of a finished ArcGIS layout, not a layer (note the stray space before `.png` in the filename). Portrait poster titled "Crater Lake - Oregon, USA": yellow-to-green elevation-tinted hillshade with the caldera at lower right, a 0–5 mile scale bar, and the SRTM/Nelson/Copony credit line. 2550x3300 px, RGBA, 300 dpi (8.5x11 in), 14.5 MB *(extracted 2026-07-18)*.

## MistEffect.png
- **Role**: Full-bleed relief render (no title, scale bar, or margins) of dissected mountain terrain with a translucent blue "mist" filling the valley bottoms — apparently an atmospheric-effect variant or experiment alongside the main layout. Whether it depicts the same extent as the layout is not determinable from the image (no caldera is visible in it).
- **Source**: Unknown. The layout's credit line attributes the DEM to NASA SRTM, but no source data or path for this specific image survives in the repo.
- **Processing**: Unknown — no script exists. Presumably an ArcGIS export given the exact layout-page dimensions (2550x3300 @ 300 dpi, matching the 8.5x11 layout export), but nothing in the repo confirms this.
- **Rationale** *(reconstructed)*: Unknown. The filename suggests it demonstrates a valley-mist effect in the John Nelson style referenced by the layout, but no record of the intent exists.
- **Facts** *(extracted 2026-07-18 via PIL)*: 2550x3300 px, RGBA, 300 dpi, 9.0 MB. No georeferencing (plain PNG, no world file or CRS).
