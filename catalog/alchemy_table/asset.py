"""An alchemist's stained oak workbench, the worker's side on -y: a thick plank top on four square legs with a low
shelf of clay jars, a back rack of two posts and a shelf of bottles; on the top a glass retort in an iron ring stand
over a small oil burner, its long neck running down into a receiving flask, round and conical flasks of red, blue and
green brews, a stone mortar with its pestle, and dark stains and scorch rings soaked into the wood."""
import math
import random

from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall size: 1.5 m wide (x), 0.7 m deep (y), the top at 0.86 m, the back rack to about 1.3 m.
W, D = 1.5, 0.7
TOP_Z, TOP_T = 0.86, 0.05
PLANKS = 4
LEG = 0.08
LEG_X, LEG_Y = W / 2 - 0.07, D / 2 - 0.07
LOW_Z, LOW_T = 0.16, 0.03  # the low shelf between the legs
RACK_H = 1.3  # top of the back rack's posts
RACK_SHELF_Z = 1.1  # top surface of the rack's shelf
RACK_D = 0.16  # depth of the rack's shelf
POST = 0.06
BACK_Y = D / 2

BURNER_AT = (-0.36, -0.06)
RING_Z = 0.17  # height of the retort's ring stand above the top
BULB_R = 0.085
RECEIVER_AT = (0.0, -0.1)
MORTAR_AT = (0.42, 0.14)

OAK = (0.19, 0.115, 0.06)  # linear RGB
OAK_OLD = (0.145, 0.09, 0.05)
OAK_TOP = (0.21, 0.13, 0.068)
STAIN = (0.07, 0.06, 0.045)
STAIN_GREEN = (0.08, 0.11, 0.05)
IRON = (0.045, 0.043, 0.04)
BRASS = (0.38, 0.26, 0.09)
GLASS = (0.28, 0.33, 0.3)  # pale, slightly green glass
BREWS = ((0.36, 0.05, 0.04), (0.06, 0.1, 0.33), (0.1, 0.28, 0.07))  # red, blue, green
AMBER = (0.42, 0.2, 0.05)
CORK = (0.3, 0.2, 0.11)
STONE = (0.3, 0.28, 0.25)
GROUND = (0.22, 0.2, 0.12)  # ground herbs in the mortar
CLAY = (0.38, 0.17, 0.08)
CLAY_PALE = (0.4, 0.3, 0.18)
FLAME = (0.5, 0.28, 0.035)


def _rod(name, r, a, b, mat, segments=8, bevel=0.003, r_top=None):
    """A round rod from point `a` to point `b`."""
    d = Vector(b) - Vector(a)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return cylinder(name, r, d.length, a, mat, r_top=r_top, segments=segments,
                    rot=tuple(math.degrees(x) for x in rot), bevel=bevel)


def _flask(name, x, y, z, r, kind, brew, glass, cork):
    """A flask standing on `z`: a round-bellied one (kind 0), a conical one (1) or a tall bottle (2), its body the
    colour of the brew in it, a pale glass neck and a cork."""
    if kind == 0:
        blob(f"{name}_body", r, (x, y, z + r * 0.95), brew, squash=(1, 1, 1), subdiv=2, seed=1, jitter=0)
        neck_z, neck_h = z + r * 1.75, r * 1.3
    elif kind == 1:
        cylinder(f"{name}_body", r, r * 1.5, (x, y, z), brew, r_top=r * 0.3, segments=10, bevel=0)
        neck_z, neck_h = z + r * 1.48, r * 0.9
    else:
        cylinder(f"{name}_body", r, r * 3.2, (x, y, z), brew, r_top=r * 0.95, segments=8, bevel=0)
        cylinder(f"{name}_shoulder", r * 0.95, r * 0.6, (x, y, z + r * 3.2 - 0.002), glass, r_top=r * 0.35,
                 segments=8, bevel=0)
        neck_z, neck_h = z + r * 3.75, r * 0.7
    cylinder(f"{name}_neck", r * 0.3, neck_h, (x, y, neck_z), glass, r_top=r * 0.28, segments=8, bevel=0)
    cylinder(f"{name}_cork", r * 0.26, 0.025, (x, y, neck_z + neck_h - 0.01), cork, r_top=r * 0.32, segments=8,
             bevel=0)


def _jar(name, x, y, z, r, h, clay, cork):
    cylinder(f"{name}_body", r * 0.85, h * 0.7, (x, y, z), clay, r_top=r, segments=10, bevel=0)
    cylinder(f"{name}_shoulder", r, h * 0.25, (x, y, z + h * 0.7 - 0.002), clay, r_top=r * 0.6, segments=10,
             bevel=0)
    cylinder(f"{name}_lid", r * 0.62, h * 0.08, (x, y, z + h * 0.93), cork, segments=10, bevel=0)


