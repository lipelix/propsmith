"""The facts a build reads back from a variant (`result.json`): bounds, triangles, manifoldness, materials, anchors and
grip points. Everything is in metres in the asset's own space (x, y, z from the centre of its base on the ground)."""
import math

import bmesh
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

from .materials import SOURCE
from .registry import ANCHOR, HANDS, SIZED

# How a hand grip's handle is measured: rays out from the grip point square to the handle, this many, this far.
RAYS = 12
REACH = 0.08


def _r(v):
    return round(v, 4) + 0.0  # + 0.0 turns -0.0 into 0.0


def _vec(co):
    return [_r(co[0]), _r(co[1]), _r(co[2])]


def _exit(tree, origin, direction):
    """How far a ray from inside the mesh travels to leave it: the last surface it leaves through before it first
    enters another one (a wrap round a shaft is left after the shaft), or None when it starts outside or hits
    nothing within REACH."""
    out, travelled, at = None, 0.0, origin
    while travelled < REACH:
        hit, normal, _, dist = tree.ray_cast(at, direction, REACH - travelled)
        if hit is None:
            break
        travelled += dist
        if normal.dot(direction) < 0:  # entering a surface: the handle ended before it
            break
        out = travelled
        at = hit + direction * 1e-5
        travelled += 1e-5
    return out


def handle_radius(tree, at, axis):
    """The handle's mean radius round a grip point on its centre line, or None when the point is not inside a
    handle (a ray square to the axis starts outside the mesh or leaves nothing within REACH)."""
    side = axis.orthogonal().normalized()
    rays = [_exit(tree, at, Matrix.Rotation(2 * math.pi * i / RAYS, 3, axis) @ side) for i in range(RAYS)]
    if any(r is None for r in rays):
        return None
    return sum(rays) / len(rays)


def measure(obj, anchors):
    grips = [a for a in anchors if not ANCHOR.match(a.name)]
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
    tree = BVHTree.FromBMesh(bm)
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
            if ANCHOR.match(a.name)
        ],
        **({"grips": [_grip(tree, g) for g in grips]} if grips else {}),
    }


def _grip(tree, g):
    """A grip point; a hand's also has its axis along the handle and the handle's radius there (None: not on one)."""
    name = g.name.split(":", 1)[1]
    at = g.matrix_world.translation
    if name not in HANDS:
        return {"name": name, "at": _vec(at)}
    axis = g.matrix_world.to_3x3().col[2].normalized()
    radius = handle_radius(tree, at, axis)
    return {"name": name, "at": _vec(at), "axis": _vec(axis), "radius": None if radius is None else _r(radius)}
