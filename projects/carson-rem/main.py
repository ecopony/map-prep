from mapprep import natural_earth as ne
import dotenv
import geopandas as gpd
from riverrem.REMMaker import REMMaker

dotenv.load_dotenv(dotenv.find_dotenv())

geopackage_name = 'output/carson-rem.gpkg'

ne.us_states(contiguous=True).to_file(geopackage_name, layer='us_states', driver='GPKG')
ne.countries(continent='North America').to_file(geopackage_name, layer='us_country', driver='GPKG')

rem_maker = REMMaker(dem='input/merged-dem.tif', out_dir='output/rem-maker')
rem_maker.make_rem()
rem_maker.make_rem_viz(cmap='mako_r')
