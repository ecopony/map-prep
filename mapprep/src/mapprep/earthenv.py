import os

import dotenv
import numpy as np
import rasterio
import requests
from rasterio.windows import from_bounds

dotenv.load_dotenv(dotenv.find_dotenv())

BASE_URL = 'https://data.earthenv.org/consensus_landcover/with_DISCover'

# EarthEnv 1-km consensus land cover (Tuanmu & Jetz 2014): 12 classes as 0-100 prevalence
# rasters that sum to 100; classes 1-4 are the tree classes.
TREE_CLASSES = (1, 2, 3, 4)


def earthenv_directory(path : str):
    return os.path.join(os.environ['EARTHENV_DIR'], path)


def _fetch_class(landcover_class : int):
    path = earthenv_directory(f'consensus_landcover/consensus_full_class_{landcover_class}.tif')
    if os.path.exists(path):
        return path

    os.makedirs(os.path.dirname(path), exist_ok=True)
    response = requests.get(f'{BASE_URL}/consensus_full_class_{landcover_class}.tif', stream=True, timeout=(30, 600))
    response.raise_for_status()
    partial = path + '.part'
    with open(partial, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1 << 20):
            f.write(chunk)
    os.replace(partial, path)
    return path


def treecover(dst_path, bounds):
    """Percent tree cover 0-100 for (west, south, east, north): the summed prevalence of the
    four EarthEnv tree classes, downloading the global class rasters on first use."""
    total = None
    for landcover_class in TREE_CLASSES:
        with rasterio.open(_fetch_class(landcover_class)) as src:
            window = from_bounds(*bounds, transform=src.transform)
            data = src.read(1, window=window, masked=True)
            if total is None:
                total = data.astype(np.int16)
                profile = src.profile | {
                    'height': data.shape[0], 'width': data.shape[1],
                    'transform': src.window_transform(window),
                    'dtype': 'uint8', 'nodata': 255,
                    'compress': 'deflate', 'tiled': True,
                }
            else:
                total += data

    with rasterio.open(dst_path, 'w', **profile) as dst:
        dst.write(total.filled(255).astype(np.uint8), 1)
    return dst_path
