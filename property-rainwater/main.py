import argparse
import os
import re

import dotenv
import geopandas as gpd
import requests
import whitebox
from osgeo import gdal, ogr, osr
from shapely.geometry import Point

from mapprep import hillshade

dotenv.load_dotenv(dotenv.find_dotenv())
gdal.UseExceptions()

# Reusable property-scale water-flow analysis, for planning rainwater-harvesting
# earthworks (Lancaster-style basins, berms on contour, overflow routes) on any lot.
# Layers per site: 1 m 3DEP DEM, hillshade, slope, D-inf flow accumulation, 25 cm
# contours, extracted flowpaths. Planning brief for the original use lives in
# mapmaking/projects/property-rainwater-harvest/brief.md.
#
# Site location comes from CLI flags, falling back to SITE_* in the untracked repo-root
# .env — street addresses and coordinates deliberately never appear in tracked files.
# Outputs land in output/<slug>/ so multiple properties can coexist.
parser = argparse.ArgumentParser(description='Property water-flow analysis for rainwater harvesting')
parser.add_argument('--slug', default=os.environ.get('SITE_SLUG'),
                    help='short name for this site; outputs go to output/<slug>/ (env SITE_SLUG)')
parser.add_argument('--bbox', default=os.environ.get('SITE_BBOX'),
                    help='west,south,east,north in WGS84 (env SITE_BBOX). Extend WELL uphill '
                         'of the parcel: flow accumulation is only meaningful if it sees run-on')
parser.add_argument('--lon', type=float, default=os.environ.get('SITE_LON'),
                    help='reference-point longitude, e.g. the geocoded address (env SITE_LON)')
parser.add_argument('--lat', type=float, default=os.environ.get('SITE_LAT'),
                    help='reference-point latitude (env SITE_LAT)')
parser.add_argument('--label', default=os.environ.get('SITE_ADDRESS', 'property'),
                    help='name attribute for the reference point (env SITE_ADDRESS)')
parser.add_argument('--footprints-url', default=os.environ.get('SITE_FOOTPRINTS_URL'),
                    help='ArcGIS REST layer URL for building footprints (env SITE_FOOTPRINTS_URL); '
                         'optional — skipped if unset')
parser.add_argument('--parcels-url', default=os.environ.get('SITE_PARCELS_URL'),
                    help='ArcGIS REST layer URL for parcel polygons (env SITE_PARCELS_URL); '
                         'optional — skipped if unset')
parser.add_argument('--stream-threshold', type=float, default=1000,
                    help='min upslope area in m^2 for a cell to count as a flowpath. 1000 '
                         '(0.1 ha) suits lot scale; basin-scale values would show nothing')
args = parser.parse_args()
missing = [n for n in ('slug', 'bbox', 'lon', 'lat') if getattr(args, n) is None]
if missing:
    parser.error(f"missing {missing}: pass the flags or set SITE_* in the repo-root .env")

bounds = tuple(float(c) for c in args.bbox.split(','))  # west, south, east, north
# NAD83 UTM zone for the site — the tool is US-only (TNM data), and the 3DEP tiles are
# NAD83, so staying in that datum avoids a silent transformation. Meters; NAVD88 vertical.
utm_epsg = 26900 + round((183 + (bounds[0] + bounds[2]) / 2) / 6)
utm = f'EPSG:{utm_epsg}'

gtiff = ['COMPRESS=DEFLATE', 'TILED=YES']
out_dir = f'output/{args.slug}'
geopackage_name = f'{out_dir}/site.gpkg'
os.makedirs(out_dir, exist_ok=True)
if os.path.exists(geopackage_name):
    os.remove(geopackage_name)  # script regenerates every layer; stale layers would linger

# --- Elevation surface ------------------------------------------------------
# USGS 3DEP 1 m DEM from The National Map (keyless; OpenTopography's usgsdem API 401s
# on non-academic keys). Good enough for flow planning; a finer DTM gridded from the
# source lidar point cloud (EPT on usgs-lidar-public S3) is a per-site phase 2.


def fetch_tnm_dem_1m(fetch_bounds, cache_dir='cache/tnm'):
    """Download the USGS 1m DEM tiles intersecting (west, south, east, north) WGS84.
    Returns the list of local tile paths (native CRS, typically UTM)."""
    os.makedirs(cache_dir, exist_ok=True)
    response = requests.get('https://tnmaccess.nationalmap.gov/api/v1/products', timeout=60, params={
        'datasets': 'Digital Elevation Model (DEM) 1 meter',
        'bbox': ','.join(str(c) for c in fetch_bounds),
        'outputFormat': 'JSON',
    })
    response.raise_for_status()
    items = response.json()['items']
    if not items:
        raise RuntimeError('TNM returned no 1m DEM tiles for these bounds')

    # Multiple lidar projects can overlap; keep only the project with the newest
    # acquisition year embedded in its name so the mosaic doesn't mix vintages.
    # (Publication date is a trap: older acquisitions get republished later.)
    def project(item):
        return item['downloadURL'].split('/Projects/')[1].split('/')[0]

    def acquisition_year(name):
        years = re.findall(r'\d{4}', name)
        return max(int(y) for y in years) if years else 0

    newest = max({project(item) for item in items}, key=acquisition_year)
    print(f'using TNM project {newest}')
    paths = []
    for item in items:
        if project(item) != newest:
            continue
        path = os.path.join(cache_dir, os.path.basename(item['downloadURL']))
        if not os.path.exists(path):
            print(f"downloading {item['title']}")
            tile = requests.get(item['downloadURL'], stream=True, timeout=(30, 600))
            tile.raise_for_status()
            with open(path + '.part', 'wb') as f:
                for chunk in tile.iter_content(chunk_size=1 << 20):
                    f.write(chunk)
            os.replace(path + '.part', path)
        paths.append(path)
    return paths


