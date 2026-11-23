"""A blacksmith's stone forge: a waist-high hearth of coursed fieldstone with a raised rim round a bed of glowing coals,
a stone back wall, a tapering plastered hood on a timber lintel drawing up into a short chimney, and at the +x side a
pair of leather bellows on a timber stand blowing through an iron pipe into the fire. A poker lies in the coals and a
pair of tongs hangs on the hood."""
import math
import random

import bpy
from mathutils import Vector

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# About 1.8 x 1.2 x 2.2 m. The hearth fills -x, the bellows stand at +x; the back wall is on +y.
X0, X1 = -0.9, 0.32  # the hearth block
Y0, Y1 = -0.55, 0.55
HEARTH_H = 0.72
COURSES = 4
FIRE_X, FIRE_Y = -0.29, -0.06  # centre of the fire pit
PIT_X, PIT_Y = 0.62, 0.56  # the pit inside the rim
RIM_W, RIM_H = 0.12, 0.08
WALL_Y = 0.36  # the back wall's front face
HOOD_Z0, HOOD_Z1 = 1.32, 1.86  # the hood's mouth and top
HOOD_Y0 = -0.42
CHIM_W, CHIM_D, CHIM_Y = 0.5, 0.42, 0.28
TOP = 2.2
STAND_X0, STAND_X1 = 0.46, 0.84  # the bellows stand's legs
STAND_H = 0.7
BELLOWS_X, BELLOWS_R = 0.68, 0.19  # centre of the boards' round end, their radius
TIP = 1.75  # the boards' point reaches TIP * BELLOWS_R towards -x

STONE = (0.29, 0.26, 0.22)  # linear RGB
STONE_DARK = (0.22, 0.2, 0.17)
SOOT = (0.06, 0.055, 0.05)
PLASTER = (0.36, 0.33, 0.28)
WOOD = (0.19, 0.115, 0.06)
WOOD_OLD = (0.15, 0.1, 0.06)
LEATHER = (0.14, 0.075, 0.04)
IRON = (0.04, 0.04, 0.04)
IRON_RUST = (0.09, 0.05, 0.03)
COAL = (0.035, 0.032, 0.03)
EMBER = (0.5, 0.15, 0.03)
FLAME = (0.5, 0.28, 0.035)


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


def _frustum(name, lo, hi, mat, bevel=0.015):
    """A box whose bottom face spans `lo` = (x0, x1, y0, y1, z) and top face `hi` the same way."""
    obj = box(name, (1, 1, 1), (0, 0, 0), mat, bevel=bevel)
    for v in obj.data.vertices:
        x0, x1, y0, y1, z = hi if v.co.z > 0 else lo
        v.co = (x0 + (x1 - x0) * (v.co.x + 0.5), y0 + (y1 - y0) * (v.co.y + 0.5), z)
    return obj


def _courses(prefix, x0, x1, y0, y1, z0, z1, n, rnd, mats):
    """A block of coursed stone: `n` courses, each a row of full-depth stones of uneven length along x."""
    ch = (z1 - z0) / n
    for c in range(n):
        x, i = x0, 0
        offset = 0.5 if c % 2 else 0.0
        while x < x1 - 1e-6:
            length = rnd.uniform(0.28, 0.42) * (0.6 if (i == 0 and offset) else 1)
            end = x1 if x1 - (x + length) < 0.16 else x + length
            j = rnd.uniform(-0.004, 0.004)
            box(f"{prefix}_{c}_{i}", (end - x - 0.008, y1 - y0 + rnd.uniform(-0.01, 0.012), ch - 0.008),
                ((x + end) / 2, (y0 + y1) / 2 + j, z0 + ch * (c + 0.5)), mats[rnd.randrange(len(mats))],
                rot=(rnd.uniform(-0.6, 0.6), 0, rnd.uniform(-0.8, 0.8)), bevel=0.018)
            x, i = end, i + 1


def _board(name, cx, z, mat, tilt=0.0):
    """A bellows board: a teardrop of wood with its point towards -x, `tilt` degrees about the point."""
    obj = cylinder(name, BELLOWS_R, 0.025, (cx, 0, z), mat, segments=16, bevel=0.006)
    for v in obj.data.vertices:
        if v.co.x < 0:
            t = -v.co.x / BELLOWS_R
            v.co.y *= 1 - 0.7 * t
            v.co.x *= TIP
    obj.rotation_euler = (0, math.radians(-tilt), 0)
    return obj


