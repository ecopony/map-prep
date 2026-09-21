"""Biome-stack transect: Tucson to Mount Lemmon, sampled from the project DEM.

Run after main.py (`uv run transect.py`); depends only on output/dem_cop90_aea.tif.
Writes the profile as CSV (distance, lon/lat, elevation, biome), the line as a GeoPackage
layer so it can be drawn on the map, and an editable SVG of the profile with the biome
bands as horizontal strata - the margin diagram the brief asks for in section 3.

Band elevations follow Whittaker & Niering's Santa Catalina gradient (1965, Ecology 46)
rounded to the nearest 50 m; they are approximate, vary with aspect, and are drawn as flat
lines for the diagram. The 1,600 m shoreline (Deyo) falls inside the oak-woodland band,
which is the point: the "sea" ends where the woodland begins.
"""
import csv
import numpy as np
import rasterio
import geopandas as gpd
from shapely.geometry import LineString, Point

dem_path = 'output/dem_cop90_aea.tif'
geopackage_name = 'output/sky-islands.gpkg'
start = ('Tucson', -110.9747, 32.2226)          # downtown
end = ('Mount Lemmon', -110.7883, 32.4433)      # summit, 2,791 m
step_m = 90
shoreline_m = 1600

# (lower bound m, name, latitude-equivalent caption)
bands = [
    (0,    'Sonoran desertscrub',  'Sonora'),
    (1200, 'Desert grassland',     'Chihuahua / New Mexico'),
    (1500, 'Madrean oak woodland', 'Sierra Madre'),
    (1950, 'Pine-oak woodland',    'Southern Rockies'),
    (2200, 'Ponderosa pine forest','Colorado'),
    (2500, 'Mixed-conifer forest', 'Canadian border'),
]

