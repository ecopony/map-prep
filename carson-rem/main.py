# %pip install geopandas python-dotenv rasterio osgeo

import os
import sys
sys.path.append('../utils/')
import natural_earth_utils as ne
import hillshade_utils as ru
import dotenv
import geopandas as gpd
from riverrem.REMMaker import REMMaker

dotenv.load_dotenv("../.env")

geopackage_name = 'output/carson-rem.gpkg'

ne.us_states_50m_contiguous().to_file(geopackage_name, layer='us_states', driver='GPKG')
ne.na_countries_50m().to_file(geopackage_name, layer='us_country', driver='GPKG')

rem_maker = REMMaker(dem='input/merged-dem.tif', out_dir='output/rem-maker')
rem_maker.make_rem()
rem_maker.make_rem_viz(cmap='mako_r')
