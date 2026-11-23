"""The door section of the prison bars: the same 1.5 m stone sill, lintel, rails and bar pitch as
`prison_bars_section`, with two square iron door posts carrying a barred door hung on three strap hinges on the left,
a box lock plate with a keyhole and a ring pull on its right stile, and a fixed barred transom over it. Joins side by
side with the bar sections along x; the front (lock and handle) is on -y."""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall dimensions (metres): 1.5 m long (x), 0.4 m deep, 2.4 m high. Matches prison_bars_section.
W = 1.5
D = 0.4
H = 2.4
SILL_H = 0.18
LINTEL_H = 0.28
JOINT = 0.012
BAR_R = 0.017
PITCH = 0.15
RAIL = (0.016, 0.07)
BAND = (0.016, 0.06)
BAND_Z = 1.15
# The door: between two posts at ±POST_X, 2.05 m clear from the floor.
POST = 0.06
POST_X = 0.42
DOOR_TOP = 2.02
STILE = (0.045, 0.035)  # door stile: width (x), depth (y)
LOCK_Z = 1.05

STONE = (0.32, 0.305, 0.28)  # linear RGB, as prison_bars_section
STONE_OLD = (0.24, 0.23, 0.205)
IRON = (0.045, 0.044, 0.042)
IRON_WORN = (0.1, 0.092, 0.082)
RUST = (0.1, 0.055, 0.033)


