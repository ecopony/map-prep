from osgeo import gdal
from PIL import Image, ImageChops, ImageEnhance
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mapprep import dem
from mapprep import hillshade


def extract_colors_from_image(image_path: str) -> np.ndarray:
    """Extract colors from the center line of an image."""
    image = Image.open(image_path).convert('RGB')
    width, height = image.size
    colors = [image.getpixel((x, int(height / 2))) for x in range(width)]
    return np.array(colors) / 255.0


def apply_colormap(array: np.ndarray, cmap: LinearSegmentedColormap) -> np.ndarray:
    """Apply a matplotlib colormap to an array."""
    colormap = plt.get_cmap(cmap) if isinstance(cmap, str) else cmap
    normed_data = (array - array.min()) / (array.max() - array.min())
    colored = colormap(normed_data)
    return (colored[:, :, :3] * 255).astype('uint8')


def adjust_brightness(img: Image.Image, brightness_factor: float) -> Image.Image:
    """Adjust the brightness of an image."""
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(brightness_factor)


def rgb_image_from_array(array: np.ndarray) -> Image.Image:
    """Create an RGB image from an array."""
    return Image.fromarray((array * 255 / array.max()).astype('uint8')).convert("RGB")


def normalize_array(array: np.ndarray, lower_percentile: float = 0.0, upper_percentile: float = 100.0) -> np.ndarray:
    """Normalize array values to a specified percentile range."""
    lower_val = np.percentile(array, lower_percentile)
    upper_val = np.percentile(array, upper_percentile)
    clipped = np.clip(array, lower_val, upper_val)
    return (clipped - lower_val) / (upper_val - lower_val)


dem_path = 'input/oblique-clip.tif'
dem_data = gdal.Open(dem_path).ReadAsArray()
normalized_dem = normalize_array(dem_data)

colors = extract_colors_from_image('input/ramp.png')
color_ramp = LinearSegmentedColormap.from_list("custom_ramp", colors)

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
warm_image.save('output/2-warming.png')
warming_blended = ImageChops.soft_light(terrain_image, warm_image)
warming_blended.save('output/3-warming_blended.png')

traditional_hillshade = hillshade.combine(dem_path, [315], [45])
traditional_hillshade_image = rgb_image_from_array(traditional_hillshade)
traditional_hillshade_image.save('output/4-traditional_hillshade.png')
traditional_hillshade_blended = ImageChops.overlay(warming_blended, traditional_hillshade_image)
traditional_hillshade_blended.save('output/5-hillshade_blended.png')

azimuths = [45, 135, 225, 315]
altitudes = [45, 45, 45, 45]
multidirectional_hillshade = hillshade.combine(dem_path, azimuths, altitudes)
multidirectional_hillshade_image = rgb_image_from_array(multidirectional_hillshade)
multidirectional_hillshade_image.save('output/6-multidirectional_hillshade.png')
multidirectional_hillshade_blended = ImageChops.multiply(traditional_hillshade_blended, multidirectional_hillshade_image)
multidirectional_hillshade_blended.save('output/7-blended-multidirectional_hillshade.png')

low_light_hillshade = hillshade.combine(dem_path, [315], [25])
low_light_hillshade_image = rgb_image_from_array(low_light_hillshade)
low_light_hillshade_image.save('output/8-low_light_hillshade.png')
low_light_hillshade_blended = ImageChops.soft_light(multidirectional_hillshade_blended, low_light_hillshade_image)
low_light_hillshade_blended.save('output/9-low_light_hillshade_blended.png')

lighting_dem = apply_colormap(normalized_dem, 'binary_r')
lighting_image = Image.fromarray(lighting_dem)
lighting_image.save('output/10-lighting.png')
lighting_blended = ImageChops.soft_light(low_light_hillshade_blended, lighting_image)
lighting_blended.save('output/11-lighting_blended.png')

colors = [
    (1.0, 1.0, 1.0, 0.85),
    (1.0, 1.0, 1.0, 0.45),
    (1.0, 1.0, 1.0, 0.15),
    (1.0, 1.0, 1.0, 0.0),
    (1.0, 1.0, 1.0, 0.0)
]
positions = [0.0, 0.15, 0.25, .35, 1.0]
mist_custom_cmap = LinearSegmentedColormap.from_list("custom_cmap", list(zip(positions, colors)))
mist_dem = mist_custom_cmap(normalized_dem)
mist_image = Image.fromarray((mist_dem * 255).astype(np.uint8), 'RGBA')
mist_image.save("output/12-dem_with_transparent_mist.png")

# terrain_image = Image.open('output/7-blended-multidirectional_hillshade.png').convert('RGBA')
# terrain_image = Image.open('output/9-low_light_hillshade_blended.png').convert('RGBA')
terrain_image = Image.open('output/11-lighting_blended.png').convert('RGBA')

combined_terrain_and_mist = Image.alpha_composite(terrain_image, mist_image).convert('RGB')
combined_terrain_and_mist.save('output/13-combined_terrain_and_mist.png')

cividis_cmap = plt.get_cmap('cividis')
slope_array = dem.slope_array(dem_path)
normalized_slope = np.ma.filled((slope_array - slope_array.min()) / (slope_array.max() - slope_array.min()), 0)
slope_dem = cividis_cmap(normalized_slope)
slope_image = rgb_image_from_array(slope_dem)
slope_image.save('output/14-slope.png', 'png')

slope_blended = ImageChops.soft_light(combined_terrain_and_mist, slope_image)
slope_blended.save('output/15-slope_blended.png')
slope_blended.show()
