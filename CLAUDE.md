# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

This is a map preparation repository containing standalone Python scripts for various geospatial data processing tasks. Each subdirectory represents a different mapping project or data processing workflow.

## Environment and Tooling (uv workspace)

The repo is a [uv](https://docs.astral.sh/uv/) workspace (Python 3.12, single `.venv` and `uv.lock` at the root):

- The root `pyproject.toml` declares workspace members. Shared code lives in the `mapprep/` package (`mapprep/src/mapprep/`); converted projects (`cropland`, `carson-rem`, `forest-loss`, `property-rainwater`, `rainfall`) each have a `pyproject.toml` declaring their dependencies plus `mapprep = { workspace = true }`.
- Run a project with `uv run main.py` from its directory (or `uv run --package <name> ...` from the root). Never use `sys.path` hacks; import shared code as `from mapprep import natural_earth as ne` / `from mapprep import hillshade`.
- **GDAL**: PyPI ships no Windows wheels, so `mapprep/pyproject.toml` pins a cgohlke geospatial-wheels URL (cp312/win_amd64 only — this is why `requires-python` is pinned to 3.12 and the root locks `environments = ["sys_platform == 'win32'"]`). Upgrading GDAL or Python means picking a new wheel from https://github.com/cgohlke/geospatial-wheels/releases.
- **riverrem**: PyPI's `riverrem` is a dead 0.0.1 stub. carson-rem installs it from the OpenTopography GitHub repo and declares its undeclared runtime deps (osmnx, scipy, seaborn, cmocean, requests) explicitly.
- Unconverted projects still assume an ad-hoc environment (historically conda); convert them by adding a `pyproject.toml` and registering the directory in the root workspace `members` list.

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
- Shared functionality is extracted to the `mapprep/` package
- Output images (.png) are tracked in git while other output files are ignored
- Environment variables stored in `.env` (not tracked)

## Data Processing Notes

- Scripts typically process geospatial raster data (elevation models, satellite imagery)
- CSV data processing uses pandas for demographic and statistical data
- Geographic data often involves coordinate system transformations and spatial operations