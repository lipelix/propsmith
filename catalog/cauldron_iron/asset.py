"""A black iron cauldron hanging from a tripod over a small fire: three wrought iron legs lashed at the top with a
hook and a short chain, a round-bellied pot on three stubby feet with a thick rim, two lugs and a bail handle, a dark
green brew with a few bubbles; under it a ring of blackened stones, ash, embers, crossed sticks and low flames."""
import math
import random

import bpy
from mathutils import Vector

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall size: about 0.9 m across the tripod's feet, the apex at about 1.2 m.
FOOT_R = 0.43  # radius of the tripod's feet
APEX_Z = 1.16
LEG_R = 0.018
POT_R = 0.21  # radius of the cauldron's belly
POT_C = 0.5  # height of the belly's centre
POT_CUT = 0.13  # the mouth, above the belly's centre
RIM_R = math.sqrt(POT_R**2 - POT_CUT**2)
BAIL_TOP = 0.86
RING_R, STONES = 0.27, 9  # the stones round the fire
ASH_R, ASH_H = 0.22, 0.03
FLAME_TOP = 0.27

IRON = (0.035, 0.034, 0.033)  # linear RGB
IRON_RUST = (0.09, 0.05, 0.03)
BREW = (0.09, 0.2, 0.05)
BREW_FOAM = (0.2, 0.32, 0.12)
STONE = (0.27, 0.25, 0.22)
SOOT = (0.06, 0.055, 0.05)
ASH = (0.15, 0.143, 0.13)
LOG = (0.15, 0.09, 0.05)
CHAR = (0.05, 0.042, 0.038)
EMBER = (0.5, 0.15, 0.03)
FLAME = (0.5, 0.28, 0.035)
ROPE = (0.3, 0.23, 0.13)


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
def cauldron_iron():
    rnd = random.Random(7)
    iron = material("cauldron_iron_iron", IRON, rough=0.6, vary=0.2, scale=12, metal=0.5, crevice=0.6)
    rust = material("cauldron_iron_rust", IRON_RUST, rough=0.8, vary=0.3, scale=16, metal=0.3)
    brew = material("cauldron_iron_brew", BREW, rough=0.2, vary=0.3, scale=9, crevice=0.2)
    foam = material("cauldron_iron_foam", BREW_FOAM, rough=0.3, vary=0.2, scale=20, crevice=0.2)
    stone = material("cauldron_iron_stone", STONE, rough=0.9, vary=0.28, scale=9, crevice=0.7)
    soot = material("cauldron_iron_soot", SOOT, rough=0.9, vary=0.3, scale=12, crevice=0.5)
    ash = material("cauldron_iron_ash", ASH, vary=0.3, scale=16, crevice=0.6)
    log = material("cauldron_iron_log", LOG, vary=0.3, scale=18)
    char = material("cauldron_iron_char", CHAR, rough=0.7, vary=0.3, scale=20)
    ember = material("cauldron_iron_ember", EMBER, rough=0.6, vary=0.35, scale=14, crevice=0.2)
    flame = material("cauldron_iron_flame", FLAME, rough=0.5, vary=0.3, scale=10, crevice=0.1)
    rope = material("cauldron_iron_rope", ROPE, rough=0.95, vary=0.25, scale=40)

    # The tripod: three legs from the ground to a lashed apex, a ring and a hook under it.
    apex = Vector((0, 0, APEX_Z))
    for i in range(3):
        a = math.radians(90 + 120 * i + rnd.uniform(-4, 4))
        foot = Vector((FOOT_R * math.cos(a), FOOT_R * math.sin(a), 0))
        top = apex + (apex - foot).normalized() * 0.03  # the legs cross a little above the lashing
        top.z = min(top.z, APEX_Z + 0.02)
        _settle(_rod(f"leg_{i}", LEG_R, foot, top, iron, r_top=LEG_R * 0.8), 0)
        _settle(_rod(f"leg_{i}_foot", LEG_R * 1.4, foot, foot + (apex - foot).normalized() * 0.05, rust,
                     bevel=0.003), 0)
    cylinder("lashing", 0.034, 0.06, (0, 0, APEX_Z - 0.08), rope, segments=10, bevel=0.004)
    torus("apex_ring", 0.035, 0.008, (0, 0, APEX_Z - 0.09), iron, major=12, minor=6)

    # A short chain of links from the apex ring to the bail.
    link_h = 0.05
    z = APEX_Z - 0.12
    n = 0
    while z - link_h / 2 > BAIL_TOP + 0.01:
        torus(f"chain_{n}", link_h / 2 - 0.006, 0.006, (0, 0, z), iron, rot=(90, 0, 90 * (n % 2)), major=10,
              minor=5)
        z -= link_h - 0.014
        n += 1
    hook = z + link_h / 2 - 0.01
    _rod("hook", 0.007, (0, 0, hook), (0, 0, BAIL_TOP - 0.002), iron, segments=6)

    # The cauldron: a round belly cut off at the mouth, a thick rim, a brew inside, feet and lugs.
    belly = blob("belly", POT_R, (0, 0, POT_C), iron, subdiv=3, seed=1, jitter=0.0)
    for v in belly.data.vertices:
        v.co.z = min(v.co.z, POT_CUT)
    belly.rotation_euler = (0, 0, 0)
    torus("rim", RIM_R + 0.004, 0.014, (0, 0, POT_C + POT_CUT), iron, major=28, minor=8)
    cylinder("brew", RIM_R - 0.004, 0.012, (0, 0, POT_C + POT_CUT - 0.016), brew, segments=24, bevel=0)
    for i in range(6):
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(0, RIM_R - 0.05)
        blob(f"bubble_{i}", rnd.uniform(0.01, 0.022), (d * math.cos(a), d * math.sin(a), POT_C + POT_CUT - 0.002),
             foam, squash=(1, 1, 0.55), subdiv=1, seed=30 + i, jitter=0.05)
    for i in range(3):
        a = math.radians(30 + 120 * i)
        r = POT_R * 0.62
        _rod(f"pot_foot_{i}", 0.02, (r * math.cos(a), r * math.sin(a), POT_C - POT_R * 0.7),
             (r * 1.15 * math.cos(a), r * 1.15 * math.sin(a), POT_C - POT_R - 0.05), iron, segments=6,
             r_top=0.014)
    for s in (-1, 1):
        x = s * (RIM_R + 0.01)
        box(f"lug_{s}", (0.04, 0.035, 0.035), (x, 0, POT_C + POT_CUT - 0.03), iron, bevel=0.006)
        torus(f"ear_{s}", 0.018, 0.006, (x + s * 0.016, 0, POT_C + POT_CUT - 0.02), iron, rot=(90, 0, 0), major=10,
              minor=5)

    # The bail: an arc of short rods from ear to ear, its top hanging on the hook.
    ex = RIM_R + 0.026
    base = POT_C + POT_CUT - 0.02
    pts = []
    for k in range(9):
        t = math.pi * k / 8
        pts.append(Vector((-ex * math.cos(t), 0, base + (BAIL_TOP - base) * math.sin(t))))
    for k in range(8):
        _rod(f"bail_{k}", 0.006, pts[k], pts[k + 1], iron, segments=6, bevel=0)

    # The fire: blackened stones round an ash bed, embers, three crossed sticks and low flames under the pot.
    for i in range(STONES):
        a = 2 * math.pi * (i + rnd.uniform(-0.15, 0.15)) / STONES
        rr = RING_R + rnd.uniform(-0.02, 0.02)
        r = rnd.uniform(0.055, 0.075)
        st = blob(f"stone_{i}", r, (rr * math.cos(a), rr * math.sin(a), 0), soot if i % 3 == 0 else stone,
                  squash=(1.25, 0.85, 0.75), subdiv=2, seed=10 + i, jitter=0.14)
        st.rotation_euler = (0, 0, a + math.pi / 2)
        _settle(st, -0.004)
    _settle(blob("ash_bed", ASH_R, (0, 0, 0), ash, squash=(1, 1, ASH_H / ASH_R), subdiv=2, seed=2, jitter=0.08),
            -0.004)
    _settle(blob("embers", 0.13, (0, 0, 0), ember, squash=(1.1, 1.0, 0.3), subdiv=2, seed=3, jitter=0.25), 0.008)
    for i in range(3):
        a = math.radians(20 + 120 * i + rnd.uniform(-10, 10))
        foot = Vector((0.2 * math.cos(a), 0.2 * math.sin(a), 0.03))
        tip = Vector((-0.04 * math.cos(a), -0.04 * math.sin(a), 0.1))
        _settle(_rod(f"stick_{i}", 0.022, foot, tip, char if i == 1 else log, segments=8), 0.006)
    for i, (fx, fy, fr, tall) in enumerate([(0.0, 0.0, 0.05, 1.0), (0.06, -0.03, 0.04, 0.7),
                                            (-0.05, 0.04, 0.04, 0.65), (-0.02, -0.06, 0.035, 0.5)]):
        h = (FLAME_TOP - 0.05) * tall
        blob(f"flame_{i}", fr, (fx, fy, 0.05 + h / 2), flame, squash=(0.85, 0.8, h / (2 * fr)), subdiv=2,
             seed=70 + i, jitter=0.12)

    anchor("fire:hearth", (0, 0, ASH_H + 0.02), size=(0.17, 0.17, POT_C - POT_R - ASH_H))
    anchor("light:fire", (0, 0, 0.2))
