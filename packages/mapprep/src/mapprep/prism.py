import os
import dotenv
from mapprep import raster

dotenv.load_dotenv(dotenv.find_dotenv())

MM_PER_INCH = 25.4

def prism_directory(path : str):
    return os.path.join(os.environ['PRISM_DIR'], path)

# 30-year (1991-2020) annual precipitation normals, 2.5 arc-minute (~4km), mm
def ppt_annual_normals_path():
    return prism_directory('prism_ppt_us_25m_2020_avg_30y/prism_ppt_us_25m_2020_avg_30y.tif')

def ppt_annual_normals_inches(dst_path):
    return raster.scale_values(ppt_annual_normals_path(), dst_path, 1 / MM_PER_INCH)
