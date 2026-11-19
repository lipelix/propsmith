"""Renders the PR shots of one asset: every variant of its asset.py, large and framed to fill the picture.

blender -b --factory-startup --python shots.py -- <job.json>

Lives outside `tools/blender/` so it is not part of the assets' input hash. The job is the build job
(`tools/build.ts` `buildJob`) plus `size` (px of the longer side) and `out`. The review rig
and style are the build's; only the framing differs: the build keeps a fixed scale per metre (a candle is a few dozen
pixels), here each view is scaled so the asset, with its shadow in the three-quarter view, fills `size` px. Output in
`out`: `<variant>_iso.png` (three-quarter view, +x and -y faces) and `<variant>_front.png` (from -y, z up), both on a
transparent film.
"""
import json
import math
import os
import sys

job = json.load(open(sys.argv[sys.argv.index("--") + 1]))
sys.path.insert(0, job["lib"])

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from propsmith import export, materials, registry, rig, textures  # noqa: E402

style = job["style"]
spec = job["asset"]
out = job["out"]
SIZE = job["size"]
MARGIN = 0.04  # of the longer side, around the content

os.makedirs(out, exist_ok=True)


def drop_camera(scene):
    cam = scene.camera
    if cam is not None:
        data = cam.data
        bpy.data.objects.remove(cam)
        bpy.data.cameras.remove(data)


def corners(obj):
    """The world corners of the object's bounding box and where its top corners' shadows fall on the ground."""
    box = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    sun = rig.sun_direction(bpy.context.scene)
    return box + [p + sun * (p.z / -sun.z) for p in box if p.z > 1e-4]


def fit(width, height):
    """`width` x `height` scaled so the longer side is SIZE minus the margins: (scale, width px, height px)."""
    inner = SIZE * (1 - 2 * MARGIN)
    scale = inner / max(width, height)
    pad = SIZE * MARGIN
    return scale, math.ceil(width * scale + 2 * pad), math.ceil(height * scale + 2 * pad)


def iso(scene, obj, path):
    # Measure at the style's own scale, then scale the rig so the content fills the picture.
    rig.camera(scene, style, 1024, 1024, (0, 0, 0), (512, 512))
    pts = [rig.project(scene, p) for p in corners(obj)]
    drop_camera(scene)
    xs, ys = [p[0] - 512 for p in pts], [p[1] - 512 for p in pts]
    scale, width, height = fit(max(xs) - min(xs), max(ys) - min(ys))
    pad = SIZE * MARGIN
    s = {**style, "pxPerTile": style["pxPerTile"] * scale}
    rig.camera(scene, s, width, height, (0, 0, 0), (pad - min(xs) * scale, pad - min(ys) * scale))
    rig.render(scene, path)
    drop_camera(scene)


def front(scene, obj, path):
    lo = Vector([min(c[i] for c in obj.bound_box) for i in range(3)])
    hi = Vector([max(c[i] for c in obj.bound_box) for i in range(3)])
    scale, width, height = fit(hi.x - lo.x, hi.z)
    data = bpy.data.cameras.new("cam")
    data.type = "ORTHO"
    data.ortho_scale = max(width, height) / scale
    data.clip_end = 100
    cam = bpy.data.objects.new("cam", data)
    cam.location, cam.rotation_euler = ((lo.x + hi.x) / 2, -40, hi.z / 2), (math.radians(90), 0, 0)
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = width, height
    rig.render(scene, path)
    drop_camera(scene)


def shoot(fn):
    name = fn.__name__
    materials.reset()
    scene = rig.new_scene(style)
    textures.configure(job["textures"])
    before = set(bpy.data.objects)
    fn()
    obj, _anchors = export.consolidate(name, [o for o in bpy.data.objects if o not in before])
    size = spec["size"]
    rig.shadow_catcher(style, max(size["x"], size["y"]) + 2 * size["z"] + 6)
    # The camera looks along world +x+y: turning the asset -90 deg about z shows its +x and -y (front) faces.
    obj.rotation_euler = (0, 0, math.radians(-90))
    bpy.context.view_layer.update()
    iso(scene, obj, f"{out}/{name}_iso.png")
    obj.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    front(scene, obj, f"{out}/{name}_front.png")
    return name


variants = registry.load(spec["file"])
if job["only"] is not None:
    variants = [v for v in variants if v.__name__ == job["only"]]
print("SHOT", json.dumps([shoot(v) for v in variants]))
