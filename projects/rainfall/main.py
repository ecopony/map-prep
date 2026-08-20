import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString
from mapprep import aridity
from mapprep import dem
from mapprep import earthenv
from mapprep import hillshade
from mapprep import legend
from mapprep import natural_earth as ne
from mapprep import prism
from mapprep import raster
import dotenv

dotenv.load_dotenv(dotenv.find_dotenv())

geopackage_name = 'output/rainfall.gpkg'

# City labels come from NE's curated scalerank (0 = most important) rather than a population
# cutoff: rank <= 2 gives 20 label-worthy cities and already excludes satellite metros
# (St. Paul, Ft. Worth, ...) that a population threshold lets through.
max_scalerank = 2

# Annual precipitation classes, in inches
rainfall_breaks = [5, 10, 15, 20, 30, 40, 60, 80, 100]

os.makedirs('output', exist_ok=True)
os.makedirs('cache', exist_ok=True)

# Bounds are the ArcGIS map frame extent (EPSG:5070) transformed to lat/lon and rounded out,
# so clipped layers cover the whole layout, not just CONUS.
map_bounds = (-140, 16.5, -56, 57)

us_states = ne.us_states(contiguous=True)
us_states.to_file(geopackage_name, layer='us_states', driver='GPKG')

# Dissolved contiguous-US outline, for the layout vignette effect. Derived from us_states
# (not the NE admin-0 country polygon) so it lines up with the state linework exactly.
us_states.dissolve()[['geometry']].to_file(geopackage_name, layer='conus_outline', driver='GPKG')
ne.us_populated_places(max_scalerank=max_scalerank, contiguous=True).to_file(geopackage_name, layer='populated_places', driver='GPKG')

# Outlines of every non-US country in the frame (Canada, Mexico, Cuba, Bahamas, Central
# America, ...) so all foreign land styles uniformly; whole countries, not their states
surrounding = ne.countries(exclude='United States of America').cx[map_bounds[0]:map_bounds[2], map_bounds[1]:map_bounds[3]]
surrounding.to_file(geopackage_name, layer='surrounding_countries', driver='GPKG')
ne.ocean().clip(map_bounds).to_file(geopackage_name, layer='ocean', driver='GPKG')

# Ocean styling option A: NE stepped depth bands (compare against the SRTM15+ raster below)
ne.bathymetry().clip(map_bounds).to_file(geopackage_name, layer='bathymetry_bands', driver='GPKG')

# Major lakes (>= ~1000 km2: Great Lakes, Winnipeg, Great Salt Lake, Champlain, Okeechobee, ...).
# The Montana/Dakotas Missouri River reservoirs are dropped as a distraction ('Fort Peck Lake'
# and 'Ft. Peck Lake' are duplicate features in the NE data).
excluded_lakes = ['Fort Peck Lake', 'Ft. Peck Lake', 'Lake Sakakawea', 'Lake Oahe']
lakes = ne.lakes(min_area_km2=1000).cx[map_bounds[0]:map_bounds[2], map_bounds[1]:map_bounds[3]]
lakes = lakes[~lakes['name'].isin(excluded_lakes)]
lakes.to_file(geopackage_name, layer='lakes', driver='GPKG')

# US share of those lakes, for styling separately from foreign water. Clipped with the
# admin-0 US polygon (NOT us_states/conus_outline: those are lakes-version polygons with the
# Great Lakes carved out, which would delete them instead of splitting them at the border).
lakes.clip(ne.countries(include='United States of America'), keep_geom_type=True).to_file(
    geopackage_name, layer='lakes_us', driver='GPKG')

# Woodland tint across the whole frame (US + surrounding countries): EarthEnv 1km consensus
# land cover tree classes summed to percent tree cover
earthenv.treecover('output/woodland_treecover.tif', map_bounds)

rainfall_inches = prism.ppt_annual_normals_inches('output/prism_ppt_annual_inches.tif')
rainfall_classes = raster.classify_to_polygons(rainfall_inches, rainfall_breaks,
                                               smooth_sigma=2, upsample=4, sieve_pixels=64, simplify_tolerance=0.02)
rainfall_classes = rainfall_classes.clip(us_states.to_crs(rainfall_classes.crs), keep_geom_type=True)
rainfall_classes.to_file(geopackage_name, layer='rainfall_classes', driver='GPKG')

# Smoother, more generalized variant to compare against rainfall_classes
rainfall_classes_smooth = raster.classify_to_polygons(rainfall_inches, rainfall_breaks,
                                                      smooth_sigma=5, upsample=4, sieve_pixels=256, simplify_tolerance=0.02)
rainfall_classes_smooth = rainfall_classes_smooth.clip(us_states.to_crs(rainfall_classes_smooth.crs), keep_geom_type=True)
rainfall_classes_smooth.to_file(geopackage_name, layer='rainfall_classes_smooth', driver='GPKG')

