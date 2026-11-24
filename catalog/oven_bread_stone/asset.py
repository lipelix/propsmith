"""A domed bread oven: a waist-high plinth of coursed fieldstone with a slab top, on it a plastered dome with a stone
front wall whose arched mouth glows with embers and low flames, a short flue above the mouth, a stone sill before it,
a long wooden peel leaning against the plinth and a few split logs on the ground."""
import math
import random

import bpy
from mathutils import Vector

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# About 1.5 x 1.5 x 1.6 m. The mouth faces -y.
PX, PY0, PY1 = 0.62, -0.6, 0.64  # the plinth: x within +-PX, y from PY0 to PY1
PLINTH_H = 0.74
DOME_Y, DOME_R, DOME_H = 0.08, 0.6, 0.7  # the dome's centre (on the plinth top), radius and height
FRONT_X, FRONT_Y0, FRONT_Y1 = 0.38, -0.58, -0.32  # the front wall
FRONT_H = 0.56  # above the plinth top
MOUTH_W, MOUTH_H = 0.42, 0.36  # the arched mouth, its full height
FLUE_W, FLUE_Y, FLUE_TOP = 0.2, -0.42, 1.595
PEEL_X, PEEL_LEN = 0.48, 1.62
PEEL_FOOT_Y = -0.8

STONE = (0.29, 0.26, 0.22)  # linear RGB
STONE_DARK = (0.22, 0.2, 0.17)
PLASTER = (0.4, 0.34, 0.26)  # a warm lime-and-clay render
SOOT = (0.06, 0.055, 0.05)
INSIDE = (0.03, 0.025, 0.022)
EMBER = (0.5, 0.15, 0.03)
FLAME = (0.5, 0.28, 0.035)
WOOD = (0.25, 0.165, 0.09)  # the peel, smooth and pale from use
WOOD_OLD = (0.19, 0.12, 0.065)
LOG = (0.15, 0.09, 0.05)
LOG_CUT = (0.3, 0.2, 0.11)


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


def _courses(prefix, x0, x1, y0, y1, z0, z1, n, rnd, mats):
    """A block of coursed stone: `n` courses, each a row of full-depth stones of uneven length along x."""
    ch = (z1 - z0) / n
    for c in range(n):
        x, i = x0, 0
        offset = 0.5 if c % 2 else 0.0
        while x < x1 - 1e-6:
            length = rnd.uniform(0.26, 0.4) * (0.6 if (i == 0 and offset) else 1)
            end = x1 if x1 - (x + length) < 0.15 else x + length
            j = rnd.uniform(-0.004, 0.004)
            box(f"{prefix}_{c}_{i}", (end - x - 0.008, y1 - y0 + rnd.uniform(-0.01, 0.012), ch - 0.008),
                ((x + end) / 2, (y0 + y1) / 2 + j, z0 + ch * (c + 0.5)), mats[rnd.randrange(len(mats))],
                rot=(rnd.uniform(-0.6, 0.6), 0, rnd.uniform(-0.8, 0.8)), bevel=0.018)
            x, i = end, i + 1


