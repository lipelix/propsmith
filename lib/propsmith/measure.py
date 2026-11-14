"""The facts a build reads back from a variant (`result.json`): bounds, triangles, manifoldness, materials and anchors.
Everything is in metres in the asset's own space (x, y, z from the centre of its base on the ground)."""
import bmesh

from .materials import SOURCE
from .registry import SIZED


def _r(v):
    return round(v, 4) + 0.0  # + 0.0 turns -0.0 into 0.0


def _vec(co):
    return [_r(co[0]), _r(co[1]), _r(co[2])]


def measure(obj, anchors):
    mesh = obj.data
    if len(mesh.vertices) == 0:
        raise ValueError(f"{obj.name}: empty mesh")
    xs = [v.co.x for v in mesh.vertices]
    ys = [v.co.y for v in mesh.vertices]
    zs = [v.co.z for v in mesh.vertices]
    mesh.calc_loop_triangles()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    used = {mesh.materials[p.material_index] for p in mesh.polygons if mesh.materials and mesh.materials[p.material_index]}
    return {
        "tris": len(mesh.loop_triangles),
        "bbox": {"min": _vec((min(xs), min(ys), min(zs))), "max": _vec((max(xs), max(ys), max(zs)))},
        "origin": _vec(obj.location),
        "nonManifoldEdges": non_manifold,
        # `source`: `palette`, `ledger:<texture id>`, or None for a material not made by `propsmith.materials`.
        "materials": [{"name": m.name, "source": m.get(SOURCE)} for m in sorted(used, key=lambda m: m.name)],
        # `size`: the anchor's extent in metres (`registry.anchor`), only when it was given one.
        "anchors": [
            {
                "name": a.name,
                "at": _vec(a.matrix_world.translation),
                **({"size": [_r(v) for v in a.matrix_world.to_scale()]} if a.get(SIZED) else {}),
            }
            for a in anchors
        ],
    }
