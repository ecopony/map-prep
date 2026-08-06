# hillshade — layer documentation

**Map**: unknown — no ArcGIS Pro project is referenced; the outputs are display PNGs, suggesting a standalone terrain-rendering experiment rather than a layer feed.
**Script**: `generate_hillshade.py` (commit `46224f7`, 2024-06-05; refactored 2026-08-06 onto the shared `mapprep` helpers — `combine_hillshades`/`generate_slope_array` became `mapprep/hillshade.py` `combine` and `mapprep/dem.py` `slope_array`, which work in memory, so the `temp_hillshade_*` byproduct files are no longer written)
**Overview**: An experimental terrain-rendering pipeline ("hillshade automation" per the initial commit message) that builds up a stylized relief image in numbered stages: an elevation tint from a custom color ramp, a "warming" overlay, traditional / multi-directional / low-light hillshades, an elevation-driven lighting pass, a transparent "mist" layer in valleys, and a slope shading pass. Each stage is saved as its own numbered PNG so intermediate results can be compared; each blended stage composites onto the previous one (soft light, overlay, or multiply via PIL `ImageChops`), with `15-slope_blended.png` as the final composite. The script is interactive (it opens matplotlib and image-viewer windows) and uses relative paths, so it must be run from the project directory.

> Entries were reconstructed from `generate_hillshade.py` and git history on 2026-07-18, long after the project was last touched (June 2024). The `output/` directory is empty — every file below is declared by the script, not present locally. Rationale marked *(reconstructed)* is inferred from code, comments, and commit messages, not a firsthand record of the decisions.

**Missing input**: the script's DEM, `input/oblique-clip.tif`, is not in the repo (only `input/ramp.png` is tracked; `input/zippy/` is an empty directory of unknown purpose). The script cannot be re-run until that DEM is restored. Nothing in the code records what area or dataset "oblique-clip" was clipped from; all outputs inherit its (unknown) extent, and all PNGs are non-georeferenced images.

**Relationship to `mapprep/hillshade.py`**: the shared module did *not* originate from this project — git shows it descends from `utils/hillshade_utils.py` (commit `b709885`, 2024-01-26, predating this project) via the uv-workspace conversion (`be271b7`). Since the 2026-08-06 refactor the script uses the shared module: `hillshade.combine` (weighted multi-azimuth averaging, extracted from this project's old `combine_hillshades`) and `dem.slope_array`. For a plain multi-directional hillshade GeoTIFF, `mapprep.hillshade.from_dem` (GDAL's `multiDirectional=True`) also exists; this script's remaining value is the layered tint/mist/slope compositing, which has no shared-module equivalent.

## 1-terrain.png
- **Role**: Base elevation tint — the DEM colored with a custom hypsometric ramp.
- **Source**: `input/oblique-clip.tif` (DEM, provenance unknown — not present); ramp colors sampled from the horizontal center line of `input/ramp.png` (`extract_colors_from_image`).
- **Processing**: DEM normalized to 0–1 (`normalize_array`, full 0–100 percentile range), colored via a `LinearSegmentedColormap` built from the ramp pixels (`apply_colormap`), saved as RGB PNG.
- **Rationale** *(reconstructed)*: Sampling a ramp image lets the palette be designed in an image editor instead of hand-coding color stops. Why this particular ramp: unknown.
- **Facts**: not extracted (file not present)

## 2-warming.png
- **Role**: "Warming" tint — the same normalized DEM rendered with matplotlib's `plasma` colormap, used only as a blend ingredient.
- **Source**: Normalized `input/oblique-clip.tif`.
- **Processing**: `apply_colormap(normalized_dem, 'plasma')`.
- **Rationale** *(reconstructed)*: unknown beyond the variable name `warm_dem` — presumably to warm the base tint's hues when blended.
- **Facts**: not extracted (file not present)

## 3-warming_blended.png
- **Role**: Stage composite — terrain tint warmed.
- **Source**: `1-terrain.png` + `2-warming.png` (in-memory images).
- **Processing**: PIL `ImageChops.soft_light(terrain_image, warm_image)`.
- **Rationale** *(reconstructed)*: Soft light shifts hue/contrast without crushing the base tint. Why soft light vs other modes: unknown.
- **Facts**: not extracted (file not present)

## 4-traditional_hillshade.png
- **Role**: Classic single-source hillshade (azimuth 315, altitude 45).
- **Source**: `input/oblique-clip.tif`.
- **Processing**: GDAL `DEMProcessing` hillshade with `computeEdges=True`, `zFactor=1`, via `mapprep/hillshade.py` `combine([315], [45])` (a single direction, so the averaging is a no-op); grayscale array converted to RGB PNG.
- **Rationale** *(reconstructed)*: 315/45 is the conventional NW-light hillshade, kept as the first shading pass.
- **Facts**: not extracted (file not present)

## 5-hillshade_blended.png
- **Role**: Stage composite — warmed tint with traditional hillshade applied.
- **Source**: `3-warming_blended.png` + `4-traditional_hillshade.png`.
- **Processing**: `ImageChops.overlay(warming_blended, traditional_hillshade_image)`.
- **Rationale** *(reconstructed)*: unknown; overlay boosts contrast more than the soft-light used elsewhere in the chain.
- **Facts**: not extracted (file not present)

