"""Sky Islands â€” the Madrean Archipelago.

Derives the "islands" (forested mountain ranges isolated by desert) from a DEM: threshold
at the definitional elevation, drop the two mainlands (Mogollon Rim / Colorado Plateau to
the north, Sierra Madre Occidental to the south), keep what is disconnected from both, and
attribute each island with its woodland cover so high-but-treeless terrain can be excluded.
The threshold is the map's sea level; banded thresholds give the reverse-bathymetry tint.
Brief: mapmaking/projects/sky-islands/brief.md
"""
import os

import dotenv
import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio
from osgeo import gdal
from rasterio import features
from scipy import ndimage
from shapely.geometry import box, shape

from mapprep import dem
from mapprep import earthenv
from mapprep import hillshade
from mapprep import natural_earth as ne
from mapprep import raster

dotenv.load_dotenv(dotenv.find_dotenv())
gdal.UseExceptions()

geopackage_name = 'output/sky-islands.gpkg'
os.makedirs('output', exist_ok=True)
os.makedirs('cache', exist_ok=True)

# Display frame in lon/lat, covering the *rotated* layout (the map draws at 56 degrees in
# Pro, so frame corners sweep far beyond the archipelago). Both mainlands still run out of
# the frame, which the mainland-removal edge test depends on.
# Rule of thumb (learned the hard way, twice): size background sources 1.5x bigger than the
# estimated layout need - frames grow and rotate. 2026-08-27: (-118.5, 22, -101.5, 39.5), the
# 1.5x rule applied. 2026-08-28: the user chose a wider layout for context (Nevada/Colorado
# to Nayarit/Zacatecas) and the rotated corners ran past the data again, so grown once more.
map_bounds = (-123.0, 19.0, -98.0, 41.5)
# The archipelago proper - the brief's 108-112W / 28-34N padded a degree. map_bounds is
# display scenery (hillshade, elevation bands, context); *membership* is this box: only
# landmasses centered inside it count as Madrean sky islands. Western AZ / Baja / deep
# Chihuahua ranges in the display frame are not sky islands in common usage. Interim rule
# until the naming pass against the Van Devender / MDE ~55-range list.
madrean_bounds = (-113.0, 27.0, -107.0, 35.0)

# Custom equal-area Albers centered on the archipelago. EPSG:5070's standard parallels
# (29.5/45.5N) are a CONUS fit and distort this far south; island areas and the gaps between
# them are the point, so equal-area with local parallels. 1/6-rule parallels for 27-35N.
crs_aea = ('+proj=aea +lat_1=28.3 +lat_2=33.7 +lat_0=31 +lon_0=-110 '
           '+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs')
pixel_m = 90
# The Albers is the processing grid only. Vectors are written in EPSG:4326 - a custom CRS
# has no authority code, and ArcGIS Pro rejects GeoPackage layers whose SRS is 'unknown'.
# Set the map's coordinate system in Pro (paste crs_aea, or import it from the DEM raster).
crs_out = 'EPSG:4326'

# Deyo's definition: >= 1,600 m with discontinuous oak woodland. The shoreline.
shoreline_m = 1600
# Hypsometric bands above the shoreline (reverse bathymetry: the basins "deepen" below
# 1,600 m, the islands rise above it). Two sub-shoreline bands show how the archipelago
# merges/splits as the sea level moves - the corridor-sensitivity margin note.
tint_breaks = [1200, 1400, 1600, 1800, 2100, 2400, 2700, 3000]

# Per-island filters (applied as attributes; the filtered layer is a second output so the
# thresholds can be tuned in Pro against the full candidate set).
min_island_km2 = 5
min_treecover_pct = 15   # EarthEnv % tree cover, island maximum - "has woodland somewhere"
# Scenery floor: failed candidates smaller than this are dropped from `other_land` (and so
# from its hillshade / tree-cover rasters). 2026-09-16: the first layout showed ~15,700
# white specks across Chihuahua, Nevada and California that out-shouted the islands. 50 km2
# keeps 86 % of the failed-candidate area in ~200 features, and nothing kept is smaller than
# a typical island (median 25 km2). Mainlands are always kept. `islands_candidates` still
# has every fragment for tuning.
min_display_km2 = 50

# --- Context vectors -----------------------------------------------------------------
frame = gpd.GeoDataFrame(geometry=[box(*map_bounds).segmentize(0.1)], crs='EPSG:4326')
frame.to_file(geopackage_name, layer='frame', driver='GPKG')

