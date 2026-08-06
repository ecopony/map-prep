"""Standalone map-legend images for ArcGIS Pro layouts.

ArcGIS Pro's Legend element is tedious to style; instead, render the legend as a
transparent PNG and drop it into the layout as a Picture element. Figure sizes are
in real inches at the given dpi, so a legend inserted at 100% scale prints at the
size specified here.

Two labeling modes:
- ``labels``: one label per color, centered on its swatch (categorical or
  pre-formatted class labels).
- ``breaks``: len(colors) - 1 boundary values; labels sit at class boundaries the
  way classed choropleth/isarithmic legends are usually read. Class ranges that
  fall off the ends are implied ("< first", "> last").
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
from matplotlib.patches import Rectangle

_INK = '#3d3d3d'          # label ink: neutral, never a data color
_EDGE = (0, 0, 0, 0.18)   # hairline swatch outline so pale colors hold shape on any backdrop

STYLES = ('stacked', 'ramp', 'bar', 'blocks')


def _class_labels(breaks, fmt):
    """Per-class range labels from boundary values: '< 5', '5-10', ..., '> 100'."""
    f = lambda v: fmt.format(v)
    inner = [f'{f(lo)}–{f(hi)}' for lo, hi in zip(breaks[:-1], breaks[1:])]
    return [f'< {f(breaks[0])}'] + inner + [f'> {f(breaks[-1])}']


def render(colors, out_path, *, labels=None, breaks=None, title=None, style='stacked',
           swatch_w=0.24, swatch_h=0.17, gap=0.05, fontsize=8.5, title_fontsize=10,
           font=None, ink=_INK, edge=_EDGE, number_format='{:g}', dpi=300,
           ascending=False):
    """Write a transparent-PNG legend and return out_path.

    colors: swatch fills, in data order (low to high for classed data).
    labels/breaks: exactly one must be given; breaks needs len(colors) - 1 values.
    style: 'stacked' (vertical swatches, label right), 'ramp' (contiguous vertical
        column, labels at boundaries), 'bar' (contiguous horizontal, labels below
        boundaries), 'blocks' (separate horizontal blocks, labels below).
    ascending: vertical styles run low-at-top when True; default puts high values
        on top, the usual convention for quantity legends.
    swatch_w/swatch_h/gap: inches per swatch. 'ramp' and 'bar' ignore gap.
    number_format: applied to break values ('{:g}' drops trailing zeros).
    """
    if (labels is None) == (breaks is None):
        raise ValueError('provide exactly one of labels or breaks')
    if breaks is not None and len(breaks) != len(colors) - 1:
        raise ValueError(f'need {len(colors) - 1} breaks for {len(colors)} colors, got {len(breaks)}')
    if labels is not None and len(labels) != len(colors):
        raise ValueError(f'need {len(labels)} == {len(colors)} labels')
    if style not in STYLES:
        raise ValueError(f'style must be one of {STYLES}')

    n = len(colors)
    text_kw = {'color': ink, 'fontsize': fontsize}
    if font:
        text_kw['fontname'] = font

    # Generous canvas; the save step below trims to the measured extent of what was drawn.
    fig = plt.figure(figsize=(max(8, n * (swatch_w + gap) + 2), max(4, n * (swatch_h + gap) + 1)))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, fig.get_figwidth())
    ax.set_ylim(0, fig.get_figheight())
    ax.set_axis_off()
    ax.set_aspect('equal')

    renderer = fig.canvas.get_renderer()
    to_inches = fig.dpi_scale_trans.inverted()

    def text_width(s, **kw):
        t = ax.text(0, 0, s, **kw)
        w = t.get_window_extent(renderer).transformed(to_inches).width
        t.remove()
        return w

    vertical = style in ('stacked', 'ramp')
    col = list(colors) if (ascending or not vertical) else list(colors)[::-1]
    if style == 'blocks':
        # Blocks carry their label beneath them: never narrower than the label
        all_labs = labels if labels is not None else _class_labels(breaks, number_format)
        swatch_w = max([swatch_w] + [text_width(lab, **text_kw) + 0.06 for lab in all_labs])
    step_h = swatch_h + (gap if style == 'stacked' else 0)
    step_w = swatch_w + (gap if style == 'blocks' else 0)
    top = n * step_h - (gap if style == 'stacked' else 0)

    def swatch(x, y, w, h, c):
        ax.add_patch(Rectangle((x, y), w, h, facecolor=c, edgecolor=edge, linewidth=0.6))

    if vertical:
        for i, c in enumerate(col):
            swatch(0.5, top - i * step_h - swatch_h, swatch_w, swatch_h, c)
        if style == 'stacked':
            labs = labels if labels is not None else _class_labels(breaks, number_format)
            labs = labs if ascending else labs[::-1]
            for i, lab in enumerate(labs):
                ax.text(0.5 + swatch_w + 0.07, top - i * step_h - swatch_h / 2, lab,
                        va='center', ha='left', **text_kw)
        else:  # ramp: boundary labels between contiguous swatches
            vals = labels[1:-1] if labels is not None else [number_format.format(b) for b in breaks]
            vals = vals if ascending else vals[::-1]
            for i, lab in enumerate(vals):
                y = top - (i + 1) * swatch_h
                ax.plot([0.5 + swatch_w, 0.5 + swatch_w + 0.05], [y, y],
                        color=ink, linewidth=0.6, solid_capstyle='butt')
                ax.text(0.5 + swatch_w + 0.1, y, lab, va='center', ha='left', **text_kw)
        title_xy, title_ha = (0.5, top + 0.14), 'left'
    else:
        base_y = 0.5
        for i, c in enumerate(col):
            swatch(0.5 + i * step_w, base_y, swatch_w, swatch_h, c)
        if style == 'blocks':
            labs = labels if labels is not None else _class_labels(breaks, number_format)
            for i, lab in enumerate(labs):
                ax.text(0.5 + i * step_w + swatch_w / 2, base_y - 0.06, lab,
                        va='top', ha='center', **text_kw)
        else:  # bar: boundary labels under the seams
            vals = labels[1:-1] if labels is not None else [number_format.format(b) for b in breaks]
            for i, lab in enumerate(vals):
                x = 0.5 + (i + 1) * swatch_w
                ax.plot([x, x], [base_y - 0.05, base_y], color=ink, linewidth=0.6,
                        solid_capstyle='butt')
                ax.text(x, base_y - 0.09, lab, va='top', ha='center', **text_kw)
        title_xy, title_ha = (0.5, base_y + swatch_h + 0.12), 'left'

    if title:
        tkw = dict(text_kw, fontsize=title_fontsize)
        ax.text(*title_xy, title, va='bottom', ha=title_ha, **tkw)

    # Trim to what was actually drawn (the axes spans the whole scratch canvas, so
    # bbox_inches='tight' alone would keep all the empty space).
    artists = ax.patches + ax.lines + ax.texts
    content = mtransforms.Bbox.union([a.get_window_extent(renderer) for a in artists])
    content = content.transformed(to_inches)
    pad = 0.04
    crop = mtransforms.Bbox.from_extents(content.x0 - pad, content.y0 - pad,
                                         content.x1 + pad, content.y1 + pad)
    fig.savefig(out_path, dpi=dpi, transparent=True, bbox_inches=crop)
    plt.close(fig)
    return out_path


def options(colors, out_dir, basename, **kwargs):
    """Render every style as '<out_dir>/<basename>_<style>.png'; returns the paths."""
    import os
    return [render(colors, os.path.join(out_dir, f'{basename}_{s}.png'), style=s, **kwargs)
            for s in STYLES]
