# ambient-occlusion — layer documentation

**Map**: unknown — no ArcGIS Pro project or map is named anywhere in the project.
**Script**: `main.py` (commit `6737d08`, 2024-10-05, "Update ambient occlusion creation")
**Overview**: Standalone experiment (per the commit messages: "ambient occlusion automation") that derives shading components from a clipped DEM: the DEM blurred at three window sizes (10/20/50 px mean filter), a single-azimuth hillshade and a slope raster for the original and each blurred DEM, and a hillshade computed *from* the slope raster. The pieces were presumably meant to be blended into an ambient-occlusion-style relief in downstream software, but no compositing step exists in the repo — how they were combined is unknown. The script processes one area per run (`area_name`, currently `'carson'`); the `carson/`, `lucky/`, `nehalem/` subdirectories indicate it was run for three areas.

> Entries were reconstructed from `main.py` and git history on 2026-07-18, long after the layers were created. Rationale marked *(reconstructed)* is inferred from code and commit messages, not a firsthand record of the decisions. **All output files are declared by the script but not present locally** — `output/carson/`, `output/lucky/`, and `output/nehalem/` exist but are empty, so no Facts could be extracted. The script's input, `input/combined_clip.tif`, is also absent (its source and extent are unknown); the only file in `input/` is an unrelated, unreferenced `Terrain.tif`.

The entries below describe one run's file set. Each of `carson/`, `lucky/`, `nehalem/` would contain the same twelve files (the script writes to `output/<area_name>/`).

## <area>/blur_10.tif, blur_20.tif, blur_50.tif
- **Role**: Intermediates — the input DEM smoothed at three scales, inputs to the blurred hillshades and slopes below.
- **Source**: `input/combined_clip.tif` (not present locally; provenance unknown — the name suggests a mosaic clipped to the area of interest).
- **Processing**: `blur_dem_raster` in `main.py` — scipy `uniform_filter` (mean filter) with window sizes 10, 20, and 50 pixels; the DEM is reflect-padded by half the window first so edges don't darken. Profile copied from the source.
- **Rationale** *(reconstructed)*: Blurring the DEM at several scales before shading is a standard way to approximate ambient-occlusion / broad-scale shadowing; three window sizes give scales to compare or blend. Why these particular sizes: unknown.
- **Facts**: not extracted — files not present locally.

## <area>/original_hillshade_315.0_45.0.tif, blur_10_hillshade_315.0_45.0.tif, blur_20_hillshade_315.0_45.0.tif, blur_50_hillshade_315.0_45.0.tif
- **Role**: Single-azimuth hillshades of the original and each blurred DEM — the shading components at increasing generalization.
- **Source**: `input/combined_clip.tif` and the `blur_*.tif` intermediates above.
- **Processing**: `generate_hillshade` in `main.py` — GDAL `DEMProcessing` hillshade with defaults azimuth 315, altitude 45, zFactor 1, `computeEdges=True` (the azimuth/altitude are baked into the filename).
- **Rationale** *(reconstructed)*: 315/45 is the conventional NW-light hillshade; all parameters are the function defaults, so no evidence of tuning. The blurred variants shade progressively broader landforms.
- **Facts**: not extracted — files not present locally.

## <area>/original_slope.tif, blur_10_slope.tif, blur_20_slope.tif, blur_50_slope.tif
- **Role**: Slope rasters of the original and each blurred DEM — usable as a darkening/occlusion component (steeper = darker) alongside the hillshades.
- **Source**: `input/combined_clip.tif` and the `blur_*.tif` intermediates above.
- **Processing**: `generate_slope` in `main.py` — GDAL `DEMProcessing` slope, zFactor 1, `computeEdges=True`.
- **Rationale** *(reconstructed)*: Slope shading is a common ingredient in manual ambient-occlusion/relief recipes; beyond that, unknown.
- **Facts**: not extracted — files not present locally.

## <area>/slope_hillshade_315.0_45.0.tif
- **Role**: A hillshade computed from the slope raster (treating slope values as elevation) — accentuates breaks in slope, another occlusion-style component.
- **Source**: `<area>/original_slope.tif` above.
- **Processing**: `generate_hillshade` applied to the slope raster, same defaults (315/45, zFactor 1, `computeEdges=True`).
- **Rationale** *(reconstructed)*: unknown — no comment or commit message explains this step; hillshading a slope surface is a known trick for edge/curvature emphasis.
- **Facts**: not extracted — files not present locally.
