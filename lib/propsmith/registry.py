"""The `@prop` registry: an asset module's variants, in file order, and the loader `build.py` uses."""
import importlib.util
import re

import bpy
from mathutils import Matrix, Vector

VARIANTS = []

ANCHOR = re.compile(r"^(light|fire|smoke|water):[a-z0-9]+(_[a-z0-9]+)*$")
# A grip point of a hand-held prop (a weapon): where a hand closes on it (`main`, `off`) or what else a holder meets.
GRIP = re.compile(r"^grip:(main|off|stock|trigger)$")
HANDS = ("main", "off")
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


def grip(name, at, axis=None):
    """A grip point of a hand-held prop: an empty named `grip:<name>` at `at` (metres, asset space).

    `main` and `off` are where a hand closes round the handle: `at` on the handle's centre line, `axis` along the
    handle towards the thumb (the end the blade, head or bolt is on). The empty's +Z is that axis and its +X the
    model's +X made square to it: the way the edge, the head or the bolt points (the model's +Z instead when the
    handle runs along x, as a crossbow's fore-stock). The build measures the handle's radius there. `stock` (where it sets against the shoulder) and `trigger` are points and take no axis."""
    key = f"grip:{name}"
    if not GRIP.match(key):
        raise ValueError(f"grip {name!r} must be one of main, off, stock, trigger")
    obj = bpy.data.objects.new(key, None)
    obj.empty_display_type, obj.empty_display_size = "ARROWS", 0.05
    if name in HANDS:
        if axis is None:
            raise ValueError(f"grip {name!r} needs an axis along the handle")
        z = Vector(axis).normalized()
        x = Vector((1, 0, 0)) - z * z.x
        if x.length < 0.5:
            x = Vector((0, 0, 1)) - z * z.z
        x.normalize()
        obj.matrix_world = Matrix.Translation(at) @ Matrix((x, z.cross(x), z)).transposed().to_4x4()
    else:
        if axis is not None:
            raise ValueError(f"grip {name!r} is a point and takes no axis")
        obj.location = at
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
