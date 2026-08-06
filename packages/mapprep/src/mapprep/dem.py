import math
import os

import dotenv
import numpy as np
import requests
from osgeo import gdal

dotenv.load_dotenv(dotenv.find_dotenv())
gdal.UseExceptions()

API_URL = 'https://portal.opentopography.org/API/globaldem'
USGS_API_URL = 'https://portal.opentopography.org/API/usgsdem'

# Per-request area limits (km^2) from https://opentopography.org/blog/introducing-api-keys-access-opentopography-global-datasets
MAX_AREA_KM2 = {
    'COP90': 4_050_000,
    'SRTMGL3': 4_050_000,
    'SRTM15Plus': 125_000_000,
}
DEFAULT_MAX_AREA_KM2 = 450_000

KM_PER_DEG_LAT = 111.19
KM_PER_DEG_LON_EQUATOR = 111.32

GTIFF_OPTIONS = ['COMPRESS=DEFLATE', 'TILED=YES', 'BIGTIFF=IF_SAFER']


def _bbox_area_km2(west, south, east, north):
    mid_lat = math.radians((south + north) / 2)
    return (east - west) * KM_PER_DEG_LON_EQUATOR * math.cos(mid_lat) * (north - south) * KM_PER_DEG_LAT


def _slabs(west, south, east, north, demtype):
    """Split a bbox into longitudinal slabs that fit under the API's per-request area limit."""
    limit = 0.9 * MAX_AREA_KM2.get(demtype, DEFAULT_MAX_AREA_KM2)
    count = max(1, math.ceil(_bbox_area_km2(west, south, east, north) / limit))
    step = (east - west) / count
    overlap = 0.02  # small overlap so the mosaic has no seams at slab edges
    return [(max(west, west + i * step - overlap), south,
             min(east, west + (i + 1) * step + overlap), north)
            for i in range(count)]


def _fetch_slab(bounds, demtype, api_key, cache_dir):
    west, south, east, north = bounds
    path = os.path.join(cache_dir, f'{demtype}_w{west:.2f}_s{south:.2f}_e{east:.2f}_n{north:.2f}.tif')
    if os.path.exists(path):
        return path

    response = requests.get(API_URL, stream=True, timeout=(30, 300), params={
        'demtype': demtype,
        'west': west, 'south': south, 'east': east, 'north': north,
        'outputFormat': 'GTiff',
        'API_Key': api_key,
    })
    response.raise_for_status()

    partial = path + '.part'
    with open(partial, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1 << 20):
            f.write(chunk)
    os.replace(partial, path)
    return path


def fetch(bounds, dst_path, demtype='COP90', resolution_arcsec=None, cache_dir='cache/opentopography'):
    """Download a global DEM covering (west, south, east, north) degrees to a GeoTIFF.

    Requires OPEN_TOPOGRAPHY_API_KEY in the environment (free key from opentopography.org).
    Areas over the API's per-request limit are fetched as cached longitudinal slabs and
    mosaicked. resolution_arcsec resamples (average) below the dataset's native resolution.
    """
    api_key = os.environ['OPEN_TOPOGRAPHY_API_KEY']
    os.makedirs(cache_dir, exist_ok=True)

    slab_paths = [_fetch_slab(slab, demtype, api_key, cache_dir)
                  for slab in _slabs(*bounds, demtype)]

    warp_kwargs = {}
    if resolution_arcsec is not None:
        degrees = resolution_arcsec / 3600
        warp_kwargs = {'xRes': degrees, 'yRes': degrees, 'resampleAlg': 'average'}
    gdal.Warp(dst_path, slab_paths, creationOptions=GTIFF_OPTIONS, **warp_kwargs)
    return dst_path


def slope(dem_path, dst_path, z_factor=1.0):
    """Slope in degrees to a GeoTIFF."""
    gdal.DEMProcessing(dst_path, dem_path, 'slope', computeEdges=True, zFactor=z_factor,
                       creationOptions=GTIFF_OPTIONS)
    return dst_path


def slope_array(dem_path):
    """Slope in degrees as an in-memory array, with nodata masked."""
    band = gdal.DEMProcessing('', dem_path, 'slope', format='MEM').GetRasterBand(1)
    data = band.ReadAsArray()
    nodata = band.GetNoDataValue()
    return np.ma.masked_equal(data, nodata) if nodata is not None else data


def fetch_usgs(bounds, dst_path, dataset='USGS1m', cache_dir='cache/opentopography'):
    """Download a USGS 3DEP DEM subset (USGS1m | USGS10m | USGS30m) covering
    (west, south, east, north) degrees to a GeoTIFF.

    Same key and caching pattern as fetch(), but against the /API/usgsdem endpoint.
    CAUTION: unlike globaldem, usgsdem rejects ordinary free API keys (401) — it is
    limited to academic-account keys. For keyless access to the same 1m tiles use
    The National Map API instead (see property-rainwater/main.py fetch_tnm_dem_1m).
    No slabbing: the USGS1m per-request limit (250 km^2) is far above the site scales
    this is for. The grid comes back in the source's native CRS (UTM for USGS1m), not
    geographic — warp it yourself if you need a specific CRS/resolution.
    """
    api_key = os.environ['OPEN_TOPOGRAPHY_API_KEY']
    os.makedirs(cache_dir, exist_ok=True)
    west, south, east, north = bounds
    path = os.path.join(cache_dir, f'{dataset}_w{west:.4f}_s{south:.4f}_e{east:.4f}_n{north:.4f}.tif')
    if not os.path.exists(path):
        response = requests.get(USGS_API_URL, stream=True, timeout=(30, 300), params={
            'datasetName': dataset,
            'west': west, 'south': south, 'east': east, 'north': north,
            'outputFormat': 'GTiff',
            'API_Key': api_key,
        })
        response.raise_for_status()
        partial = path + '.part'
        with open(partial, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1 << 20):
                f.write(chunk)
        os.replace(partial, path)
    gdal.Translate(dst_path, path, creationOptions=GTIFF_OPTIONS)
    return dst_path
