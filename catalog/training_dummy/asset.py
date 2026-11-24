"""A straw-stuffed sackcloth training dummy, front on -y: a square post on crossed feet, a sack body tied at the waist
with straw poking out below, sack arms on a crossbar with straw tufts at the ends, a sack head under a dented flat-topped
iron pot helm with an eye slit, and a battered round shield with a lost rim piece hung on its left arm."""
import math
import random

from mathutils import Matrix, Vector

import bpy
from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall size: about 0.9 m across the arms (x), 0.5 m deep (y), 1.9 m high to the top of the helm.
FOOT_X, FOOT_Y, FOOT_H = 0.6, 0.46, 0.08  # the two crossed feet
POST = 0.1
POST_H = 1.68  # top of the post (inside the head)
ARM_Z, ARM_L = 1.48, 0.84  # crossbar height and length
SLEEVE_R = 0.062
BODY_R, BODY_Z = 0.2, 1.26  # the stuffed sack body: radius before squash, centre height
HEAD_R, HEAD_Z = 0.12, 1.72
HELM_R, HELM_H = 0.135, 0.17
SHIELD_R, SHIELD_T = 0.24, 0.025

WOOD = (0.2, 0.125, 0.065)  # linear RGB
WOOD_OLD = (0.15, 0.1, 0.06)
SACK = (0.36, 0.27, 0.15)
SACK_DARK = (0.24, 0.17, 0.09)
STRAW = (0.45, 0.35, 0.12)
ROPE = (0.3, 0.22, 0.12)
IRON = (0.12, 0.115, 0.11)
IRON_DARK = (0.045, 0.045, 0.045)
PAINT = (0.3, 0.07, 0.045)
SHIELD_WOOD = (0.24, 0.155, 0.08)
LEATHER = (0.13, 0.07, 0.035)


def _rod(name, r, a, b, mat, segments=8, bevel=0.003, r_top=None):
    """A round rod from point `a` to point `b`."""
    d = Vector(b) - Vector(a)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return cylinder(name, r, d.length, a, mat, r_top=r_top, segments=segments,
                    rot=tuple(math.degrees(x) for x in rot), bevel=bevel)


def _moved(build, matrix):
    """Run `build`, then move every object it added by `matrix`."""
    before = set(bpy.data.objects)
    build()
    for obj in set(bpy.data.objects) - before:
        obj.matrix_basis = matrix @ obj.matrix_basis


def _shield(rnd, wood, paint, iron, dark, leather):
    """A battered round shield centred on the origin, its back on y = 0 and its face towards -y."""
    r, t = SHIELD_R, SHIELD_T
    cylinder("shield_board", r, t, (0, 0, 0), wood, segments=28, rot=(90, 0, 0), bevel=0.005)
    # Faded paint: a red field with worn patches showing the planks.
    cylinder("shield_paint", r - 0.02, 0.003, (0, -t + 0.001, 0), paint, segments=28, rot=(90, 0, 0), bevel=0)
    for i in range(4):
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(0.06, 0.15)
        cylinder(f"shield_worn_{i}", rnd.uniform(0.03, 0.06), 0.003, (d * math.cos(a), -t - 0.0005, d * math.sin(a)),
                 wood, segments=10, rot=(90, 0, 0), bevel=0).scale = (rnd.uniform(1, 1.6), 1, 1)
    for i, x in enumerate((-0.12, -0.04, 0.04, 0.12)):  # plank seams
        h = 2 * math.sqrt(r * r - x * x) - 0.03
        box(f"shield_seam_{i}", (0.004, 0.004, h), (x, -t - 0.0015, 0), dark, bevel=0)
    for i in range(5):  # sword cuts
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(0.07, 0.17)
        box(f"shield_cut_{i}", (rnd.uniform(0.06, 0.12), 0.005, 0.006), (d * math.cos(a), -t - 0.002, d * math.sin(a)),
            dark, rot=(0, rnd.uniform(-70, 70), 0), bevel=0)
    # The boss and what is left of the iron rim: a few pieces are torn away.
    cylinder("shield_boss_rim", 0.07, 0.008, (0, -t, 0), iron, segments=16, rot=(90, 0, 0), bevel=0.003)
    blob("shield_boss", 0.055, (0, -t - 0.008, 0), iron, squash=(1, 0.6, 1), subdiv=2, seed=3, jitter=0.04)
    n = 20
    for k in range(n):
        if k in (3, 4, 11):
            continue
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        p0 = (r * math.cos(a0), -t / 2, r * math.sin(a0))
        p1 = (r * math.cos(a1), -t / 2, r * math.sin(a1))
        _rod(f"shield_rim_{k}", 0.016, p0, p1, iron, segments=6, bevel=0)


