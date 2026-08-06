# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

This is a map preparation repository containing standalone Python scripts for various geospatial data processing tasks. The top level separates directories by kind:

- `packages/` — shared code that other things import (currently just `mapprep`)
- `projects/` — mapping projects that are run; each subdirectory is self-contained
- `archive/` — finished poster exports with no reproducible pipeline (documentation only, no scripts)
- `shared/` — non-code assets used across projects (e.g. `attribution.txt`, the Natural Earth attribution string)

## Environment and Tooling (uv workspace)

The repo is a [uv](https://docs.astral.sh/uv/) workspace (Python 3.12, single `.venv` and `uv.lock` at the root):

- The root `pyproject.toml` declares workspace members. Shared code lives in the `mapprep` package (`packages/mapprep/src/mapprep/`); converted projects (`ambient-occlusion`, `carson-rem`, `conferences`, `cropland`, `forest-loss`, `hillshade`, `property-rainwater`, `rainfall` under `projects/`) each have a `pyproject.toml` declaring their dependencies plus `mapprep = { workspace = true }`.
- Run a project with `uv run main.py` from its directory (or `uv run --package <name> ...` from the root). Never use `sys.path` hacks; import shared code as `from mapprep import natural_earth as ne` / `from mapprep import hillshade`.
- **GDAL**: PyPI ships no Windows wheels, so `packages/mapprep/pyproject.toml` pins a cgohlke geospatial-wheels URL (cp312/win_amd64 only — this is why `requires-python` is pinned to 3.12 and the root locks `environments = ["sys_platform == 'win32'"]`). Upgrading GDAL or Python means picking a new wheel from https://github.com/cgohlke/geospatial-wheels/releases.
- **riverrem**: PyPI's `riverrem` is a dead 0.0.1 stub. carson-rem installs it from the OpenTopography GitHub repo and declares its undeclared runtime deps (osmnx, scipy, seaborn, cmocean, requests) explicitly.
- Unconverted projects still assume an ad-hoc environment (historically conda); convert them by adding a `pyproject.toml` and registering the directory (as `projects/<name>`) in the root workspace `members` list.

## Environment Variables

Source data lives outside the repo; scripts locate it through variables in a `.env` file at
the repo root (not tracked). Copy `.env.example` and set the paths for your machine.

| Variable | Points at | Used by |
| --- | --- | --- |
| `NATURAL_EARTH_DIR` | Natural Earth shapefiles, per-theme subdirs (`Countries/`, `StatesProvinces/`, `Lakes/`) | `mapprep.natural_earth`, and so every project importing it; also `conferences`, `wind-turbines` |
| `NASA_DIR` | NASA elevation data, containing `SRTM_30/` | `forest-loss` |
| `TNM_DIR` | USGS The National Map, by state code (`OR/`, `WA/`) | `stylized-pdx` |
| `NHD_DIR` | USGS National Hydrography Dataset, by state code | `stylized-pdx` |
| `DATA_DIR` | Catch-all for project-specific downloads | `wind-turbines` |

Projects reading only from a local `input/` directory (`cropland`, `ambient-occlusion`,
`topo-blocks`, `ridge-maps`) need none of these. `census-poverty` calls the Census API
without a key.

Load with `dotenv.load_dotenv(dotenv.find_dotenv())`, as `packages/mapprep/src/mapprep/natural_earth.py`
does — it searches upward from the caller and works regardless of the directory a script is
run from. Always use `find_dotenv()` — hardcoded relative paths like `load_dotenv("../.env")`
break whenever a script moves or is run from a different directory (all call sites were
normalized to `find_dotenv()` during the 2026-08 reorg).

## Layer Documentation

Every file written to a project's `output/` directory must be documented in that project's `output/LAYERS.md` — use the `make-layer` skill, which covers the entry format, the facts-extraction script, and update semantics. `CATALOG.md` at the repo root indexes documented projects; it is the entry point for Claude sessions in the user's map-planning directory, which see only files and rely on this documentation for the reasoning and processing chain behind each layer.

## Key Dependencies

The codebase primarily uses:
- **rasterio**: Raster data I/O and processing
- **GDAL/osgeo**: Geospatial data processing and DEM operations
- **pandas**: Data manipulation for CSV processing
- **numpy/scipy**: Numerical operations and filtering
- **requests**: HTTP requests for data fetching

## Common Patterns

1. **Input/Output Structure**: Most projects follow the pattern:
   - `input/` directory for source data
   - `output/` directory for generated files (tracked in git for .png files only)
   - `main.py` as the primary processing script

2. **Caching**: Projects with data fetching implement JSON-based caching in `.osm_cache/` or `cache/` directories

3. **DEM Processing**: Multiple projects use GDAL's DEMProcessing for hillshade, slope, and aspect calculations

## File Organization

- Individual project directories are self-contained with their own data and processing scripts
- Shared functionality is extracted to the `mapprep` package in `packages/`
- Output images (.png) are tracked in git while other output files are ignored
- Environment variables stored in `.env` (not tracked); see Environment Variables above and `.env.example`

## Data Processing Notes

- Scripts typically process geospatial raster data (elevation models, satellite imagery)
- CSV data processing uses pandas for demographic and statistical data
- Geographic data often involves coordinate system transformations and spatial operations