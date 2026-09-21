---
name: style
description: Save and retrieve ArcGIS Pro layer styling recipes so the user never has to reopen an old project to remember how a layer was styled. Use when the user says "save style", "retrieve style", "how did I style X", "style reference", or describes a symbology treatment they want to keep. Styles live in shared/styles/ (tracked in git).
---

# Style library

Symbology decisions happen in ArcGIS Pro and are invisible to this repo, so the user records them here in words. `shared/styles/<name>.md` is one recipe per file; `shared/styles/README.md` is the index (name + one-line hook), kept alphabetical.

## Save

Trigger: `save "<Name>, <recipe...>"`, "save this as the X style", or a described treatment worth keeping.

1. Slug the name (`Treecover subtle` → `treecover-subtle.md`). If a file with that slug exists, **update** it: replace the recipe, keep the history line(s) and append a dated one saying what changed.
2. Write the file from the template below. Keep the user's wording — they will recognize their own phrasing later. Do not embellish with settings the user didn't state; if something is obviously missing (which layer it applies to, draw order), ask in one line *after* saving.
3. Add/update the README index line.

Template:

```markdown
# <Name>

**Layer kind**: <what it's for — tree cover raster, hillshade, ocean, contours...>
**First used**: <project> (<date>)

## Recipe
<the steps, verbatim from the user, as a numbered list if they are sequential>

## Draw order
<what it sits above/below, if stated>

## Notes
<anything the user added — when it works, when it doesn't, variants>

## History
- <date>: created (<project>)
```

## Retrieve

Trigger: `retrieve <name> style`, "how did I style X", "style for tree cover".

1. Match against README hooks and file names loosely (a "treecover" request matches `treecover-subtle` and any other `treecover-*`). If several match, show all of them, briefly.
2. Print the recipe in full — it is short by design. Don't summarize it away.
3. If the user then applies it in a new project, offer to note that project in **History** (one line), so the file records where a style has been used.

## Listing

"what styles do I have" → print the README index.
