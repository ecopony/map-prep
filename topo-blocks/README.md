# Topographic Block Designer

Create artistic three-block topographic designs from contour shapefiles. This tool transforms elevation contours into stylized block art with customizable color schemes.

## Features

- **Artistic Design**: Creates three-panel block designs with topographic contour "cutouts"
- **Multiple Color Schemes**: 16 built-in color schemes optimized for t-shirt printing and fabric
- **Batch Processing**: Process multiple mountains automatically
- **Optimized Performance**: Uses spatial indexing for fast contour clipping
- **Flexible Output**: High-resolution PNG exports with customizable settings
- **Progress Tracking**: Visual progress bars for batch operations
- **CLI Interface**: Command-line interface for easy automation

## Installation

### Required Dependencies

```bash
pip install geopandas matplotlib numpy shapely tqdm
```

### Optional: Create a virtual environment

```bash
python -m venv topo-blocks-env
source topo-blocks-env/bin/activate  # On Windows: topo-blocks-env\Scripts\activate
pip install geopandas matplotlib numpy shapely tqdm
```

## Usage

### Command Line Interface

#### Single Mountain Processing

```bash
# Basic usage
python main.py --contours path/to/contours.shp --name "Mt Adams" --output output/designs

# With optional border shapefile
python main.py --contours contours.shp --border border.shp --name "Mt Adams" --output output/designs
```

#### Batch Processing Multiple Mountains

```bash
python main.py --batch input/mountain_data --batch-output output/all_designs
```

#### Show Help and Examples

```bash
python main.py
```

### Programmatic Usage

```python
from main import TopoBlockDesigner, process_mountain_design, batch_process_mountains

# Single mountain
designer = TopoBlockDesigner("path/to/contours.shp")
designer.create_block_design("Mt Adams", "output/mt_adams_black.png",
                           colors=['#1A1A1A', '#333333', '#4D4D4D'])

# Create all color schemes
created_files = process_mountain_design("contours.shp", "Mt Adams", "output/mt_adams/")

# Batch process multiple mountains
results = batch_process_mountains("input/mountains/", "output/all_designs/")
```

## Input Data Requirements

### Shapefile Format
- **Contour files**: Must be in shapefile format (`.shp` with associated `.shx`, `.dbf`, `.prj` files)
- **Coordinate system**: Any projected coordinate system (geographic coordinates will work but may look distorted)
- **Geometry**: LineString or MultiLineString geometries representing elevation contours

### Folder Structure for Batch Processing

```
input/mountain_data/
├── mt_adams/
│   ├── contours.shp
│   ├── contours.shx
│   ├── contours.dbf
│   ├── contours.prj
│   └── border.shp (optional)
├── mt_rainier/
│   └── contours.shp (+ associated files)
└── mt_baker/
    └── elevation_contours.shp (+ associated files)
```

## Output

### File Naming
- Single processing: Uses your specified filename
- Batch processing: `{mountain_name}_{color_scheme}.png`
- Example: `Mt_Adams_sunset.png`, `Mt_Adams_ocean.png`

### Built-in Color Schemes

#### Monochrome (excellent for screen printing)
- **black**: Dark grays
- **charcoal**: Medium grays
- **white**: Light grays
- **navy**: Dark blue tones

#### Muted Earth Tones (work well on fabric)
- **desert**: Tan and beige
- **clay**: Terracotta reds
- **sage**: Muted greens
- **stone**: Gray tones

#### Tetradic Complementary
- **autumn**: Oranges and browns
- **forest**: Greens
- **ocean**: Blue-grays
- **burgundy**: Deep reds

#### Single-Color Gradients (minimalist prints)
- **indigo**: Blue-purple gradient
- **rust**: Orange-red gradient
- **pine**: Teal-green gradient
- **plum**: Brown gradient

## Customization

### Custom Colors

```python
# Use custom colors (must provide exactly 3)
custom_colors = ['#FF0000', '#00FF00', '#0000FF']
designer.create_block_design("Mountain Name", "output.png", colors=custom_colors)
```

### Advanced Options

```python
designer.create_block_design(
    mountain_name="Mt Adams",
    output_path="output/custom_design.png",
    colors=['#FF6B6B', '#4ECDC4', '#45B7D1'],
    gap_percent=0.03,          # Gap between blocks (0-0.5)
    dpi=600,                   # Higher resolution
    figsize=(16, 12),          # Larger figure size
    line_width=0.5,            # Thinner contour lines
    background_color='black',   # Black background
    text_size=48,              # Custom text size
    adaptive_text=True,        # Auto-adjust text size
    show_text=True             # Display mountain name
)
```

## Troubleshooting

### Common Issues

1. **"Missing required packages" error**
   ```bash
   pip install geopandas matplotlib numpy shapely tqdm
   ```

2. **"Shapefile not found" error**
   - Verify the file path is correct
   - Ensure all shapefile components (.shp, .shx, .dbf, .prj) are present

3. **"Shapefile is empty" error**
   - Check that your shapefile contains contour line geometries
   - Verify the data loaded correctly in QGIS or another GIS tool

4. **"Invalid bounds" error**  
   - Your contour data might have invalid coordinates
   - Check the coordinate reference system (CRS)

5. **Poor visual results**
   - Try adjusting `line_width` (0.3-2.0 range)
   - Experiment with different `gap_percent` values
   - Consider filtering your contour data to reduce density

### Performance Tips

- **Large datasets**: The spatial indexing optimization handles large contour files efficiently
- **Memory usage**: For very large datasets, consider simplifying contour geometries first
- **Batch processing**: Use `show_progress=True` to monitor long-running operations

## Data Sources

### Getting Contour Data

1. **USGS National Map**: Download elevation contours for US locations
2. **OpenStreetMap**: Extract contour data using tools like osmium
3. **GDAL contour generation**: Create contours from DEM rasters:
   ```bash
   gdal_contour -a elevation -i 50 input_dem.tif output_contours.shp
   ```

### Processing Tips

- **Contour interval**: 10-50 meter intervals work well for mountain designs
- **Extent**: Crop to your area of interest for better performance
- **Simplification**: Simplify complex geometries if needed for performance

## Examples

Check the repository for example data and outputs in the `examples/` folder (if available).

## License

This project follows the repository's main license. See the main repository README for details.

## Contributing

This tool is part of the map-prep repository. Please refer to the main repository's contribution guidelines.