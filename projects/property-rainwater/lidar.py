import argparse
import json
import os
import shutil
import subprocess

import dotenv
import geopandas as gpd
import numpy as np
import rasterio
from pyproj import Transformer
from rasterstats import zonal_stats

dotenv.load_dotenv(dotenv.find_dotenv())

# Phase 2: grid the source lidar point cloud into DTM / DSM / nDSM at 0.5 m, and stamp
# building footprints (from main.py's `buildings` layer) with their lidar heights.
# Answers "how tall is the roof / the canopy" directly — no separate product needed.
#
# Needs the PDAL CLI, which is conda-only (`conda create -n pdal -c conda-forge pdal`);
# it is NOT part of the uv env. Point PDAL_EXE at it, or let the default find it.
# Run main.py first: lidar.py reuses its site.gpkg for the buildings layer.
parser = argparse.ArgumentParser(description='Lidar DTM/DSM/nDSM + building heights')
parser.add_argument('--slug', default=os.environ.get('SITE_SLUG'))
parser.add_argument('--bbox', default=os.environ.get('SITE_BBOX'),
                    help='west,south,east,north WGS84 (env SITE_BBOX)')
parser.add_argument('--ept-url', default=os.environ.get('SITE_EPT_URL'),
                    help='EPT endpoint for the lidar collection, e.g. on the '
                         'usgs-lidar-public S3 bucket (env SITE_EPT_URL)')
parser.add_argument('--resolution', type=float, default=0.5,
                    help='output grid size in m; 0.5 suits >=8 pts/m^2 collections')
parser.add_argument('--pdal', default=os.environ.get('PDAL_EXE') or shutil.which('pdal')
                    or os.path.expanduser('~/miniconda3/envs/pdal/Library/bin/pdal.exe'))
args = parser.parse_args()
missing = [n for n in ('slug', 'bbox', 'ept_url') if getattr(args, n) is None]
if missing:
    parser.error(f"missing {missing}: pass the flags or set SITE_* in the repo-root .env")
if not args.pdal or not os.path.exists(args.pdal):
    parser.error('PDAL CLI not found — conda create -n pdal -c conda-forge pdal, '
                 'or set PDAL_EXE')

bounds = tuple(float(c) for c in args.bbox.split(','))
utm_epsg = 26900 + round((183 + (bounds[0] + bounds[2]) / 2) / 6)  # keep in sync with main.py
out_dir = f'output/{args.slug}'
cache_dir = f'cache/lidar/{args.slug}'
os.makedirs(out_dir, exist_ok=True)
os.makedirs(cache_dir, exist_ok=True)

# writers.gdal bounds pin DTM and DSM to the identical grid, so the nDSM subtraction
# needs no resampling. EPT queries want the EPT's own CRS (3857 on usgs-lidar-public).
to_3857 = Transformer.from_crs(4326, 3857, always_xy=True)
to_utm = Transformer.from_crs(4326, utm_epsg, always_xy=True)
w3857, s3857 = to_3857.transform(bounds[0], bounds[1])
e3857, n3857 = to_3857.transform(bounds[2], bounds[3])
corners = [to_utm.transform(x, y) for x, y in
           [(bounds[0], bounds[1]), (bounds[2], bounds[1]),
            (bounds[0], bounds[3]), (bounds[2], bounds[3])]]
minx = min(c[0] for c in corners); maxx = max(c[0] for c in corners)
miny = min(c[1] for c in corners); maxy = max(c[1] for c in corners)
grid_bounds = f'([{minx},{maxx}],[{miny},{maxy}])'


def run_pipeline(name, stages):
    path = os.path.join(cache_dir, f'{name}.pipeline.json')
    with open(path, 'w') as f:
        json.dump({'pipeline': stages}, f, indent=2)
    print(f'pdal: {name}')
    subprocess.run([args.pdal, 'pipeline', path], check=True)


# One EPT download, reprojected to UTM, cached as LAZ; both grids read it locally.
local_laz = os.path.join(cache_dir, 'points_utm.laz')
if not os.path.exists(local_laz):
    run_pipeline('fetch', [
        {'type': 'readers.ept', 'filename': args.ept_url,
         'bounds': f'([{w3857},{e3857}],[{s3857},{n3857}])'},
        {'type': 'filters.reprojection', 'out_srs': f'EPSG:{utm_epsg}'},
        {'type': 'writers.las', 'filename': local_laz, 'compression': True,
         'a_srs': f'EPSG:{utm_epsg}'},
    ])

dtm_path = f'{out_dir}/dtm_50cm.tif'
dsm_path = f'{out_dir}/dsm_50cm.tif'
gdal_common = {'type': 'writers.gdal', 'resolution': args.resolution,
               'bounds': grid_bounds, 'data_type': 'float32', 'nodata': -9999,
               'gdaldriver': 'GTiff', 'gdalopts': 'COMPRESS=DEFLATE,TILED=YES',
               'window_size': 6}  # window_size interpolates small gaps (under canopy etc.)
run_pipeline('dtm', [
    local_laz,
    # Class 2 = ground per ASPRS; IDW of ground returns is the standard bare-earth grid
    {'type': 'filters.range', 'limits': 'Classification[2:2]'},
    dict(gdal_common, filename=dtm_path, output_type='idw'),
])
run_pipeline('dsm', [
    local_laz,
    # First returns hit the highest surface (roof, canopy); drop noise classes 7/18
    {'type': 'filters.range', 'limits': 'ReturnNumber[1:1]'},
    {'type': 'filters.range', 'limits': 'Classification![7:7]'},
    {'type': 'filters.range', 'limits': 'Classification![18:18]'},
    dict(gdal_common, filename=dsm_path, output_type='max'),
])

# nDSM = DSM - DTM: height of everything above bare earth (roofs, trees). Negatives
# (returns under the interpolated ground, edge artifacts) clamp to 0.
with rasterio.open(dsm_path) as dsm_src, rasterio.open(dtm_path) as dtm_src:
    dsm = dsm_src.read(1, masked=True)
    dtm = dtm_src.read(1, masked=True)
    ndsm = np.ma.filled(np.ma.clip(dsm - dtm, 0, None), -9999)
    profile = dsm_src.profile
ndsm_path = f'{out_dir}/ndsm_50cm.tif'
with rasterio.open(ndsm_path, 'w', **profile) as dst:
    dst.write(ndsm.astype('float32'), 1)

# Building heights: zonal stats of the nDSM per footprint. Median resists edge pixels
# bleeding ground into the footprint; max catches the ridge line.
geopackage_name = f'{out_dir}/site.gpkg'
layers = gpd.list_layers(geopackage_name)['name'].tolist() if os.path.exists(geopackage_name) else []
if 'buildings' in layers:
    buildings = gpd.read_file(geopackage_name, layer='buildings')
    stats = zonal_stats(buildings.to_crs(profile['crs']), ndsm_path,
                        stats=['median', 'max'], nodata=-9999)
    buildings['height_med_m'] = [s['median'] for s in stats]
    buildings['height_max_m'] = [s['max'] for s in stats]
    buildings.to_file(geopackage_name, layer='buildings', driver='GPKG')
    with_height = buildings['height_med_m'].notna().sum()
    print(f'buildings: {with_height}/{len(buildings)} stamped with lidar heights')
else:
    print('no buildings layer in site.gpkg (run main.py with --footprints-url) — '
          'skipping height stamping')

print(f'done -> {dtm_path}, {dsm_path}, {ndsm_path}')
