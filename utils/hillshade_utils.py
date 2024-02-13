import os
import rasterio
from rasterio.merge import merge
from osgeo import gdal
import os
import zipfile
import numpy as np

def generate_hillshade_raster(directory_path):
    hgt_files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.endswith('.hgt')]

    if not hgt_files:
        raise FileNotFoundError("No HGT files found in the provided directory.")

    rasters = [rasterio.open(f) for f in hgt_files]
    combined_raster, out_trans = merge(rasters)

    out_fp = 'combined_raster.tif'
    out_meta = rasters[0].meta.copy()
    out_meta.update({"driver": "GTiff",
                     "height": combined_raster.shape[1],
                     "width": combined_raster.shape[2],
                     "transform": out_trans})

    with rasterio.open(out_fp, "w", **out_meta) as dest:
        dest.write(combined_raster)

    hillshade_fp = 'hillshade_raster.tif'
    gdal.DEMProcessing(hillshade_fp, out_fp, 'hillshade')

    for raster in rasters:
        raster.close()

    return out_fp, hillshade_fp

def combine_tif_files(directory_path, output_file):
    hgt_files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.endswith('.tif')]

    if not hgt_files:
        raise FileNotFoundError("No TIFF files found in the provided directory.")

    rasters = [rasterio.open(f) for f in hgt_files]
    combined_raster, out_trans = merge(rasters)

    out_fp = output_file
    out_meta = rasters[0].meta.copy()
    out_meta.update({"driver": "GTiff",
                     "height": combined_raster.shape[1],
                     "width": combined_raster.shape[2],
                     "transform": out_trans})

    with rasterio.open(out_fp, "w", **out_meta) as dest:
        dest.write(combined_raster)


def extract_zip_files(directory_path):
    output_directory = os.path.join(directory_path, "output")
    os.makedirs(output_directory, exist_ok=True)

    zip_files = [f for f in os.listdir(directory_path) if f.endswith('.zip')]

    for zip_file in zip_files:
        zip_file_path = os.path.join(directory_path, zip_file)
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(output_directory)

    return output_directory






