"""Line helpers for effects ArcGIS Pro cannot symbolize directly."""
import geopandas as gpd
import numpy as np
from scipy import ndimage
from shapely.geometry import LineString, Point
from shapely.ops import linemerge, substring


def faded_dashes(line, solid_area, crs, dash=40_000, gap=25_000, fade=400_000):
    """Cut a line into one feature per dash, fading out beyond an area.

    ArcGIS Pro cannot run a gradient along a line (its gradient stroke runs across the
    width), so the fade is carried in the data: each dash is its own feature with an
    `opacity` attribute (percent) to drive transparency-by-attribute on a plain solid
    stroke. Dashes are cut here rather than with a Pro dash effect because a dash effect
    restarts on every feature.

    Dashes inside `solid_area` are fully opaque. Beyond where the line leaves the area,
    opacity eases (smoothstep) to zero over `fade`; dashes that round to zero are dropped.

    line: GeoDataFrame/GeoSeries holding a single LineString.
    solid_area: GeoDataFrame/GeoSeries of polygons the line stays solid within.
    crs: projected CRS to measure in — use the map frame's, so dashes are even on the page.
    dash, gap, fade: lengths in `crs` units.

    Returns a GeoDataFrame in `crs` with fields `zone` ('before'/'inside'/'after', in the
    line's drawing direction), `opacity` and `transparency` (integer percent, summing to 100).
    """
    geometry = line.to_crs(crs).geometry.iloc[0]
    area = solid_area.to_crs(crs).geometry.union_all()

    # Extent of the solid stretch as distances along the line. Using the outermost
    # crossings keeps the line solid across any gaps in the area (lakes, river meanders).
    inside = geometry.intersection(area)
    if inside.is_empty:
        raise ValueError('line does not cross solid_area')
    parts = getattr(inside, 'geoms', [inside])
    crossings = [geometry.project(Point(xy)) for part in parts for xy in part.coords]
    solid_start, solid_end = min(crossings), max(crossings)

    rows = []
    start = max(0.0, solid_start - fade)
    end = min(geometry.length, solid_end + fade)
    while start < end:
        stop = min(start + dash, end)
        middle = (start + stop) / 2
        beyond = max(solid_start - middle, middle - solid_end, 0.0)
        t = min(beyond / fade, 1.0)
        opacity = round(100 * (1 - t * t * (3 - 2 * t)))
        if opacity > 0:
            zone = 'before' if middle < solid_start else 'after' if middle > solid_end else 'inside'
            rows.append({'zone': zone, 'opacity': opacity, 'transparency': 100 - opacity,
                         'geometry': substring(geometry, start, stop)})
        start += dash + gap
    return gpd.GeoDataFrame(rows, geometry='geometry', crs=crs)


def shared_boundary(a, b, crs):
    """The boundary two sets of polygons share, as one feature per connected line.

    For pulling a single class edge out of classed polygons (e.g. the zero line between
    the deficit and surplus classes) so it can be drawn as its own line and still sit
    exactly on the color edge. Edges either set has with anything else — coastlines,
    borders — are not part of the result.

    a, b: GeoDataFrames/GeoSeries of polygons in the same CRS.
    crs: projected CRS to measure in.

    Returns a GeoDataFrame in the inputs' CRS with `length_km` and `closed` (True for a
    ring, i.e. an island of one set inside the other), longest first.
    """
    shared = a.geometry.union_all().boundary.intersection(b.geometry.union_all().boundary)
    merged = shared if shared.geom_type == 'LineString' else linemerge(shared)
    pieces = [g for g in getattr(merged, 'geoms', [merged]) if g.geom_type == 'LineString']
    out = gpd.GeoDataFrame(geometry=pieces, crs=a.crs)
    out['length_km'] = (out.to_crs(crs).length / 1000).round(1)
    out['closed'] = [g.is_ring for g in pieces]
    return out.sort_values('length_km', ascending=False, ignore_index=True)


def north_south_average(line, step=0.05, smooth=1.5, extend=0.0):
    """Generalize a wandering, roughly north-south line into one smooth curve that can be
    drawn like a meridian.

    At each latitude the line's crossings are averaged to a single longitude (so
    switchbacks and bulges collapse to their middle), and that longitude series is
    gaussian-smoothed along latitude. The result has one longitude per latitude.

    line: GeoDataFrame/GeoSeries holding a single LineString, in a geographic CRS.
    step: latitude spacing of the result, degrees.
    smooth: gaussian sigma along latitude, degrees — the generalization knob.
    extend: degrees of latitude to run past each end, continuing the end direction in a
        straight line. Gives faded_dashes something to fade out along.

    Returns a GeoDataFrame in the same CRS with one LineString, south to north.
    """
    geometry = line.geometry.iloc[0]
    west, south, east, north = geometry.bounds
    lats, lons = [], []
    for lat in np.arange(south + step / 2, north, step):
        hits = geometry.intersection(LineString([(west - 1, lat), (east + 1, lat)]))
        xs = [p.x for p in getattr(hits, 'geoms', [hits]) if p.geom_type == 'Point']
        if xs:
            lats.append(lat)
            lons.append(sum(xs) / len(xs))
    lats, lons = np.array(lats), np.array(lons)
    if smooth:
        lons = ndimage.gaussian_filter1d(lons, smooth / step, mode='nearest')
    if extend:
        # End direction from a straight fit over the last `smooth` degrees at each end
        n = max(2, int(round(max(smooth, step * 2) / step)))
        steps = np.arange(step, extend + step / 2, step)
        south_slope = np.polyfit(lats[:n], lons[:n], 1)[0]
        north_slope = np.polyfit(lats[-n:], lons[-n:], 1)[0]
        lons = np.concatenate([lons[0] - south_slope * steps[::-1], lons, lons[-1] + north_slope * steps])
        lats = np.concatenate([lats[0] - steps[::-1], lats, lats[-1] + steps])
    return gpd.GeoDataFrame(geometry=[LineString(np.column_stack([lons, lats]))], crs=line.crs)
