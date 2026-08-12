import os
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
