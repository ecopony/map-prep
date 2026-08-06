from mapprep import dem
from mapprep import hillshade
from mapprep import raster

input_path = 'input/combined_clip.tif'
area_name = 'carson'
output_directory = f'output/{area_name}'

raster.blur(input_path, f'{output_directory}/blur_10.tif', 10)
raster.blur(input_path, f'{output_directory}/blur_20.tif', 20)
raster.blur(input_path, f'{output_directory}/blur_50.tif', 50)

hillshade.from_dem(input_path, f'{output_directory}/original_hillshade.tif')
hillshade.from_dem(f'{output_directory}/blur_10.tif', f'{output_directory}/blur_10_hillshade.tif')
hillshade.from_dem(f'{output_directory}/blur_20.tif', f'{output_directory}/blur_20_hillshade.tif')
hillshade.from_dem(f'{output_directory}/blur_50.tif', f'{output_directory}/blur_50_hillshade.tif')

dem.slope(input_path, f'{output_directory}/original_slope.tif')
dem.slope(f'{output_directory}/blur_10.tif', f'{output_directory}/blur_10_slope.tif')
dem.slope(f'{output_directory}/blur_20.tif', f'{output_directory}/blur_20_slope.tif')
dem.slope(f'{output_directory}/blur_50.tif', f'{output_directory}/blur_50_slope.tif')

# Hillshade of the slope surface (slope values treated as elevation) — accentuates
# breaks in slope as another occlusion-style component
hillshade.from_dem(f'{output_directory}/original_slope.tif', f'{output_directory}/slope_hillshade.tif')
