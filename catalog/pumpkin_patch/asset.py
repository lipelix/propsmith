"""A pumpkin patch: five ribbed pumpkins of different sizes and ripeness (a big orange one, two smaller orange ones, a
pale yellow one and a green unripe one) with curled stems, lying on a patch of dug earth among broad leaves on stalks
and creeping vines with curly tendrils."""
import math
import random

import bmesh
import bpy
from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, cylinder, torus

# Overall size: about 1.5 × 1.5 m (x, y), 0.5 m high to the stem of the biggest pumpkin.
PATCH_R = 0.72  # the earth patch
# Pumpkins: (x, y, radius, colour index); the biggest stands about 0.45 m with its stem.
PUMPKINS = [(-0.1, 0.08, 0.31, 0), (0.42, -0.3, 0.17, 0), (-0.45, -0.38, 0.14, 1), (0.38, 0.4, 0.13, 0),
            (-0.5, 0.42, 0.1, 2)]
SQUASH = 0.72  # pumpkins are wider than tall
LEAF_R = (0.11, 0.17)

ORANGE = (0.42, 0.15, 0.035)  # linear RGB
PALE = (0.45, 0.3, 0.07)
UNRIPE = (0.14, 0.2, 0.05)
STEM = (0.12, 0.11, 0.045)
LEAF = (0.08, 0.16, 0.04)
LEAF_DARK = (0.05, 0.1, 0.03)
VINE = (0.1, 0.15, 0.04)
EARTH = (0.1, 0.07, 0.042)


def _link(name, bm, mat):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth()
    mesh.set_sharp_from_angle(angle=math.radians(60))
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _pumpkin(name, r, x, y, mat, rnd):
    """A ribbed pumpkin of radius `r` sitting on the ground at (x, y); returns the height of its top."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=10, radius=r)
    ribs = 8 + 2 * rnd.randrange(2)
    for v in bm.verts:
        px, py, pz = v.co
        th = math.atan2(py, px)
        k = 1 - 0.07 * math.sin(ribs * th / 2) ** 2
        rho = math.hypot(px, py) / r
        z = pz * SQUASH * (1 - 0.35 * math.exp(-rho * rho * 8))  # dimples at top and bottom
        v.co = Vector((px * k, py * k * rnd.uniform(0.99, 1.01), z))
    lo = min(v.co.z for v in bm.verts)
    hi = max(v.co.z for v in bm.verts)
    obj = _link(name, bm, mat)
    obj.location = (x, y, -lo)
    obj.rotation_euler = (0, 0, rnd.uniform(0, 2 * math.pi))
    return hi - lo


def _rod(name, r, a, b, mat, segments=6, r_top=None):
    d = Vector(b) - Vector(a)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return cylinder(name, r, d.length, a, mat, r_top=r_top, segments=segments,
                    rot=tuple(math.degrees(x) for x in rot), bevel=0)


@prop
def pumpkin_patch():
    rnd = random.Random(20)
    skins = [
        material("pumpkin_patch_orange", ORANGE, rough=0.5, vary=0.25, scale=10, crevice=0.8),
        material("pumpkin_patch_pale", PALE, rough=0.5, vary=0.25, scale=10, crevice=0.8),
        material("pumpkin_patch_unripe", UNRIPE, rough=0.5, vary=0.35, scale=10, crevice=0.8),
    ]
    stem = material("pumpkin_patch_stem", STEM, rough=0.8, vary=0.3, scale=40)
    leaves = [
        material("pumpkin_patch_leaf", LEAF, rough=0.6, vary=0.3, scale=14, crevice=0.6),
        material("pumpkin_patch_leaf_dark", LEAF_DARK, rough=0.6, vary=0.3, scale=14, crevice=0.6),
    ]
    vine = material("pumpkin_patch_vine", VINE, rough=0.7, vary=0.3, scale=30)
    earth = material("pumpkin_patch_earth", EARTH, rough=1.0, vary=0.35, scale=10)

    # Dug earth with a few clods.
    cylinder("earth", PATCH_R, 0.02, (0, 0, 0), earth, r_top=PATCH_R - 0.03, segments=20, bevel=0).scale = (
        1.02, 0.98, 1)
    for i in range(6):
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(0.3, 0.62)
        blob(f"clod_{i}", rnd.uniform(0.025, 0.04), (d * math.cos(a), d * math.sin(a), 0.025), earth,
             squash=(1, 1, 0.6), subdiv=1, seed=10 + i)

    # The pumpkins, each with a curled stem.
    for i, (x, y, r, c) in enumerate(PUMPKINS):
        h = _pumpkin(f"pumpkin_{i}", r, x, y, skins[c], rnd)
        top = h - 0.35 * r * SQUASH * 0.9
        s = max(0.6, r / 0.2)
        lean = (rnd.uniform(-0.03, 0.03) * s, rnd.uniform(-0.03, 0.03) * s)
        mid = (x + lean[0], y + lean[1], top + 0.05 * s)
        _rod(f"stem_{i}", 0.018 * s, (x, y, top - 0.01), mid, stem, r_top=0.014 * s)
        _rod(f"stem_tip_{i}", 0.014 * s, mid, (mid[0] + lean[0] * 1.5, mid[1] + lean[1] * 1.5, mid[2] + 0.015 * s),
             stem, r_top=0.008 * s)

    # Vines creeping out from the pumpkins over the earth, with leaves on stalks and curly tendrils.
    n_leaf = 0
    for v, (x, y, r, c) in enumerate(PUMPKINS):
        a = math.atan2(y, x) + rnd.uniform(-0.8, 0.8)
        p = Vector((x + r * 0.9 * math.cos(a), y + r * 0.9 * math.sin(a), 0.012))
        steps = 4 if r > 0.12 else 3
        for k in range(steps):
            a += rnd.uniform(-0.6, 0.6)
            q = p + Vector((0.16 * math.cos(a), 0.16 * math.sin(a), 0))
            if q.xy.length > PATCH_R - 0.04:  # turn back inside the patch
                a += math.pi * 0.6
                q = p + Vector((0.16 * math.cos(a), 0.16 * math.sin(a), 0))
            _rod(f"vine_{v}_{k}", 0.012, p, q, vine)
            # A leaf on a stalk at every joint, broad and cupped, tilted up.
            side = 1 if k % 2 else -1
            la = a + side * 1.2
            stalk_h = rnd.uniform(0.08, 0.3)
            leaf_at = q + Vector((0.08 * math.cos(la), 0.08 * math.sin(la), stalk_h))
            if leaf_at.xy.length > PATCH_R - 0.12:  # keep the leaves over the patch
                leaf_at.xy *= (PATCH_R - 0.12) / leaf_at.xy.length
            _rod(f"stalk_{v}_{k}", 0.007, q, leaf_at, vine)
            lr = rnd.uniform(*LEAF_R)
            leaf = blob(f"leaf_{v}_{k}", lr, leaf_at, leaves[n_leaf % 2], squash=(1.1, 1, 0.12), subdiv=1,
                        seed=100 + n_leaf, jitter=0.18)
            leaf.rotation_euler = (math.radians(rnd.uniform(-25, 25)), math.radians(rnd.uniform(-25, 25)),
                                   rnd.uniform(0, 2 * math.pi))
            n_leaf += 1
            if k == steps - 1:
                torus(f"tendril_{v}", 0.025, 0.004, q + Vector((0.03 * math.cos(a), 0.03 * math.sin(a), 0.03)), vine,
                      rot=(80, 0, math.degrees(a)), major=12, minor=4)
            p = q
