from typing import List, Optional
from osgeo import gdal
from PIL import Image, ImageChops, ImageEnhance
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


def extract_colors_from_image(image_path: str) -> np.ndarray:
    """Extract colors from the center line of an image."""
    image = Image.open(image_path)
    image = image.convert('RGB')
    width, height = image.size
    colors = [image.getpixel((x, int(height / 2))) for x in range(width)]
    return np.array(colors) / 255.0


def create_custom_colormap(colors: np.ndarray) -> LinearSegmentedColormap:
    """Create a custom colormap from a list of colors."""
    return LinearSegmentedColormap.from_list("custom_ramp", colors)


def apply_colormap(array: np.ndarray, cmap: LinearSegmentedColormap) -> np.ndarray:
    """Apply a matplotlib colormap to an array."""
    colormap = plt.get_cmap(cmap)
    normed_data = (array - array.min()) / (array.max() - array.min())
    colored = colormap(normed_data)
    return (colored[:, :, :3] * 255).astype('uint8')


def generate_hillshade(dem_path: str, azimuth: float, altitude: float, zFactor: float = 1.0) -> np.ndarray:
    """Generate a hillshade for a specific azimuth and altitude."""
    options = gdal.DEMProcessingOptions(format='GTiff', computeEdges=True, zFactor=zFactor, azimuth=azimuth, altitude=altitude)
    hillshade_path = f'output/temp_hillshade_{azimuth}_{altitude}.tif'
    gdal.DEMProcessing(hillshade_path, dem_path, 'hillshade', options=options)
    return gdal.Open(hillshade_path).ReadAsArray()


def combine_hillshades(dem_path: str, azimuths: List[float], altitudes: List[float], weights: Optional[List[float]] = None) -> np.ndarray:
    """Combine hillshades from multiple directions."""
    hillshades = [generate_hillshade(dem_path, az, alt) for az, alt in zip(azimuths, altitudes)]

    if weights is None:
        weights = np.ones(len(azimuths))

    weights = np.array(weights) / np.sum(weights)
    combined_hillshade = np.average(hillshades, axis=0, weights=weights)
    combined_hillshade = np.clip(combined_hillshade, 0, 255)
    return combined_hillshade

def generate_slope_array(dem_path: str) -> np.ndarray:
    """
    Generate a slope array from a DEM.

    Parameters:
    dem_path (str): The file path to the DEM raster.

    Returns:
    np.ndarray: Array representing the slope raster.
    """
    dem_ds = gdal.Open(dem_path, gdal.GA_ReadOnly)
    if dem_ds is None:
        raise FileNotFoundError("Failed to open DEM file: " + dem_path)

    slope_ds = gdal.DEMProcessing('output/stuff.tiff', dem_ds, 'slope', slope_format='MEM', scale=1)
        
    if slope_ds is None:
        raise Exception("Slope computation failed.")

    slope_band = slope_ds.GetRasterBand(1)
    slope_array = slope_band.ReadAsArray()
    return slope_array


def generate_slope_array(dem_path):
    """
    Generate a slope array from a DEM.

    Parameters:
    dem_path (str): The file path to the DEM raster.

    Returns:
    numpy.ndarray: Array representing the slope raster.
    """
    dem_ds = gdal.Open(dem_path, gdal.GA_ReadOnly)
    if dem_ds is None:
        raise FileNotFoundError("Failed to open DEM file: " + dem_path)

    slope_ds = gdal.DEMProcessing('output/stuff.tiff', dem_ds, 'slope', slope_format='MEM', scale=1)
    
    if slope_ds is None:
        raise Exception("Slope computation failed.")

    slope_band = slope_ds.GetRasterBand(1)
    slope_array = slope_band.ReadAsArray()
    return slope_array


def adjust_brightness(img, brightness_factor):
    """Adjust the brightness of an image."""
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(brightness_factor)  # Increase the brightness factor > 1 to lighten the image


def generate_slope_array(dem_path):
    dem_ds = gdal.Open(dem_path, gdal.GA_ReadOnly)
    if dem_ds is None:
        raise FileNotFoundError("Failed to open DEM file.")
    
    slope_ds = gdal.DEMProcessing('', dem_ds, 'slope', format='MEM', scale=1)
    slope_band = slope_ds.GetRasterBand(1)
    slope_array = slope_band.ReadAsArray()
    no_data_value = slope_band.GetNoDataValue()
    return slope_array, no_data_value


dem_path = 'input/oblique-clip.tif'
dem_data = gdal.Open(dem_path).ReadAsArray()

# lower_percentile = np.percentile(dem_data, 0.5)
# upper_percentile = np.percentile(dem_data, 99.5)
lower_percentile = np.percentile(dem_data, 0.0)
upper_percentile = np.percentile(dem_data, 100.0)
normalized_dem = np.clip(dem_data, lower_percentile, upper_percentile)

