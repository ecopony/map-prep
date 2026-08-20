import io
import os
import zipfile
import dotenv
import requests
from mapprep import raster

dotenv.load_dotenv(dotenv.find_dotenv())

MM_PER_INCH = 25.4

# PRISM's public data server; 'us_25m' is the 2.5 arc-minute (~4km) CONUS grid and '2020'
# marks the 1991-2020 normals release. The zips unpack to the same <name>/<name>.tif layout
# used for manually downloaded grids in $PRISM_DIR.
NORMALS_URL = 'https://data.prism.oregonstate.edu/normals/us/4km/{var}/monthly/{name}.zip'

def prism_directory(path : str):
    return os.path.join(os.environ['PRISM_DIR'], path)

def _fetch_normals(var : str, month : int = None):
    """Return the path of a 1991-2020 normals grid in $PRISM_DIR, downloading it if absent.
    month=None fetches the annual grid, 1-12 a monthly one."""
    name = f'prism_{var}_us_25m_2020{"" if month is None else f"{month:02d}"}_avg_30y'
    tif = prism_directory(f'{name}/{name}.tif')
    if not os.path.exists(tif):
        response = requests.get(NORMALS_URL.format(var=var, name=name), timeout=300)
        response.raise_for_status()
        zipfile.ZipFile(io.BytesIO(response.content)).extractall(prism_directory(name))
    return tif

# 30-year (1991-2020) annual precipitation normals, 2.5 arc-minute (~4km), mm
def ppt_annual_normals_path():
    return prism_directory('prism_ppt_us_25m_2020_avg_30y/prism_ppt_us_25m_2020_avg_30y.tif')

def ppt_annual_normals_inches(dst_path):
    return raster.scale_values(ppt_annual_normals_path(), dst_path, 1 / MM_PER_INCH)

def monthly_normals_paths(var : str):
    """The twelve 1991-2020 monthly normals grids for a PRISM variable ('tmean', 'tmin',
    'tmax', 'ppt', ...), January first. Temperatures are degrees C, ppt is mm."""
    return [_fetch_normals(var, month) for month in range(1, 13)]

# Monthly time series (1895-present), AN ("all networks") variant at 4km. LT would be more
# temporally consistent but is published at 800m only (~38 MB/month vs ~2 MB).
TIME_SERIES_URL = 'https://data.prism.oregonstate.edu/time_series/us/an/4km/{var}/monthly/{year}/{name}.zip'

def monthly_path(var : str, year : int, month : int):
    """One monthly time-series grid, downloaded to $PRISM_DIR/time_series/ if absent."""
    name = f'prism_{var}_us_25m_{year}{month:02d}'
    directory = prism_directory(f'time_series/{var}/{name}')
    tif = os.path.join(directory, f'{name}.tif')
    if not os.path.exists(tif):
        response = requests.get(TIME_SERIES_URL.format(var=var, year=year, name=name), timeout=300)
        response.raise_for_status()
        zipfile.ZipFile(io.BytesIO(response.content)).extractall(directory)
    return tif

def monthly_climatology_paths(var : str, years, dst_dir : str):
    """Twelve grids (January first): the mean of each calendar month over `years`, computed
    from the monthly time series and cached in dst_dir. The DIY equivalent of PRISM's
    normals for an arbitrary 30-year window (e.g. years=range(1901, 1931))."""
    years = list(years)
    os.makedirs(dst_dir, exist_ok=True)
    paths = []
    for month in range(1, 13):
        dst = os.path.join(dst_dir, f'prism_{var}_climatology_{years[0]}_{years[-1]}_{month:02d}.tif')
        if not os.path.exists(dst):
            raster.mean([monthly_path(var, year, month) for year in years], dst)
        paths.append(dst)
    return paths