tiles = fetch_tnm_dem_1m(bounds)
dem_1m = f'{out_dir}/dem_1m.tif'
gdal.Warp(dem_1m, tiles, dstSRS=utm, xRes=1, yRes=1, resampleAlg='bilinear',
          outputBounds=bounds, outputBoundsSRS='EPSG:4326', creationOptions=gtiff)

hillshade.from_dem(dem_1m, f'{out_dir}/hillshade.tif', multi_directional=True)
gdal.DEMProcessing(f'{out_dir}/slope_degrees.tif', dem_1m, 'slope', creationOptions=gtiff)

# --- Hydrology (WhiteboxTools) ----------------------------------------------
# Breach (not fill) depressions: filling would erase exactly the kind of natural
# basins we want to find and enlarge; breaching only carves through digital dams.
wbt = whitebox.WhiteboxTools()
wbt.verbose = False
wbt.set_working_dir(os.path.abspath(out_dir))
wbt_cache = os.path.abspath(f'cache/wbt/{args.slug}')
os.makedirs(wbt_cache, exist_ok=True)
breached = os.path.join(wbt_cache, 'dem_breached.tif')
d8_pointer = os.path.join(wbt_cache, 'd8_pointer.tif')
d8_accum = os.path.join(wbt_cache, 'flow_accum_d8_m2.tif')
streams_raster = os.path.join(wbt_cache, 'streams.tif')
streams_shp = os.path.join(wbt_cache, 'streams.shp')

wbt.breach_depressions_least_cost(dem=os.path.abspath(dem_1m), output=breached,
                                  dist=100, fill=True)
wbt.d8_pointer(dem=breached, output=d8_pointer)
# D-infinity for display (smooth, realistic dispersion on hillslopes); log-scaled so
# symbology doesn't have to fight a range spanning 6 orders of magnitude.
wbt.d_inf_flow_accumulation(i=breached, output='flow_accum_log.tif',
                            out_type='catchment area', log=True)
# D8 (single-direction) in m^2 for extracting discrete flowpath lines.
wbt.d8_flow_accumulation(i=breached, output=d8_accum, out_type='catchment area')
wbt.extract_streams(flow_accum=d8_accum, output=streams_raster,
                    threshold=args.stream_threshold)
wbt.raster_streams_to_vector(streams=streams_raster, d8_pntr=d8_pointer,
                             output=streams_shp)

flowpaths = gpd.read_file(streams_shp).set_crs(utm)
flowpaths.to_file(geopackage_name, layer='flowpaths', driver='GPKG')

# --- Contours ----------------------------------------------------------------
# 0.25 m interval: fine enough to lay berms out on contour, coarse enough that the
# 1 m DEM isn't just drawing its own noise.
contour_ds = ogr.GetDriverByName('GPKG').Open(geopackage_name, update=1)
srs = osr.SpatialReference()
srs.ImportFromEPSG(utm_epsg)
contour_layer = contour_ds.CreateLayer('contours_25cm', srs=srs, geom_type=ogr.wkbLineString)
contour_layer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))
contour_layer.CreateField(ogr.FieldDefn('elev_m', ogr.OFTReal))
dem_ds = gdal.Open(dem_1m)
gdal.ContourGenerate(dem_ds.GetRasterBand(1), 0.25, 0, [], 0, 0, contour_layer, 0, 1)
contour_ds = None
dem_ds = None

# --- Cadastral context (optional) ---------------------------------------------
# Any ArcGIS MapServer/FeatureServer layer endpoint works (county assessor portals
# mostly are one). For Pima County both live in GISOpenData/LandRecords (buildings=3,
# parcels=12, found via the gisopendata.pima.gov Hub search API — the human-facing
# REST directory 403s scripts, the gisdata host doesn't).


def fetch_arcgis_layer(layer_url, fetch_bounds):
    """Features from an ArcGIS REST layer intersecting a WGS84 bbox, as a GeoDataFrame."""
    west, south, east, north = fetch_bounds
    response = requests.get(f'{layer_url}/query', timeout=120,
                            headers={'User-Agent': 'Mozilla/5.0'}, params={
                                'geometry': f'{west},{south},{east},{north}',
                                'geometryType': 'esriGeometryEnvelope',
                                'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
                                'outFields': '*', 'outSR': 4326, 'f': 'geojson',
                            })
    response.raise_for_status()
    collection = response.json()
    if collection.get('exceededTransferLimit') or any(
            f.get('exceededTransferLimit') for f in (collection.get('properties'),) if f):
        print(f'WARNING: {layer_url} hit the server record limit; layer is incomplete')
    return gpd.GeoDataFrame.from_features(collection.get('features', []), crs='EPSG:4326')


for layer_name, url in (('buildings', args.footprints_url), ('parcels', args.parcels_url)):
    if not url:
        continue
    features = fetch_arcgis_layer(url, bounds)
    if len(features):
        features.to_crs(utm).to_file(geopackage_name, layer=layer_name, driver='GPKG')
    print(f'{layer_name}: {len(features)} features')

# --- Reference point ----------------------------------------------------------
# Geocoded address point; replace with the assessor parcel polygon when available
# (geocoders land near the street centerline, not the lot centroid).
gpd.GeoDataFrame({'name': [args.label]},
                 geometry=[Point(args.lon, args.lat)], crs='EPSG:4326').to_crs(utm).to_file(
    geopackage_name, layer='address_point', driver='GPKG')

print(f'done -> {out_dir}/')
