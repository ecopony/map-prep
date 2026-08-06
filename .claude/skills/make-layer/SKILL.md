---
name: make-layer
description: Use whenever creating, regenerating, or modifying map layers in any project's output/ directory. Does the geospatial processing AND documents each layer's provenance, processing chain, and rationale in output/LAYERS.md so map-planning sessions elsewhere can understand the layers, not just see the files.
---

# Make Layer

Output layers here are consumed by ArcGIS Pro *and* by Claude sessions running in the user's map-planning directory. Those sessions can only see files — `output/LAYERS.md` is how they learn what each layer is, how it was made, and why. Documentation is part of the deliverable: a layer isn't done until its entry exists.

## Workflow

1. Do the processing work as usual (edit the project's `main.py`, run with `uv run main.py` from the project directory).
2. Extract technical facts from the files just written (run from the project directory):

   ```
   uv run python ../../.claude/skills/make-layer/scripts/extract_facts.py output
   ```

3. Create or update `output/LAYERS.md` using the template below. One entry per output file; a geopackage gets one sub-entry per internal layer.
4. If this is the project's first `LAYERS.md`, move the project from "Not yet documented" to "Documented projects" in `CATALOG.md` at the repo root, with a one-line summary.

## Writing the entries

Each entry mixes two kinds of content — keep them straight:

- **Facts** (CRS, resolution, extent, dtype, nodata, feature counts, fields): always paste from the extract script, never hand-written or from memory. Re-extract after regenerating a layer so they never drift from the file.
- **Context** (role, source, processing, rationale): written from what actually happened in the conversation. The rationale line is the whole point of this file — record decisions *as they are made*: why this dataset over the alternative, why these parameter values, what was tried and rejected and why. If documenting a pre-existing layer whose creation you weren't part of, reconstruct what you can from code and comments and mark it *(reconstructed)* — never invent rationale.

Update semantics:

- Regenerating a layer with changed parameters updates its **Processing** and **Facts** and *appends* to **Rationale** (the history of changes is valuable — "raised sieve_pixels 64→256 because small speckles survived at layout scale").
- Deleting an output file deletes its entry.
- Date the Facts line and any appended rationale, not just the file header.

## Entry template

```markdown
# <project> — layer documentation

**Map**: <which map this feeds; ArcGIS Pro project name>
**Script**: `main.py` (<commit or branch>, <date>)
**Overview**: 2–4 sentences on the map's goal and how the layers fit together —
draw order, blend modes, which layers are alternatives to compare vs finals.

## <file.tif>
- **Role**: cartographic purpose, one or two sentences
- **Source**: dataset name; where it lives (env-var path, or API + cache dir); vintage/license if known
- **Processing**: chain from source to this file, with the parameters that mattered and a code pointer (e.g. `mapprep/raster.py` `classify_to_polygons`)
- **Rationale**: why this approach/dataset/parameters; alternatives tried and rejected
- **Facts** *(extracted <date>)*: paste from extract_facts.py

## <file.gpkg>
### <layer_name>
Same fields; Facts come from the geopackage section of extract_facts.py.
```
