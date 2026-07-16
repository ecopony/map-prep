from mapprep import natural_earth as ne
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
