"""Builds one asset: every variant of its asset.py, measured, exported and rendered for review.

blender -b --factory-startup --python build.py -- <job.json>

The job is written and validated by `tools/build.ts`: `lib` (put on sys.path), `style` (tools/blender/style.json),
`textures` ({ledger id: {kind: file}}), `asset` ({id, file, variants, size}), `only` (a variant id or null),
`inputHash` and `out`. Each variant is built in a fresh scene, its modifiers applied and its parts joined into one mesh
with the origin at the centre of the base on the ground. Output in `out`:

- `<variant>.glb`: the mesh and its anchor empties (procedural materials do not survive glTF; the publish step bakes);
- `review/<variant>_{iso,top,front}.png`: snapshots for the look: iso (the three-quarter view, +x and -y faces), and
  orthographic views with x to the right (top: +y up, the declared size outlined; front: from -y, z up);
- `result.json`: per variant the measured facts (`measure.py`), in metres.
"""
import json
import math
import os
import sys
import time

job = json.load(open(sys.argv[sys.argv.index("--") + 1]))
sys.path.insert(0, job["lib"])

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import propsmith  # noqa: E402
from propsmith import export, materials, measure, registry, rig, textures  # noqa: E402

style = job["style"]
spec = job["asset"]
out = job["out"]
PAD = 4  # transparent px around the content
PX_PER_M = style["pxPerTile"] / style["tileMetres"]
ISO_SCALE = 2  # the iso snapshot is rendered at twice the style's scale

os.makedirs(f"{out}/review", exist_ok=True)


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
    shadows = [p + sun * (p.z / -sun.z) for p in box if p.z > 1e-4]
    return box + shadows


def iso(scene, obj, path):
    """Renders the three-quarter view, framed tight around the asset and its shadow."""
    s = {**style, "pxPerTile": style["pxPerTile"] * ISO_SCALE}
    rig.camera(scene, s, 1024, 1024, (0, 0, 0), (512, 512))
    pts = [rig.project(scene, p) for p in corners(obj)]
    drop_camera(scene)
    dx = [p[0] - 512 for p in pts]
    dy = [p[1] - 512 for p in pts]
    ox, oy = math.ceil(PAD - min(dx)), math.ceil(PAD - min(dy))
    width, height = math.ceil(ox + max(dx) + PAD), math.ceil(oy + max(dy) + PAD)
    rig.camera(scene, s, width, height, (0, 0, 0), (ox, oy))
    rig.render(scene, path)
    drop_camera(scene)


def ortho(scene, path, centre, rotation, width, height):
    data = bpy.data.cameras.new("cam")
    data.type = "ORTHO"
    data.ortho_scale = max(width, height) / PX_PER_M
    data.clip_end = 100
    cam = bpy.data.objects.new("cam", data)
    cam.location, cam.rotation_euler = centre, rotation
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = width, height
    rig.render(scene, path)
    drop_camera(scene)


def outline(sx, sy):
    """The declared size as a thin bright rectangle on the ground (top review only)."""
    mat = bpy.data.materials.new("size_outline")
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Emission Color"].default_value = (1.0, 0.25, 0.1, 1)
    bsdf.inputs["Emission Strength"].default_value = 2.0
    hx, hy, t = sx / 2, sy / 2, 0.02
    edges = [((0, hy), (2 * hx + t, t)), ((0, -hy), (2 * hx + t, t)), ((hx, 0), (t, 2 * hy)), ((-hx, 0), (t, 2 * hy))]
    objs = []
    for i, ((x, y), (ex, ey)) in enumerate(edges):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0.002))
        o = bpy.context.active_object
        o.name = f"size_{i}"
        o.scale = (ex, ey, 0.002)
        o.data.materials.append(mat)
        o.visible_shadow = False
        objs.append(o)
    return objs


def review(scene, obj, name):
    # The camera looks along world +x+y: turning the asset -90 deg about z shows its +x and -y (front) faces.
    obj.rotation_euler = (0, 0, math.radians(-90))
    bpy.context.view_layer.update()
    iso(scene, obj, f"{out}/review/{name}_iso.png")

    obj.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    size = spec["size"]
    lo = Vector([min(c[i] for c in obj.bound_box) for i in range(3)])
    hi = Vector([max(c[i] for c in obj.bound_box) for i in range(3)])
    x0, x1 = min(lo.x, -size["x"] / 2), max(hi.x, size["x"] / 2)
    y0, y1 = min(lo.y, -size["y"] / 2), max(hi.y, size["y"] / 2)
    z1 = max(hi.z, size["z"])

    def px(m):
        return math.ceil(m * PX_PER_M) + 2 * PAD

    marks = outline(size["x"], size["y"])
    ortho(scene, f"{out}/review/{name}_top.png", ((x0 + x1) / 2, (y0 + y1) / 2, 40), (0, 0, 0), px(x1 - x0), px(y1 - y0))
    for o in marks:
        bpy.data.objects.remove(o)
    ortho(
        scene, f"{out}/review/{name}_front.png", ((x0 + x1) / 2, -40, z1 / 2), (math.radians(90), 0, 0),
        px(x1 - x0), px(z1),
    )


def build(fn):
    name = fn.__name__
    started = time.monotonic()
    materials.reset()
    scene = rig.new_scene(style)
    textures.configure(job["textures"])
    before = set(bpy.data.objects)
    fn()
    added = [o for o in bpy.data.objects if o not in before]
    obj, anchors = export.consolidate(name, added)
    facts = measure.measure(obj, anchors)
    export.glb(obj, anchors, f"{out}/{name}.glb")

    size = spec["size"]
    rig.shadow_catcher(style, max(size["x"], size["y"]) + 2 * size["z"] + 6)
    review(scene, obj, name)
    return {
        "id": name,
        **facts,
        "textures": sorted(textures.USED),
        "glb": f"{name}.glb",
        "review": {k: f"review/{name}_{k}.png" for k in ("iso", "top", "front")},
        "seconds": round(time.monotonic() - started, 2),
    }


variants = registry.load(spec["file"])
found = [v.__name__ for v in variants]
if found != spec["variants"]:
    raise SystemExit(f"{spec['id']}: asset.py registers {found}, asset.json lists {spec['variants']}")
if job["only"] is not None:
    variants = [v for v in variants if v.__name__ == job["only"]]

result = {
    "schema": 1,
    "id": spec["id"],
    "inputHash": job["inputHash"],
    "only": job["only"],
    "libVersion": propsmith.LIB_VERSION,
    "blender": bpy.app.version_string,
    "variants": [build(v) for v in variants],
}
with open(f"{out}/result.json", "w") as f:
    json.dump(result, f, indent=2)
print("BUILT", json.dumps({v["id"]: v["tris"] for v in result["variants"]}))
