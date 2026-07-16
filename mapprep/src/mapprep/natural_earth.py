import os
import geopandas as gpd
import dotenv

dotenv.load_dotenv(dotenv.find_dotenv())

NON_CONTIGUOUS = ['Alaska', 'Hawaii', 'Puerto Rico']

# Populated places columns are uppercase in the 10m dataset, lowercase in the 50m simple one.
POPULATED_PLACES = {
    '10m': ('PopulatedPlaces/ne_10m_populated_places/ne_10m_populated_places.shp', str.upper),
    '50m': ('PopulatedPlaces/ne_50m_populated_places_simple/ne_50m_populated_places_simple.shp', str.lower),
}

def ne_directory(path : str):
    return os.path.join(os.environ['NATURAL_EARTH_DIR'], path)

def _as_list(names):
    return [names] if isinstance(names, str) else names

# Countries
def read_countries(scale : str = '50m'):
    return gpd.read_file(ne_directory(f'Countries/ne_{scale}_admin_0_countries/ne_{scale}_admin_0_countries.shp'))

def countries(scale : str = '50m', continent : str = None):
    countries = read_countries(scale)
    if continent is not None:
        countries = countries[countries['CONTINENT'] == continent]
    return countries

# StatesProvinces
def read_states_provinces(scale : str = '50m'):
    return gpd.read_file(ne_directory(f'StatesProvinces/ne_{scale}_admin_1_states_provinces_lakes/ne_{scale}_admin_1_states_provinces_lakes.shp'))

def states_provinces(scale : str = '50m', include=None, exclude=None):
    states_provinces = read_states_provinces(scale)
    if include is not None:
        states_provinces = states_provinces[states_provinces['name'].isin(_as_list(include))]
    if exclude is not None:
        states_provinces = states_provinces[~states_provinces['name'].isin(_as_list(exclude))]
    return states_provinces

def us_states(scale : str = '50m', contiguous : bool = False):
    states = read_states_provinces(scale)
    states = states[states['iso_a2'] == 'US']
    if contiguous:
        states = states[~states['name'].isin(NON_CONTIGUOUS)]
    return states

# PopulatedPlaces ('50m' is the ne_50m_populated_places_simple dataset)
def read_populated_places(scale : str = '50m'):
    path, _ = POPULATED_PLACES[scale]
    return gpd.read_file(ne_directory(path))

def us_populated_places(scale : str = '50m', min_population : int = 0, contiguous : bool = False):
    _, case = POPULATED_PLACES[scale]
    places = read_populated_places(scale)
    places = places[(places[case('adm0name')] == 'United States of America') & (places[case('pop_max')] >= min_population)]
    if contiguous:
        places = places[~places[case('adm1name')].isin(NON_CONTIGUOUS)]
    return places
