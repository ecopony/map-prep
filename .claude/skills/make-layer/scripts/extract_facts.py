"""Print markdown Facts lines for every raster/geopackage in an output directory.

Usage (from a project directory):
    uv run python ../../.claude/skills/make-layer/scripts/extract_facts.py output

Paste the emitted lines into the Facts field of each entry in output/LAYERS.md.
"""
import os
import sys
from datetime import date

import pyogrio
import rasterio


def describe_raster(path):
    size_mb = os.path.getsize(path) / 1e6
    with rasterio.open(path) as src:
        res = src.res[0]
        unit = 'deg' if src.crs and src.crs.is_geographic else 'units'
        bounds = ', '.join(f'{b:.4f}' for b in src.bounds)
        overviews = src.overviews(1)
        return (f'{src.crs}, {src.width}x{src.height} px @ {res:g} {unit}, '
                f'bounds ({bounds}), {src.dtypes[0]}, nodata={src.nodata}, '
                f'overviews {overviews or "none"}, '
                f'{src.profile.get("compress") or "uncompressed"}, {size_mb:.1f} MB')


def describe_gpkg_layer(path, layer):
    info = pyogrio.read_info(path, layer=layer)
    fields = list(info['fields'])
    shown = ', '.join(fields[:8]) + (f', ... ({len(fields)} total)' if len(fields) > 8 else '')
    return (f'{info["crs"]}, {info["geometry_type"]}, {info["features"]} features, '
            f'fields [{shown}]')


def main(output_dir):
    today = date.today().isoformat()
    for name in sorted(os.listdir(output_dir)):
        path = os.path.join(output_dir, name)
        if name.endswith('.tif'):
            print(f'## {name}')
            print(f'- **Facts** *(extracted {today})*: {describe_raster(path)}\n')
        elif name.endswith('.gpkg'):
            print(f'## {name} ({os.path.getsize(path) / 1e6:.1f} MB)')
            for layer, _ in pyogrio.list_layers(path):
                print(f'### {layer}')
                print(f'- **Facts** *(extracted {today})*: {describe_gpkg_layer(path, layer)}\n')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'output')
