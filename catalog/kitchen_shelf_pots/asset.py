"""A kitchen shelf unit for a wall: two plank sides, a plank back and four shelves on a kick board. Big clay storage
jars stand on the bottom shelf, copper pots and pans, clay bowls and glazed jars on the shelves above, and three
ladles and a skimmer hang from hooks on an iron rail along the front of the upper shelf."""
import math
import random

import bpy
from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# About 1.2 x 0.35 x 1.6 m. The back is on +y, against the wall; the front faces -y.
W, D, H = 1.2, 0.33, 1.6
CARCASS_H = 1.44  # the pots on top reach H
SIDE_T, BACK_T, SHELF_T = 0.03, 0.02, 0.028
SHELVES = (0.1, 0.5, 0.98, CARCASS_H - SHELF_T)  # the shelves' undersides
RAIL_Z, RAIL_Y = 0.962, -D / 2 - 0.025  # the ladle rail, on brackets in front of the upper shelf

WOOD = (0.2, 0.125, 0.065)  # linear RGB
WOOD_OLD = (0.16, 0.1, 0.055)
BACK = (0.12, 0.075, 0.04)
COPPER = (0.42, 0.16, 0.07)
COPPER_DARK = (0.24, 0.09, 0.04)
CLAY = (0.36, 0.16, 0.07)
CLAY_PALE = (0.4, 0.27, 0.15)
GLAZE = (0.12, 0.16, 0.1)
IRON = (0.04, 0.04, 0.04)
CORK = (0.3, 0.2, 0.11)


def _rod(name, r, a, b, mat, segments=8, bevel=0.003, r_top=None):
    """A round rod from point `a` to point `b`."""
    d = Vector(b) - Vector(a)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return cylinder(name, r, d.length, a, mat, r_top=r_top, segments=segments,
                    rot=tuple(math.degrees(x) for x in rot), bevel=bevel)


def _pot(name, r, h, at, mat, rim, lid=None, handle=None, ears=False):
    """A copper pot: a body, a rolled rim, a lid with a knob, a long pan handle at angle `handle` or two ear handles."""
    x, y, z = at
    cylinder(f"{name}_body", r, h, (x, y, z), mat, segments=14, bevel=0.006)
    torus(f"{name}_rim", r, 0.007, (x, y, z + h), rim, major=14, minor=4)
    if lid:
        cylinder(f"{name}_lid", r * 0.97, 0.012, (x, y, z + h), lid, r_top=r * 0.75, segments=12, bevel=0.003)
        blob(f"{name}_knob", 0.016, (x, y, z + h + 0.026), rim, squash=(1, 1, 0.8), subdiv=1, seed=1, jitter=0.05)
    if handle is not None:
        a = math.radians(handle)
        d = Vector((math.cos(a), math.sin(a), 0))
        p = Vector((x, y, z + h * 0.78)) + d * (r - 0.004)
        _rod(f"{name}_handle", 0.009, p, p + d * r * 1.4 + Vector((0, 0, 0.03)), rim, segments=6)
    if ears:
        for s in (-1, 1):
            torus(f"{name}_ear_{s}", 0.022, 0.006, (x + s * (r + 0.012), y, z + h * 0.8), rim, rot=(90, 0, 0),
                  major=8, minor=4)


def _jar(name, r, h, at, mat, lip, neck=0.55, cap=None):
    """A clay jar: a belly widening to the shoulder, a narrower neck and a lip, a cork or cloth cap when given."""
    x, y, z = at
    sh = h * 0.62
    cylinder(f"{name}_foot", r * 0.72, sh, (x, y, z), mat, r_top=r, segments=12, bevel=0.006)
    cylinder(f"{name}_shoulder", r, h - sh - 0.03, (x, y, z + sh), mat, r_top=r * neck, segments=12, bevel=0.006)
    cylinder(f"{name}_neck", r * neck * 0.92, 0.03, (x, y, z + h - 0.03), lip, segments=10, bevel=0)
    torus(f"{name}_lip", r * neck * 0.92, 0.008, (x, y, z + h), lip, major=10, minor=4)
    if cap:
        cylinder(f"{name}_cap", r * neck * 0.8, 0.025, (x, y, z + h - 0.01), cap, segments=8, bevel=0)