## 6-multidirectional_hillshade.png
- **Role**: Multi-directional hillshade — evens out slope illumination across aspects.
- **Source**: `input/oblique-clip.tif`.
- **Processing**: `mapprep/hillshade.py` `combine` with azimuths [45, 135, 225, 315], all at altitude 45, equal weights — four GDAL hillshades averaged with `np.average` and clipped to 0–255.
- **Rationale** *(reconstructed)*: Hand-rolled equivalent of GDAL's `multiDirectional` option (the script predates `mapprep.hillshade.from_dem`); the explicit weights parameter suggests direction weighting was meant to be tunable, though the defaults are equal.
- **Facts**: not extracted (file not present)

## 7-blended-multidirectional_hillshade.png
- **Role**: Stage composite — multi-directional shading multiplied into the running composite. One of three commented-out candidates for the final terrain base (see `13-combined_terrain_and_mist.png`).
- **Source**: `5-hillshade_blended.png` + `6-multidirectional_hillshade.png`.
- **Processing**: `ImageChops.multiply(traditional_hillshade_blended, multidirectional_hillshade_image)`.
- **Rationale** *(reconstructed)*: Multiply darkens shadowed slopes cumulatively rather than re-lighting them. Why multiply here specifically: unknown.
- **Facts**: not extracted (file not present)

## 8-low_light_hillshade.png
- **Role**: Low-sun hillshade (azimuth 315, altitude 25) — deepens shadow detail.
- **Source**: `input/oblique-clip.tif`.
- **Processing**: `combine([315], [25])`, same GDAL hillshade path as stage 4.
- **Rationale** *(reconstructed)*: A lower sun angle exaggerates relief in low-slope areas that a 45-degree sun flattens; blended in gently rather than replacing the main shading.
- **Facts**: not extracted (file not present)

## 9-low_light_hillshade_blended.png
- **Role**: Stage composite — low-light shadows blended in. A commented-out candidate for the final terrain base.
- **Source**: `7-blended-multidirectional_hillshade.png` + `8-low_light_hillshade.png`.
- **Processing**: `ImageChops.soft_light(...)`.
- **Rationale** *(reconstructed)*: unknown.
- **Facts**: not extracted (file not present)

## 10-lighting.png
- **Role**: Elevation-based lighting layer — high elevations light, low elevations dark.
- **Source**: Normalized `input/oblique-clip.tif`.
- **Processing**: `apply_colormap(normalized_dem, 'binary_r')` (reversed grayscale).
- **Rationale** *(reconstructed)*: Simulates aerial-perspective brightening of high terrain using elevation directly rather than illumination.
- **Facts**: not extracted (file not present)

## 11-lighting_blended.png
- **Role**: Stage composite — elevation lighting applied. This is the terrain base actually used for the mist composite (the stage-7 and stage-9 alternatives are commented out in the script).
- **Source**: `9-low_light_hillshade_blended.png` + `10-lighting.png`.
- **Processing**: `ImageChops.soft_light(...)`.
- **Rationale** *(reconstructed)*: The commented-out lines show stages 7, 9, and 11 were each tried as the base for the mist composite; 11 (the fullest stack) is the one left active. Why it won: unknown.
- **Facts**: not extracted (file not present)

## 12-dem_with_transparent_mist.png
- **Role**: Valley "mist" — semi-transparent white that pools in low elevations and fades out by mid-elevation. RGBA overlay, not a standalone image.
- **Source**: Normalized `input/oblique-clip.tif`.
- **Processing**: Custom RGBA colormap: white at alpha 0.85 at the lowest elevations, fading through 0.45 / 0.15 to fully transparent at 35% of the elevation range and above (stops at 0.0, 0.15, 0.25, 0.35, 1.0).
- **Rationale** *(reconstructed)*: An atmospheric-depth effect — fog in valleys — driven purely by elevation. The specific alpha stops: unknown (presumably tuned by eye).
- **Facts**: not extracted (file not present)

## 13-combined_terrain_and_mist.png
- **Role**: Terrain base with mist composited on top.
- **Source**: `11-lighting_blended.png` (re-opened from disk as RGBA) + `12-dem_with_transparent_mist.png`.
- **Processing**: `Image.alpha_composite`, flattened back to RGB.
- **Rationale** *(reconstructed)*: See stage 11 — base image was selected from three candidates by trial.
- **Facts**: not extracted (file not present)

## 14-slope.png
- **Role**: Slope shading layer, cividis-colored.
- **Source**: `input/oblique-clip.tif`.
- **Processing**: GDAL `DEMProcessing` slope (in-memory) with nodata masked (`mapprep/dem.py` `slope_array`), min-max normalized in the script, colored with matplotlib `cividis`, converted to RGB.
- **Rationale** *(reconstructed)*: Slope shading emphasizes steep faces independent of sun direction. Why cividis: unknown. Note `scale=1` is only correct if the DEM's horizontal units match its vertical units (i.e. a projected DEM in meters).
- **Facts**: not extracted (file not present)

## 15-slope_blended.png
- **Role**: Final composite — the finished stylized terrain render (also displayed on screen at the end of the run).
- **Source**: `13-combined_terrain_and_mist.png` + `14-slope.png`.
- **Processing**: `ImageChops.soft_light(...)`.
- **Rationale** *(reconstructed)*: Last pass of the stack; nothing further is derived from it.
- **Facts**: not extracted (file not present)

## temp_hillshade_{azimuth}_{altitude}.tif (5 files)
- **Role**: Byproducts of the pre-2026-08-06 script only — per-direction GDAL hillshade rasters written because the old local `generate_hillshade` needed an output path. The shared `mapprep/hillshade.py` `combine` works on in-memory `MEM` datasets, so re-runs no longer produce these.
- **Facts**: not extracted (files not present)
