# propsmith

Text to game props: a coding agent writes a Blender model, the tools check it, and finished props are published in an
open catalogue (code MIT, assets CC0-1.0).

## Who uses the site

- Indie game developers looking for a prop to drop into a game: they search, look at the model from every side under
  their kind of light, check its size and triangle count, and download the GLB or copy how to import it.
- People who run coding agents on the catalogue and want to see what the agent made.

They sit at a desk with an editor, Blender or a game engine open, often in the evening.

## What the site is

A tool, not a pitch (owner's choice, 2026-11-14: "workshop / tool"). Two surfaces:

- the catalogue: search and facets over every asset;
- the asset page: a live 3D view that looks like the Blender review render, with controls for light, rotation and
  camera, background and ground (owner's choice, 2026-11-14), next to the facts and the download.

## Voice

Plain and exact. Sizes in metres, counts as numbers. No marketing copy.

## Must stay true

- Every number shown comes from `catalog/index.json`, `catalog/measurements.json` or the bake manifest.
- The view is honest about what it is: the published GLB, lit in the browser; not the Blender render.