# Cadillac Desert aridity classes: Marc Reisner's thresholds — under 20 in/yr is "hostile
# terrain to a farmer"; 7 in or less (Phoenix, El Paso, Reno) "arguably no place to inhabit
# at all". Same generalization recipe as rainfall_classes_smooth.
rainfall_cadillac = raster.classify_to_polygons(rainfall_inches, [7, 20],
                                                smooth_sigma=5, upsample=4, sieve_pixels=256, simplify_tolerance=0.02)
rainfall_cadillac = rainfall_cadillac.clip(us_states.to_crs(rainfall_cadillac.crs), keep_geom_type=True)
rainfall_cadillac.to_file(geopackage_name, layer='rainfall_classes_cadillac', driver='GPKG')

# The shifting 100th meridian (Seager et al. 2018, "Whither the 100th Meridian?", Earth
# Interactions 22): Powell's 1878 line vs. today's effective arid-humid divide, from
# P/PET with PRISM 1991-2020 normals and Hargreaves PET. The divide sits east of Powell's
# meridian (~98W in the central Plains); the epoch lines below show it moved WEST over the
# instrumental record (Plains wetting has outrun rising PET so far — the eastward march is
# model-projected). Segmentized so the meridian curves properly when projected.
meridian_100 = gpd.GeoDataFrame(
    {'label': ['100th meridian (Powell, 1878)']},
    geometry=[LineString([(-100, map_bounds[1]), (-100, map_bounds[3])]).segmentize(0.5)], crs='EPSG:4326')
meridian_100.to_file(geopackage_name, layer='meridian_100', driver='GPKG')

pet = aridity.hargreaves_pet_annual(prism.monthly_normals_paths('tmin'), prism.monthly_normals_paths('tmax'),
                                    'output/pet_annual_mm.tif')
aridity_path = aridity.aridity_index(prism.ppt_annual_normals_path(), pet, 'output/aridity_index.tif')

# Not a raw 0.65 iso-line (that detours around the humid Rockies high country); see
# aridity.effective_divide for the easternmost-arid-pixel formulation.
aridity.effective_divide(aridity_path).to_file(geopackage_name, layer='arid_humid_divide', driver='GPKG')

# UNEP aridity classes (World Atlas of Desertification, 1992): hyper-arid < 0.05, arid
# 0.05-0.2, semi-arid 0.2-0.5, dry subhumid 0.5-0.65, humid >= 0.65. The 0.65 edge is the
# drylands boundary behind arid_humid_divide. Same generalization recipe as the Cadillac
# classes — a handful of classes carry the story.
aridity_classes = raster.classify_to_polygons(aridity_path, [0.05, 0.2, 0.5, 0.65],
                                              smooth_sigma=5, upsample=4, sieve_pixels=256, simplify_tolerance=0.02)
aridity_classes = aridity_classes.clip(us_states.to_crs(aridity_classes.crs), keep_geom_type=True)
aridity_classes.to_file(geopackage_name, layer='aridity_classes', driver='GPKG')

# Annual water balance (P - PET) in inches: the absolute twin of the aridity ratio.
# Negative = deficit (Tucson runs ~56 inches short a year), positive = surplus.
raster.difference(prism.ppt_annual_normals_path(), pet, 'cache/water_balance_mm.tif')
raster.scale_values('cache/water_balance_mm.tif', 'output/water_balance_in.tif', 1 / prism.MM_PER_INCH)

# Classed vector bands hinged at zero, symmetric per-inch breaks so equal magnitudes get
# equal color depth on both sides; the asymmetry shows through area (11% of pixels < -40,
# 1.2% > +40). The zero boundary between the two center classes is the break-even line.
water_balance_breaks = [-40, -20, -10, -5, 0, 5, 10, 20, 40]
water_balance = raster.classify_to_polygons('output/water_balance_in.tif', water_balance_breaks,
                                            smooth_sigma=5, upsample=4, sieve_pixels=256, simplify_tolerance=0.02)
water_balance = water_balance.clip(us_states.to_crs(water_balance.crs), keep_geom_type=True)
water_balance.to_file(geopackage_name, layer='water_balance_classes', driver='GPKG')

# Brown-teal diverging ramp (BrBG-derived), hinge pair lightness-offset so the zero edge
# stays legible for CVD readers (validated: worst adjacent protan dE 10.3, hinge dE 13.7).
water_balance_colors = ['#543005', '#8c510a', '#bf812d', '#dfc27d', '#f9f0da',
                        '#7fcbbd', '#38a493', '#0d8172', '#03604f', '#003c30']
legend.options(water_balance_colors, 'output', 'legend_water_balance', breaks=water_balance_breaks,
               title='Annual water balance (inches)', font='Kumbh Sans')

