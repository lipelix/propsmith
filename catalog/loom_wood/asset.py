"""An upright warp-weighted loom: two timber uprights on foot beams with back braces, a cloth beam across the top with
a half-woven striped cloth hanging from it, and below the cloth the warp threads hanging down in two layers, the back
layer over a shed rod, each bundle tied to a clay doughnut weight; a heddle rod rests on brackets in front."""
import math
import random

import bpy
from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# About 1.4 x 0.6 x 1.8 m; the cloth faces the front (-y).
POST_X = 0.62  # the uprights' centres
POST_W = 0.09
POST_H = 1.78
FOOT_Y = 0.29  # the foot beams run to +-FOOT_Y
BEAM_Z, BEAM_R = 1.64, 0.055  # the cloth beam
BEAM_X = 0.7
CLOTH_X = 0.53  # half-width of the cloth and warp
FELL_Z = 1.02  # the bottom edge of the woven cloth
SHED_Z, SHED_Y = 0.84, 0.075  # the shed rod, behind the uprights
HEDDLE_Z, HEDDLE_Y = 0.94, -0.1  # the heddle rod, in front
WEIGHTS = 7  # per layer
WEIGHT_Z = 0.3  # around this height
THREADS = 3  # warp threads tied to each weight

WOOD = (0.2, 0.125, 0.065)  # linear RGB
WOOD_OLD = (0.16, 0.105, 0.062)
POLISHED = (0.26, 0.165, 0.085)
WOOL = (0.42, 0.37, 0.28)
WOOL_BLUE = (0.09, 0.12, 0.16)
WOOL_RED = (0.3, 0.085, 0.05)
WARP = (0.38, 0.34, 0.26)
CLAY = (0.31, 0.16, 0.085)
CLAY_DARK = (0.24, 0.13, 0.075)


def _settle(obj, z_min=0.0):
    """Move `obj` up or down so its lowest point is at `z_min`."""
    bpy.context.view_layer.update()
    lowest = min((obj.matrix_world @ v.co).z for v in obj.data.vertices)
    obj.location.z += z_min - lowest
    return obj


def _rod(name, r, a, b, mat, segments=8, bevel=0.004, r_top=None):
    """A round rod from point `a` to point `b`."""
    d = Vector(b) - Vector(a)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return cylinder(name, r, d.length, a, mat, r_top=r_top, segments=segments,
                    rot=tuple(math.degrees(x) for x in rot), bevel=bevel)


def _thread(name, a, b, mat, w=0.005):
    """A thin square-section warp thread from `a` to `b`."""
    a, b = Vector(a), Vector(b)
    d = b - a
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return box(name, (w, w, d.length), tuple((a + b) / 2), mat, rot=tuple(math.degrees(x) for x in rot), bevel=0)


