"""Potential evapotranspiration and the P/PET aridity index.

The UNEP aridity index (annual precipitation / annual potential evapotranspiration) is the
measure behind the "effective" arid-humid divide of Seager et al. 2018 ("Whither the 100th
Meridian?", Earth Interactions 22). They define the divide by an aridity level rather than
a fixed longitude but never commit to a value (their one passing reference is AI ~ 1); the
0.65 used here is the UNEP drylands threshold (World Atlas of Desertification, 1992).
PET follows Hargreaves-Samani (1985), which needs only monthly min/max
temperature and latitude -- a good fit for PRISM normals. (Thornthwaite was tried first and
rejected: it underestimates PET in cool climates badly enough to push the northern half of
the divide ~5 degrees west of Penman-based analyses; Hargreaves lands on Seager's ~98W.)
"""
import datetime
import os
import geopandas as gpd
import numpy as np
import rasterio
from scipy import ndimage
from shapely.geometry import LineString
from mapprep import raster

ARID_HUMID_THRESHOLD = 0.65  # UNEP drylands boundary (Seager et al. fix no value)

def _hargreaves_monthly(tmin_paths, tmax_paths):
    """Yield (month, pet_mm, valid, meta) for the twelve months: Hargreaves-Samani (1985)
    daily PET scaled to a monthly total, from monthly minimum and maximum temperature grids
    (deg C, January first, geographic CRS)."""
    with rasterio.open(tmin_paths[0]) as src:
        meta = src.meta.copy()
        transform = src.transform
        nodata = src.nodata

    tmin = np.stack([rasterio.open(p).read(1) for p in tmin_paths])
    tmax = np.stack([rasterio.open(p).read(1) for p in tmax_paths])
    valid = np.all((tmin != nodata) & (tmax != nodata), axis=0) if nodata is not None \
        else (np.isfinite(tmin) & np.isfinite(tmax)).all(axis=0)
    tmin = np.where(valid, tmin, 0.0)
    tmax = np.where(valid, tmax, 0.0)

    lat = np.radians(transform.f + (np.arange(meta['height']) + 0.5) * transform.e)[:, None]

    for month in range(1, 13):
        doy = datetime.date(2001, month, 15).timetuple().tm_yday
        days = (datetime.date(2001 + (month == 12), month % 12 + 1, 1) - datetime.date(2001, month, 1)).days
        # FAO-56 extraterrestrial radiation, expressed as equivalent evaporation (mm/day)
        inv_distance = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
        declination = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
        sunset_angle = np.arccos(np.clip(-np.tan(lat) * np.tan(declination), -1.0, 1.0))
        radiation = 0.408 * (24 * 60 / np.pi) * 0.0820 * inv_distance * (
            sunset_angle * np.sin(lat) * np.sin(declination) + np.cos(lat) * np.cos(declination) * np.sin(sunset_angle))
        t = (tmin[month - 1] + tmax[month - 1]) / 2.0
        daily = 0.0023 * radiation * (t + 17.8) * np.sqrt(np.maximum(tmax[month - 1] - tmin[month - 1], 0.0))
        yield month, np.maximum(daily, 0.0) * days, valid, meta

def hargreaves_pet_annual(tmin_paths, tmax_paths, dst_path):
    """Annual PET (mm) by Hargreaves-Samani (1985) from 12 monthly minimum and maximum
    temperature grids. Needs only temperatures plus computed extraterrestrial radiation,
    and tracks Penman-Monteith far better than Thornthwaite, which underestimates PET in
    cool climates."""
    pet = 0.0
    for month, monthly, valid, meta in _hargreaves_monthly(tmin_paths, tmax_paths):
        pet = pet + monthly
    meta.update(dtype='float32', nodata=-9999.0, compress='deflate')
    with rasterio.open(dst_path, 'w', **meta) as dst:
        dst.write(np.where(valid, pet, -9999.0).astype('float32'), 1)
    return dst_path

def hargreaves_pet_monthly(tmin_paths, tmax_paths, dst_dir):
    """The twelve monthly PET grids (mm/month, January first), written to dst_dir. Noisier
    month-by-month than the annual sum (the sqrt(tmax-tmin) proxy is coarser at monthly
    scale) — fine where only the sign of P - PET matters, as in surplus_months."""
    os.makedirs(dst_dir, exist_ok=True)
    paths = []
    for month, monthly, valid, meta in _hargreaves_monthly(tmin_paths, tmax_paths):
        meta = dict(meta, dtype='float32', nodata=-9999.0, compress='deflate')
        dst = os.path.join(dst_dir, f'pet_{month:02d}.tif')
        with rasterio.open(dst, 'w', **meta) as f:
            f.write(np.where(valid, monthly, -9999.0).astype('float32'), 1)
        paths.append(dst)
    return paths