# Seasonality: JAS (North American Monsoon season) share of annual precipitation — near 0
# on the winter-wet Pacific coast, approaching 0.5 in the monsoon Southwest. Denominator is
# the sum of the same twelve monthlies (not the official annual grid) so the fraction is
# self-consistent.
ppt_monthly = prism.monthly_normals_paths('ppt')
raster.total(ppt_monthly[6:9], 'cache/ppt_jas_mm.tif')
raster.total(ppt_monthly, 'cache/ppt_monthly_annual_mm.tif')
raster.ratio('cache/ppt_jas_mm.tif', 'cache/ppt_monthly_annual_mm.tif', 'output/summer_rain_fraction.tif')

# Months of surplus: how many months a year P >= PET. 0 across the desert Southwest,
# winter-only counts on the Pacific coast (the Mediterranean-climate trap), 12 in the East.
pet_monthly = aridity.hargreaves_pet_monthly(prism.monthly_normals_paths('tmin'),
                                             prism.monthly_normals_paths('tmax'), 'cache/pet_monthly')
aridity.surplus_months(ppt_monthly, pet_monthly, 'output/surplus_months.tif')

# The divide's migration: the same math over three 30-year windows of the PRISM AN 4km
# monthly time series (DIY climatologies; first run downloads ~2.4 GB of monthlies per
# epoch into $PRISM_DIR). All epochs derive from the same series and method so the lines
# are comparable; the normals-based arid_humid_divide above remains the canonical present
# line (PRISM's official product), and its 1991-2020 twin here is the one to compare
# against the earlier epochs.
epoch_divides = []
for start, end in ((1901, 1930), (1946, 1975), (1991, 2020)):
    label = f'{start}-{end}'
    tmin = prism.monthly_climatology_paths('tmin', range(start, end + 1), 'cache/climatology')
    tmax = prism.monthly_climatology_paths('tmax', range(start, end + 1), 'cache/climatology')
    ppt = prism.monthly_climatology_paths('ppt', range(start, end + 1), 'cache/climatology')
    pet = aridity.hargreaves_pet_annual(tmin, tmax, f'cache/climatology/pet_annual_{label}.tif')
    ppt_annual = raster.total(ppt, f'cache/climatology/ppt_annual_{label}.tif')
    ai = aridity.aridity_index(ppt_annual, pet, f'cache/climatology/aridity_index_{label}.tif')
    epoch_divides.append(aridity.effective_divide(ai).assign(epoch=label))
gpd.GeoDataFrame(pd.concat(epoch_divides, ignore_index=True)).to_file(
    geopackage_name, layer='arid_humid_divide_epochs', driver='GPKG')

# A century of aridity change: delta-AI between the endpoint epoch climatologies above.
# Positive = wetter since 1901-1930 (the Plains wetting that pulled the divide west),
# negative = drier. Magnitude caveats (AN series consistency, Hargreaves PET trend) are
# documented in LAYERS.md; the spatial pattern is the story.
raster.difference('cache/climatology/aridity_index_1991-2020.tif',
                  'cache/climatology/aridity_index_1901-1930.tif', 'output/aridity_change.tif')

# Legend graphics for the layout, dropped in as Picture elements at 100% scale (300 dpi,
# transparent, sized in real inches). Colors mirror the rainfall_classes symbology in the
# Pro project (first color = the <Null>/"< 5" class) — re-run if the symbology changes.
# Four style options; only the chosen one goes on the layout.
rainfall_colors = ['#c2523c', '#da7528', '#efaa11', '#f9dd07', '#c0f700',
                   '#32e300', '#0ec546', '#1ea088', '#166c8b', '#0b2c7a']
legend.options(rainfall_colors, 'output', 'legend_rainfall', breaks=rainfall_breaks,
               title='Annual precipitation (inches)', font='Kumbh Sans')

# Relief backdrops to compare: Copernicus GLO-90 hillshade vs Natural Earth manual shaded relief.
raster.clip(ne.us_manual_shaded_relief_path(), 'output/relief_ne_msr.tif', map_bounds, dst_nodata=0)

if os.environ.get('OPEN_TOPOGRAPHY_API_KEY'):
    conus_dem = dem.fetch(map_bounds, 'output/conus_cop90_dem.tif', demtype='COP90', resolution_arcsec=9)
    raster.build_overviews(conus_dem)
    hillshade.from_dem(conus_dem, 'output/relief_cop90_hillshade.tif', z_factor=3, multi_directional=True)
    raster.build_overviews('output/relief_cop90_hillshade.tif')

    # Ocean styling option B: SRTM15+ continuous topo-bathymetry, masked to the NE ocean
    # polygon so only water draws (compare against bathymetry_bands above)
    bathy_raw = dem.fetch(map_bounds, 'cache/bathy_srtm15plus_raw.tif', demtype='SRTM15Plus')
    raster.clip(bathy_raw, 'output/bathy_srtm15plus.tif', map_bounds, dst_nodata=-9999,
                cutline=geopackage_name, cutline_layer='ocean')
    raster.build_overviews('output/bathy_srtm15plus.tif')
else:
    print('OPEN_TOPOGRAPHY_API_KEY not set; skipping Copernicus GLO-90 hillshade and SRTM15+ bathymetry')
