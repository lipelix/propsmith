"""Primitives for prop builders, in metres. Every shape is a mesh object linked to the scene with one material,
smooth-shaded with sharp edges above 35 deg, and an optional bevel modifier (edge highlights read at 2 px/pt)."""
import math

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector


def _object(name, bm, mat, bevel, segments=2):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth()
    mesh.set_sharp_from_angle(angle=math.radians(35))
    if mat:
        mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width, mod.segments, mod.limit_method = bevel, segments, "ANGLE"
        mod.harden_normals = False
    return obj


def _place(obj, at, rot):
    obj.location = Vector(at)
    obj.rotation_euler = Euler([math.radians(a) for a in rot])
    return obj


def box(name, size, at, mat, rot=(0, 0, 0), bevel=0.012):
    """A box `size` (x, y, z) centred on `at`, rotated by `rot` degrees (XYZ)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    return _place(_object(name, bm, mat, bevel), at, rot)


def cylinder(name, r, h, at, mat, r_top=None, segments=24, rot=(0, 0, 0), bevel=0.01, caps=True):
    """A cylinder (a frustum when `r_top` is given) standing on `at` along its local +Z."""
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=caps, segments=segments, radius1=r, radius2=r if r_top is None else r_top, depth=h,
        matrix=Matrix.Translation((0, 0, h / 2)),
    )
    return _place(_object(name, bm, mat, bevel), at, rot)


def torus(name, R, r, at, mat, rot=(0, 0, 0), major=32, minor=10):
    """A torus of ring radius `R` and tube radius `r` in the local XY plane."""
    bm = bmesh.new()
    rings = []
    for i in range(major):
        a = 2 * math.pi * i / major
        ring = []
        for j in range(minor):
            b = 2 * math.pi * j / minor
            d = R + r * math.cos(b)
            ring.append(bm.verts.new((d * math.cos(a), d * math.sin(a), r * math.sin(b))))
        rings.append(ring)
    for i in range(major):
        for j in range(minor):
            a, b = rings[i], rings[(i + 1) % major]
            bm.faces.new((a[j], b[j], b[(j + 1) % minor], a[(j + 1) % minor]))
    return _place(_object(name, bm, mat, 0), at, rot)


def blob(name, radius, at, mat, squash=(1, 1, 1), subdiv=2, seed=0, jitter=0.12):
    """A lumpy icosphere (stones, sacks, foliage): deterministic per `seed`."""
    import random

    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=radius)
    for v in bm.verts:
        v.co *= 1 + rnd.uniform(-jitter, jitter)
        v.co = Vector((v.co.x * squash[0], v.co.y * squash[1], v.co.z * squash[2]))
    return _place(_object(name, bm, mat, 0), at, (0, 0, rnd.uniform(0, 360)))