# US and Mexican states in the frame (only the 10m admin-1 file covers Mexico).
states = gpd.read_file(ne.ne_directory('StatesProvinces/ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces.shp'))
states = states[['name', 'admin', 'iso_3166_2', 'geometry']].clip(map_bounds, keep_geom_type=True)
states.to_file(geopackage_name, layer='states', driver='GPKG')

# The international border as its own line (2026-09-19: the layout needs it readable apart
# from the state lines - half the islands are in Mexico). Derived from the 10m states layer
# rather than NE's boundary_lines file (only the 50m version is on disk, and it would not
# sit on the 10m state edges): dissolve each country, take the shared edge of the two.
us = states[states['admin'] == 'United States of America'].dissolve().geometry.iloc[0]
mx = states[states['admin'] == 'Mexico'].dissolve().geometry.iloc[0]
border = gpd.GeoDataFrame({'name': ['United States – Mexico']},
                          geometry=[us.boundary.intersection(mx.boundary)], crs=states.crs)
border = border.explode(index_parts=False)
border = border[border.geom_type.isin(['LineString', 'MultiLineString'])].dissolve()
border['name'] = 'United States – Mexico'
border.to_file(geopackage_name, layer='border', driver='GPKG')
# The real ocean (Gulf of California / Pacific in the SW corner), to style distinctly from
# the desert "sea" so the metaphor doesn't collide with actual water.
# 10m to match the 10m states coastline. Clipped: the unclipped 10m ocean is one global
# polygon and bogged Pro's rendering (tried 2026-08-28). map_bounds already carries margin.
ne.ocean(scale='10m').clip(map_bounds, keep_geom_type=True).to_file(geopackage_name, layer='ocean', driver='GPKG')

places = ne.read_populated_places().cx[map_bounds[0]:map_bounds[2], map_bounds[1]:map_bounds[3]]
places[['name', 'adm0name', 'scalerank', 'pop_max', 'geometry']].to_file(geopackage_name, layer='populated_places', driver='GPKG')
# The handful that go on the map, as "ports": orientation marks, not a data layer. Juarez is
# not in the source at this scalerank, so El Paso carries both names.
city_names = ['Tucson', 'Phoenix', 'El Paso', 'Hermosillo', 'Chihuahua', 'Albuquerque']
cities = places[places['name'].isin(city_names)].copy()
cities['label'] = cities['name'].replace({'El Paso': 'El Paso / Ciudad Juárez'})
cities[['name', 'label', 'adm0name', 'pop_max', 'geometry']].to_file(geopackage_name, layer='cities', driver='GPKG')

# USGS Fenneman physiographic divisions (CONUS only) - reference for placing the mainland
# labels: "Colorado Plateaus" is a province, the Mogollon Rim is its southern edge, and the
# northern mainland's coast on this map is actually the Transition Zone south of the Rim.
os.makedirs('cache/physio', exist_ok=True)
if not os.path.exists('cache/physio/physio.shp'):
    import io, zipfile, requests
    response = requests.get('https://water.usgs.gov/GIS/dsdl/physio_shp.zip', timeout=120)
    response.raise_for_status()
    zipfile.ZipFile(io.BytesIO(response.content)).extractall('cache/physio')
physio = gpd.read_file('cache/physio/physio.shp')[['DIVISION', 'PROVINCE', 'SECTION', 'geometry']]
physio.columns = ['division', 'province', 'section', 'geometry']
for column in ('division', 'province', 'section'):
    physio[column] = physio[column].str.title()
physio = physio.to_crs(crs_out).clip(map_bounds, keep_geom_type=True)
physio.dissolve(by=['division', 'province', 'section'], as_index=False)     .to_file(geopackage_name, layer='physiographic_sections', driver='GPKG')
physio.dissolve(by=['division', 'province'], as_index=False)[['division', 'province', 'geometry']]     .to_file(geopackage_name, layer='physiographic_provinces', driver='GPKG')

# Global countries for the extent-indicator inset (an orthographic "globe" in Pro; `frame`
# is the extent rectangle to draw on it). Europe, Asia and Greenland dropped - on a disc
# centered on the archipelago they only clutter the rim. 50m is ~200 small polygons.
countries = ne.countries()
countries = countries[~countries['CONTINENT'].isin(['Europe', 'Asia']) & (countries['ADMIN'] != 'Greenland')]
countries[['ADMIN', 'ISO_A3', 'CONTINENT', 'geometry']].rename(columns=str.lower)     .to_file(geopackage_name, layer='countries', driver='GPKG')

