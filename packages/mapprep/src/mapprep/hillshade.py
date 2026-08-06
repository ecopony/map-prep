import os
import rasterio
from rasterio.merge import merge
from osgeo import gdal
import os
import zipfile
import numpy as np

gdal.UseExceptions()

def from_dem(dem_path, dst_path, z_factor=1.0, multi_directional=False, azimuth=315, altitude=45):
    """Hillshade a DEM into an 8-bit GeoTIFF. Handles geographic DEMs (degrees + meters)
    via GDAL's scale option. multi_directional ignores azimuth (GDAL forbids combining them)."""
    ds = gdal.Open(dem_path)
    srs = ds.GetSpatialRef()
    scale = 111120 if srs is not None and srs.IsGeographic() else 1

    options = {'scale': scale, 'zFactor': z_factor, 'altitude': altitude, 'computeEdges': True,
               'creationOptions': ['COMPRESS=DEFLATE', 'TILED=YES']}
    if multi_directional:
        options['multiDirectional'] = True
    else:
        options['azimuth'] = azimuth
    gdal.DEMProcessing(dst_path, ds, 'hillshade', **options)
    return dst_path


def array_from_dem(dem_path, z_factor=1.0, azimuth=315, altitude=45):
    """Single-azimuth hillshade as an in-memory array (nothing written to disk)."""
    ds = gdal.DEMProcessing('', dem_path, 'hillshade', format='MEM', computeEdges=True,
                            zFactor=z_factor, azimuth=azimuth, altitude=altitude)
    return ds.ReadAsArray()


def combine(dem_path, azimuths, altitudes, weights=None, z_factor=1.0):
    """Weighted blend of hillshades from multiple azimuth/altitude pairs, as an array.

    Unlike from_dem(multi_directional=True) (GDAL's fixed formula), this gives control
    over the directions and their weights."""
    arrays = [array_from_dem(dem_path, z_factor=z_factor, azimuth=azimuth, altitude=altitude)
              for azimuth, altitude in zip(azimuths, altitudes)]
    return np.clip(np.average(arrays, axis=0, weights=weights), 0, 255)


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






