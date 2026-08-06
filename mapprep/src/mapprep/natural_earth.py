import glob
import os
import geopandas as gpd
import pandas as pd
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

def countries(scale : str = '50m', continent : str = None, include=None, exclude=None):
    countries = read_countries(scale)
    if continent is not None:
        countries = countries[countries['CONTINENT'] == continent]
    if include is not None:
        countries = countries[countries['NAME'].isin(_as_list(include))]
    if exclude is not None:
        countries = countries[~countries['NAME'].isin(_as_list(exclude))]
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

# Lakes
def read_lakes(scale : str = '50m'):
    return gpd.read_file(ne_directory(f'Lakes/ne_{scale}_lakes/ne_{scale}_lakes.shp'))

def lakes(scale : str = '50m', min_area_km2 : float = 0):
    """min_area_km2 filters by polygon area (equal-area EPSG:6933) — NE scalerank is not a
    reliable size proxy (rank 0 spans Lake Superior down to the Finger Lakes)."""
    lakes = read_lakes(scale)
    if min_area_km2:
        area_km2 = lakes.geometry.to_crs('EPSG:6933').area / 1e6
        lakes = lakes[area_km2 >= min_area_km2]
    return lakes

# Ocean
def ocean(scale : str = '50m'):
    return gpd.read_file(ne_directory(f'Ocean/ne_{scale}_ocean/ne_{scale}_ocean.shp'))

def bathymetry(scale : str = '10m'):
    """Nested depth-band polygons (one source shapefile per depth: 0, 200, 1000, ... 10000 m).
    Returned sorted shallow-to-deep so deeper bands draw on top of shallower ones."""
    paths = sorted(glob.glob(ne_directory(f'Ocean/ne_{scale}_bathymetry_all/*.shp')))
    bands = pd.concat([gpd.read_file(p) for p in paths], ignore_index=True)
    return bands.sort_values('depth').reset_index(drop=True)

# Rasters (pre-rendered shaded relief images, not elevation data)
def us_manual_shaded_relief_path():
    """Tom Patterson's manual shaded relief of the contiguous US (uint8, EPSG:3857)."""
    return ne_directory('Raster/US_MSR_10M/US_MSR_10M/US_MSR.tif')

def shaded_relief_path(scale : str = '50m'):
    return ne_directory(f'Raster/SR_{scale.upper()}/SR_{scale.upper()}.tif')

# PopulatedPlaces ('50m' is the ne_50m_populated_places_simple dataset)
def read_populated_places(scale : str = '50m'):
    path, _ = POPULATED_PLACES[scale]
    return gpd.read_file(ne_directory(path))

def us_populated_places(scale : str = '50m', min_population : int = 0, contiguous : bool = False, exclude=None):
    _, case = POPULATED_PLACES[scale]
    places = read_populated_places(scale)
    places = places[(places[case('adm0name')] == 'United States of America') & (places[case('pop_max')] >= min_population)]
    if contiguous:
        places = places[~places[case('adm1name')].isin(NON_CONTIGUOUS)]
    if exclude is not None:
        places = places[~places[case('name')].isin(_as_list(exclude))]
    return places
