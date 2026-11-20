"""A plank field gate on two round posts, in the weathered grey-brown wood of `fence_wood` so it sits in a fence
line: one 1.5 m section with a leaf of four horizontal rails, two stiles and a diagonal brace, hung on iron strap
hinges from the left (-x) post and closed with a latch on the right (+x) post."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder

MODULE = 1.5  # metres: the length wall and fence sections join at
# Overall dimensions: the gate runs along x through the origin, one module wide and about 1.25 m high at the posts.
L = MODULE - 0.01
POST_R = 0.085  # gate posts: a little stouter than the fence's 0.075
POST_H = 1.25
POST_X = L / 2 - 0.09  # posts near the ends
LEAF_X0 = -POST_X + POST_R + 0.025  # hinge stile edge
LEAF_X1 = POST_X - POST_R - 0.02  # latch stile edge
LEAF_Z0, LEAF_Z1 = 0.14, 1.06  # bottom and top of the leaf
LEAF_Y = -0.035  # the leaf hangs a little to the front (-y) of the posts' centre line
RAIL_H, RAIL_T = 0.1, 0.035
STILE_W, STILE_T = 0.085, 0.05
RAILS = 4

WOOD = (0.25, 0.22, 0.175)  # weathered grey-brown, as fence_wood
WOOD_OLD = (0.20, 0.18, 0.15)
IRON = (0.045, 0.045, 0.045)


@prop
def gate_wood():
    rnd = random.Random(31)
    wood = material("gate_wood_wood", WOOD, vary=0.3, scale=14)
    wood_old = material("gate_wood_old", WOOD_OLD, vary=0.32, scale=14)
    iron = material("gate_wood_iron", IRON, rough=0.55, vary=0.2, scale=20, metal=0.6)

    # Two round posts, slightly tapered, each with a weathered cap cut flat.
    for s in (-1, 1):
        cylinder(f"post_{s}", POST_R * rnd.uniform(0.97, 1.03), POST_H, (s * POST_X, 0, 0),
                 wood_old if s > 0 else wood, r_top=POST_R * 0.85, segments=10,
                 rot=(rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0, 360)), bevel=0.014)

    # The leaf: hinge and latch stiles, four rails between them, a diagonal brace from the bottom hinge corner up to
    # the top latch corner (the brace pushes the latch end up so the gate does not sag).
    stile_h = LEAF_Z1 - LEAF_Z0
    hx = LEAF_X0 + STILE_W / 2
    lx = LEAF_X1 - STILE_W / 2
    for name, x, mat in (("stile_hinge", hx, wood), ("stile_latch", lx, wood_old)):
        box(name, (STILE_W, STILE_T, stile_h), (x, LEAF_Y, LEAF_Z0 + stile_h / 2), mat, bevel=0.01)
    rail_len = LEAF_X1 - LEAF_X0 - 0.01
    for i in range(RAILS):
        z = LEAF_Z0 + RAIL_H / 2 + 0.02 + i * (stile_h - RAIL_H - 0.04) / (RAILS - 1)
        box(f"rail_{i}", (rail_len, RAIL_T, RAIL_H * rnd.uniform(0.94, 1.02)),
            ((LEAF_X0 + LEAF_X1) / 2, LEAF_Y - (STILE_T + RAIL_T) / 2 + 0.004, z),
            wood_old if i % 2 else wood, rot=(rnd.uniform(-1, 1), rnd.uniform(-0.6, 0.6), 0), bevel=0.008)
    bx0, bz0 = hx + STILE_W / 2, LEAF_Z0 + 0.07
    bx1, bz1 = lx - STILE_W / 2, LEAF_Z1 - 0.07
    length = math.hypot(bx1 - bx0, bz1 - bz0)
    angle = math.degrees(math.atan2(bz1 - bz0, bx1 - bx0))
    box("brace", (length, RAIL_T, 0.085), ((bx0 + bx1) / 2, LEAF_Y + (STILE_T + RAIL_T) / 2 - 0.004, (bz0 + bz1) / 2),
        wood, rot=(0, -angle, 0), bevel=0.008)

    # Iron strap hinges over the top and bottom rails, on pins driven into the hinge post.
    front = LEAF_Y - STILE_T / 2 - RAIL_T - 0.003
    for k, z in enumerate((LEAF_Z0 + RAIL_H / 2 + 0.02, LEAF_Z1 - RAIL_H / 2 - 0.02)):
        x0 = -POST_X + POST_R * 0.6
        box(f"strap_{k}", (0.42, 0.008, 0.04), (x0 + 0.21, front, z), iron, bevel=0.003)
        cylinder(f"pin_{k}", 0.018, 0.08, (-POST_X + POST_R * 0.55, LEAF_Y, z - 0.04), iron, segments=8, bevel=0.003)
        for j in range(3):
            cylinder(f"nail_{k}_{j}", 0.008, 0.006, (x0 + 0.1 + j * 0.13, front - 0.004, z), iron, segments=6,
                     rot=(90, 0, 0), bevel=0)

    # The latch: a bar on the latch stile that drops into a hook on the right post.
    lz = LEAF_Z1 - RAIL_H / 2 - 0.02 - 0.12
    box("latch_bar", (0.24, 0.012, 0.025), (lx + 0.07, front - 0.004, lz), iron, rot=(0, -4, 0), bevel=0.003)
    box("latch_keeper", (0.035, 0.04, 0.06), (POST_X - POST_R * 0.7, LEAF_Y - 0.03, lz - 0.015), iron, bevel=0.004)
    box("latch_guide", (0.03, 0.03, 0.06), (lx - 0.01, front - 0.01, lz), iron, bevel=0.003)