colors = extract_colors_from_image('input/ramp.png')
color_ramp = create_custom_colormap(colors)

plt.imshow([colors], aspect='auto')
plt.title('Custom Color Ramp')
plt.axis('off')
plt.show()

plt.imshow(normalized_dem, cmap=color_ramp)
plt.colorbar()
plt.title('DEM with Custom Color Ramp')
plt.show()


terrain_dem = apply_colormap(normalized_dem, color_ramp)
terrain_image = Image.fromarray(terrain_dem)
terrain_image.save('output/1-terrain.png')

warm_dem = apply_colormap(normalized_dem, 'plasma')
warm_image = Image.fromarray(warm_dem)
warm_image.save('output/warm.png')
warming_blended = ImageChops.soft_light(terrain_image, warm_image)
warming_blended.save('output/2-warming_blended.png')

traditional_hillshade = combine_hillshades(dem_path, [315], [47])
traditional_hillshade_image = Image.fromarray((traditional_hillshade * 255 / traditional_hillshade.max()).astype('uint8'))
traditional_hillshade_rgb = traditional_hillshade_image.convert("RGB")
traditional_hillshade_rgb.save('output/traditional_hillshade.png')
traditional_hillshade_blended = ImageChops.overlay(warming_blended, traditional_hillshade_rgb)
traditional_hillshade_blended.save('output/3-hillshade_blended.png')

azimuths = [45, 135, 225, 315]
altitudes = [45, 45, 45, 45]
weights = [1, 1, 1, 1]
multidirectional_hillshade = combine_hillshades(dem_path, azimuths, altitudes, weights)
multidirectional_hillshade_image = Image.fromarray((multidirectional_hillshade * 255 / multidirectional_hillshade.max()).astype('uint8'))
multidirectional_hillshade_rgb = multidirectional_hillshade_image.convert("RGB")
multidirectional_hillshade_rgb.save('output/multidirectional_hillshade.png')
multidirectional_hillshade_blended = ImageChops.multiply(traditional_hillshade_blended, multidirectional_hillshade_rgb)
multidirectional_hillshade_blended.save('output/5-blended-multidirectional_hillshade.png')

colors = [
    (1.0, 1.0, 1.0, 0.85),
    (1.0, 1.0, 1.0, 0.45),
    (1.0, 1.0, 1.0, 0.15),
    (1.0, 1.0, 1.0, 0.0),
    (1.0, 1.0, 1.0, 0.0)
]
positions = [0.0, 0.15, 0.25, .35, 1.0]

mist_custom_cmap = LinearSegmentedColormap.from_list("custom_cmap", list(zip(positions, colors)))
dem_data_normalized = (dem_data - dem_data.min()) / (dem_data.max() - dem_data.min())
norm = plt.Normalize(vmin=0, vmax=1)
mist_image_rgba = mist_custom_cmap(norm(dem_data_normalized))
mist_image_pil = Image.fromarray((mist_image_rgba * 255).astype(np.uint8), 'RGBA')
mist_image_pil.save("output/dem_with_transparent_mist.png")

terrain_image = Image.open('output/5-blended-multidirectional_hillshade.png').convert('RGBA')
mist_image = Image.open('output/dem_with_transparent_mist.png').convert('RGBA')

if terrain_image.size != mist_image.size:
    mist_image = mist_image.resize(terrain_image.size, Image.ANTIALIAS)

combined_image = Image.alpha_composite(terrain_image, mist_image)
combined_image.save('output/6-combined_terrain_and_mist.png')

slope_array, no_data_value = generate_slope_array(dem_path)

if no_data_value is not None:
    mask = slope_array == no_data_value
    slope_array = np.ma.masked_where(mask, slope_array)
    
min_val = np.min(slope_array)
max_val = np.max(slope_array)
norm_slope_array = (slope_array - min_val) / (max_val - min_val)
norm_slope_array = np.ma.filled(norm_slope_array, 0)

cmap = plt.get_cmap('cividis')
colored_slope = cmap(norm_slope_array)

colored_image = (colored_slope[:, :, :3] * 255).astype(np.uint8)
slope_image = Image.fromarray(colored_image)

slope_image.save('output/7-slope.png', 'png')

combined_image = combined_image.convert('RGBA')
slope_image = slope_image.convert('RGBA')

if combined_image.size != slope_image.size:
    slope_image = slope_image.resize(combined_image.size, Image.ANTIALIAS)

slope_blended = ImageChops.soft_light(combined_image, slope_image)
slope_blended.save('output/8-slope_blended.png')
slope_blended.show()
