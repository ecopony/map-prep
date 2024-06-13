import os
import dotenv
import pandas as pd
import geopandas as gpd
from pyproj import CRS
import plotly.graph_objects as go

dotenv.load_dotenv("../.env")

geopackage_name = 'output/acc.gpkg'

states_provinces_50m = gpd.read_file(os.path.join(os.environ['NATURAL_EARTH_DIR'], 'StatesProvinces/ne_50m_admin_1_states_provinces_lakes/ne_50m_admin_1_states_provinces_lakes.shp'))
us_states_50m = states_provinces_50m[states_provinces_50m['iso_a2'] == 'US']
us_states_50m.to_file(geopackage_name, layer='us_states_50m', driver='GPKG')

acc_schools_data = {
    "School": [
        "Clemson University", "Duke University", "Georgia Tech",
        "University of Maryland", "University of North Carolina",
        "North Carolina State University", "University of Virginia",
        "Wake Forest University", "Florida State University", 
        "University of Miami", "Virginia Tech", "Boston College", 
        "Syracuse University", "University of Pittsburgh", "University of Louisville", 
        "University of Notre Dame", "University of California, Berkeley", 
        "Southern Methodist University", "Stanford University"
    ],
    "City": [
        "Clemson, SC", "Durham, NC", "Atlanta, GA",
        "College Park, MD", "Chapel Hill, NC", "Raleigh, NC",
        "Charlottesville, VA", "Winston-Salem, NC", "Tallahassee, FL",
        "Coral Gables, FL", "Blacksburg, VA", "Chestnut Hill, MA",
        "Syracuse, NY", "Pittsburgh, PA", "Louisville, KY",
        "Notre Dame, IN", "Berkeley, CA", "Dallas, TX", "Stanford, CA"
    ],
    "Year_Joined": [
        1953, 1953, 1979, 1953, 1953, 1953, 1953, 1953, 1991,
        2004, 2004, 2005, 2013, 2013, 2014, 2013, 2024, 2024, 2024
    ],
    "Year_Left": [
        None, None, None, 2014, None, None, None, None, None,
        None, None, None, None, None, None, None, None, None, None
    ]
}

coordinates = {
    "Clemson, SC": (34.6834, -82.8374),
    "Durham, NC": (35.9993, -78.9382),
    "Atlanta, GA": (33.7490, -84.3880),
    "College Park, MD": (38.9907, -76.9378),
    "Chapel Hill, NC": (35.9132, -79.0558),
    "Raleigh, NC": (35.7796, -78.6382),
    "Charlottesville, VA": (38.0293, -78.4767),
    "Winston-Salem, NC": (36.0999, -80.2442),
    "Tallahassee, FL": (30.4383, -84.2807),
    "Coral Gables, FL": (25.7215, -80.2684),
    "Blacksburg, VA": (37.2296, -80.4139),
    "Chestnut Hill, MA": (42.3355, -71.1685),
    "Syracuse, NY": (43.0481, -76.1474),
    "Pittsburgh, PA": (40.4406, -79.9959),
    "Louisville, KY": (38.2527, -85.7585),
    "Notre Dame, IN": (41.7056, -86.2353),
    "Berkeley, CA": (37.8715, -122.2730),
    "Dallas, TX": (32.7767, -96.7970),
    "Stanford, CA": (37.4275, -122.1697)
}

acc_schools_df = pd.DataFrame(acc_schools_data)
acc_schools_df['Latitude'] = acc_schools_df['City'].map(lambda x: coordinates[x][0])
acc_schools_df['Longitude'] = acc_schools_df['City'].map(lambda x: coordinates[x][1])

acc_schools_gdf = gpd.GeoDataFrame(
    acc_schools_df, 
    geometry=gpd.points_from_xy(acc_schools_df.Longitude, acc_schools_df.Latitude),
    crs=CRS.from_epsg(4326)
)

acc_schools_1984_gdf = acc_schools_gdf[(acc_schools_gdf['Year_Joined'] <= 1984) & 
                                       ((acc_schools_gdf['Year_Left'].isna()) | (acc_schools_gdf['Year_Left'] > 1984))]
acc_schools_2024_gdf = acc_schools_gdf[(acc_schools_gdf['Year_Joined'] <= 2023) & 
                                       ((acc_schools_gdf['Year_Left'].isna()) | (acc_schools_gdf['Year_Left'] > 2024))]
acc_schools_2025_gdf = acc_schools_gdf[(acc_schools_gdf['Year_Joined'] <= 2024) & 
                                       ((acc_schools_gdf['Year_Left'].isna()) | (acc_schools_gdf['Year_Left'] > 2025))]

acc_schools_1984_gdf.to_file(geopackage_name, layer='acc_schools_1984', driver='GPKG')
acc_schools_2024_gdf.to_file(geopackage_name, layer='acc_schools_2024', driver='GPKG')
acc_schools_2025_gdf.to_file(geopackage_name, layer='acc_schools_2025', driver='GPKG')

acc_schools_1984_gdf.plot()
acc_schools_2024_gdf.plot()
acc_schools_2025_gdf.plot()

def create_convex_hull_trace(gdf, color, name):
    hull = gdf.unary_union.convex_hull
    x, y = hull.exterior.xy
    return go.Scattergeo(
        lon = list(x),
        lat = list(y),
        mode = 'lines',
        line = dict(color=color, width=2),
        name = name
    )

fig = go.Figure()

fig.add_trace(create_convex_hull_trace(acc_schools_1984_gdf, 'blue', 'ACC Footprint 1984'))
fig.add_trace(create_convex_hull_trace(acc_schools_2024_gdf, 'green', 'ACC Footprint 2024'))
fig.add_trace(create_convex_hull_trace(acc_schools_2025_gdf, 'red', 'ACC Footprint 2025'))

fig.update_layout(
    title = 'ACC Conference Footprints for 1984, 2024, and 2025',
    geo = dict(
        scope = 'usa',
        projection = dict(type = 'albers usa'),
        showland = True,
    )
)

fig.show()