# --- Elevation -----------------------------------------------------------------------
# Copernicus GLO-90 (cross-border; GLO-30 would be 9x the data for no gain at 1:2-3M),
# warped once to the equal-area grid so every derived raster shares it.
dem_geo = dem.fetch(map_bounds, 'cache/cop90_geographic.tif', demtype='COP90')
dem_path = 'output/dem_cop90_aea.tif'
gdal.Warp(dem_path, dem_geo, dstSRS=crs_aea, xRes=pixel_m, yRes=pixel_m, resampleAlg='bilinear',
          outputBounds=tuple(frame.to_crs(crs_aea).total_bounds), dstNodata=-9999,
          creationOptions=dem.GTIFF_OPTIONS)
raster.build_overviews(dem_path)
hillshade.from_dem(dem_path, 'output/hillshade_multidirectional.tif', z_factor=1.5, multi_directional=True)
raster.build_overviews('output/hillshade_multidirectional.tif')

# --- Woodland mask (interim) --------------------------------------------------------
# EarthEnv 1 km consensus tree cover, resampled onto the DEM grid. Stand-in until Brown &
# Lowe biotic communities (the canonical Madrean evergreen woodland classes) or NALCMS 30 m
# is downloaded - see LAYERS.md.
earthenv.treecover('cache/treecover_geographic.tif', map_bounds)
treecover_path = 'output/treecover_earthenv_aea.tif'
gdal.Warp(treecover_path, 'cache/treecover_geographic.tif', dstSRS=crs_aea, xRes=pixel_m, yRes=pixel_m,
          resampleAlg='bilinear', outputBounds=tuple(frame.to_crs(crs_aea).total_bounds),
          srcNodata=255, dstNodata=255, creationOptions=dem.GTIFF_OPTIONS)

# --- Islands -------------------------------------------------------------------------
with rasterio.open(dem_path) as src:
    elevation = src.read(1)
    transform = src.transform
    nodata = src.nodata
with rasterio.open(treecover_path) as src:
    treecover = src.read(1).astype(np.float32)
    treecover[treecover == 255] = np.nan

high = (elevation >= shoreline_m) & (elevation != nodata)
# 8-connectivity: diagonal pixel contacts count as land bridges, which errs toward merging
# ranges (a ridge saddle at exactly the threshold keeps them one island).
labels, count = ndimage.label(high, structure=np.ones((3, 3)))

# Mainland removal: the Colorado Plateau / Mogollon Rim block and the Sierra Madre
# Occidental both run out of the frame, so any component touching the frame edge is
# mainland, not island. Kept as their own layer so the drop is inspectable.
# "Edge" is the edge of valid data, not the array edge: the lon/lat frame warps to a curved
# quadrilateral in Albers, so the array corners are nodata wedges and the mainlands meet
# nodata before they meet the array boundary.
valid = np.pad(elevation != nodata, 1, constant_values=False)
at_edge = valid[1:-1, 1:-1] & ~ndimage.binary_erosion(valid, structure=np.ones((3, 3)))[1:-1, 1:-1]
edge_labels = np.unique(labels[at_edge])
edge_labels = edge_labels[edge_labels > 0]

pixel_km2 = (pixel_m / 1000) ** 2
index = np.arange(1, count + 1)
area_km2 = ndimage.sum_labels(high, labels, index) * pixel_km2
elev_max = ndimage.maximum(elevation, labels, index)
tree_max = ndimage.maximum(np.nan_to_num(treecover, nan=0), labels, index)
tree_mean = ndimage.mean(np.nan_to_num(treecover, nan=0), labels, index)

records = []
for geometry, value in features.shapes(labels.astype(np.int32), mask=high, transform=transform):
    records.append({'island_id': int(value), 'geometry': shape(geometry)})
polys = gpd.GeoDataFrame(records, crs=crs_aea).dissolve(by='island_id', as_index=False)
polys['area_km2'] = area_km2[polys['island_id'] - 1]
polys['elev_max_m'] = elev_max[polys['island_id'] - 1]
polys['prominence_m'] = polys['elev_max_m'] - shoreline_m
polys['treecover_max'] = tree_max[polys['island_id'] - 1]
polys['treecover_mean'] = tree_mean[polys['island_id'] - 1]
polys['mainland'] = polys['island_id'].isin(edge_labels)
polys['name'] = None   # to be filled against the ~55-range list (Van Devender / MDE)