@prop
def prison_bars_door():
    rnd = random.Random(6)
    stone = material("prison_bars_door_stone", STONE, vary=0.28, scale=8, crevice=0.7)
    old = material("prison_bars_door_stone_old", STONE_OLD, vary=0.3, scale=9, crevice=0.7)
    iron = material("prison_bars_door_iron", IRON, rough=0.55, vary=0.25, scale=18, metal=0.6)
    worn = material("prison_bars_door_iron_worn", IRON_WORN, rough=0.5, vary=0.25, scale=22, metal=0.7)
    rust = material("prison_bars_door_rust", RUST, rough=0.85, vary=0.3, scale=24, metal=0.25)

    # Stone sill and lintel, as the bar section.
    half = (W - JOINT) / 2
    for k, s in enumerate((-1, 1)):
        box(f"sill_{k}", (half - JOINT, D * rnd.uniform(0.97, 1.0), SILL_H), (s * (W / 4), 0, SILL_H / 2),
            rnd.choice((stone, old)), rot=(0, 0, rnd.uniform(-0.4, 0.4)), bevel=0.02)
    box("lintel", (W - JOINT, D, LINTEL_H - JOINT / 2), (0, 0, H - (LINTEL_H - JOINT / 2) / 2), stone, bevel=0.022)
    box("lintel_bed", (W - 0.02, D - 0.06, JOINT), (0, 0, H - LINTEL_H + JOINT / 2), old, bevel=0)

    z0, z1 = SILL_H, H - LINTEL_H
    box("rail_sill", (W - 0.004, RAIL[1], RAIL[0]), (0, 0, z0 + RAIL[0] / 2), iron, bevel=0.004)
    box("rail_lintel", (W - 0.004, RAIL[1], RAIL[0]), (0, 0, z1 - RAIL[0] / 2), iron, bevel=0.004)

    # Square door posts from the sill rail to the lintel rail, and a transom rail across the top of the door.
    for k, s in enumerate((-1, 1)):
        box(f"post_{k}", (POST, POST, z1 - z0), (s * POST_X, 0, (z0 + z1) / 2), iron, bevel=0.006)
    box("transom", (2 * POST_X, 0.05, 0.05), (0, 0, DOOR_TOP + 0.04), iron, bevel=0.005)

    # Fixed bars at the section's pitch: full height beside the door, short ones in the transom above it.
    n = round(W / PITCH)
    for i in range(n):
        x = -W / 2 + PITCH * (i + 0.5)
        mat = rust if rnd.random() < 0.25 else iron
        tilt = (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0)
        if abs(x) > POST_X:
            cylinder(f"bar_{i}", BAR_R, z1 - z0, (x, 0, z0), mat, segments=10, rot=tilt, bevel=0)
            cylinder(f"collar_{i}", BAR_R + 0.008, 0.03, (x, 0, z0 + RAIL[0]), worn, segments=10, bevel=0.003)
        elif abs(x) < POST_X - POST / 2 - BAR_R:
            cylinder(f"transom_bar_{i}", BAR_R, z1 - DOOR_TOP - 0.06, (x, 0, DOOR_TOP + 0.06), mat, segments=10,
                     bevel=0)

    # Cross bands on both faces of the fixed bars, either side of the door, riveted through each bar.
    seg = W / 2 - POST_X - POST / 2 - 0.002
    for s in (-1, 1):
        for f in (-1, 1):
            box(f"band_{s}_{f}", (seg, BAND[0], BAND[1]), (s * (W / 2 - seg / 2 - 0.002), f * (BAR_R + BAND[0] / 2),
                BAND_Z), iron, bevel=0.004)
    for i in range(n):
        x = -W / 2 + PITCH * (i + 0.5)
        if abs(x) > POST_X:
            cylinder(f"rivet_{i}", 0.014, 2 * (BAR_R + BAND[0]) + 0.012, (x, BAR_R + BAND[0] + 0.006, BAND_Z), worn,
                     segments=8, rot=(90, 0, 0), bevel=0.003)

    # The door leaf: two stiles, three rails, bars at the section's pitch, a diagonal brace.
    dx = POST_X - POST / 2 - 0.008  # half the door's width
    d0, d1 = z0 + RAIL[0] + 0.01, DOOR_TOP
    for k, s in enumerate((-1, 1)):
        box(f"stile_{k}", (STILE[0], STILE[1], d1 - d0), (s * (dx - STILE[0] / 2), 0, (d0 + d1) / 2), iron,
            bevel=0.005)
    for k, z in enumerate((d0 + 0.03, BAND_Z, d1 - 0.03)):
        for f in (-1, 1):
            box(f"door_rail_{k}_{f}", (2 * dx - 2 * STILE[0] + 0.004, BAND[0], 0.06),
                (0, f * (BAR_R + BAND[0] / 2), z), iron, bevel=0.003)
    for i in range(n):
        x = -W / 2 + PITCH * (i + 0.5)
        if abs(x) < dx - STILE[0]:
            cylinder(f"door_bar_{i}", BAR_R, d1 - d0 - 0.06, (x, 0, d0 + 0.03), rust if rnd.random() < 0.2 else iron,
                     segments=10, bevel=0)
            for k, z in enumerate((d0 + 0.03, BAND_Z, d1 - 0.03)):
                cylinder(f"door_rivet_{i}_{k}", 0.013, 2 * (BAR_R + BAND[0]) + 0.012,
                         (x, BAR_R + BAND[0] + 0.006, z), worn, segments=8, rot=(90, 0, 0), bevel=0)

    # Three strap hinges on the left: knuckles on pintles in the post, straps across the door's front.
    for k, z in enumerate((d0 + 0.2, (d0 + d1) / 2 + 0.25, d1 - 0.2)):
        cylinder(f"knuckle_{k}", 0.024, 0.13, (-dx - 0.004, -0.03, z - 0.065), iron, segments=10, bevel=0.004)
        box(f"pintle_{k}", (0.05, 0.03, 0.035), (-POST_X + 0.01, -0.03, z - 0.08), iron, bevel=0.004)
        box(f"hinge_strap_{k}", (0.32, 0.012, 0.05), (-dx + 0.16, -(BAR_R + BAND[0] + 0.006), z), worn,
            bevel=0.004)

    # Box lock on the right stile with a keyhole plate and a ring pull; a keeper on the post behind it.
    ly = -(BAR_R + BAND[0] + 0.03)
    box("lock_box", (0.2, 0.05, 0.24), (dx - 0.1, ly, LOCK_Z), rust, bevel=0.012)
    box("lock_plate", (0.15, 0.008, 0.18), (dx - 0.1, ly - 0.028, LOCK_Z), worn, bevel=0.004)
    box("keyhole", (0.016, 0.006, 0.045), (dx - 0.1, ly - 0.033, LOCK_Z - 0.03), iron, bevel=0.002)
    cylinder("keyhole_top", 0.014, 0.006, (dx - 0.1, ly - 0.03, LOCK_Z - 0.005), iron, segments=8, rot=(90, 0, 0),
             bevel=0)
    for k, z in enumerate((LOCK_Z + 0.07, LOCK_Z - 0.07)):
        cylinder(f"lock_rivet_{k}", 0.012, 0.012, (dx - 0.17, ly - 0.03, z), iron, segments=6, rot=(90, 0, 0),
                 bevel=0)
    cylinder("pull_boss", 0.02, 0.02, (dx - 0.24, ly + 0.005, LOCK_Z + 0.02), iron, segments=8, rot=(90, 0, 0),
             bevel=0)
    torus("pull_ring", 0.055, 0.009, (dx - 0.24, ly - 0.02, LOCK_Z - 0.03), worn, rot=(80, 0, 0), major=16, minor=6)
    box("keeper", (0.05, 0.05, 0.16), (POST_X - 0.005, -0.045, LOCK_Z), iron, bevel=0.006)