@prop
def oven_bread_stone():
    rnd = random.Random(12)
    stone = material("oven_bread_stone_stone", STONE, rough=0.9, vary=0.28, scale=8, crevice=0.7)
    dark = material("oven_bread_stone_stone_dark", STONE_DARK, rough=0.9, vary=0.3, scale=9, crevice=0.7)
    plaster = material("oven_bread_stone_plaster", PLASTER, rough=0.95, vary=0.25, scale=4, crevice=0.6)
    soot = material("oven_bread_stone_soot", SOOT, rough=0.9, vary=0.3, scale=10, crevice=0.5)
    inside = material("oven_bread_stone_inside", INSIDE, rough=0.9, vary=0.2, scale=8, crevice=0.2)
    ember = material("oven_bread_stone_ember", EMBER, rough=0.6, vary=0.35, scale=14, crevice=0.2)
    flame = material("oven_bread_stone_flame", FLAME, rough=0.5, vary=0.3, scale=10, crevice=0.1)
    wood = material("oven_bread_stone_peel", WOOD, vary=0.22, scale=14)
    wood_old = material("oven_bread_stone_wood_old", WOOD_OLD, vary=0.3, scale=11)
    log = material("oven_bread_stone_log", LOG, rough=0.9, vary=0.3, scale=12, crevice=0.6)
    log_cut = material("oven_bread_stone_log_cut", LOG_CUT, vary=0.25, scale=20)

    # The plinth: three courses of full-depth stones and a slab top.
    top = PLINTH_H
    _courses("plinth", -PX, PX, PY0, PY1, 0, top - 0.07, 3, rnd, [stone, stone, dark])
    box("plinth_slab", (2 * PX + 0.04, PY1 - PY0 + 0.04, 0.07), (0, (PY0 + PY1) / 2, top - 0.035), dark,
        bevel=0.02)

    # The dome: a plastered half-ellipsoid.
    dome = blob("dome", DOME_R, (0, DOME_Y, top), plaster, squash=(1.0, 0.98, DOME_H / DOME_R), subdiv=3, seed=3,
                jitter=0.025)
    dome.rotation_euler = (0, 0, 0)

    # The front wall: stone blocks round the arched mouth, the mouth a dark recess with embers and flames.
    fy = (FRONT_Y0 + FRONT_Y1) / 2
    fd = FRONT_Y1 - FRONT_Y0
    mw, ms = MOUTH_W / 2, MOUTH_H - MOUTH_W / 2  # half width, height of the straight jambs
    for s in (-1, 1):
        w = FRONT_X - mw
        for k in range(3):
            h = FRONT_H / 3
            box(f"jamb_{s}_{k}", (w - 0.008, fd + rnd.uniform(-0.01, 0.01), h - 0.008),
                (s * (mw + w / 2), fy, top + h * (k + 0.5)), (stone, dark)[(k + (s > 0)) % 2],
                rot=(0, rnd.uniform(-0.8, 0.8), 0), bevel=0.016)
    # Voussoirs: wedge-ish blocks round the arch, and a lintel course above them.
    n_v = 7
    arch_z = top + ms
    for i in range(n_v):
        a = math.pi * (i + 0.5) / n_v
        r = mw + 0.06
        box(f"voussoir_{i}", (0.11, fd + 0.02, 0.13 if i % 2 else 0.12),
            (r * math.cos(a), fy - 0.01, arch_z + r * math.sin(a)), (dark, stone)[i % 2],
            rot=(0, math.degrees(math.pi / 2 - a), 0), bevel=0.014)
    for s in (-1, 1):
        fill_w = FRONT_X - mw - 0.05
        box(f"spandrel_{s}", (fill_w, fd - 0.01, FRONT_H - ms - 0.02),
            (s * (FRONT_X - fill_w / 2), fy, top + ms + (FRONT_H - ms) / 2 - 0.01), stone, bevel=0.016)
    box("front_cap", (2 * FRONT_X + 0.04, fd + 0.06, 0.07), (0, fy - 0.01, top + FRONT_H + 0.035), dark, bevel=0.018)
    # The recess: a dark back and an arched dark vault set into the wall behind the mouth.
    box("mouth_back", (MOUTH_W + 0.02, 0.24, ms + 0.01), (0, FRONT_Y1 - 0.03, top + (ms + 0.01) / 2), inside, bevel=0)
    cylinder("mouth_vault", mw + 0.01, 0.24, (0, FRONT_Y1 + 0.09, arch_z), inside, segments=16, rot=(90, 0, 0),
             bevel=0)
    box("mouth_soot", (2 * mw + 0.06, 0.012, 0.22), (0, FRONT_Y0 - 0.002, arch_z + mw - 0.02), soot, bevel=0)
    _settle(blob("embers", 0.16, (0, FRONT_Y1 - 0.1, top), ember, squash=(1.2, 0.9, 0.22), subdiv=2, seed=5,
                 jitter=0.25), top - 0.005)
    for i, (fx, fy2, fr, tall) in enumerate([(0.0, -0.02, 0.045, 1.0), (0.07, 0.03, 0.035, 0.7),
                                             (-0.07, 0.02, 0.035, 0.65)]):
        h = 0.17 * tall
        blob(f"flame_{i}", fr, (fx, FRONT_Y1 - 0.1 + fy2, top + 0.03 + h / 2), flame,
             squash=(0.85, 0.8, h / (2 * fr)), subdiv=1, seed=70 + i, jitter=0.12)
    # The sill: a worn stone slab sticking out under the mouth.
    box("sill", (MOUTH_W + 0.16, 0.16, 0.05), (0, FRONT_Y0 - 0.05, top + 0.025), dark, rot=(0, 0, 0.8), bevel=0.016)

    # The flue: a short stone stack rising from the front wall's cap.
    fz0 = top + FRONT_H + 0.07
    for k, z in enumerate((fz0, fz0 + (FLUE_TOP - 0.05 - fz0) / 2)):
        hh = (FLUE_TOP - 0.05 - fz0) / 2
        box(f"flue_{k}", (FLUE_W - 0.008 * k, FLUE_W, hh - 0.006), (0, FLUE_Y, z + hh / 2), (stone, dark)[k],
            rot=(0, 0, rnd.uniform(-2, 2)), bevel=0.014)
    box("flue_cap", (FLUE_W + 0.06, FLUE_W + 0.06, 0.05), (0, FLUE_Y, FLUE_TOP - 0.025), soot, bevel=0.012)

    # The peel: a long pole with a flat blade, leaning against the plinth's front with its blade up.
    foot = Vector((PEEL_X, PEEL_FOOT_Y, 0.0))
    rest = Vector((PEEL_X + 0.03, PY0 - 0.035, top))
    d = (rest - foot).normalized()
    pole_len = PEEL_LEN - 0.36
    tip = foot + d * pole_len
    _rod("peel_pole", 0.019, foot + Vector((0, 0, 0.012)), tip, wood_old, segments=8)
    blade = box("peel_blade", (0.3, 0.014, 0.36), tuple(tip + d * 0.17), wood, bevel=0.005)
    blade.rotation_euler = Vector((0, 0, 1)).rotation_difference(d).to_euler()
    neck = box("peel_neck", (0.09, 0.02, 0.08), tuple(tip + d * 0.0), wood, bevel=0.004)
    neck.rotation_euler = blade.rotation_euler

    # Split logs on the ground beside the plinth, ready for the next firing.
    for i, (x, y, z, yaw) in enumerate([(-0.46, -0.72, 0.055, 4), (-0.24, -0.72, 0.055, -3),
                                        (-0.35, -0.71, 0.15, 1)]):
        cylinder(f"log_{i}", 0.055, 0.5, (x - 0.25, y, z), log, segments=7, rot=(0, 90, yaw), bevel=0.006)
        cylinder(f"log_end_{i}", 0.048, 0.006, (x + 0.252, y, z), log_cut, segments=7, rot=(0, 90, yaw), bevel=0)

    fire_h = MOUTH_H - 0.08
    anchor("fire:hearth", (0, FRONT_Y1 - 0.1, top + 0.02), size=(mw - 0.04, 0.1, fire_h))
    anchor("light:fire", (0, FRONT_Y0 - 0.02, top + 0.2))
