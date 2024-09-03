# %pip install geopandas python-dotenv rasterio osgeo

import os
import sys
sys.path.append('../utils/')
import natural_earth_utils as ne
import hillshade_utils as ru
import dotenv
import geopandas as gpd

dotenv.load_dotenv()

geopackage_name = 'output/forest-loss.gpkg'

ru.extract_zip_files(os.path.join(os.environ['NASA_DIR'], 'SRTM_30'))
ru.generate_hillshade_raster(os.path.join(os.environ['NASA_DIR'], 'SRTM_30/output'))
ru.combine_tif_files(os.path.join('input'), 'combined_forest_loss.tif')

ne.us_states_50m_contiguous().to_file(geopackage_name, layer='us_states', driver='GPKG')
ne.na_countries_50m().to_file(geopackage_name, layer='us_country', driver='GPKG')
ne.us_state_50m("Oregon").to_file(geopackage_name, layer='oregon', driver='GPKG')
ne.all_the_other_states_50m("Oregon").to_file(geopackage_name, layer='other_states', driver='GPKG')
populated_places = ne.us_populated_places_10m(min_population=70000)
populated_places[populated_places['ADM1NAME'] == 'Oregon'].to_file(geopackage_name, layer='us_populated_places', driver='GPKG')