def surplus_months(ppt_paths, pet_paths, dst_path):
    """Count of months (0-12) where monthly precipitation meets or exceeds monthly PET —
    how much of the year the sky runs a water surplus. Robust to the monthly-Hargreaves
    noise since only the sign of P - PET matters."""
    count, valid = 0, True
    for ppt_path, pet_path in zip(ppt_paths, pet_paths, strict=True):
        with rasterio.open(ppt_path) as src:
            ppt = src.read(1)
            month_valid = ppt != src.nodata if src.nodata is not None else np.isfinite(ppt)
            meta = src.meta.copy()
        with rasterio.open(pet_path) as src:
            pet = src.read(1)
            month_valid &= pet != src.nodata if src.nodata is not None else np.isfinite(pet)
            if pet.shape != ppt.shape:
                raise ValueError(f'grid mismatch: ppt {ppt.shape} vs pet {pet.shape}')
        valid = valid & month_valid
        count = count + ((ppt >= pet) & month_valid).astype(np.uint8)
    meta.update(dtype='uint8', nodata=255, compress='deflate')
    with rasterio.open(dst_path, 'w', **meta) as dst:
        dst.write(np.where(valid, count, 255).astype('uint8'), 1)
    return dst_path

def effective_divide(aridity_index_path, threshold : float = ARID_HUMID_THRESHOLD,
                     smooth_sigma : float = 5, latitude_smooth_sigma : float = 10):
    """The effective arid-humid divide as a single north-south line: at each latitude, the
    point east of which the country is contiguously humid (P/PET >= threshold).

    A raw iso-line of the aridity surface won't do here — it detours around the humid
    Rocky Mountain high country, which connects to the humid East and drags the contour
    deep into Colorado. Scanning rows for the easternmost arid pixel matches the divide
    concept in Seager et al. 2018 instead: everything east of the line is humid, even if
    humid islands sit west of it.

    smooth_sigma: gaussian smoothing of the aridity surface (pixels) before thresholding.
    latitude_smooth_sigma: smoothing of the resulting longitude series (rows), the
        line-generalization knob.
    """
    with rasterio.open(aridity_index_path) as src:
        data = src.read(1).astype(np.float64)
        transform = src.transform
        crs = src.crs
        valid = np.isfinite(data) if src.nodata is None else data != src.nodata

    if smooth_sigma:
        weights = ndimage.gaussian_filter(valid.astype(np.float64), smooth_sigma)
        smoothed = ndimage.gaussian_filter(np.where(valid, data, 0.0), smooth_sigma)
        data = np.where(valid, smoothed / np.maximum(weights, 1e-9), 0.0)

    arid = valid & (data < threshold)
    has_arid = arid.any(axis=1)
    easternmost = data.shape[1] - 1 - np.argmax(arid[:, ::-1], axis=1)
    # A row belongs on the line only if humid data actually lies east of its last arid pixel
    # (drops all-humid rows like south Florida, where the "divide" would hug the coastline)
    humid = valid & ~arid
    has_humid_east = np.array([humid[row, easternmost[row] + 1:].any() for row in range(data.shape[0])])
    rows = np.flatnonzero(has_arid & has_humid_east)
    if np.any(np.diff(rows) > 1):
        raise ValueError(f'divide rows are not contiguous ({np.count_nonzero(np.diff(rows) > 1)} gaps): '
                         'the longitude smoothing would bridge the gaps and distort the line. '
                         'The threshold likely admits arid pockets far east of the plains divide '
                         '(this happens by ~1.0 on the Hargreaves surface).')

    lon = transform.c + (easternmost[rows] + 1.0) * transform.a  # east edge of the arid pixel
    if latitude_smooth_sigma:
        lon = ndimage.gaussian_filter1d(lon, latitude_smooth_sigma)
    lat = transform.f + (rows + 0.5) * transform.e
    return gpd.GeoDataFrame({'threshold': [threshold]},
                            geometry=[LineString(np.column_stack([lon, lat]))], crs=crs)

def aridity_index(ppt_annual_path, pet_annual_path, dst_path):
    """P/PET on the shared PRISM grid. < 0.65 is drylands (UNEP); higher is humid."""
    return raster.ratio(ppt_annual_path, pet_annual_path, dst_path)