def _ladle(name, x, kind, rail, wood_mat, metal_mat):
    """A ladle (`kind` 'ladle'), a skimmer ('skimmer') or a spoon ('spoon') hanging from an S-hook on the rail."""
    top = Vector((x, RAIL_Y, RAIL_Z))
    torus(f"{name}_hook", 0.014, 0.003, (x, RAIL_Y, RAIL_Z - 0.006), rail, rot=(0, 90, 0), major=10, minor=4)
    length = {"ladle": 0.26, "skimmer": 0.24, "spoon": 0.2}[kind]
    a = top + Vector((0, 0, -0.04))
    b = a + Vector((0, 0, -length))
    torus(f"{name}_loop", 0.012, 0.004, tuple(top + Vector((0, 0, -0.03))), metal_mat, rot=(0, 90, 0), major=10,
          minor=4)
    _rod(f"{name}_shaft", 0.0065, a, b, wood_mat if kind == "spoon" else metal_mat,
         segments=6, bevel=0)
    if kind == "ladle":
        bowl = blob(f"{name}_bowl", 0.05, tuple(b + Vector((0, -0.004, -0.03))), metal_mat, squash=(1, 0.75, 0.8),
                    subdiv=1, seed=3, jitter=0.03)
    elif kind == "skimmer":
        bowl = cylinder(f"{name}_bowl", 0.055, 0.008, tuple(b + Vector((0, -0.004, -0.05))), metal_mat,
                        segments=14, rot=(90, 0, 0), bevel=0.002)
    else:
        bowl = blob(f"{name}_bowl", 0.03, tuple(b + Vector((0, -0.008, -0.025))), wood_mat, squash=(0.8, 0.4, 1.2),
                    subdiv=1, seed=4, jitter=0.04)
    return bowl


