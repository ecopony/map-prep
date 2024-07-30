import os
import dotenv
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from simplification.cutil import simplify_coords
from shapely.geometry import Polygon, MultiPolygon

def simplify_geometry(geometry, tolerance):
    def ensure_valid_polygon(coords):
        if len(coords) < 4:
            return None
        return Polygon(coords)

    if geometry.geom_type == 'Polygon':
        simplified_coords = simplify_coords(geometry.exterior.coords, tolerance)
        return ensure_valid_polygon(simplified_coords)
    elif geometry.geom_type == 'MultiPolygon':
        simplified_polygons = []
        for polygon in geometry.geoms:
            simplified_coords = simplify_coords(polygon.exterior.coords, tolerance)
            simplified_polygon = ensure_valid_polygon(simplified_coords)
            if simplified_polygon:
                simplified_polygons.append(simplified_polygon)
        return MultiPolygon(simplified_polygons) if simplified_polygons else None

dotenv.load_dotenv("./../.env")

geopackage_name = 'output/stylized-pdx.gpkg'

pdx_boundary = gpd.read_file(os.path.join(os.environ['TNM_DIR'], 'OR/GOVTUNIT_Oregon_State_GPKG/GOVTUNIT_Oregon_State_GPKG.gpkg'),
                            layer='GU_IncorporatedPlace',
                            where="place_name = 'Portland' or place_name = 'Maywood Park'"
                         )
pdx_boundary = pdx_boundary.to_crs('EPSG:4326')
pdx_boundary = pdx_boundary.dissolve()
pdx_boundary.plot()
pdx_boundary.to_file(geopackage_name, layer='pdx_boundary', driver='GPKG')


tolerance = 0.0025
pdx_boundary['geometry'] = pdx_boundary['geometry'].apply(lambda geom: simplify_geometry(geom, tolerance))
simplified_pdx_boundary = gpd.GeoDataFrame(pdx_boundary, geometry=pdx_boundary['geometry'])
simplified_pdx_boundary = simplified_pdx_boundary.set_crs('EPSG:4326')
simplified_pdx_boundary.plot()


if pdx_boundary.crs is None:
    pdx_boundary = pdx_boundary.set_crs('EPSG:4326')
pdx_boundary = pdx_boundary.to_crs('EPSG:3857')
pdx_centroid = pdx_boundary.centroid
centroid_point = pdx_centroid.geometry[0]
pdx_radius = 25000
pdx_circle = centroid_point.buffer(pdx_radius)
pdx_circle_gdf = gpd.GeoDataFrame(geometry=[pdx_circle], crs='EPSG:3857')
pdx_circle_gdf = pdx_circle_gdf.to_crs('EPSG:4326')
pdx_circle_gdf.plot()
pdx_circle_gdf.to_file(geopackage_name, layer='pdx_circle', driver='GPKG')
pdx_boundary = pdx_boundary.to_crs('EPSG:4326')


or_roads = gpd.read_file(os.path.join(os.environ['TNM_DIR'], 'OR/TRAN_Oregon_State_GPKG/TRAN_Oregon_State_GPKG.gpkg'),
                            layer='Trans_RoadSegment',
                            mask=pdx_circle_gdf
                         )
or_roads = or_roads.to_crs('EPSG:4326')
or_roads_clip = gpd.clip(or_roads, pdx_circle_gdf)
or_roads_clip.plot()


wa_roads = gpd.read_file(os.path.join(os.environ['TNM_DIR'], 'WA/TRAN_Washington_State_GPKG/TRAN_Washington_State_GPKG.gpkg'),
                            layer='Trans_RoadSegment',
                            mask=pdx_circle_gdf
                        )
wa_roads = wa_roads.to_crs('EPSG:4326')
wa_roads_clip = gpd.clip(wa_roads, pdx_circle_gdf)
wa_roads_clip.plot()


all_roads = gpd.GeoDataFrame(pd.concat([or_roads_clip, wa_roads_clip], ignore_index=True))
all_roads.plot()  
all_roads.to_file(geopackage_name, layer='all_roads', driver='GPKG')


nhd_rivers_path = os.path.join(os.environ['NHD_DIR'], 'OR/NHD_H_Oregon_State_GDB/NHD_H_Oregon_State_GDB.gdb')
nhd_area = gpd.read_file(nhd_rivers_path, layer='NHDArea', mask=pdx_circle_gdf)
nhd_area = nhd_area.to_crs('EPSG:4326')
nhd_area_clip = gpd.clip(nhd_area, pdx_circle_gdf)
nhd_area_clip.plot()


nhd_waterbodies_path = os.path.join(os.environ['NHD_DIR'], 'OR/NHD_H_Oregon_State_GDB/NHD_H_Oregon_State_GDB.gdb')
nhd_waterbodies = gpd.read_file(nhd_waterbodies_path, 
                                layer='NHDWaterbody', 
                                where="FType = 390 AND AREASQKM > 0.248",
                                mask=pdx_circle_gdf)
nhd_waterbodies = nhd_waterbodies.to_crs('EPSG:4326')
nhd_waterbodies_clip = gpd.clip(nhd_waterbodies, pdx_circle_gdf)
nhd_waterbodies_clip.plot()


pdx_circle_gdf = pdx_circle_gdf.reset_index(drop=True)
pdx_boundary = pdx_boundary.reset_index(drop=True)
nhd_area_clip = nhd_area_clip.reset_index(drop=True)
nhd_waterbodies_clip = nhd_waterbodies_clip.reset_index(drop=True)

pdx_mask = pdx_circle_gdf.geometry.difference(pdx_boundary.unary_union).difference(nhd_area_clip.unary_union).difference(nhd_waterbodies_clip.unary_union)  
pdx_mask_gdf = gpd.GeoDataFrame(geometry=pdx_mask, crs=pdx_circle_gdf.crs)
pdx_mask_gdf.plot()


# Create a plot that is 10" wide and 12" tall
fig, ax = plt.subplots(figsize=(10, 12))
ax.axis('off')

# Circular layout frame
pdx_circle_gdf.plot(ax=ax, color='white', edgecolor='black', linewidth=1, zorder=0)

# Freeways
all_roads[all_roads['tnmfrc'].isin([1, 8])].plot(ax=ax, color='#828282', linewidth=1, zorder=3)

# Arterial
all_roads[all_roads['tnmfrc'].isin([2, 3])].plot(ax=ax, color='#828282', linewidth=.6, zorder=3)

# Collectors
all_roads[all_roads['tnmfrc'].isin([4, 5])].plot(ax=ax, color='#B2B2B2', linewidth=.3, zorder=3)

# Portland's boundary
pdx_boundary.plot(ax=ax, color='#E1E1E1', linewidth=0, alpha=0.5, zorder=1)

# Water
nhd_area_clip.plot(ax=ax, color='#004C73', linewidth=0.5, zorder=2)
nhd_waterbodies_clip.plot(ax=ax, color='#004C73', linewidth=0.5, zorder=2)

# Mask
pdx_mask_gdf.plot(ax=ax, color='white', alpha=.8, edgecolor='black', linewidth=0.1, zorder=4)

fig.text(0.5, 0.075, 'portland, oregon', ha='center', fontsize=20, fontfamily='Arial', fontweight='bold', color='gray')
fig.text(0.5, 0.01, 'Map created by Edward Copony', ha='center', fontsize=6, fontfamily='Arial', color='grey', alpha=0.5)

plt.show()


