"""A camp cooking spit over a small fire: two forked stakes driven into the ground, an iron spit laid across their forks
with a bent crank at one end and a trussed bird on it, a sooty iron pot hanging from the middle of the spit by its bail
and a hook; under it a ring of blackened stones, ash, embers, crossed sticks and low flames."""
import math
import random

import bpy
from mathutils import Vector

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, cylinder, torus

# About 1.2 x 0.6 x 1 m.
STAKE_X = 0.5  # the stakes stand at +-STAKE_X
STAKE_R = 0.028
FORK_Z = 0.78  # where a stake splits
FORK_TOP = 0.96
FORK_SPREAD = 0.07
SPIT_Z = 0.85  # the spit's axis, resting in the forks
SPIT_R = 0.012
SPIT_X = 0.56  # the spit runs to +-SPIT_X, the crank at +x
POT_R = 0.13  # the pot's belly
POT_C = 0.44  # height of the belly's centre
POT_CUT = 0.08  # the mouth, above the belly's centre
RIM_R = math.sqrt(POT_R**2 - POT_CUT**2)
RING_R, STONES = 0.21, 9
ASH_R, ASH_H = 0.18, 0.03
FLAME_TOP = 0.24

WOOD = (0.17, 0.1, 0.052)  # linear RGB: barked stakes
WOOD_CUT = (0.3, 0.2, 0.11)
IRON = (0.035, 0.034, 0.033)
IRON_RUST = (0.09, 0.05, 0.03)
STONE = (0.27, 0.25, 0.22)
SOOT = (0.06, 0.055, 0.05)
ASH = (0.15, 0.143, 0.13)
LOG = (0.15, 0.09, 0.05)
CHAR = (0.05, 0.042, 0.038)
EMBER = (0.5, 0.15, 0.03)
FLAME = (0.5, 0.28, 0.035)
ROAST = (0.22, 0.095, 0.04)  # browned skin
STEW = (0.2, 0.11, 0.05)
TWINE = (0.3, 0.23, 0.13)


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