with rasterio.open(dem_path) as dem:
    crs_aea = dem.crs
    line_ll = gpd.GeoSeries([LineString([start[1:], end[1:]])], crs='EPSG:4326')
    line = line_ll.to_crs(crs_aea).iloc[0]
    n = int(line.length // step_m) + 1
    dists = np.linspace(0, line.length, n)
    pts = [line.interpolate(d) for d in dists]
    elev = np.array([v[0] for v in dem.sample([(p.x, p.y) for p in pts])], dtype=float)
    elev[elev == dem.nodata] = np.nan
ll = gpd.GeoSeries(pts, crs=crs_aea).to_crs('EPSG:4326')

def biome(z):
    return next(name for lo, name, _ in reversed(bands) if z >= lo)

with open('output/transect_catalina.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['distance_km', 'lon', 'lat', 'elev_m', 'biome'])
    for d, p, z in zip(dists, ll, elev):
        w.writerow([f'{d / 1000:.3f}', f'{p.x:.5f}', f'{p.y:.5f}', f'{z:.0f}', biome(z)])

gpd.GeoDataFrame({'name': [f'{start[0]} – {end[0]} transect'], 'length_km': [line.length / 1000]},
                 geometry=[line_ll.iloc[0]], crs='EPSG:4326').to_file(geopackage_name, layer='transect', driver='GPKG')

# --- SVG ---------------------------------------------------------------------------------
W, H = 720, 360
ml, mr, mt, mb = 60, 150, 30, 44          # margins: right one holds band labels
z0, z1 = 500, 3000
km = dists / 1000
def X(k): return ml + (W - ml - mr) * k / km[-1]
def Y(z): return mt + (H - mt - mb) * (z1 - z) / (z1 - z0)
# Blues sampled from the layout's sea ramp and ocean (2026-09-20; the panel sits in the
# furniture, so it takes the water palette rather than the islands' greens).
# 2026-09-20: sea blues below the shoreline, island greens (sampled from the styled
# islands, #cdd4bd flat fill to #97a175 in shade) above it - the panel shows the map's
# own two colours meaning the same two things.
band_fill = ['#d6e6ee', '#bdd9e5', '#cdd4bd', '#b5bf9d', '#97a175', '#7a875c']
ink = '#4f7590'          # text and profile stroke
ink_light = '#7fa0b4'    # captions, axis
profile = ' '.join(f'{X(k):.1f},{Y(z):.1f}' for k, z in zip(km, elev))
closed = f'{X(0):.1f},{Y(z0):.1f} {profile} {X(km[-1]):.1f},{Y(z0):.1f}'
s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
     f'font-family="Georgia, serif" font-size="12" fill="{ink}">',
     '<defs><clipPath id="mtn"><polygon points="%s"/></clipPath></defs>' % closed]
# strata clipped to the mountain silhouette
for i, (lo, name, lat) in enumerate(bands):
    hi = bands[i + 1][0] if i + 1 < len(bands) else z1
    s.append(f'<rect x="{ml}" y="{Y(hi):.1f}" width="{W - ml - mr}" height="{Y(lo) - Y(hi):.1f}" '
             f'fill="{band_fill[i]}" clip-path="url(#mtn)"/>')
s.append(f'<polyline points="{profile}" fill="none" stroke="{ink}" stroke-width="1.2"/>')
s.append(f'<line x1="{ml}" x2="{W - mr}" y1="{Y(shoreline_m):.1f}" y2="{Y(shoreline_m):.1f}" '
         f'stroke="{ink}" stroke-width="1" stroke-dasharray="4 3"/>')
s.append(f'<text x="{ml + 4}" y="{Y(shoreline_m) - 4:.1f}" font-size="10" font-style="italic" fill="{ink}">'
         f'shoreline 1,600 m — the island begins</text>')
# band labels on the right, with latitude equivalents
for i, (lo, name, lat) in enumerate(bands):
    hi = bands[i + 1][0] if i + 1 < len(bands) else z1
    ym = (Y(lo) + Y(max(hi, lo + 1))) / 2
    s.append(f'<line x1="{W - mr + 2}" x2="{W - mr + 8}" y1="{Y(lo):.1f}" y2="{Y(lo):.1f}" stroke="{ink_light}"/>')
    s.append(f'<text x="{W - mr + 12}" y="{ym + 4:.1f}">{name}</text>')
    # latitude-equivalent captions dropped 2026-09-20: no room at the size the panel sits on the sheet
# elevation axis
for z in range(1000, z1 + 1, 500):
    s.append(f'<line x1="{ml - 5}" x2="{ml}" y1="{Y(z):.1f}" y2="{Y(z):.1f}" stroke="{ink_light}"/>')
    s.append(f'<text x="{ml - 8}" y="{Y(z) + 4:.1f}" text-anchor="end" font-size="10">{z:,} m</text>')
s.append(f'<line x1="{ml}" x2="{ml}" y1="{mt}" y2="{Y(z0):.1f}" stroke="{ink_light}"/>')
# endpoints
s.append(f'<text x="{X(0):.1f}" y="{H - 14}" text-anchor="start">{start[0]}, {elev[0]:.0f} m</text>')
s.append(f'<text x="{X(km[-1]):.1f}" y="{H - 14}" text-anchor="end">{end[0]}, {np.nanmax(elev):.0f} m</text>')
s.append(f'<text x="{(X(0) + X(km[-1])) / 2:.1f}" y="{H - 14}" text-anchor="middle" font-size="10" fill="{ink}">'
         f'{km[-1]:.0f} km, vertical exaggeration {((H - mt - mb) / (z1 - z0)) / ((W - ml - mr) / (km[-1] * 1000)):.0f}×</text>')
s.append('</svg>')
open('output/transect_catalina.svg', 'w', encoding='utf-8').write('\n'.join(s))
print(f'{n} samples over {km[-1]:.1f} km, {np.nanmin(elev):.0f}–{np.nanmax(elev):.0f} m; '
      f'shoreline crossed at {km[np.argmax(elev >= shoreline_m)]:.1f} km')
for lo, name, _ in bands:
    k = km[elev >= lo]
    print(f'  {lo:>5} m  {name:24} first reached at {k[0]:.1f} km' if len(k) else f'  {lo:>5} m  {name:24} not reached')
