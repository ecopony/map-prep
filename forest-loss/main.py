import os
from mapprep import natural_earth as ne
from mapprep import hillshade as ru
import dotenv
import geopandas as gpd

dotenv.load_dotenv()

geopackage_name = 'output/forest-loss.gpkg'

ru.extract_zip_files(os.path.join(os.environ['NASA_DIR'], 'SRTM_30'))
ru.generate_hillshade_raster(os.path.join(os.environ['NASA_DIR'], 'SRTM_30/output'))
ru.combine_tif_files(os.path.join('input'), 'combined_forest_loss.tif')

ne.us_states(contiguous=True).to_file(geopackage_name, layer='us_states', driver='GPKG')
ne.countries(continent='North America').to_file(geopackage_name, layer='us_country', driver='GPKG')
ne.states_provinces(include="Oregon").to_file(geopackage_name, layer='oregon', driver='GPKG')
ne.states_provinces(exclude="Oregon").to_file(geopackage_name, layer='other_states', driver='GPKG')
populated_places = ne.us_populated_places(scale='10m', min_population=70000)
populated_places[populated_places['ADM1NAME'] == 'Oregon'].to_file(geopackage_name, layer='us_populated_places', driver='GPKG')