@prop
def cooking_spit():
    rnd = random.Random(23)
    wood = material("cooking_spit_wood", WOOD, rough=0.9, vary=0.3, scale=18, crevice=0.6)
    cut = material("cooking_spit_wood_cut", WOOD_CUT, vary=0.25, scale=24)
    iron = material("cooking_spit_iron", IRON, rough=0.6, vary=0.2, scale=14, metal=0.5, crevice=0.6)
    rust = material("cooking_spit_rust", IRON_RUST, rough=0.8, vary=0.3, scale=16, metal=0.3)
    stone = material("cooking_spit_stone", STONE, rough=0.9, vary=0.28, scale=9, crevice=0.7)
    soot = material("cooking_spit_soot", SOOT, rough=0.9, vary=0.3, scale=12, crevice=0.5)
    ash = material("cooking_spit_ash", ASH, vary=0.3, scale=16, crevice=0.6)
    log = material("cooking_spit_log", LOG, vary=0.3, scale=18)
    char = material("cooking_spit_char", CHAR, rough=0.7, vary=0.3, scale=20)
    ember = material("cooking_spit_ember", EMBER, rough=0.6, vary=0.35, scale=14, crevice=0.2)
    flame = material("cooking_spit_flame", FLAME, rough=0.5, vary=0.3, scale=10, crevice=0.1)
    roast = material("cooking_spit_roast", ROAST, rough=0.45, vary=0.35, scale=14, crevice=0.6)
    stew = material("cooking_spit_stew", STEW, rough=0.25, vary=0.3, scale=12, crevice=0.2)
    twine = material("cooking_spit_twine", TWINE, rough=0.95, vary=0.25, scale=40)

    # Two forked stakes: a straight shaft, then two prongs spreading across the spit (along y).
    for s in (-1, 1):
        x = s * STAKE_X
        lean = rnd.uniform(-0.015, 0.015)
        top = Vector((x + lean, 0, FORK_Z))
        _rod(f"stake_{s}", STAKE_R, (x, 0, 0), top, wood, segments=8)
        cylinder(f"stake_{s}_point", STAKE_R * 1.08, 0.04, (x, 0, 0), wood, segments=8, bevel=0.004)
        for k in (-1, 1):
            tip = Vector((x + lean, k * FORK_SPREAD, FORK_TOP + rnd.uniform(-0.03, 0)))
            _rod(f"prong_{s}_{k}", STAKE_R * 0.7, top - Vector((0, 0, 0.03)), tip, wood, segments=7,
                 r_top=STAKE_R * 0.5)
            cylinder(f"prong_{s}_{k}_end", STAKE_R * 0.5, 0.006, tuple(tip), cut, segments=7, bevel=0)

    # The spit, its crank at +x, and the trussed bird skewered on it at -x.
    _rod("spit", SPIT_R, (-SPIT_X, 0, SPIT_Z), (SPIT_X - 0.02, 0, SPIT_Z), iron, segments=8, bevel=0.003)
    crank_a = Vector((SPIT_X - 0.02, 0, SPIT_Z))
    crank_b = crank_a + Vector((0, 0, -0.13))
    _rod("crank_arm", SPIT_R, crank_a + Vector((0, 0, SPIT_R)), crank_b, iron, segments=8, bevel=0.003)
    _rod("crank_grip", SPIT_R * 1.6, crank_b + Vector((-0.004, 0, 0)), crank_b + Vector((0.05, 0, 0)), rust,
         segments=8)
    bird_x = -0.28
    blob("bird", 0.08, (bird_x, 0, SPIT_Z), roast, squash=(1.5, 1.05, 0.85), subdiv=2, seed=5, jitter=0.07)
    for k in (-1, 1):
        a = Vector((bird_x - 0.06, k * 0.04, SPIT_Z + 0.01))
        b = Vector((bird_x - 0.17, k * 0.065, SPIT_Z + 0.08))
        _rod(f"leg_{k}", 0.028, a, b, roast, segments=8, r_top=0.013, bevel=0.006)
        blob(f"knuckle_{k}", 0.016, tuple(b), cut, subdiv=1, seed=8 + k, jitter=0.1)
        torus(f"truss_{k}", 0.075 * (1 - 0.1 * abs(k)), 0.005, (bird_x + k * 0.04, 0, SPIT_Z), twine,
              rot=(0, 90, 0), major=14, minor=4)

    # The pot: a round belly cut off at the mouth, a rim, stew inside, hanging by a bail and a hook from the spit.
    belly = blob("pot_belly", POT_R, (0, 0, POT_C), iron, subdiv=3, seed=1, jitter=0.0)
    for v in belly.data.vertices:
        v.co.z = min(v.co.z, POT_CUT)
    belly.rotation_euler = (0, 0, 0)
    mouth = POT_C + POT_CUT
    torus("pot_rim", RIM_R + 0.003, 0.01, (0, 0, mouth), iron, major=24, minor=6)
    cylinder("stew", RIM_R - 0.004, 0.01, (0, 0, mouth - 0.014), stew, segments=20, bevel=0)
    bail_top = SPIT_Z - 0.12
    ex = RIM_R + 0.016
    for s in (-1, 1):
        torus(f"pot_ear_{s}", 0.013, 0.005, (s * ex, 0, mouth - 0.012), iron, rot=(90, 0, 0), major=10, minor=5)
    pts = [Vector((-ex * math.cos(math.pi * k / 8), 0, mouth - 0.012 + (bail_top - mouth + 0.012)
                   * math.sin(math.pi * k / 8))) for k in range(9)]
    for k in range(8):
        _rod(f"bail_{k}", 0.005, pts[k], pts[k + 1], iron, segments=6, bevel=0)
    _rod("hook", 0.006, (0, 0, bail_top - 0.004), (0, 0, SPIT_Z - SPIT_R + 0.002), iron, segments=6, bevel=0)
    torus("hook_eye", 0.018, 0.005, (0, 0, SPIT_Z), iron, rot=(90, 0, 0), major=10, minor=5)
    torus("hook_curl", 0.014, 0.005, (0, 0, bail_top + 0.004), iron, rot=(90, 0, 0), major=10, minor=5)

    # The fire: blackened stones round an ash bed, embers, crossed sticks and low flames under the pot.
    for i in range(STONES):
        a = 2 * math.pi * (i + rnd.uniform(-0.15, 0.15)) / STONES
        rr = RING_R + rnd.uniform(-0.015, 0.015)
        st = blob(f"stone_{i}", rnd.uniform(0.045, 0.06), (rr * math.cos(a), rr * math.sin(a), 0),
                  soot if i % 3 == 0 else stone, squash=(1.25, 0.85, 0.75), subdiv=2, seed=10 + i, jitter=0.14)
        st.rotation_euler = (0, 0, a + math.pi / 2)
        _settle(st, -0.004)
    _settle(blob("ash_bed", ASH_R, (0, 0, 0), ash, squash=(1, 1, ASH_H / ASH_R), subdiv=2, seed=2, jitter=0.08),
            -0.004)
    _settle(blob("embers", 0.11, (0, 0, 0), ember, squash=(1.1, 1.0, 0.3), subdiv=2, seed=3, jitter=0.25), 0.008)
    for i in range(3):
        a = math.radians(40 + 120 * i + rnd.uniform(-10, 10))
        foot = Vector((0.17 * math.cos(a), 0.17 * math.sin(a), 0.03))
        tip = Vector((-0.03 * math.cos(a), -0.03 * math.sin(a), 0.09))
        _settle(_rod(f"stick_{i}", 0.019, foot, tip, char if i == 1 else log, segments=8), 0.006)
    for i, (fx, fy, fr, tall) in enumerate([(0.0, 0.0, 0.045, 1.0), (0.05, -0.03, 0.035, 0.7),
                                            (-0.045, 0.035, 0.035, 0.65), (-0.02, -0.05, 0.03, 0.5)]):
        h = (FLAME_TOP - 0.05) * tall
        blob(f"flame_{i}", fr, (fx, fy, 0.05 + h / 2), flame, squash=(0.85, 0.8, h / (2 * fr)), subdiv=2,
             seed=70 + i, jitter=0.12)

    anchor("fire:camp", (0, 0, ASH_H + 0.02), size=(0.15, 0.15, POT_C - POT_R - ASH_H))
    anchor("light:fire", (0, 0, 0.18))
