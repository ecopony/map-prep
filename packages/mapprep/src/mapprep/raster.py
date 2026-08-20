import numpy as np
import geopandas as gpd
import rasterio
import shapely
from osgeo import gdal
from rasterio import features
from rasterio.transform import Affine
from scipy import ndimage
from shapely.geometry import shape

gdal.UseExceptions()

def clip(src_path, dst_path, bounds, bounds_crs='EPSG:4326', dst_nodata=None, cutline=None, cutline_layer=None):
    """Clip a raster to (west, south, east, north) given in bounds_crs, keeping the native CRS.
    Bounds beyond the source extent are filled with dst_nodata. cutline/cutline_layer
    optionally mask to a polygon layer (e.g. a geopackage layer); outside becomes dst_nodata."""
    gdal.Warp(dst_path, src_path, outputBounds=tuple(bounds), outputBoundsSRS=bounds_crs,
              dstNodata=dst_nodata, cutlineDSName=cutline, cutlineLayer=cutline_layer,
              creationOptions=['COMPRESS=DEFLATE', 'TILED=YES'])
    return dst_path

def build_overviews(path, levels=(2, 4, 8, 16, 32), resampling='AVERAGE'):
    """Build internal overviews so large rasters display quickly at small scales."""
    ds = gdal.Open(path, gdal.GA_Update)
    ds.BuildOverviews(resampling, list(levels))
    return path

def blur(src_path, dst_path, pixel_window : int):
    """Mean-filter blur of a single-band raster; reflect-padded so edges don't darken."""
    with rasterio.open(src_path) as src:
        data = src.read(1)
        meta = src.meta.copy()
    pad = pixel_window // 2
    padded = np.pad(data, pad, mode='reflect')
    blurred = ndimage.uniform_filter(padded, size=pixel_window, mode='constant', cval=0)
    with rasterio.open(dst_path, 'w', **meta) as dst:
        dst.write(blurred[pad:-pad, pad:-pad], 1)
    return dst_path

def scale_values(src_path, dst_path, factor : float):
    with rasterio.open(src_path) as src:
        data = src.read(1)
        meta = src.meta.copy()
        if src.nodata is not None:
            data = np.where(data == src.nodata, src.nodata, data * factor)
        else:
            data = data * factor
    with rasterio.open(dst_path, 'w', **meta) as dst:
        dst.write(data.astype(meta['dtype']), 1)
    return dst_path

def _reduce(src_paths, dst_path, reducer):
    """Pixelwise reduction across aligned single-band rasters; nodata where any input is."""
    stack = []
    for path in src_paths:
        with rasterio.open(path) as src:
            data = src.read(1).astype(np.float64)
            if stack and data.shape != stack[0].shape:
                raise ValueError(f'grid mismatch: {path} is {data.shape}, expected {stack[0].shape}')
            valid = np.isfinite(data) if src.nodata is None else data != src.nodata
            stack.append(np.where(valid, data, np.nan))
            meta = src.meta.copy()
    result = reducer(np.stack(stack), axis=0)
    meta.update(dtype='float32', nodata=-9999.0, compress='deflate')
    with rasterio.open(dst_path, 'w', **meta) as dst:
        dst.write(np.where(np.isfinite(result), result, -9999.0).astype('float32'), 1)
    return dst_path

def mean(src_paths, dst_path):
    return _reduce(src_paths, dst_path, np.mean)

def total(src_paths, dst_path):
    return _reduce(src_paths, dst_path, np.sum)

def difference(src_path, subtract_path, dst_path):
    """Pixelwise src - subtract."""
    return _reduce([src_path, subtract_path], dst_path, lambda stack, axis: stack[0] - stack[1])

def ratio(numerator_path, denominator_path, dst_path):
    """Pixelwise numerator / denominator; nodata where either input is, or denominator <= 0."""
    def _ratio(stack, axis):
        with np.errstate(divide='ignore', invalid='ignore'):
            return np.where(stack[1] > 0, stack[0] / stack[1], np.nan)
    return _reduce([numerator_path, denominator_path], dst_path, _ratio)

def classify_to_polygons(raster_path, breaks, smooth_sigma : float = 0, upsample : int = 1, sieve_pixels : int = 0, simplify_tolerance : float = 0):
    """Classify a single-band raster into bins and vectorize to a polygon coverage.

    breaks: class boundaries, e.g. [10, 20, 40] -> classes <10, 10-20, 20-40, >40.
    smooth_sigma: gaussian pre-smoothing of values, in pixels. The main knob for smooth lines.
    upsample: resample factor before vectorizing; removes pixel staircase at class edges.
    sieve_pixels: merge class patches smaller than this many (upsampled) pixels into their
        largest neighbor; the de-speckling knob.
    simplify_tolerance: coverage simplification in CRS units; shared class boundaries stay aligned.
    """
    with rasterio.open(raster_path) as src:
        data = src.read(1).astype(np.float64)
        transform = src.transform
        crs = src.crs
        valid = np.isfinite(data) if src.nodata is None else data != src.nodata

    if smooth_sigma:
        weights = ndimage.gaussian_filter(valid.astype(np.float64), smooth_sigma)
        smoothed = ndimage.gaussian_filter(np.where(valid, data, 0.0), smooth_sigma)
        data = np.where(valid, smoothed / np.maximum(weights, 1e-9), 0.0)

    if upsample > 1:
        data = ndimage.zoom(np.where(valid, data, 0.0), upsample, order=1)
        valid = ndimage.zoom(valid, upsample, order=0)
        transform = transform * Affine.scale(1 / upsample)

    classes = np.digitize(data, breaks).astype(np.uint8)

    if sieve_pixels:
        classes = features.sieve(classes, size=sieve_pixels, mask=valid)

    records = [{'class': int(value), 'geometry': shape(geometry)}
               for geometry, value in features.shapes(classes, mask=valid, transform=transform)]
    gdf = gpd.GeoDataFrame(records, crs=crs).dissolve(by='class', as_index=False).sort_values('class')

    if simplify_tolerance:
        gdf['geometry'] = shapely.coverage_simplify(gdf.geometry, simplify_tolerance)

    bounds = [None, *breaks, None]
    gdf['lower'] = [bounds[c] for c in gdf['class']]
    gdf['upper'] = [bounds[c + 1] for c in gdf['class']]
    gdf['label'] = [f'< {bounds[c + 1]}' if bounds[c] is None
                    else f'> {bounds[c]}' if bounds[c + 1] is None
                    else f'{bounds[c]}-{bounds[c + 1]}'
                    for c in gdf['class']]
    return gdf
