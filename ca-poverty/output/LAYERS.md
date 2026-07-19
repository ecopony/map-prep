# ca-poverty — layer documentation

**Map**: "Poverty in California — Comparing the Far North with the rest of the state" (ArcGIS Pro; project name unknown)
**Script**: `poverty.ipynb` (commit `ce7c55f`, 2024-01-19)
**Overview**: A California county choropleth of the 2022 ACS poverty rate (percent below poverty level, 18–64), annotated with population-weighted regional rates comparing nine "Far North" counties (17.3%) against the rest of the state (11.1%). The notebook does the statistics only — it computes per-county poverty rates from `poverty.csv`, the two weighted regional rates, and a t-test — and writes no files; the choropleth itself was assembled in ArcGIS (the class breaks and regional callouts on the layout match the notebook's numbers, but the county join/symbology step is not in the repo). This `output/` holds only final exports, no ArcGIS-consumable layers.

> Entries were reconstructed from `poverty.ipynb`, `poverty.csv`, and git history on 2026-07-18, long after the outputs were created. Rationale marked *(reconstructed)* is inferred from code and the images themselves, not a firsthand record of the decisions.

## PovertyLayout.png
Final map export of the finished ArcGIS layout (not a layer): the county choropleth in 5 blue classes (6.0%–26.6%), Far North vs rest-of-state callouts, legend, scale bar, Natural Earth basemap credit. **Facts** *(extracted 2026-07-18)*: 2550x3300 px, RGBA (8.5x11 in at 300 dpi).

## poverty-data.png
- **Role**: Illustration for sharing alongside the map — a rendered table of the first five rows of the working DataFrame (FIPS, County Name, Total Population, Number under poverty, Poverty Rate). Not a map layer.
- **Source**: `poverty.csv` — U.S. Census Bureau, 2022 American Community Survey, "POVERTY STATUS IN THE PAST 12 MONTHS" (per the notebook's markdown cell), hand-prepared to 58 California counties with columns [FIPS, County Name, Total Population, Number under poverty].
- **Processing**: `poverty.ipynb` computes `Poverty Rate = Number under poverty / Total Population * 100` and shows `df.head()`; the image is a styled capture of that table (the notebook has no code that writes it).
- **Rationale** *(reconstructed)*: unknown — presumably to document the data behind the map; no code or commit message explains it.
- **Facts** *(extracted 2026-07-18)*: 1568x464 px, RGBA.

## Notes
- The notebook declares no file outputs, so nothing is "declared but missing" — but note that no county-geometry layer (shapefile/geopackage) exists in the repo; the ArcGIS join of `poverty.csv` to county boundaries is unrecorded.
- Notebook statistics (not files): Far North weighted poverty rate 17.3% (Del Norte, Siskiyou, Modoc, Humboldt, Trinity, Shasta, Lassen, Tehama, Plumas), rest-of-state 11.1%, plus a `scipy.stats.ttest_ind` comparing the two counties' rate distributions.
