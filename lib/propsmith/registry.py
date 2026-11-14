"""The `@prop` registry: an asset module's variants, in file order, and the loader `build.py` uses."""
import importlib.util
import re

import bpy

VARIANTS = []

ANCHOR = re.compile(r"^(light|fire|smoke|water):[a-z0-9]+(_[a-z0-9]+)*$")
# Custom property on an anchor empty made with a `size` (its scale is then the effect's extent).
SIZED = "propsmith_anchor_sized"


def prop(fn):
    """Registers a variant builder (the function name is the variant id)."""
    if any(v.__name__ == fn.__name__ for v in VARIANTS):
        raise ValueError(f"variant {fn.__name__} is registered twice")
    VARIANTS.append(fn)
    return fn


def anchor(name, at, size=None):
    """An ambient anchor: an empty named `<light|fire|smoke|water>:<name>` at `at` (metres, asset space).

    `size` (x, y, z metres, all positive) becomes the empty's scale; consumers read it as the extent of the effect: a
    fire's half width (x) and flame height (z) from its base, a water spout's lip radius and a water basin's surface
    radii (x, y). Fires, spouts and basins need one; lights and smoke are points and take none."""
    if not ANCHOR.match(name):
        raise ValueError(f"anchor {name!r} must be <light|fire|smoke|water>:<snake_case>")
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type, obj.empty_display_size = "SPHERE", 0.05
    obj.location = at
    if size is not None:
        if len(size) != 3 or min(size) <= 0:
            raise ValueError(f"anchor {name!r}: size must be three positive metres, not {size!r}")
        obj.scale = size
        obj[SIZED] = True
    bpy.context.scene.collection.objects.link(obj)
    return obj


def load(path, name="asset_module"):
    """Imports an asset.py and returns its variant functions in file order."""
    VARIANTS.clear()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not VARIANTS:
        raise ValueError(f"{path}: no @prop variant")
    return list(VARIANTS)