@prop
def forge_stone():
    rnd = random.Random(31)
    stone = material("forge_stone_stone", STONE, rough=0.9, vary=0.28, scale=8, crevice=0.7)
    dark = material("forge_stone_stone_dark", STONE_DARK, rough=0.9, vary=0.3, scale=9, crevice=0.7)
    soot = material("forge_stone_soot", SOOT, rough=0.9, vary=0.3, scale=10, crevice=0.5)
    plaster = material("forge_stone_plaster", PLASTER, rough=0.95, vary=0.22, scale=5, crevice=0.6)
    wood = material("forge_stone_wood", WOOD, vary=0.28, scale=14)
    old = material("forge_stone_wood_old", WOOD_OLD, vary=0.3, scale=11)
    leather = material("forge_stone_leather", LEATHER, rough=0.7, vary=0.3, scale=10, crevice=0.7)
    iron = material("forge_stone_iron", IRON, rough=0.55, vary=0.2, scale=14, metal=0.6, crevice=0.6)
    rust = material("forge_stone_rust", IRON_RUST, rough=0.8, vary=0.3, scale=16, metal=0.3)
    coal = material("forge_stone_coal", COAL, rough=0.6, vary=0.3, scale=20, crevice=0.4)
    ember = material("forge_stone_ember", EMBER, rough=0.6, vary=0.35, scale=14, crevice=0.2)
    flame = material("forge_stone_flame", FLAME, rough=0.5, vary=0.3, scale=10, crevice=0.1)

    # The hearth block: four courses of full-depth stones, a capstone slab on top.
    _courses("hearth", X0, X1, Y0, Y1, 0, HEARTH_H - 0.06, COURSES, rnd, [stone, stone, dark])
    box("hearth_cap", (X1 - X0 + 0.03, Y1 - Y0 + 0.03, 0.06), ((X0 + X1) / 2, 0, HEARTH_H - 0.03), dark,
        bevel=0.02)

    # The rim round the fire pit, four soot-blackened kerb stones, and the coal bed inside it.
    px, py = PIT_X / 2, PIT_Y / 2
    for i, (sx, sy, lx, ly) in enumerate([(0, -1, PIT_X + 2 * RIM_W, RIM_W), (0, 1, PIT_X + 2 * RIM_W, RIM_W),
                                          (-1, 0, RIM_W, PIT_Y), (1, 0, RIM_W, PIT_Y)]):
        box(f"rim_{i}", (lx - 0.006, ly - 0.006, RIM_H), (FIRE_X + sx * (px + RIM_W / 2), FIRE_Y + sy * (py + RIM_W / 2),
                                                          HEARTH_H + RIM_H / 2),
            soot if i % 2 else dark, rot=(0, 0, rnd.uniform(-1, 1)), bevel=0.015)
    bed = HEARTH_H + 0.01
    _settle(blob("coal_bed", 0.3, (FIRE_X, FIRE_Y, bed), coal, squash=(1.0, 0.9, 0.16), subdiv=2, seed=4,
                 jitter=0.2), HEARTH_H - 0.005)
    _settle(blob("embers", 0.17, (FIRE_X, FIRE_Y, bed), ember, squash=(1.1, 0.95, 0.35), subdiv=2, seed=5,
                 jitter=0.25), HEARTH_H + 0.02)
    for i in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0.12, 0.26)
        lump = blob(f"coal_{i}", rnd.uniform(0.025, 0.04),
                    (FIRE_X + rr * math.cos(a), FIRE_Y + rr * math.sin(a) * 0.85, 0), coal if i % 4 else ember,
                    subdiv=1, seed=40 + i, jitter=0.2)
        _settle(lump, HEARTH_H + 0.02 + rnd.uniform(0, 0.03))
    for i, (fx, fy, fr, tall) in enumerate([(0.0, 0.0, 0.05, 1.0), (0.06, -0.04, 0.04, 0.7),
                                            (-0.06, 0.04, 0.04, 0.65)]):
        h = 0.16 * tall
        blob(f"flame_{i}", fr, (FIRE_X + fx, FIRE_Y + fy, HEARTH_H + 0.05 + h / 2), flame,
             squash=(0.85, 0.8, h / (2 * fr)), subdiv=1, seed=70 + i, jitter=0.12)

    # The back wall up to the hood, and the hood: a plastered frustum on a timber lintel, drawing into the chimney.
    _courses("wall", X0, X1, WALL_Y, Y1, HEARTH_H, HOOD_Z0, 3, rnd, [dark, stone, soot])
    hx0, hx1 = X0 + 0.02, X1 - 0.02
    cx = FIRE_X
    _frustum("hood", (hx0, hx1, HOOD_Y0, Y1, HOOD_Z0 + 0.1),
             (cx - CHIM_W / 2, cx + CHIM_W / 2, CHIM_Y - CHIM_D / 2, CHIM_Y + CHIM_D / 2, HOOD_Z1), plaster)
    box("hood_soot", (hx1 - hx0 - 0.04, Y1 - HOOD_Y0 - 0.06, 0.012), ((hx0 + hx1) / 2, (HOOD_Y0 + Y1) / 2 + 0.02,
                                                                       HOOD_Z0 + 0.094), soot, bevel=0)
    box("lintel", (hx1 - hx0 + 0.06, 0.14, 0.12), ((hx0 + hx1) / 2, HOOD_Y0 + 0.06, HOOD_Z0 + 0.06), old,
        rot=(0, 0.6, 0), bevel=0.014)
    for s in (-1, 1):
        box(f"lintel_side_{s}", (0.12, Y1 - HOOD_Y0 - 0.12, 0.1),
            ((hx0, hx1)[s > 0] - s * 0.04, (HOOD_Y0 + Y1) / 2 + 0.06, HOOD_Z0 + 0.06), old, bevel=0.012)
    _courses("chimney", cx - CHIM_W / 2, cx + CHIM_W / 2, CHIM_Y - CHIM_D / 2, CHIM_Y + CHIM_D / 2, HOOD_Z1 - 0.02,
             TOP - 0.07, 2, rnd, [stone, dark])
    box("chimney_cap", (CHIM_W + 0.08, CHIM_D + 0.08, 0.07), (cx, CHIM_Y, TOP - 0.035), dark, bevel=0.015)

    # Tongs hanging from a peg on the lintel's front, a poker resting across the rim into the coals.
    peg = Vector((X0 + 0.22, HOOD_Y0 - 0.02, HOOD_Z0 + 0.06))
    _rod("tongs_peg", 0.012, peg + Vector((0, 0.03, 0)), peg + Vector((0, -0.04, 0)), iron, segments=6, bevel=0)
    for k in (-1, 1):
        a = peg + Vector((k * 0.012, -0.03, -0.01))
        b = peg + Vector((k * 0.05, -0.035, -0.42))
        _rod(f"tongs_{k}", 0.008, a, b, iron, segments=6, bevel=0)
        _rod(f"tongs_jaw_{k}", 0.011, b, b + Vector((-k * 0.03, 0, -0.08)), rust, segments=6, bevel=0)
    _rod("poker", 0.009, (FIRE_X + 0.08, FIRE_Y - 0.05, HEARTH_H + 0.05),
         (FIRE_X + 0.2, FIRE_Y - PIT_Y / 2 - RIM_W - 0.18, HEARTH_H + RIM_H + 0.03), iron, segments=6, bevel=0)
    torus_end = Vector((FIRE_X + 0.2, FIRE_Y - PIT_Y / 2 - RIM_W - 0.18, HEARTH_H + RIM_H + 0.03))
    cylinder("poker_grip", 0.016, 0.1, tuple(torus_end), old, segments=8, rot=(-75, 0, 25), bevel=0.003)

    # The bellows stand: four legs, rails and a top frame.
    for i, (lx, ly) in enumerate([(STAND_X0, -0.2), (STAND_X0, 0.2), (STAND_X1, -0.2), (STAND_X1, 0.2)]):
        box(f"stand_leg_{i}", (0.07, 0.07, STAND_H), (lx, ly, STAND_H / 2), wood if i % 3 else old,
            rot=(0, 0, rnd.uniform(-3, 3)), bevel=0.01)
    for s in (-1, 1):
        box(f"stand_rail_{s}", (STAND_X1 - STAND_X0 + 0.1, 0.06, 0.07),
            ((STAND_X0 + STAND_X1) / 2, s * 0.2, STAND_H - 0.035), wood, bevel=0.01)
        box(f"stand_low_{s}", (STAND_X1 - STAND_X0, 0.045, 0.05), ((STAND_X0 + STAND_X1) / 2, s * 0.2, 0.18), old,
            bevel=0.008)
    for x in (STAND_X0, STAND_X1):
        box(f"stand_cross_{x:.2f}", (0.06, 0.46, 0.06), (x, 0, STAND_H + 0.03), wood, bevel=0.01)

    # The bellows: a lower board, a leather body, an upper board tilted open, a handle and an iron nozzle.
    zb = STAND_H + 0.06
    _board("bellows_low", BELLOWS_X, zb, wood)
    blob("bellows_leather", BELLOWS_R * 0.95, (BELLOWS_X - 0.02, 0, zb + 0.08), leather,
         squash=(1.12, 0.95, 0.3), subdiv=2, seed=9, jitter=0.06)
    top_board = _board("bellows_high", BELLOWS_X, zb + 0.13, old, tilt=7)
    top_board.location.x += 0.01
    for i in range(4):
        a = math.radians(-60 + 40 * i)
        box(f"bellows_nail_{i}", (0.02, 0.02, 0.012),
            (BELLOWS_X + 0.14 * math.cos(a), 0.14 * math.sin(a), zb + 0.17 + 0.01 * i), iron, bevel=0)
    _rod("bellows_handle", 0.018, (BELLOWS_X + BELLOWS_R - 0.03, 0, zb + 0.16),
         (STAND_X1 + 0.05, 0, zb + 0.32), old, segments=8)
    nose = Vector((BELLOWS_X - BELLOWS_R * TIP + 0.02, 0, zb + 0.05))
    _rod("bellows_nozzle", 0.04, nose, nose + Vector((-0.1, 0, 0)), iron, segments=10, r_top=0.022)
    pipe_in = Vector((FIRE_X + PIT_X / 2 + RIM_W * 0.4, FIRE_Y + 0.02, HEARTH_H + RIM_H * 0.5))
    _rod("tuyere", 0.024, nose + Vector((-0.09, 0, 0)), pipe_in, rust, segments=10)

    fire_h = HOOD_Z0 - HEARTH_H - 0.1
    anchor("fire:hearth", (FIRE_X, FIRE_Y, HEARTH_H + 0.04), size=(PIT_X / 2 - 0.04, PIT_Y / 2 - 0.04, fire_h))
    anchor("light:fire", (FIRE_X, FIRE_Y, HEARTH_H + 0.25))