@prop
def training_dummy():
    rnd = random.Random(31)
    wood = material("training_dummy_wood", WOOD, vary=0.28, scale=10)
    old = material("training_dummy_wood_old", WOOD_OLD, vary=0.3, scale=9)
    sack = material("training_dummy_sack", SACK, rough=0.95, vary=0.3, scale=40, crevice=0.7)
    sack_dark = material("training_dummy_sack_dark", SACK_DARK, rough=0.95, vary=0.3, scale=40)
    straw = material("training_dummy_straw", STRAW, rough=0.9, vary=0.35, scale=60)
    rope = material("training_dummy_rope", ROPE, rough=0.9, vary=0.25, scale=50)
    iron = material("training_dummy_iron", IRON, rough=0.45, metal=0.85, vary=0.35, scale=25, crevice=0.8)
    dark = material("training_dummy_iron_dark", IRON_DARK, rough=0.6, metal=0.6, vary=0.2, scale=20)
    paint = material("training_dummy_paint", PAINT, rough=0.8, vary=0.4, scale=18)
    shield_wood = material("training_dummy_shield_wood", SHIELD_WOOD, vary=0.3, scale=14)
    leather = material("training_dummy_leather", LEATHER, rough=0.7, vary=0.25, scale=30)

    # The stand: two crossed feet, the post, a collar and four short braces.
    box("foot_x", (FOOT_X, 0.08, FOOT_H), (0, 0, FOOT_H / 2), old, rot=(0, 0, rnd.uniform(-2, 2)), bevel=0.012)
    box("foot_y", (0.08, FOOT_Y, FOOT_H - 0.004), (0, 0, (FOOT_H - 0.004) / 2), wood, bevel=0.012)
    box("post", (POST, POST, POST_H - 0.02), (0, 0, (POST_H - 0.02) / 2 + 0.01), wood, rot=(0, 0, 3), bevel=0.012)
    for k in range(4):
        a = math.radians(90 * k)
        L = (FOOT_X if k % 2 == 0 else FOOT_Y) / 2
        _rod(f"brace_{k}", 0.022, (0.78 * L * math.cos(a), 0.78 * L * math.sin(a), FOOT_H - 0.01),
             (0.05 * math.cos(a), 0.05 * math.sin(a), 0.34), old, segments=6)

    # The arms: a crossbar through the post, sack sleeves bound with rope, straw out of the ends.
    _rod("crossbar", 0.03, (-ARM_L / 2, 0, ARM_Z), (ARM_L / 2, 0, ARM_Z), old, segments=8)
    for side in (-1, 1):
        x0, x1 = side * 0.1, side * (ARM_L / 2 - 0.02)
        _rod(f"sleeve_{side}", SLEEVE_R, (x0, 0, ARM_Z), (x1, 0, ARM_Z), sack, segments=10, bevel=0.012,
             r_top=SLEEVE_R * 0.85)
        for f in (0.35, 0.95):
            x = x0 + (x1 - x0) * f
            torus(f"sleeve_tie_{side}_{f}", SLEEVE_R * (1.02 - 0.13 * f), 0.011, (x, 0, ARM_Z), rope,
                  rot=(0, 90, 0), major=14, minor=6)
        for i in range(6):
            a = 2 * math.pi * i / 6 + rnd.uniform(-0.3, 0.3)
            y, z = 0.03 * math.cos(a), 0.03 * math.sin(a)
            tip = (side * (ARM_L / 2 + rnd.uniform(0.02, 0.045)), y * 1.8, ARM_Z + z * 1.8)
            _rod(f"arm_straw_{side}_{i}", 0.014, (x1 - side * 0.02, y, ARM_Z + z), tip, straw, segments=5, bevel=0,
                 r_top=0.002)

    # The body: a stuffed sack, darker patches where it is mended, tied at the waist, straw spilling below.
    blob("body", BODY_R, (0, 0, BODY_Z), sack, squash=(1.0, 0.7, 1.5), subdiv=3, seed=5, jitter=0.04)
    for i, (x, z) in enumerate([(-0.08, 1.4), (0.1, 1.14)]):
        box(f"patch_{i}", (0.09, 0.02, 0.08), (x, -0.12, z), sack_dark, rot=(rnd.uniform(-8, 8), 0,
                                                                             rnd.uniform(-10, 10)), bevel=0.004)
    torus("waist_rope", 0.15, 0.018, (0, 0, BODY_Z - 0.2), rope, major=24, minor=6).scale = (1, 0.72, 1)
    for i in range(10):
        a = 2 * math.pi * i / 10 + rnd.uniform(-0.2, 0.2)
        x, y = 0.09 * math.cos(a), 0.06 * math.sin(a)
        _rod(f"body_straw_{i}", 0.02, (x, y, BODY_Z - 0.27), (x * 1.9, y * 1.9, BODY_Z - rnd.uniform(0.42, 0.5)),
             straw, segments=5, bevel=0, r_top=0.003)

    # The head: a sack tied at the neck, under a dented pot helm with an eye slit and a nose strip.
    torus("neck_rope", 0.065, 0.014, (0, 0, HEAD_Z - 0.105), rope, major=16, minor=6)
    blob("head", HEAD_R, (0, 0, HEAD_Z), sack, squash=(1, 0.95, 1.05), subdiv=2, seed=9, jitter=0.05)

    def helm():
        z0 = -0.05
        cylinder("helm", HELM_R, HELM_H, (0, 0, z0), iron, r_top=HELM_R * 0.94, segments=16, bevel=0.006)
        cylinder("helm_top", HELM_R * 0.94 + 0.004, 0.014, (0, 0, z0 + HELM_H - 0.004), iron, r_top=HELM_R * 0.8,
                 segments=16, bevel=0.004)
        torus("helm_band", HELM_R + 0.003, 0.009, (0, 0, z0 + 0.012), dark, major=16, minor=6)
        box("helm_slit", (0.2, 0.03, 0.02), (0, -HELM_R + 0.008, z0 + 0.1), dark, bevel=0.003)
        box("helm_nose", (0.03, 0.02, HELM_H - 0.02), (0, -HELM_R + 0.004, z0 + HELM_H / 2), iron, bevel=0.004)
        for i in range(6):  # breathing holes below the slit
            box(f"helm_hole_{i}", (0.008, 0.02, 0.008), ((i % 3 - 1) * 0.022 + (0.06 if i < 3 else -0.06),
                                                         -HELM_R + 0.012, z0 + 0.045), dark, bevel=0)
        blob("helm_dent", 0.03, (0.07, -0.1, z0 + HELM_H - 0.02), dark, squash=(1.2, 0.5, 0.6), subdiv=1, seed=2)

    _moved(helm, Matrix.Translation((0.005, 0, HEAD_Z)) @ Matrix.Rotation(math.radians(7), 4, "X") @
           Matrix.Rotation(math.radians(-6), 4, "Y") @ Matrix.Rotation(math.radians(8), 4, "Z"))

    # The shield on its left arm (-x), hung from the arm by its strap, face towards -y.
    _moved(lambda: _shield(rnd, shield_wood, paint, iron, dark, leather),
           Matrix.Translation((-0.23, -0.175, ARM_Z - SHIELD_R + 0.02)) @ Matrix.Rotation(math.radians(-8), 4, "Z") @
           Matrix.Rotation(math.radians(-6), 4, "X") @ Matrix.Rotation(math.radians(12), 4, "Y"))
    _rod("shield_strap", 0.012, (-0.2, -0.16, ARM_Z), (-0.2, -0.04, ARM_Z + SLEEVE_R * 0.9), leather, segments=6)
