"""Bakes one asset for publishing: every variant as a GLB whose materials any engine can read.

blender -b --factory-startup --python bake.py -- <job.json>

The library's materials are procedural shader nodes (noise, crevice darkening, box-projected textures), which glTF
cannot carry. Per variant this script builds the mesh as `build.py` does, unwraps it into one UV atlas, bakes what the
shaders feed the surface (base colour, roughness, metallic, and the normal) into images with Cycles, replaces the
materials with one plain PBR material on those images and exports `<variant>.glb` with its anchors.

The job is written by `tools/bake.ts`: the build job (`lib`, `style`, `textures`, `asset`, `inputHash`, `out`) plus
`resolution` (px edge of the atlas) and `samples`. Output in `out`: `<variant>.glb` and `bake.json`.
"""
import json
import math
import os
import sys
import tempfile
import time

job = json.load(open(sys.argv[sys.argv.index("--") + 1]))
sys.path.insert(0, job["lib"])

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import propsmith  # noqa: E402
from propsmith import export, materials, registry, rig, textures  # noqa: E402

spec = job["asset"]
out = job["out"]
SIZE = job["resolution"]
os.makedirs(out, exist_ok=True)
work = tempfile.mkdtemp(prefix="propsmith-bake-")


def select_only(obj):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def unwrap(obj):
    """One UV layer, every face in its own island group, packed into the atlas."""
    mesh = obj.data
    for layer in list(mesh.uv_layers):
        mesh.uv_layers.remove(layer)
    mesh.uv_layers.new(name="atlas")
    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004, area_weight=0.0)
    bpy.ops.object.mode_set(mode="OBJECT")


def image(name, colour):
    img = bpy.data.images.new(name, SIZE, SIZE, alpha=False)
    img.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    return img


def principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def output(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output)


def target(mats, img):
    """Makes `img` the image every material bakes into (its active image node)."""
    for mat in mats:
        nt = mat.node_tree
        node = nt.nodes.get("bake_target") or nt.nodes.new("ShaderNodeTexImage")
        node.name = "bake_target"
        node.image = img
        for n in nt.nodes:
            n.select = False
        node.select = True
        nt.nodes.active = node


def bake_socket(obj, mats, socket, img):
    """Bakes what feeds `socket` of each material's Principled shader, exactly, by showing it as emission."""
    target(mats, img)
    added = []
    for mat in mats:
        nt = mat.node_tree
        sock = principled(mat).inputs[socket]
        emit = nt.nodes.new("ShaderNodeEmission")
        if sock.is_linked:
            nt.links.new(sock.links[0].from_socket, emit.inputs["Color"])
        else:
            v = sock.default_value
            emit.inputs["Color"].default_value = tuple(v) if hasattr(v, "__len__") else (v, v, v, 1)
        nt.links.new(emit.outputs["Emission"], output(mat).inputs["Surface"])
        added.append((mat, emit))
    bpy.ops.object.bake(type="EMIT", margin=6, use_clear=True)
    for mat, emit in added:
        nt = mat.node_tree
        nt.nodes.remove(emit)
        nt.links.new(principled(mat).outputs["BSDF"], output(mat).inputs["Surface"])


def pixels(img):
    buf = np.empty(SIZE * SIZE * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    return buf.reshape(-1, 4)


def save(img, name):
    path = os.path.join(work, f"{name}.png")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return path


def bake(fn):
    name = fn.__name__
    started = time.monotonic()
    materials.reset()
    scene = rig.new_scene(job["style"])
    textures.configure(job["textures"])
    before = set(bpy.data.objects)
    fn()
    added = [o for o in bpy.data.objects if o not in before]
    obj, anchors = export.consolidate(name, added)
    mats = [m for m in obj.data.materials if m is not None]

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = job["samples"]
    scene.cycles.use_denoising = False
    unwrap(obj)
    select_only(obj)

    base = image(f"{name}_base", True)
    bake_socket(obj, mats, "Base Color", base)
    rough = image(f"{name}_rough", False)
    bake_socket(obj, mats, "Roughness", rough)
    metal = image(f"{name}_metal", False)
    bake_socket(obj, mats, "Metallic", metal)
    normal = image(f"{name}_normal", False)
    target(mats, normal)
    bpy.ops.object.bake(type="NORMAL", margin=6, use_clear=True)

    # glTF packs roughness in green and metallic in blue of one image.
    orm = image(f"{name}_orm", False)
    packed = np.ones((SIZE * SIZE, 4), dtype=np.float32)
    packed[:, 1] = pixels(rough)[:, 0]
    packed[:, 2] = pixels(metal)[:, 0]
    orm.pixels.foreach_set(packed.ravel())
    for img, kind in ((base, "base"), (orm, "orm"), (normal, "normal")):
        save(img, f"{name}_{kind}")

    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    bsdf = principled(mat)

    def tex(img):
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = img
        return node

    nt.links.new(tex(base).outputs["Color"], bsdf.inputs["Base Color"])
    split = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(tex(orm).outputs["Color"], split.inputs["Color"])
    nt.links.new(split.outputs["Green"], bsdf.inputs["Roughness"])
    nt.links.new(split.outputs["Blue"], bsdf.inputs["Metallic"])
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex(normal).outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.material_index = 0

    select_only(obj)
    for a in anchors:
        a.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=f"{out}/{name}.glb",
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_extras=False,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_image_format="JPEG",
        export_image_quality=job["quality"],
    )
    return {"id": name, "glb": f"{name}.glb", "materials": len(mats), "seconds": round(time.monotonic() - started, 2)}


variants = registry.load(spec["file"])
found = [v.__name__ for v in variants]
if found != spec["variants"]:
    raise SystemExit(f"{spec['id']}: asset.py registers {found}, asset.json lists {spec['variants']}")

result = {
    "schema": 1,
    "id": spec["id"],
    "inputHash": job["inputHash"],
    "libVersion": propsmith.LIB_VERSION,
    "blender": bpy.app.version_string,
    "resolution": SIZE,
    "variants": [bake(v) for v in variants],
}
with open(f"{out}/bake.json", "w") as f:
    json.dump(result, f, indent=2)
print("BAKED", json.dumps({v["id"]: v["seconds"] for v in result["variants"]}))
