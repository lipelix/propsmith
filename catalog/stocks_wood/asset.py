"""A village pillory: a low plank platform on three sill beams with a step at the front (-y), two square oak posts
braced to the deck and tied by a top rail, and between them a pair of heavy boards that close on one round head hole
and two hand holes. The upper board is hinged to the lower one on the left with iron strap hinges and held shut on the
right by a hasp and a padlock; iron bands bind the board ends."""
import math
import random

import bmesh
import bpy

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall dimensions (metres): about 1.6 m wide, 1 m deep, 1.6 m high.
PLAT_X, PLAT_Y = 1.6, 0.8  # the platform
PLAT_YC = 0.1  # its centre, behind the origin to leave room for the step
SILL_H = 0.14  # sill beams on the ground
PLANK_T = 0.04  # deck planks
DECK = SILL_H + PLANK_T  # top of the deck
STEP = (1.0, 0.2, 0.09)  # the step at the front
POST = 0.14  # square posts
POST_X = 0.62  # post centres, either side
POST_TOP = 1.55
RAIL_H = 0.08  # the top rail between the posts
BOARD_T = 0.08  # board thickness (y)
BOARD_W = 2 * POST_X + POST + 0.02  # the boards run through the posts
SPLIT = 1.26  # where the two boards meet
LOW_H, UP_H = 0.2, 0.18  # board heights below and above the split
HEAD_R, HAND_R, HAND_X = 0.095, 0.05, 0.31

OAK = (0.2, 0.12, 0.062)  # linear RGB
OAK_OLD = (0.155, 0.095, 0.052)
IRON = (0.045, 0.044, 0.042)
IRON_WORN = (0.1, 0.092, 0.082)
RUST = (0.1, 0.055, 0.033)


def _link(name, bm, mat):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth()
    mesh.set_sharp_from_angle(angle=math.radians(35))
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _board(name, w, h, t, holes, at, mat, down=False, seg=10):
    """A board `w` long, `h` high and `t` thick (y), its bottom centre at `at`, with a half-round notch of radius r at
    each (x, r) of `holes` cut into its top edge (into its bottom edge when `down`)."""
    pts = [(-w / 2, 0.0), (w / 2, 0.0)]
    for cx, r in sorted(holes, reverse=True):
        for i in range(seg + 1):
            a = math.pi * i / seg
            pts.append((cx + r * math.cos(a), h - r * math.sin(a)))
    pts.append((-w / 2, h))
    if down:
        pts = [(x, h - z) for x, z in reversed(pts)]
    bm = bmesh.new()
    front = [bm.verts.new((at[0] + x, at[1] - t / 2, at[2] + z)) for x, z in pts]
    back = [bm.verts.new((at[0] + x, at[1] + t / 2, at[2] + z)) for x, z in pts]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], front[j], back[j], back[i]))
    return _link(name, bm, mat)


