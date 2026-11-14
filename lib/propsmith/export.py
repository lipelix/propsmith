"""Turns what a variant builder added into one mesh object, and exports it as GLB."""
import bpy

from .registry import ANCHOR

_CONVERTIBLE = {"MESH", "CURVE", "SURFACE", "META", "FONT"}


def consolidate(name, added):
    """Applies every modifier, joins all geometry into one mesh object `name` with its origin at the world origin (the
    centre of the base on the ground) and no transform, and parents the anchor empties to it. Other objects (helper
    empties, cameras, lights) are removed. Returns (object, anchors sorted by name)."""
    bpy.context.view_layer.update()  # objects made this frame have no matrix_world yet
    anchors = sorted((o for o in added if o.type == "EMPTY" and ANCHOR.match(o.name)), key=lambda o: o.name)
    for a in anchors:
        world = a.matrix_world.copy()
        a.parent = None
        a.matrix_world = world
    geometry = [o for o in added if o.type in _CONVERTIBLE]
    if not geometry:
        raise ValueError(f"{name}: the variant added no geometry")
    for o in added:
        if o not in geometry and o not in anchors:
            for child in o.children:
                world = child.matrix_world.copy()
                child.parent = None
                child.matrix_world = world
    for o in [o for o in added if o not in geometry and o not in anchors]:
        bpy.data.objects.remove(o)

    view_layer = bpy.context.view_layer
    for o in view_layer.objects:
        o.select_set(False)
    for o in geometry:
        o.select_set(True)
    view_layer.objects.active = geometry[0]
    bpy.ops.object.convert(target="MESH")
    geometry = [o for o in view_layer.objects if o.select_get()]
    view_layer.objects.active = geometry[0]
    if len(geometry) > 1:
        bpy.ops.object.join()
    obj = view_layer.objects.active
    for o in obj.children:
        world = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = world
    obj.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.name = obj.data.name = name
    for a in anchors:
        a.parent = obj
    obj.select_set(False)
    return obj, anchors


def glb(obj, anchors, path):
    """Exports the variant (mesh and anchors, no rig) at rotation 0 to `path`."""
    view_layer = bpy.context.view_layer
    for o in view_layer.objects:
        o.select_set(False)
    for o in [obj, *anchors]:
        o.select_set(True)
    view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_extras=False,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
    )
    for o in (obj, *anchors):
        o.select_set(False)
