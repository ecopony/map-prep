# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

This is a map preparation repository containing standalone Python scripts for various geospatial data processing tasks. Each subdirectory represents a different mapping project or data processing workflow.

## Key Dependencies

The codebase primarily uses:
- **rasterio**: Raster data I/O and processing
- **GDAL/osgeo**: Geospatial data processing and DEM operations
- **pandas**: Data manipulation for CSV processing
- **numpy/scipy**: Numerical operations and filtering
- **requests**: HTTP requests for data fetching (in utils)

## Common Patterns

1. **Input/Output Structure**: Most projects follow the pattern:
   - `input/` directory for source data
   - `output/` directory for generated files (tracked in git for .png files only)
   - `main.py` as the primary processing script

2. **Caching**: Projects with data fetching implement JSON-based caching in `.osm_cache/` or `cache/` directories

3. **DEM Processing**: Multiple projects use GDAL's DEMProcessing for hillshade, slope, and aspect calculations

## File Organization

- Individual project directories are self-contained with their own data and processing scripts
- Shared functionality is extracted to `utils/` module
- Output images (.png) are tracked in git while other output files are ignored
- Environment variables stored in `.env` (not tracked)

## Data Processing Notes

- Scripts typically process geospatial raster data (elevation models, satellite imagery)
- CSV data processing uses pandas for demographic and statistical data
- Geographic data often involves coordinate system transformations and spatial operations