@prop
def stocks_wood():
    rnd = random.Random(7)
    oak = material("stocks_wood_oak", OAK, vary=0.25, scale=14)
    old = material("stocks_wood_oak_old", OAK_OLD, vary=0.3, scale=12)
    iron = material("stocks_wood_iron", IRON, rough=0.55, vary=0.25, scale=18, metal=0.6)
    worn = material("stocks_wood_iron_worn", IRON_WORN, rough=0.5, vary=0.25, scale=22, metal=0.7)
    rust = material("stocks_wood_rust", RUST, rough=0.85, vary=0.3, scale=24, metal=0.25)

    # Platform: three sill beams along x, deck planks across them, a step block at the front.
    y0, y1 = PLAT_YC - PLAT_Y / 2, PLAT_YC + PLAT_Y / 2
    for k, y in enumerate((y0 + 0.07, PLAT_YC, y1 - 0.07)):
        box(f"sill_{k}", (PLAT_X - 0.04, 0.13, SILL_H), (0, y, SILL_H / 2), old,
            rot=(0, 0, rnd.uniform(-0.4, 0.4)), bevel=0.012)
    n = 10
    pw = PLAT_X / n
    for i in range(n):
        x = -PLAT_X / 2 + pw * (i + 0.5)
        box(f"plank_{i}", (pw - 0.008, PLAT_Y * rnd.uniform(0.97, 1.0), PLANK_T + rnd.uniform(-0.004, 0.004)),
            (x, PLAT_YC + rnd.uniform(-0.01, 0.01), SILL_H + PLANK_T / 2), old if i % 4 == 1 else oak,
            rot=(0, 0, rnd.uniform(-0.6, 0.6)), bevel=0.008)
        for j, y in enumerate((y0 + 0.07, y1 - 0.07)):
            cylinder(f"peg_{i}_{j}", 0.008, 0.004, (x, y, DECK - 0.001), worn, segments=6, bevel=0)
    sw, sd, sh = STEP
    box("step", (sw, sd, sh), (0, y0 - sd / 2 + 0.01, sh / 2), oak, rot=(0, 0, 0.8), bevel=0.012)
    box("step_block", (sw - 0.1, 0.12, sh - 0.02), (0, y0 - 0.03, (sh - 0.02) / 2), old, bevel=0.008)

    # Posts, cap boards, the top rail and diagonal braces down to the deck front and back.
    py = PLAT_YC
    for k, s in enumerate((-1, 1)):
        x = s * POST_X
        box(f"post_{k}", (POST, POST, POST_TOP - DECK + 0.02), (x, py, (POST_TOP + DECK - 0.02) / 2), oak,
            rot=(0, rnd.uniform(-0.5, 0.5), 0), bevel=0.016)
        box(f"cap_{k}", (POST + 0.04, POST + 0.04, 0.05), (x, py, POST_TOP + 0.02), old, bevel=0.012)
        for j, d in enumerate((-1, 1)):
            run, drop = 0.3, 0.46
            ln = math.hypot(run, drop)
            a = math.degrees(math.atan2(run, drop))
            box(f"brace_{k}_{j}", (0.09, 0.09, ln), (x, py + d * (POST / 2 + run / 2 - 0.02), DECK + drop / 2 - 0.02),
                old, rot=(d * a, 0, 0), bevel=0.01)
    box("rail", (2 * POST_X + POST + 0.06, 0.12, RAIL_H), (0, py, POST_TOP - RAIL_H / 2 - 0.02), oak,
        rot=(0, rnd.uniform(-0.4, 0.4), 0), bevel=0.014)
    for k, s in enumerate((-1, 1)):
        cylinder(f"rail_peg_{k}", 0.014, POST + 0.02, (s * POST_X, py - POST / 2 - 0.01, POST_TOP - 0.06), worn,
                 segments=8, rot=(-90, 0, 0), bevel=0)

    # The two boards that close on the holes.
    holes = [(0.0, HEAD_R), (-HAND_X, HAND_R), (HAND_X, HAND_R)]
    _board("board_low", BOARD_W, LOW_H, BOARD_T, holes, (0, py, SPLIT - LOW_H), oak)
    _board("board_up", BOARD_W - 0.01, UP_H, BOARD_T, holes, (0, py, SPLIT + 0.006), old, down=True)

    # Iron bands round the board ends, inside the posts.
    fy = py - BOARD_T / 2
    for k, s in enumerate((-1, 1)):
        x = s * (POST_X - POST / 2 - 0.05)
        box(f"band_low_{k}", (0.045, BOARD_T + 0.012, LOW_H - 0.02), (x, py, SPLIT - LOW_H / 2), iron, bevel=0.003)
        box(f"band_up_{k}", (0.045, BOARD_T + 0.012, UP_H - 0.02), (x, py, SPLIT + UP_H / 2 + 0.006), iron,
            bevel=0.003)

    # Strap hinges on the left, across the split: a knuckle on the line and a strap on each board.
    for k, x in enumerate((-0.47, -0.17)):
        cylinder(f"knuckle_{k}", 0.016, 0.08, (x - 0.04, fy - 0.014, SPLIT + 0.003), worn, segments=8,
                 rot=(0, 90, 0), bevel=0)
        box(f"strap_up_{k}", (0.035, 0.01, 0.15), (x, fy - 0.005, SPLIT + 0.08), iron, bevel=0.003)
        box(f"strap_low_{k}", (0.035, 0.01, 0.15), (x, fy - 0.005, SPLIT - 0.075), iron, bevel=0.003)
        for j, dz in enumerate((0.13, -0.13)):
            cylinder(f"strap_nail_{k}_{j}", 0.009, 0.006, (x, fy - 0.01, SPLIT + dz), worn, segments=6,
                     rot=(90, 0, 0), bevel=0)

    # Hasp over the split on the right, a staple on the lower board and a closed padlock.
    hx = 0.47
    box("hasp", (0.05, 0.012, 0.16), (hx, fy - 0.006, SPLIT + 0.01), iron, bevel=0.003)
    torus("staple", 0.018, 0.006, (hx, fy - 0.02, SPLIT - 0.05), iron, rot=(0, 90, 0), major=10, minor=6)
    torus("padlock_shackle", 0.022, 0.006, (hx, fy - 0.03, SPLIT - 0.07), worn, rot=(90, 0, 0), major=12, minor=6)
    box("padlock", (0.06, 0.03, 0.065), (hx, fy - 0.03, SPLIT - 0.11), rust, bevel=0.008)
