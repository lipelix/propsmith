"""An old cut tree stump: a weathered ringed cut face, an axe notch in its side, ridged bark and thick spreading roots."""
import math
import random

import bpy

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall dimensions (metres), from the description.
R_BASE, R_TOP = 0.33, 0.3  # trunk radius at the ground and under the cut: about 0.7 m across with bark
H = 0.5  # height of the cut face
CUT = 0.03  # thickness of the cut-face slab
NOTCH_YAW = -40.0  # heading of the axe notch (degrees from +x), toward the review camera
NOTCH_Z, NOTCH_S = 0.31, 0.22  # height of the notch centre and the side of its square cutter (V depth = S / sqrt 2)
ROOT_L = 0.5  # length of a root from the trunk to where it dives into the ground

BARK = (0.085, 0.06, 0.042)
BARK_DARK = (0.06, 0.045, 0.034)
CUT_OLD = (0.25, 0.2, 0.15)  # weathered grey-brown cut face
RING = (0.17, 0.13, 0.09)
HEART = (0.2, 0.14, 0.085)
CHOPPED = (0.46, 0.34, 0.2)  # the fresher wood inside the axe notch
CRACK = (0.06, 0.045, 0.035)


def _apply_cut(obj, cutter):
    """Subtracts `cutter` from `obj` and bakes the result (bevel included) into `obj`'s mesh."""
    mod = obj.modifiers.new("notch", "BOOLEAN")
    mod.operation, mod.solver, mod.object = "DIFFERENCE", "EXACT", cutter
    mod.material_mode = "TRANSFER"
    bpy.context.view_layer.update()
    ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = bpy.data.meshes.new_from_object(ev)
    obj.modifiers.clear()
    obj.data = mesh


def _root(name, yaw, tilt, r0, r1, length, mat):
    """A tapered root leaving the trunk at heading `yaw`, sloping down `tilt` degrees, its tip resting on the ground."""
    t = math.radians(tilt)
    z_end = r1 * math.cos(t) + 0.003
    z0 = max(z_end + length * math.sin(t), r0 * math.cos(t) + 0.003)
    length = (z0 - z_end) / math.sin(t)
    a = math.radians(yaw)
    d0 = R_BASE - 0.13
    at = (d0 * math.cos(a), d0 * math.sin(a), z0)
    cylinder(name, r0, length, at, mat, r_top=r1, segments=8, rot=(0, 90 + tilt, yaw), bevel=0.0)
    tip = d0 + length * math.cos(t)
    return tip


@prop
def tree_stump():
    rnd = random.Random(11)
    bark = material("tree_stump_bark", BARK, vary=0.45, scale=30, rough=1.0, crevice=0.8)
    bark_dark = material("tree_stump_bark_dark", BARK_DARK, vary=0.4, scale=24, rough=1.0, crevice=0.8)
    cut = material("tree_stump_cut", CUT_OLD, vary=0.3, scale=11, rough=0.95)
    ring = material("tree_stump_ring", RING, vary=0.2, scale=12)
    heart = material("tree_stump_heart", HEART, vary=0.25, scale=14)
    chopped = material("tree_stump_chopped", CHOPPED, vary=0.25, scale=16)
    crack = material("tree_stump_crack", CRACK, vary=0.1, scale=10)

    # The trunk: a tapered bark cylinder with a flared foot, and the weathered cut slab on top.
    trunk = cylinder("trunk", R_BASE, H - CUT + 0.004, (0, 0, 0), bark, r_top=R_TOP, segments=20, bevel=0.012)
    foot = cylinder("foot", R_BASE + 0.05, 0.14, (0, 0, 0), bark, r_top=R_BASE - 0.01, segments=20, bevel=0.012)
    face = cylinder("cut_face", R_TOP - 0.018, CUT, (0, 0, H - CUT), cut, segments=20, bevel=0.008)

    # The axe notch: a square cutter turned 45 deg about the tangent, centred on the bark, carves a V into the side.
    na = math.radians(NOTCH_YAW)
    r_notch = R_BASE + (R_TOP - R_BASE) * NOTCH_Z / (H - CUT) + 0.01
    cutter = box(
        "notch_cutter", (NOTCH_S, 0.34, NOTCH_S), (r_notch * math.cos(na), r_notch * math.sin(na), NOTCH_Z), chopped,
        rot=(0, 45, NOTCH_YAW), bevel=0,
    )
    _apply_cut(trunk, cutter)
    bpy.data.objects.remove(cutter)

    # Rough bark: ragged vertical ridges leaning with the taper, left out where the notch is.
    lean = math.degrees(math.atan2(R_BASE - R_TOP, H))
    n = 22
    for i in range(n):
        ang = 360 * i / n + rnd.uniform(-5, 5)
        if abs((ang - NOTCH_YAW + 180) % 360 - 180) < 26:
            continue
        h = rnd.uniform(0.36, H - 0.035)
        z = h / 2 + 0.03
        rr = R_BASE + (R_TOP - R_BASE) * z / H + 0.008
        a = math.radians(ang)
        box(
            f"ridge_{i}", (0.035, rnd.uniform(0.04, 0.07), h), (rr * math.cos(a), rr * math.sin(a), z),
            bark_dark if i % 3 == 0 else bark, rot=(rnd.uniform(-2, 2), -lean, ang), bevel=0.012,
        )

    # Growth rings, a darker heart and a few radial weather checks on the cut face.
    for i, rr in enumerate((0.235, 0.19, 0.145, 0.1, 0.06)):
        torus(f"ring_{i}", rr, 0.0045, (0.004 * i, -0.003 * i, H - 0.002), ring, major=28, minor=4)
    cylinder("heart", 0.028, 0.004, (0.02, -0.015, H - 0.002), heart, segments=10, bevel=0)
    for i in range(4):
        a = rnd.uniform(0, 360)
        length = rnd.uniform(0.1, 0.17)
        c = 0.06 + length / 2
        box(
            f"check_{i}", (length, 0.009, 0.01), (c * math.cos(math.radians(a)), c * math.sin(math.radians(a)), H - 0.003),
            crack, rot=(0, 0, a), bevel=0,
        )

    # Thick roots spreading out and diving into the ground, with knuckles where they leave the trunk.
    for i, base in enumerate((10, 75, 140, 200, 262, 318)):
        yaw = base + rnd.uniform(-12, 12)
        r0 = rnd.uniform(0.11, 0.14)
        tip = _root(f"root_{i}", yaw, rnd.uniform(16, 22), r0, 0.05, ROOT_L * rnd.uniform(0.75, 1.0), bark)
        a = math.radians(yaw)
        blob(f"root_tip_{i}", 0.065, (tip * math.cos(a), tip * math.sin(a), 0.046), bark,
             squash=(1.1, 1.1, 0.6), subdiv=1, seed=60 + i, jitter=0.08)
        d = R_BASE + 0.02
        blob(f"knuckle_{i}", r0 * 1.05, (d * math.cos(a), d * math.sin(a), r0 * 0.92), bark_dark,
             squash=(1.2, 1.2, 0.75), subdiv=1, seed=40 + i, jitter=0.1)