mainlands = polys[polys['mainland']].copy()
# Label the two mainlands by latitude: northernmost edge-touching block is the Plateau side,
# southernmost the Sierra Madre; anything else is a fragment that clipped the E/W edge.
if len(mainlands):
    cy = mainlands.geometry.centroid.y
    mainlands.loc[cy.idxmax(), 'name'] = 'Colorado Plateau / Mogollon Rim'
    mainlands.loc[cy.idxmin(), 'name'] = 'Sierra Madre Occidental'

candidates = polys[~polys['mainland']].drop(columns='mainland')
madrean_area = gpd.GeoSeries([box(*madrean_bounds).segmentize(0.1)], crs='EPSG:4326').to_crs(crs_aea).iloc[0]
candidates['madrean'] = candidates.geometry.representative_point().within(madrean_area)
candidates.to_crs(crs_out).to_file(geopackage_name, layer='islands_candidates', driver='GPKG')

islands = candidates[candidates['madrean'] & (candidates['area_km2'] >= min_island_km2)
                     & (candidates['treecover_max'] >= min_treecover_pct)]
islands = islands.sort_values('area_km2', ascending=False)

# Names (2026-09-19): `names.csv` is the literature's range list (Wikipedia list of Madrean
# Sky Island ranges + the MDE / Van Devender Sonoran sierras) as one summit or interior
# point per range, with a `confidence` column - the US rows are Wikipedia coordinates, the
# Sonoran rows are placed from towns and landmarks because neither Wikipedia nor OSM
# geocodes them; low-confidence rows are worth eyeballing in Pro. Matched to the nearest
# island within `name_match_km` rather than point-in-polygon so a run-to-run grid shift
# doesn't drop names. Points that land on a mainland (Peloncillos, Animas, Sierra San
# Luis - fused to the Sierra Madre block at 1,600 m) or in the sea (Superstitions,
# Tumacacoris - below the shoreline) are reported, not forced.
# `tier` is the label hierarchy for Pro (1 = the eight marquee ranges, 2 = the next dozen,
# 3 = named but normally unlabeled): 39 labels on this archipelago crammed together
# (2026-09-19), so the label class is `tier <= 1` or `tier <= 2`, not `name IS NOT NULL`.
name_match_km = 5
names = pd.read_csv('names.csv', encoding='utf-8')
name_pts = gpd.GeoDataFrame(names, geometry=gpd.points_from_xy(names.lon, names.lat),
                            crs='EPSG:4326').to_crs(crs_aea)
matched = gpd.sjoin_nearest(name_pts, islands[['island_id', 'geometry']], how='left',
                            max_distance=name_match_km * 1000, distance_col='dist_m')
on_mainland = gpd.sjoin(name_pts, mainlands[['geometry']], how='inner', predicate='within')
for _, row in matched.iterrows():
    if pd.isna(row['island_id']):
        why = 'on a mainland' if row['name'] in set(on_mainland['name']) else 'no island within range'
        print(f'  name not placed: {row["name"]} ({why})')
matched = matched.dropna(subset=['island_id']).sort_values('dist_m').drop_duplicates('island_id')
islands = islands.drop(columns='name').merge(matched[['island_id', 'name', 'tier', 'confidence']],
                                              on='island_id', how='left')
islands = gpd.GeoDataFrame(islands, geometry='geometry', crs=crs_aea)
print(f'{islands["name"].notna().sum()} of {len(islands)} islands named from {len(names)} list entries')
islands.to_crs(crs_out).to_file(geopackage_name, layer='islands', driver='GPKG')

# Everything that is land but not a sky island - the two mainlands plus the candidates that
# failed the filter - as ONE layer, because the layout styles them identically (2026-08-28:
# separate mainlands / candidates layers doubled the styling work for no visual difference).
# `kind` keeps the distinction queryable.
failed = candidates[~candidates['island_id'].isin(islands['island_id'])].drop(columns='madrean')
other_land = pd.concat([mainlands.drop(columns='mainland').assign(kind='mainland'),
                        failed[failed['area_km2'] >= min_display_km2].assign(kind='candidate')])
other_land.to_crs(crs_out).to_file(geopackage_name, layer='other_land', driver='GPKG')
print(f'{count} components at {shoreline_m} m: {len(mainlands)} mainland, {len(candidates)} candidates, '
      f'{len(islands)} Madrean islands >= {min_island_km2} km2 with tree cover >= {min_treecover_pct}%; '
      f'other_land keeps {len(other_land)} of {len(mainlands) + len(failed)} (scenery floor {min_display_km2} km2)')
print(islands[['island_id', 'area_km2', 'elev_max_m', 'treecover_max']].head(60).to_string())

