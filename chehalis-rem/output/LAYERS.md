# chehalis-rem — layer documentation

**Map**: unknown (no ArcGIS Pro project name recorded anywhere in the repo)
**Script**: none — no `main.py` or any other file exists in this project, and `git log` (including `--follow` and `--all`) shows the directory was never committed
**Overview**: A relative elevation model (REM) project directory, presumably for the Chehalis River (WA), that today contains **no files at all** — only empty directories. The layout (`input/`, `output/rem-maker/`, `.osm_cache/`, `.cache/`) matches the sibling `carson-rem` project, whose `main.py` feeds a DEM at `input/merged-dem.tif` to `riverrem.REMMaker(out_dir='output/rem-maker')` and calls `make_rem()` / `make_rem_viz()`. This project was therefore *likely produced similarly to carson-rem*, but that is an analogy from the directory layout, not a fact: no script, DEM, REM raster, or visualization survives here.

> Entries were reconstructed on 2026-07-18, long after the directory was created and after all of its contents were removed. Nothing below comes from a firsthand record; everything marked *(reconstructed)* is inferred from the empty directory layout, filesystem timestamps, and analogy to `carson-rem`. No generating script exists in the repo.

## Directory inventory (no layers exist)

There are no `.tif`, `.gpkg`, `.png`, or any other files to document. `extract_facts.py` was run against `output/` on 2026-07-18 and found nothing. What exists:

```
chehalis-rem/
  .cache/                          (empty; dir dated 2024-11-29)
  .osm_cache/                      (empty; dir dated 2025-09-02)
  input/                           (empty; dir dated 2025-09-02)
  output/                          (dir dated 2024-10-18)
    rem-maker/                     (dir dated 2024-11-29)
      colorado-delta/              (empty)
      colorado-moab/               (empty)
      colorado-texas/              (empty)
      deschutes/                   (empty)
      deschutes-combined/          (empty)
      deschutes-img/               (empty)
      deschutes-north/             (empty)
      rogue/                       (empty)
      shenandoah-north-fork/       (empty)
      snake-tetons/                (empty)
```

- **Role** *(reconstructed)*: The `output/rem-maker/` subdirectory names show this directory was used as a working area for REMs of **many rivers** — three Colorado River reaches (delta, Moab, Texas), four Deschutes variants, the Rogue, the Shenandoah North Fork, and the Snake near the Tetons — despite the `chehalis-rem` name. Whether a Chehalis REM was ever produced here is unknown.
- **Source** *(reconstructed)*: unknown. By analogy to `carson-rem`, the input would have been a merged DEM in `input/` and river centerlines fetched from OpenStreetMap by riverrem (the empty `.osm_cache/` is consistent with the repo-wide OSM caching pattern), but no input data remains.
- **Processing** *(reconstructed)*: unknown. Likely `riverrem.REMMaker` (`make_rem()` + `make_rem_viz()`), as in `carson-rem/main.py`, given the identical `output/rem-maker/` convention; per-river subdirectories suggest `out_dir` was pointed at a different subfolder per run. No script confirms this.
- **Rationale**: unknown. No script, commit message, comment, or output survives to reconstruct from.
- **Facts**: not extracted — no raster or vector files exist in the project.
- **History**: The project has zero git history; everything here was always untracked (the repo's `.gitignore` ignores `output/**` except `.png`, and no `.png` was ever committed). Directory timestamps suggest activity from October–November 2024, with the surviving subdirectories emptied (contents deleted or moved out of the repo) around 2025-09-02.
