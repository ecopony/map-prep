import rasterio
from osgeo import gdal
from scipy.ndimage import uniform_filter
import numpy as np


def blur_dem_raster(input_path, output_path, pixel_window):
    """
    Blurs a DEM raster by applying a mean filter with a specified window size.
    Handles edge padding to avoid artifacts.
    
    :param input_path: Path to the input DEM raster file.
    :param output_path: Path to save the blurred DEM raster file.
    :param pixel_window: The size of the window (in pixels) to use for the mean filter.
    """
    
    with rasterio.open(input_path) as src:
        dem_data = src.read(1)
        pad_width = pixel_window // 2
        padded_dem_data = np.pad(dem_data, pad_width, mode='reflect')
        blurred_padded_dem = uniform_filter(padded_dem_data, size=pixel_window, mode='constant', cval=0)
        blurred_dem = blurred_padded_dem[pad_width:-pad_width, pad_width:-pad_width]
        assert blurred_dem.shape == dem_data.shape
        out_meta = src.meta.copy()

    with rasterio.open(output_path, 'w', **out_meta) as dest:
        dest.write(blurred_dem, 1)

    dest.close()


def generate_hillshade(dem_path: str, output_name: str, azimuth: float = 315.0, altitude: float = 45.0, zFactor: float = 1.0) -> np.ndarray:
    """Generate a hillshade for a specific azimuth and altitude."""
    options = gdal.DEMProcessingOptions(format='GTiff', computeEdges=True, zFactor=zFactor, azimuth=azimuth, altitude=altitude)
    hillshade_path = f'output/{output_name}_hillshade_{azimuth}_{altitude}.tif'
    gdal.DEMProcessing(hillshade_path, dem_path, 'hillshade', options=options)
    return gdal.Open(hillshade_path).ReadAsArray()


def generate_slope(dem_path: str, output_name: str, zFactor: float = 1.0) -> np.ndarray:
    """Generate a slope."""
    options = gdal.DEMProcessingOptions(format='GTiff', computeEdges=True, zFactor=zFactor)
    slope_path = f'output/{output_name}_slope.tif'
    gdal.DEMProcessing(slope_path, dem_path, 'slope', options=options)
    return gdal.Open(slope_path).ReadAsArray()

input_path = 'input/combined_clip.tif'

blur_dem_raster(input_path, 'output/blur_10.tif', 10)
blur_dem_raster(input_path, 'output/blur_20.tif', 20)
blur_dem_raster(input_path, 'output/blur_50.tif', 50)

original_hillshade = generate_hillshade(input_path, 'original')
hillshade_blur_10 = generate_hillshade('output/blur_10.tif', 'blur_10')
hillshade_blur_20 = generate_hillshade('output/blur_20.tif', 'blur_20')
hillshade_blur_50 = generate_hillshade('output/blur_50.tif', 'blur_50')

original_slope = generate_slope(input_path, 'original')
slope_blur_10 = generate_slope('output/blur_10.tif', 'blur_10')
slope_blur_20 = generate_slope('output/blur_20.tif', 'blur_20')
slope_blur_50 = generate_slope('output/blur_50.tif', 'blur_50')

hillshade_from_slope = generate_hillshade('output/original_slope.tif', 'slope')