# --- Hypsometric tint bands ----------------------------------------------------------
# Smoothed/generalized so the bands read as a chart at 1:2-3M; the islands layer above is
# the precise (unsmoothed) derivation, so the two will differ slightly along the shoreline.
tint = raster.classify_to_polygons(dem_path, tint_breaks, smooth_sigma=2, upsample=2,
                                   sieve_pixels=200, simplify_tolerance=60)
tint.to_crs(crs_out).to_file(geopackage_name, layer='elevation_bands', driver='GPKG')

# --- Chart styling: sea vs land --------------------------------------------------------
# The bathymetry look needs the two worlds styled separately: a flat depth ramp in the
# "sea" (< shoreline), hillshade + contours on the "land". Splitting them
# here (rather than with masks in Pro) keeps the split exact and the layers self-describing.
contour_interval_m = 200          # land contours above the shoreline

# Sea depth raster: the DEM masked to below the shoreline, in metres relative to it
# (negative = deeper), for a continuous light-to-dark blue ramp in Pro - the rainfall map's
# "option B" (bathy_srtm15plus.tif) transplanted; `elevation_bands` is its stepped option A.
with rasterio.open(dem_path) as src:
    profile = src.profile
depth = np.where(high | (elevation == nodata), -9999, elevation - shoreline_m).astype(np.float32)
profile.update(nodata=-9999, compress='deflate', predictor=3, tiled=True, bigtiff='IF_SAFER')
with rasterio.open('output/sea_depth.tif', 'w', **profile) as dst:
    dst.write(depth, 1)
raster.build_overviews('output/sea_depth.tif')
del depth

# One contour pass on the full DEM at fixed levels above the shoreline. They lie inside the
# >= 1,600 m mask by construction, so no clipping to islands/mainlands. The 1,600 m line
# itself is the shoreline (`islands`).
from osgeo import ogr, osr
land_levels = list(range(shoreline_m + contour_interval_m, int(elevation.max()) + 1, contour_interval_m))
mem = ogr.GetDriverByName('MEM').CreateDataSource('contours')
srs = osr.SpatialReference()
srs.ImportFromProj4(crs_aea)
layer = mem.CreateLayer('contours', srs, ogr.wkbLineString)
layer.CreateField(ogr.FieldDefn('elev_m', ogr.OFTReal))
ds = gdal.Open(dem_path)
gdal.ContourGenerate(ds.GetRasterBand(1), 0, 0, land_levels, 1, nodata, layer, -1, 0)
ds = None
contours = gpd.GeoDataFrame.from_features([f.ExportToJson(as_object=True) for f in layer], crs=crs_aea)
mem = None
contours['elev_m'] = contours['elev_m'].astype(int)
contours['geometry'] = contours.simplify(60)
contours = contours[contours.length > 2000]    # drop closed-loop specks (single 90 m pixels)
contours['index'] = contours['elev_m'] % 1000 == 0
contours.to_crs(crs_out).to_file(geopackage_name, layer='contours', driver='GPKG')
print(f'{len(contours)} contour lines at {contour_interval_m} m')

# --- Hillshade and tree cover per land class ---------------------------------------------
# The islands are the subject and everything else is scenery, so each raster comes in two
# masked copies - `islands` and `other_land` - and the sea (below the shoreline) is nodata in
# both. Islands also get a z 3 hillshade option: at 1:2-3M the z 1.5 base is too gentle and
# the first layout (2026-08-28) had islands and mainlands looking the same.
land_classes = {'islands': islands, 'other_land': other_land}
masks = {name: features.rasterize(((g, 1) for g in subset.geometry), out_shape=elevation.shape,
                                  transform=transform, fill=0, dtype=np.uint8).astype(bool)
         for name, subset in land_classes.items()}

def write_masked(src_path, dst_path, mask, nodata_value):
    with rasterio.open(src_path) as src:
        profile = src.profile
        data = src.read(1)
    data[~mask] = nodata_value
    profile.update(nodata=nodata_value, compress='deflate', predictor=2, tiled=True, bigtiff='IF_SAFER')
    with rasterio.open(dst_path, 'w', **profile) as dst:
        dst.write(data, 1)
    raster.build_overviews(dst_path)

hillshade.from_dem(dem_path, 'cache/hillshade_z3.tif', z_factor=3, multi_directional=True)
for name, mask in masks.items():
    write_masked('output/hillshade_multidirectional.tif', f'output/hillshade_{name}.tif', mask, 0)
    write_masked(treecover_path, f'output/treecover_{name}.tif', mask, 255)
write_masked('cache/hillshade_z3.tif', 'output/hillshade_islands_z3.tif', masks['islands'], 0)