@prop
def alchemy_table():
    rnd = random.Random(53)
    oak = material("alchemy_table_oak", OAK, vary=0.25, scale=14)
    old = material("alchemy_table_oak_old", OAK_OLD, vary=0.3, scale=11)
    top_mat = material("alchemy_table_top", OAK_TOP, vary=0.32, scale=10, crevice=0.65)
    stain = material("alchemy_table_stain", STAIN, rough=0.6, vary=0.3, scale=18, crevice=0.3)
    stain_g = material("alchemy_table_stain_green", STAIN_GREEN, rough=0.5, vary=0.3, scale=18, crevice=0.3)
    iron = material("alchemy_table_iron", IRON, rough=0.55, vary=0.12, scale=20, metal=0.6)
    brass = material("alchemy_table_brass", BRASS, rough=0.4, vary=0.2, scale=16, metal=0.7)
    glass = material("alchemy_table_glass", GLASS, rough=0.08, vary=0.08, scale=12, crevice=0.25)
    brews = [material(f"alchemy_table_brew_{i}", c, rough=0.12, vary=0.12, scale=12, crevice=0.3)
             for i, c in enumerate(BREWS)]
    amber = material("alchemy_table_amber", AMBER, rough=0.12, vary=0.1, scale=12, crevice=0.3)
    cork = material("alchemy_table_cork", CORK, rough=0.9, vary=0.3, scale=40)
    stone = material("alchemy_table_stone", STONE, rough=0.9, vary=0.25, scale=14, crevice=0.7)
    ground = material("alchemy_table_ground", GROUND, rough=0.95, vary=0.35, scale=50)
    clay = material("alchemy_table_clay", CLAY, rough=0.9, vary=0.2, scale=8)
    clay_pale = material("alchemy_table_clay_pale", CLAY_PALE, rough=0.9, vary=0.2, scale=8)
    flame = material("alchemy_table_flame", FLAME, rough=0.5, vary=0.3, scale=10, crevice=0.1)

    # The top: thick planks along x, slightly uneven, with stains and scorch rings.
    pw = D / PLANKS
    for i in range(PLANKS):
        y = -D / 2 + pw / 2 + i * pw
        box(f"plank_{i}", (W - rnd.uniform(0, 0.02), pw - 0.005, TOP_T - rnd.uniform(0, 0.004)),
            (rnd.uniform(-0.006, 0.006), y, TOP_Z - TOP_T / 2), old if i == 2 else top_mat,
            rot=(0, 0, rnd.uniform(-0.25, 0.25)), bevel=0.012)
    for i, (sx, sy, sr, m) in enumerate([(-0.36, -0.06, 0.13, stain), (0.18, 0.05, 0.07, stain_g),
                                         (0.55, -0.2, 0.06, stain), (-0.05, 0.22, 0.09, stain_g),
                                         (-0.6, 0.18, 0.05, stain)]):
        blob(f"stain_{i}", sr, (sx, sy, TOP_Z + 0.001), m, squash=(1.2, 0.9, 0.012 / sr), subdiv=1, seed=80 + i,
             jitter=0.2)

    # Four square legs, an apron under the top and a low shelf of jars.
    under = TOP_Z - TOP_T
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        box(f"leg_{i}", (LEG, LEG, under), (sx * LEG_X, sy * LEG_Y, under / 2), oak if i % 2 else old,
            rot=(0, 0, rnd.uniform(-1, 1)), bevel=0.01)
    for s in (-1, 1):
        box(f"apron_x_{s}", (2 * LEG_X - LEG, 0.025, 0.1), (0, s * LEG_Y, under - 0.05), old, bevel=0.005)
        box(f"apron_y_{s}", (0.025, 2 * LEG_Y - LEG, 0.1), (s * LEG_X, 0, under - 0.05), old, bevel=0.005)
    box("low_shelf", (2 * LEG_X - LEG + 0.004, 2 * LEG_Y + LEG - 0.01, LOW_T), (0, 0, LOW_Z - LOW_T / 2), oak,
        bevel=0.006)
    x = -LEG_X + 0.14
    n = 0
    while x < LEG_X - 0.14:
        r = rnd.uniform(0.06, 0.085)
        _jar(f"low_jar_{n}", x, rnd.uniform(-0.08, 0.08), LOW_Z, r, rnd.uniform(0.16, 0.24),
             clay_pale if n % 2 else clay, cork)
        x += 2 * r + rnd.uniform(0.04, 0.14)
        n += 1

    # The back rack: two posts, a shelf of bottles and jars, a top rail.
    py = BACK_Y - POST / 2
    for s in (-1, 1):
        box(f"post_{s}", (POST, POST, RACK_H - TOP_Z), (s * (W / 2 - POST / 2 - 0.02), py, (RACK_H + TOP_Z) / 2),
            oak, bevel=0.008)
    sy = BACK_Y - RACK_D / 2
    box("rack_shelf", (W - 0.04, RACK_D, 0.025), (0, sy, RACK_SHELF_Z - 0.0125), old, bevel=0.006)
    box("rack_rail", (W - 0.04, 0.03, 0.05), (0, py, RACK_H - 0.025), old, bevel=0.006)
    box("rack_back", (W - 0.16, 0.015, 0.06), (0, BACK_Y - 0.0075, RACK_SHELF_Z + 0.03), oak, bevel=0.004)
    x = -W / 2 + 0.12
    n = 0
    while x < W / 2 - 0.1:
        pick = rnd.random()
        if pick < 0.3:
            r = rnd.uniform(0.045, 0.055)
            _jar(f"rack_jar_{n}", x, sy, RACK_SHELF_Z, r, rnd.uniform(0.1, 0.14), clay if n % 3 else clay_pale, cork)
        else:
            r = rnd.uniform(0.028, 0.036)
            kind = 2 if pick < 0.75 else 0
            _flask(f"rack_flask_{n}", x, sy + rnd.uniform(-0.02, 0.02), RACK_SHELF_Z, r if kind == 2 else r * 1.3,
                   kind, amber if pick > 0.9 else rnd.choice(brews), glass, cork)
        x += 2 * r + rnd.uniform(0.04, 0.09)
        n += 1

    # The burner: a squat brass oil lamp with a wick and a flame, under an iron ring stand.
    bx, by = BURNER_AT
    cylinder("burner_base", 0.05, 0.02, (bx, by, TOP_Z), brass, r_top=0.045, segments=12, bevel=0.004)
    cylinder("burner_body", 0.045, 0.04, (bx, by, TOP_Z + 0.018), brass, r_top=0.03, segments=12, bevel=0.004)
    cylinder("burner_collar", 0.012, 0.02, (bx, by, TOP_Z + 0.056), brass, segments=8, bevel=0.002)
    blob("burner_flame", 0.016, (bx, by, TOP_Z + 0.1), flame, squash=(0.8, 0.8, 1.9), subdiv=2, seed=9, jitter=0.1)
    ring_z = TOP_Z + RING_Z
    torus("stand_ring", 0.06, 0.006, (bx, by, ring_z), iron, major=16, minor=6)
    for i in range(3):
        a = math.radians(90 + 120 * i)
        top = (bx + 0.06 * math.cos(a), by + 0.06 * math.sin(a), ring_z)
        foot = (bx + 0.1 * math.cos(a), by + 0.1 * math.sin(a), TOP_Z)
        _rod(f"stand_leg_{i}", 0.006, foot, top, iron, segments=6, bevel=0)

    # The retort: a round bulb sitting in the ring, its neck bending away and down into a receiving flask.
    bulb_c = Vector((bx, by, ring_z + BULB_R * 0.75))
    blob("retort_bulb", BULB_R, bulb_c, brews[2], subdiv=2, seed=2, jitter=0)
    rx, ry = RECEIVER_AT
    recv_r = 0.065
    recv_c = Vector((rx, ry, TOP_Z + recv_r * 0.95))
    neck_start = bulb_c + Vector((0.03, 0, BULB_R * 0.75))
    knee = neck_start + Vector((0.07, 0, 0.06))
    mouth = Vector((rx, ry, TOP_Z + recv_r * 1.75 + 0.04))
    _rod("retort_neck_0", 0.026, neck_start, knee, glass, segments=10, r_top=0.018, bevel=0)
    _rod("retort_neck_1", 0.018, knee, mouth, glass, segments=10, r_top=0.009, bevel=0)
    blob("receiver_body", recv_r, recv_c, brews[2], subdiv=2, seed=3, jitter=0)
    cylinder("receiver_neck", 0.02, 0.05, (rx, ry, TOP_Z + recv_r * 1.75), glass, r_top=0.018, segments=10,
             bevel=0)

    # Flasks of red, blue and green brew, one tall amber bottle.
    for i, (fx, fy, r, kind, m) in enumerate([(0.2, -0.16, 0.055, 1, brews[0]), (0.3, -0.04, 0.05, 0, brews[1]),
                                              (0.12, 0.08, 0.04, 2, amber), (0.6, 0.02, 0.06, 0, brews[0]),
                                              (0.65, -0.17, 0.045, 1, brews[1]), (-0.62, -0.1, 0.035, 2, brews[2])]):
        _flask(f"flask_{i}", fx, fy, TOP_Z, r, kind, m, glass, cork)

    # The mortar: a heavy stone bowl of ground herbs with the pestle leaning in it.
    mx, my = MORTAR_AT
    cylinder("mortar_foot", 0.07, 0.03, (mx, my, TOP_Z), stone, r_top=0.065, segments=14, bevel=0.006)
    cylinder("mortar_bowl", 0.065, 0.07, (mx, my, TOP_Z + 0.028), stone, r_top=0.09, segments=14, bevel=0.008)
    torus("mortar_lip", 0.084, 0.01, (mx, my, TOP_Z + 0.096), stone, major=16, minor=6)
    cylinder("mortar_herbs", 0.076, 0.006, (mx, my, TOP_Z + 0.094), ground, segments=14, bevel=0)
    _rod("pestle", 0.016, (mx + 0.01, my, TOP_Z + 0.07), (mx - 0.1, my - 0.05, TOP_Z + 0.24), stone, segments=10,
         r_top=0.012, bevel=0.004)
