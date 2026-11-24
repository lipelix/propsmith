"""A small plank hen house on four legs, front on -y: board walls on corner posts, a hinged egg door with a turn-button
latch and a slatted window on the front, a pop hole with a slide shutter in the +x end, a cleated ramp from it down to
the ground, and a steep thatched gable roof with a bound ridge, its eaves drooping past the walls."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall size: about 1.5 m long with the ramp (x), 1.2 m deep across the eaves (y), 1.6 m to the ridge.
X0, X1 = -0.65, 0.25  # the house's end walls (the ramp runs down to x = 0.75)
HALF_Y = 0.4  # half the house's depth
FLOOR_Z, WALL_Z = 0.4, 0.95  # floor top and wall top
POST = 0.07
EAVE_Y, EAVE_Z = 0.5, 0.92  # the underside of the thatch at the eaves
RIDGE_Z = 1.3  # the underside of the thatch at the ridge
OVERHANG = 0.09  # thatch past the end walls
THATCH_T = 0.13
RAMP_X, RAMP_W = 0.75, 0.2
PLANK_T = 0.025

WOOD = (0.2, 0.125, 0.065)  # linear RGB
WOOD_OLD = (0.15, 0.105, 0.065)
WOOD_GREY = (0.17, 0.14, 0.11)
DARK = (0.025, 0.02, 0.015)
THATCH = (0.34, 0.26, 0.1)
THATCH_OLD = (0.24, 0.19, 0.09)
ROPE = (0.3, 0.22, 0.12)
IRON = (0.05, 0.048, 0.045)
STRAW = (0.45, 0.35, 0.12)


@prop
def chicken_coop():
    rnd = random.Random(16)
    wood = material("chicken_coop_wood", WOOD, vary=0.28, scale=10)
    old = material("chicken_coop_wood_old", WOOD_OLD, vary=0.3, scale=9)
    grey = material("chicken_coop_wood_grey", WOOD_GREY, vary=0.3, scale=9)
    dark = material("chicken_coop_dark", DARK, rough=1.0, vary=0.1, crevice=0.2)
    thatch = material("chicken_coop_thatch", THATCH, rough=0.95, vary=0.4, scale=45, crevice=0.8)
    thatch_old = material("chicken_coop_thatch_old", THATCH_OLD, rough=0.95, vary=0.4, scale=45, crevice=0.8)
    rope = material("chicken_coop_rope", ROPE, rough=0.9, vary=0.25, scale=50)
    iron = material("chicken_coop_iron", IRON, rough=0.6, metal=0.7, vary=0.3, scale=25)
    straw = material("chicken_coop_straw", STRAW, rough=0.9, vary=0.35, scale=60)
    boards = (wood, old, grey)

    cx, lx = (X0 + X1) / 2, X1 - X0
    wall_h = WALL_Z - FLOOR_Z

    # Legs: the four corner posts run from the ground to the wall top; braces under the floor.
    for i, x in enumerate((X0 + POST / 2, X1 - POST / 2)):
        for j, y in enumerate((-HALF_Y + POST / 2, HALF_Y - POST / 2)):
            box(f"post_{i}{j}", (POST, POST, WALL_Z), (x, y, WALL_Z / 2), old, rot=(0, 0, rnd.uniform(-2, 2)),
                bevel=0.01)
    box("floor", (lx - 0.02, 2 * HALF_Y - 0.02, 0.05), (cx, 0, FLOOR_Z - 0.025), old, bevel=0.008)
    for j, y in enumerate((-HALF_Y + POST / 2, HALF_Y - POST / 2)):
        # Two knee braces a side, each from a leg up to the floor bearer nearer the middle.
        for k, (xp, sx) in enumerate(((X0 + POST, 1), (X1 - POST, -1))):
            run, rise = 0.24, FLOOR_Z - 0.06 - 0.16
            box(f"brace_{j}{k}", (math.hypot(run, rise), 0.04, 0.045),
                (xp + sx * run / 2, y, 0.16 + rise / 2), old,
                rot=(0, -sx * math.degrees(math.atan2(rise, run)), 0), bevel=0.006)

    # The house: a core box behind the boards, vertical boards front and back, horizontal boards on the ends.
    box("core", (lx - 0.06, 2 * HALF_Y - 0.06, wall_h), (cx, 0, FLOOR_Z + wall_h / 2), dark, bevel=0)
    n = 7
    w = (lx - 2 * POST) / n
    for side, y in (("front", -HALF_Y + 0.03), ("back", HALF_Y - 0.03)):
        for k in range(n):
            x = X0 + POST + w * (k + 0.5)
            h = wall_h - rnd.uniform(0, 0.02)
            box(f"{side}_board_{k}", (w - 0.008, PLANK_T, h), (x, y - math.copysign(PLANK_T / 2, -y), FLOOR_Z + h / 2),
                boards[rnd.randrange(3)], rot=(0, rnd.uniform(-0.8, 0.8), 0), bevel=0.006)
    for end, x in (("left", X0 + 0.03), ("right", X1 - 0.03)):
        m = 4
        bh = wall_h / m
        for k in range(m):
            box(f"{end}_board_{k}", (PLANK_T, 2 * HALF_Y - 2 * POST, bh - 0.008),
                (x + math.copysign(PLANK_T / 2, x - cx), 0, FLOOR_Z + bh * (k + 0.5)), boards[rnd.randrange(3)],
                rot=(rnd.uniform(-0.8, 0.8), 0, 0), bevel=0.006)
        # The gable: stepped boards under the thatch.
        for k in range(4):
            z = WALL_Z + 0.07 * k + 0.035
            half = EAVE_Y - (z + 0.035 - EAVE_Z) * EAVE_Y / (RIDGE_Z - EAVE_Z) - 0.01
            box(f"{end}_gable_{k}", (PLANK_T, 2 * half, 0.062),
                (x + math.copysign(PLANK_T / 2, x - cx), 0, z), boards[rnd.randrange(3)], bevel=0.005)
        box(f"{end}_gable_core", (PLANK_T, 0.16, 0.3), (x, 0, WALL_Z + 0.15), dark, bevel=0)
    box("wall_plate_front", (lx, 0.06, 0.05), (cx, -HALF_Y + 0.03, WALL_Z + 0.02), old, bevel=0.008)
    box("wall_plate_back", (lx, 0.06, 0.05), (cx, HALF_Y - 0.03, WALL_Z + 0.02), old, bevel=0.008)

    # Front: the egg door with strap hinges and a turn button, and a small slatted window.
    fy = -HALF_Y - PLANK_T
    dx, dw, dh = X1 - 0.33, 0.36, 0.38
    dz = FLOOR_Z + 0.06 + dh / 2
    box("door", (dw, 0.022, dh), (dx, fy - 0.006, dz), grey, rot=(0, 1.2, 0), bevel=0.006)
    box("door_brace", (0.05, 0.02, dh * 1.1), (dx, fy - 0.022, dz), old, rot=(0, 42, 0), bevel=0)
    for i, z in enumerate((dz - dh / 2 + 0.07, dz + dh / 2 - 0.07)):
        box(f"door_batten_{i}", (dw - 0.03, 0.02, 0.06), (dx, fy - 0.022, z), old, bevel=0)
        box(f"hinge_{i}", (0.2, 0.008, 0.03), (dx - dw / 2 + 0.07, fy - 0.035, z), iron, bevel=0)
        cylinder(f"hinge_pin_{i}", 0.01, 0.05, (dx - dw / 2 - 0.01, fy - 0.03, z - 0.025), iron, segments=8,
                 bevel=0)
    cylinder("latch_pivot", 0.012, 0.03, (dx + dw / 2 + 0.04, fy - 0.0, dz), iron, segments=8, rot=(90, 0, 0),
             bevel=0)
    box("latch", (0.025, 0.02, 0.11), (dx + dw / 2 + 0.04, fy - 0.035, dz), old, rot=(0, 20, 0), bevel=0)
    wx, wz = X0 + 0.2, FLOOR_Z + wall_h * 0.62
    box("window", (0.2, 0.02, 0.16), (wx, fy + 0.005, wz), dark, bevel=0)
    for i in range(3):
        box(f"window_slat_{i}", (0.025, 0.02, 0.17), (wx - 0.06 + 0.06 * i, fy - 0.006, wz), old, bevel=0)
    box("window_frame_top", (0.26, 0.025, 0.035), (wx, fy - 0.008, wz + 0.095), old, bevel=0)
    box("window_frame_sill", (0.28, 0.04, 0.03), (wx, fy - 0.014, wz - 0.095), old, bevel=0)

    # The pop hole in the +x end with a slide shutter in two guides, and the cleated ramp down to the ground.
    ex = X1 + PLANK_T
    hz = FLOOR_Z + 0.13
    box("pop_hole", (0.02, 0.17, 0.22), (ex, -0.08, hz), dark, bevel=0)
    box("shutter", (0.018, 0.19, 0.2), (ex + 0.012, -0.08, hz + 0.19), grey, bevel=0.004)
    for i, y in enumerate((-0.19, 0.03)):
        box(f"shutter_guide_{i}", (0.03, 0.025, 0.5), (ex + 0.012, y, hz + 0.11), old, bevel=0)
    run, rise = RAMP_X - X1, FLOOR_Z
    a = math.degrees(math.atan2(rise, run))
    length = math.hypot(run, rise)
    box("ramp", (length, RAMP_W, 0.025), ((X1 + RAMP_X) / 2 + 0.01, -0.08, rise / 2 + 0.01), wood,
        rot=(0, a, 0), bevel=0.005)
    for k in range(5):
        t = (k + 0.7) / 6
        x = RAMP_X - run * t
        z = rise * t + 0.012 / math.cos(math.radians(a)) + 0.008
        box(f"ramp_cleat_{k}", (0.025, RAMP_W - 0.03, 0.02), (x, -0.08 + rnd.uniform(-0.01, 0.01), z), old,
            rot=(0, a, 0), bevel=0)

    # The thatch: two courses a side, the upper one lapping over the lower, and a ridge roll tied with rope.
    slope = math.atan2(RIDGE_Z - EAVE_Z, EAVE_Y)
    deg = math.degrees(slope)
    run = EAVE_Y / math.cos(slope)  # along the slope, eave to ridge
    nx, nz = math.sin(slope), math.cos(slope)  # outward normal (for the +y side)
    tx0, tx1 = X0 - OVERHANG, X1 + OVERHANG
    for side in (-1, 1):
        for c, (s0, s1, t, lift) in enumerate(((0.0, 0.58, THATCH_T, 0.0), (0.45, 1.04, THATCH_T, 0.05))):
            mid = (s0 + s1) / 2 * run
            y = side * (EAVE_Y - mid * math.cos(slope))
            z = EAVE_Z + mid * math.sin(slope)
            y += side * nx * (t / 2 + lift)
            z += nz * (t / 2 + lift)
            box(f"thatch_{side}_{c}", (tx1 - tx0 - c * 0.02, (s1 - s0) * run, t),
                ((tx0 + tx1) / 2 + rnd.uniform(-0.01, 0.01), y, z), thatch if c else thatch_old,
                rot=(-side * deg + rnd.uniform(-1.5, 1.5), 0, rnd.uniform(-0.6, 0.6)), bevel=0.03)
        # A ragged fringe of tufts along the eave.
        for k in range(5):
            x = tx0 + 0.1 + (tx1 - tx0 - 0.2) * k / 4 + rnd.uniform(-0.02, 0.02)
            blob(f"eave_tuft_{side}_{k}", 0.055, (x, side * (EAVE_Y + 0.0), EAVE_Z + 0.04), thatch_old,
                 squash=(1.3, 0.7, 0.6), subdiv=1, seed=40 + k + (side > 0) * 10, jitter=0.2)
    ridge_z = RIDGE_Z + (THATCH_T + 0.05) / math.cos(slope) - 0.02
    cylinder("ridge", 0.075, tx1 - tx0 + 0.04, (tx0 - 0.02, 0, ridge_z), thatch, segments=10, rot=(0, 90, 0),
             bevel=0.02)
    for k in range(4):
        x = tx0 + 0.1 + (tx1 - tx0 - 0.2) * k / 3
        cylinder(f"ridge_tie_{k}", 0.08, 0.025, (x, 0, ridge_z), rope, segments=10, rot=(0, 90, 0), bevel=0)

    # Straw scattered under the house.
    for k in range(10):
        x, y = rnd.uniform(X0, X1), rnd.uniform(-HALF_Y, HALF_Y)
        box(f"straw_{k}", (rnd.uniform(0.1, 0.18), 0.008, 0.006), (x, y, 0.004), straw,
            rot=(0, 0, rnd.uniform(0, 180)), bevel=0)