@prop
def loom_wood():
    rnd = random.Random(13)
    wood = material("loom_wood_wood", WOOD, vary=0.28, scale=14)
    old = material("loom_wood_wood_old", WOOD_OLD, vary=0.3, scale=11)
    polished = material("loom_wood_polished", POLISHED, rough=0.5, vary=0.2, scale=16)
    wool = material("loom_wood_cloth", WOOL, rough=0.95, vary=0.2, scale=60, crevice=0.5)
    blue = material("loom_wood_cloth_blue", WOOL_BLUE, rough=0.95, vary=0.2, scale=60, crevice=0.5)
    red = material("loom_wood_cloth_red", WOOL_RED, rough=0.95, vary=0.2, scale=60, crevice=0.5)
    warp = material("loom_wood_warp", WARP, rough=0.95, vary=0.15, scale=40, crevice=0.3)
    clay = material("loom_wood_clay", CLAY, rough=0.9, vary=0.3, scale=18, crevice=0.6)
    clay_dark = material("loom_wood_clay_dark", CLAY_DARK, rough=0.9, vary=0.3, scale=18, crevice=0.6)

    # The frame: two uprights on foot beams, each braced from the back of its foot, and a top rail.
    for s in (-1, 1):
        x = s * POST_X
        box(f"post_{s}", (POST_W, POST_W, POST_H), (x, 0, POST_H / 2), wood if s < 0 else old,
            rot=(0, 0, rnd.uniform(-2, 2)), bevel=0.012)
        box(f"foot_{s}", (0.1, 2 * FOOT_Y, 0.085), (x, 0, 0.0425), old, bevel=0.012)
        brace = Vector((x, FOOT_Y - 0.05, 0.07)), Vector((x, POST_W / 2, 0.78))
        _settle(box(f"brace_{s}", (0.06, 0.05, (brace[1] - brace[0]).length),
                    tuple((brace[0] + brace[1]) / 2), wood,
                    rot=(math.degrees(math.atan2(brace[0].y - brace[1].y, brace[1].z - brace[0].z)), 0, 0),
                    bevel=0.008), 0.07)
        box(f"front_block_{s}", (0.1, 0.07, 0.12), (x, -POST_W / 2 - 0.035, 0.145), wood, bevel=0.01)
        # Brackets: behind for the shed rod, in front for the heddle rod.
        box(f"shed_bracket_{s}", (0.06, 0.09, 0.05), (x, POST_W / 2 + 0.04, SHED_Z - 0.04), old, bevel=0.008)
        box(f"heddle_bracket_{s}", (0.06, 0.12, 0.05), (x, -POST_W / 2 - 0.055, HEDDLE_Z - 0.04), old,
            bevel=0.008)
    box("top_rail", (2 * POST_X + 0.12, 0.08, 0.07), (0, 0, POST_H - 0.035), wood, bevel=0.012)

    # The cloth beam with the woven cloth rolled on it and hanging down to the fell, two coloured bands in it.
    _rod("cloth_beam", BEAM_R, (-BEAM_X, 0, BEAM_Z), (BEAM_X, 0, BEAM_Z), polished, segments=14, bevel=0.006)
    _rod("cloth_roll", BEAM_R + 0.03, (-CLOTH_X, 0, BEAM_Z), (CLOTH_X, 0, BEAM_Z), wool, segments=14, bevel=0.01)
    for s in (-1, 1):
        _rod(f"beam_peg_{s}", 0.012, (s * (BEAM_X - 0.03), 0, BEAM_Z - 0.09), (s * (BEAM_X - 0.03), 0, BEAM_Z + 0.09),
             old, segments=6, bevel=0)
    cloth_top = BEAM_Z - 0.02
    yc = -BEAM_R - 0.012
    box("cloth", (2 * CLOTH_X, 0.014, cloth_top - FELL_Z), (0, yc, (cloth_top + FELL_Z) / 2), wool, bevel=0.003)
    for i, (z, h, mat) in enumerate([(1.42, 0.07, blue), (1.33, 0.025, red), (1.18, 0.07, blue),
                                     (1.09, 0.025, red)]):
        box(f"band_{i}", (2 * CLOTH_X + 0.004, 0.018, h), (0, yc, z), mat, bevel=0)
    # The cloth's last weft rolls into the beam's front face at the fell.
    _rod("fell", 0.01, (-CLOTH_X, yc, FELL_Z), (CLOTH_X, yc, FELL_Z), wool, segments=6, bevel=0)

    # The heddle and shed rods.
    _rod("heddle_rod", 0.022, (-POST_X - 0.05, HEDDLE_Y, HEDDLE_Z), (POST_X + 0.05, HEDDLE_Y, HEDDLE_Z), polished,
         segments=10)
    _rod("shed_rod", 0.03, (-POST_X - 0.05, SHED_Y, SHED_Z), (POST_X + 0.05, SHED_Y, SHED_Z), wood, segments=10)

    # The warp: two layers of thread bundles; the front hangs straight down, the back runs over the shed rod.
    pitch = 2 * CLOTH_X / (2 * WEIGHTS * THREADS)
    for layer, (wy, mats) in enumerate([(yc - 0.01, (clay, clay_dark)), (SHED_Y + 0.01, (clay_dark, clay))]):
        for w in range(WEIGHTS):
            wx = -CLOTH_X + (2 * w + 0.5 + layer) * THREADS * pitch + THREADS * pitch / 2 - pitch / 2
            wz = WEIGHT_Z + rnd.uniform(-0.05, 0.05)
            top = wz + 0.075
            for t in range(THREADS):
                tx = -CLOTH_X + ((2 * w + layer) * THREADS + t + 0.5) * pitch * 1.0
                start = Vector((tx, yc, FELL_Z))
                knot = Vector((wx, wy, top))
                if layer:
                    over = Vector((tx, SHED_Y + 0.03, SHED_Z + 0.02))
                    _thread(f"warp_{layer}_{w}_{t}_a", start, over, warp)
                    _thread(f"warp_{layer}_{w}_{t}_b", over, knot, warp)
                    # A heddle leash from the rod in front to the back thread.
                    if t == 1:
                        _thread(f"leash_{w}", (tx, HEDDLE_Y, HEDDLE_Z - 0.01), (tx, SHED_Y + 0.02, SHED_Z + 0.06),
                                warp, w=0.004)
                else:
                    _thread(f"warp_{layer}_{w}_{t}", start, knot, warp)
            _thread(f"tie_{layer}_{w}", (wx, wy, top + 0.004), (wx, wy, wz + 0.03), warp, w=0.007)
            torus(f"weight_{layer}_{w}", 0.034, 0.026, (wx, wy, wz), mats[w % 2],
                  rot=(90, 0, rnd.uniform(-15, 15)), major=10, minor=6)
