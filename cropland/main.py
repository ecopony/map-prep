import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../utils')))
import natural_earth_utils as ne
import rasterio
import numpy as np
from rasterio.mask import mask
import pandas as pd

states = ne.us_states_50m_contiguous()
fruit_values = [212, 213, 68, 66, 221]

raster_path = '2023_30m_cdls.tif'

with rasterio.open(raster_path) as src:
    raster_crs = src.crs

vector_crs = states.crs

if vector_crs != raster_crs:
    states = states.to_crs(raster_crs)

def calculate_fruit_areas(raster_path, states_gdf, fruit_values):
    results = []
    
    with rasterio.open(raster_path) as src:
        for _, state in states_gdf.iterrows():
            state_name = state['name']
            geometry = [state['geometry']]
            
            out_image, out_transform = mask(src, geometry, crop=True)
            out_image = out_image[0]
            
            fruit_areas = {}
            for value in fruit_values:
                count = np.sum(out_image == value)
                area_hectares = count * 900 / 10_000
                fruit_areas[value] = area_hectares
            
            results.append({
                'state': state_name,
                **fruit_areas
            })
    
    return results

fruit_areas_by_state = calculate_fruit_areas(raster_path, states, fruit_values)

df = pd.DataFrame(fruit_areas_by_state)

fruit_name_map = {68: 'Apples', 66: 'Cherries', 213: 'Melons', 212: 'Oranges', 221: 'Strawberries'}
df.rename(columns=fruit_name_map, inplace=True)

output_csv = 'fruit_areas_by_state.csv'
df.to_csv(output_csv, index=False)