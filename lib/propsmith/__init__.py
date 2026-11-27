"""propsmith: the asset library for Blender. Put on `sys.path` by the build; an `asset.py` imports from here.

An asset module registers its variants with `@prop`, in file order. Each variant is a zero-argument function that adds
its objects to the current scene, in metres, z up, standing on z = 0 around the origin, which is the centre of its base
on the ground. Local x spans the asset's `size.x` and local y its `size.y`; the front (door, drawer, face) is on -y.
Anchors for effects are empties named `light:*`, `fire:*`, `smoke:*` or `water:*` (`registry.anchor`); a hand-held
prop's grip points are empties named `grip:main`, `grip:off`, `grip:stock`, `grip:trigger` (`registry.grip`).

Modules: `registry` (`@prop`, loading an asset.py), `materials`, `textures`, `shapes`, `rig` (light and camera),
`measure` and `export` (used by the build).
"""
from .registry import VARIANTS, anchor, grip, prop

# Bumped when the library changes what a build produces in a way the file hashes would not show.
LIB_VERSION = 1

__all__ = ["LIB_VERSION", "VARIANTS", "anchor", "grip", "prop"]
