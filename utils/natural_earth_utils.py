import os
import geopandas as gpd
import dotenv

dotenv.load_dotenv(dotenv.find_dotenv())

def ne_directory(path : str):
    return os.path.join(os.environ['NATURAL_EARTH_DIR'], path)

# Countries 50m
def read_countries_50m():
    return gpd.read_file(ne_directory('Countries/ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp'))

def na_countries_50m():
    countries_50m = read_countries_50m()
    return countries_50m[countries_50m['CONTINENT'] == 'North America']

# StatesProvinces 50m
def read_states_provinces_50m():
    return gpd.read_file(ne_directory('StatesProvinces/ne_50m_admin_1_states_provinces_lakes/ne_50m_admin_1_states_provinces_lakes.shp'))

def us_states_50m():
    states_provinces_50m = read_states_provinces_50m()
    return states_provinces_50m[states_provinces_50m['iso_a2'] == 'US']

def us_states_50m_contiguous():
    states_provinces_50m = read_states_provinces_50m()
    return states_provinces_50m[states_provinces_50m['iso_a2'] == 'US'].loc[~states_provinces_50m['name'].isin(['Alaska', 'Hawaii', 'Puerto Rico'])]

def us_state_50m(name : str):
    states_provinces_50m = read_states_provinces_50m()
    return states_provinces_50m[states_provinces_50m['name'] == name]

def all_the_other_states_50m(name : str):
    states_provinces_50m = read_states_provinces_50m()
    return states_provinces_50m[states_provinces_50m['name'] != name]

# PopulatedPlaces 10m
def read_populated_places_10m():
    return gpd.read_file(ne_directory('PopulatedPlaces/ne_10m_populated_places/ne_10m_populated_places.shp'))

def us_populated_places_10m(min_population : int = 0):
    populated_places_10m = read_populated_places_10m()
    return populated_places_10m[(populated_places_10m['ADM0NAME'] == 'United States of America') & (populated_places_10m['POP_MAX'] >= min_population)]

# PopulatedPlaces 50m
def read_populated_places_simple_50m():
    return gpd.read_file(ne_directory('PopulatedPlaces/ne_50m_populated_places_simple/ne_50m_populated_places_simple.shp'))

def us_populated_places_simple_50m(min_population : int = 0):
    populated_places_simple_50m = read_populated_places_simple_50m()
    return populated_places_simple_50m[(populated_places_simple_50m['adm0name'] == 'United States of America') & (populated_places_simple_50m['pop_max'] >= min_population)]