@prop
def kitchen_shelf_pots():
    rnd = random.Random(23)
    wood = material("kitchen_shelf_pots_wood", WOOD, vary=0.28, scale=14)
    old = material("kitchen_shelf_pots_wood_old", WOOD_OLD, vary=0.3, scale=11)
    back = material("kitchen_shelf_pots_back", BACK, vary=0.25, scale=12, crevice=0.7)
    copper = material("kitchen_shelf_pots_copper", COPPER, rough=0.4, vary=0.3, scale=12, metal=0.75, crevice=0.6)
    copper_dark = material("kitchen_shelf_pots_copper_dark", COPPER_DARK, rough=0.5, vary=0.3, scale=14, metal=0.6)
    clay = material("kitchen_shelf_pots_clay", CLAY, rough=0.85, vary=0.25, scale=10, crevice=0.6)
    pale = material("kitchen_shelf_pots_clay_pale", CLAY_PALE, rough=0.85, vary=0.25, scale=10, crevice=0.6)
    glaze = material("kitchen_shelf_pots_glaze", GLAZE, rough=0.35, vary=0.3, scale=12, crevice=0.6)
    iron = material("kitchen_shelf_pots_iron", IRON, rough=0.55, vary=0.2, scale=14, metal=0.6)
    cork = material("kitchen_shelf_pots_cork", CORK, rough=0.9, vary=0.3, scale=30)

    # The carcass: sides, back planks, a kick board and four shelves.
    xs = W / 2 - SIDE_T / 2
    for s in (-1, 1):
        box(f"side_{s}", (SIDE_T, D, CARCASS_H), (s * xs, 0, CARCASS_H / 2), wood, rot=(0, 0, rnd.uniform(-0.3, 0.3)), bevel=0.008)
    n_back = 5
    bw = (W - 2 * SIDE_T) / n_back
    for i in range(n_back):
        box(f"back_{i}", (bw + 0.004, BACK_T, CARCASS_H - 0.02),  # overlapping, staggered: no light through the seams
            (-W / 2 + SIDE_T + bw * (i + 0.5), D / 2 - BACK_T / 2 - 0.004 * (i % 2), CARCASS_H / 2), (back, old)[i % 3 == 1], bevel=0.005)
    box("kick", (W - 2 * SIDE_T, 0.025, SHELVES[0]), (0, -D / 2 + 0.03, SHELVES[0] / 2), old, bevel=0.006)
    for k, z in enumerate(SHELVES):
        box(f"shelf_{k}", (W - 2 * SIDE_T + (0.06 if k == 3 else 0), D - BACK_T + (0.03 if k == 3 else 0), SHELF_T),
            (0, -BACK_T / 2 - (0.015 if k == 3 else 0), z + SHELF_T / 2), (wood, old)[k % 2],
            rot=(rnd.uniform(-0.3, 0.3), 0, 0), bevel=0.007)
        if 0 < k < 3:  # a lip along the front so nothing slides off
            box(f"shelf_lip_{k}", (W - 2 * SIDE_T, 0.018, 0.035), (0, -D / 2 + 0.012, z + SHELF_T + 0.017), wood,
                bevel=0.005)

    # Bottom shelf: three big clay storage jars, one capped with cloth-tied cork.
    z0 = SHELVES[0] + SHELF_T
    for i, (x, r, h, m, cap) in enumerate([(-0.36, 0.13, 0.42, clay, cork), (-0.02, 0.11, 0.36, pale, None),
                                          (0.3, 0.14, 0.44, clay, cork)]):
        _jar(f"store_jar_{i}", r, h, (x + rnd.uniform(-0.02, 0.02), 0.01, z0), m, (pale, clay)[m is pale], cap=cap)

    # Middle shelf: a big two-eared stock pot, a stack of clay bowls and a lidded copper pot, set back from the ladles.
    z1 = SHELVES[1] + SHELF_T
    _pot("stock_pot", 0.14, 0.22, (-0.34, 0.03, z1), copper, copper_dark, ears=True)
    for i in range(3):
        cylinder(f"bowl_{i}", 0.1 - 0.004 * i, 0.04, (0.02 + rnd.uniform(-0.006, 0.006), 0.04, z1 + 0.032 * i), pale,
                 r_top=0.12 - 0.004 * i, segments=14, bevel=0.004)
    _pot("lidded_pot", 0.1, 0.15, (0.34, 0.04, z1), copper, copper_dark, lid=copper)

    # Upper shelf: a row of pans, small spice jars and a glazed crock.
    z2 = SHELVES[2] + SHELF_T
    _pot("sauce_pan", 0.09, 0.1, (-0.4, 0.0, z2), copper, copper_dark, handle=-120)
    _pot("milk_pan", 0.075, 0.12, (-0.18, 0.04, z2), copper, copper_dark, lid=copper, handle=-75)
    for i, (x, r, h) in enumerate([(0.05, 0.045, 0.14), (0.2, 0.05, 0.16)]):
        _jar(f"spice_jar_{i}", r, h, (x, 0.05 + rnd.uniform(-0.03, 0.02), z2), (clay, pale, clay)[i], pale,
             neck=0.75, cap=cork)
    _jar("crock", 0.09, 0.22, (0.4, 0.02, z2), glaze, glaze, neck=0.8)

    # Top: a pot and two stacked bowls.
    z3 = CARCASS_H
    _pot("top_pot", 0.09, 0.11, (0.3, 0.0, z3), copper_dark, copper)
    for i in range(2):
        cylinder(f"top_bowl_{i}", 0.08, 0.035, (-0.25, 0.02, z3 + 0.03 * i), clay, r_top=0.1, segments=12,
                 bevel=0.004)

    # The rail along the upper shelf's front, on two brackets, with two ladles, a skimmer and a wooden spoon.
    _rod("rail", 0.007, (-W / 2 + SIDE_T + 0.05, RAIL_Y, RAIL_Z), (W / 2 - SIDE_T - 0.05, RAIL_Y, RAIL_Z), iron,
         segments=6, bevel=0)
    for s in (-1, 1):
        box(f"rail_bracket_{s}", (0.014, 0.05, 0.03), (s * (W / 2 - SIDE_T - 0.05), RAIL_Y + 0.025, RAIL_Z + 0.008),
            iron, bevel=0)
    for i, (x, kind) in enumerate([(-0.3, "ladle"), (-0.12, "skimmer"), (0.08, "ladle"), (0.26, "spoon")]):
        _ladle(f"ladle_{i}", x + rnd.uniform(-0.01, 0.01), kind, iron, old, copper if kind == "ladle" else iron)
