"""A heavy iron-bound crypt door standing closed in a dressed stone frame: a thick leaf of dark vertical planks crossed
by three iron bands set with round studs, the bands running on into strap hinges on the left, a ring pull and a lock
plate with a keyhole on the front (-y); two jambs of stacked blocks, a deep lintel and a worn threshold."""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall dimensions (metres): within about 1.5 x 0.3 m on the ground and 2.4 m high.
W, T, H = 1.5, 0.3, 2.4  # frame width (x), frame depth (y), overall height (z)
OPEN_W, OPEN_H = 1.0, 2.0  # clear opening
JAMB = (W - OPEN_W) / 2  # each jamb, 0.25 m
LINTEL_H = H - OPEN_H  # 0.4 m
SILL_H = 0.04  # threshold slab
JAMB_COURSES = 5
JOINT = 0.012  # mortar joint between stones

LEAF_T = 0.09  # door leaf thickness (y)
LEAF_Y = -0.03  # leaf centre: set a little towards the front of the frame
LEAF_W = OPEN_W - 0.02
LEAF_H = OPEN_H - SILL_H - 0.012
PLANKS = 6
FRONT_Y = LEAF_Y - LEAF_T / 2  # front face of the planks
BACK_Y = LEAF_Y + LEAF_T / 2
BAND_H, BAND_T = 0.1, 0.016  # iron bands
BANDS_Z = (0.3, 1.02, 1.72)  # band centres
STUD_R = 0.022
STUDS = 7  # studs per band
HANDLE_X, HANDLE_Z = 0.3, 1.33
RING_R, RING_T = 0.075, 0.013

STONE = (0.19, 0.195, 0.205)  # linear RGB: the crypt wall kit's cool dark ashlar
STONE_OLD = (0.145, 0.148, 0.155)
STONE_PALE = (0.24, 0.243, 0.25)
MORTAR = (0.04, 0.04, 0.042)
OAK = (0.16, 0.098, 0.054)  # old dark oak
OAK_OLD = (0.125, 0.078, 0.044)
IRON = (0.045, 0.044, 0.043)
IRON_WORN = (0.12, 0.11, 0.1)
RUST = (0.09, 0.055, 0.035)


@prop
def door_iron_bound():
    rnd = random.Random(64)
    stone = material("door_iron_bound_stone", STONE, vary=0.28, scale=8, crevice=0.7)
    old = material("door_iron_bound_stone_old", STONE_OLD, vary=0.3, scale=9, crevice=0.7)
    pale = material("door_iron_bound_stone_pale", STONE_PALE, vary=0.22, scale=7, crevice=0.65)
    mortar = material("door_iron_bound_mortar", MORTAR, vary=0.1, scale=12)
    oak = material("door_iron_bound_plank", OAK, vary=0.28, scale=14)
    oak_old = material("door_iron_bound_plank_old", OAK_OLD, vary=0.3, scale=14)
    iron = material("door_iron_bound_iron", IRON, rough=0.55, vary=0.22, scale=20, metal=0.6)
    worn = material("door_iron_bound_iron_worn", IRON_WORN, rough=0.45, vary=0.2, scale=18, metal=0.7)
    rust = material("door_iron_bound_rust", RUST, rough=0.8, vary=0.3, scale=24, metal=0.3)

    def pick():
        return rnd.choice((stone, stone, old, pale))

    # --- Stone frame: a threshold, two jambs of stacked blocks over a mortar core, a deep lintel.
    box("sill", (OPEN_W + 0.04, T - 0.02, SILL_H), (0, 0, SILL_H / 2), old, bevel=0.01)
    x_in = OPEN_W / 2
    for s in (-1, 1):
        xc = s * (x_in + W / 2) / 2
        box(f"core_{s}", (JAMB - 0.04, T - 0.05, OPEN_H), (xc, 0, OPEN_H / 2), mortar, bevel=0)
        ch = OPEN_H / JAMB_COURSES
        for c in range(JAMB_COURSES):
            # Alternate a full-depth block with a slightly narrower one so the coursing reads.
            w = JAMB * (rnd.uniform(0.96, 1.0) if c % 2 == 0 else rnd.uniform(0.9, 0.94))
            box(f"jamb_{s}_{c}", (w, T * rnd.uniform(0.96, 0.99), ch - JOINT),
                (s * (W / 2 - w / 2 - rnd.uniform(0, 0.004)), rnd.uniform(-0.004, 0.004), ch * (c + 0.5) + 0.002),
                old if c == 0 else pick(), rot=(rnd.uniform(-0.6, 0.6), 0, rnd.uniform(-0.8, 0.8)), bevel=0.02)
    box("lintel_core", (W - 0.06, T - 0.05, LINTEL_H - 0.02), (0, 0, OPEN_H + LINTEL_H / 2), mortar, bevel=0)
    box("lintel", (W - 0.01, T - 0.004, LINTEL_H - JOINT - 0.004), (0, 0, OPEN_H + JOINT / 2 + (LINTEL_H - JOINT) / 2),
        stone, rot=(0, rnd.uniform(-0.3, 0.3), 0), bevel=0.025)
    # Stops round the opening behind the leaf, so the joint round the leaf reads dark and never lets light through.
    stop_y = BACK_Y + 0.025
    box("stop_top", (OPEN_W, 0.05, 0.05), (0, stop_y, OPEN_H - 0.025), mortar, bevel=0)
    for s in (-1, 1):
        box(f"stop_{s}", (0.1, 0.05, OPEN_H - SILL_H), (s * (x_in + 0.0), stop_y, (OPEN_H + SILL_H) / 2), mortar,
            bevel=0)

    # --- Door leaf: a recessed dark core and six heavy vertical planks with a little jitter.
    leaf_z0 = SILL_H + 0.001
    box("leaf_core", (LEAF_W - 0.03, LEAF_T - 0.02, LEAF_H - 0.025), (0, LEAF_Y, leaf_z0 + 0.002 + (LEAF_H - 0.025) / 2), oak_old,
        bevel=0)
    pw = LEAF_W / PLANKS
    for i in range(PLANKS):
        h = LEAF_H - rnd.uniform(0.0, 0.02)
        box(f"plank_{i}", (pw - 0.006, LEAF_T * rnd.uniform(0.95, 1.0), h),
            (-LEAF_W / 2 + pw * (i + 0.5) + rnd.uniform(-0.002, 0.002), LEAF_Y + rnd.uniform(-0.002, 0.002),
             leaf_z0 + h / 2),
            rnd.choice((oak, oak, oak_old)), rot=(0, rnd.uniform(-0.25, 0.25), 0), bevel=0.01)

    # --- Iron bands across both faces; on the front they carry studs and run on past the hinge edge as strap hinges.
    fy = FRONT_Y - BAND_T / 2 + 0.002
    by = BACK_Y + BAND_T / 2 - 0.002
    for k, z in enumerate(BANDS_Z):
        z += rnd.uniform(-0.01, 0.01)
        box(f"band_front_{k}", (LEAF_W - 0.01, BAND_T, BAND_H), (0, fy, z), iron, bevel=0.004)
        box(f"band_back_{k}", (LEAF_W - 0.04, BAND_T, BAND_H), (0, by, z), iron, bevel=0.004)
        for j in range(STUDS):
            x = -LEAF_W / 2 + 0.07 + (LEAF_W - 0.14) * j / (STUDS - 1)
            cylinder(f"stud_{k}_{j}", STUD_R, 0.018, (x, fy - BAND_T / 2 + 0.002, z), worn,
                     r_top=STUD_R * 0.55, rot=(90, 0, 0), segments=8, bevel=0)
        # Hinge: a knuckle on a pintle in the left jamb, the band's end widened into a round foot.
        cylinder(f"knuckle_{k}", 0.024, 0.16, (-LEAF_W / 2 - 0.004, FRONT_Y + 0.01, z - 0.08), iron, segments=10,
                 bevel=0)
        box(f"pintle_{k}", (0.05, 0.03, 0.035), (-x_in - 0.012, FRONT_Y + 0.02, z - 0.1), rust, bevel=0.005)
    # Studs between the bands, one per plank, in two rows.
    for r, z in enumerate((0.66, 1.37)):
        for i in range(PLANKS):
            x = -LEAF_W / 2 + pw * (i + 0.5)
            if r == 1 and abs(x - HANDLE_X) < pw / 2:
                continue
            cylinder(f"plank_stud_{r}_{i}", STUD_R * 0.9, 0.016, (x, FRONT_Y + 0.002, z + rnd.uniform(-0.01, 0.01)),
                     worn, r_top=STUD_R * 0.5, rot=(90, 0, 0), segments=8, bevel=0)

    # --- Ring pull and a lock plate with a keyhole on the right.
    box("handle_plate", (0.11, 0.012, 0.13), (HANDLE_X, FRONT_Y - 0.004, HANDLE_Z), iron, bevel=0.004)
    cylinder("handle_boss", 0.022, 0.025, (HANDLE_X, FRONT_Y - 0.008, HANDLE_Z + 0.03), worn, rot=(90, 0, 0),
             segments=10, bevel=0)
    torus("handle_ring", RING_R, RING_T, (HANDLE_X, FRONT_Y - 0.04, HANDLE_Z + 0.03 - RING_R), worn,
          rot=(90 - 12, 0, 0), major=20, minor=8)
    lz = BANDS_Z[1] + BAND_H / 2 + 0.1
    lx = HANDLE_X - 0.16
    box("lock_plate", (0.12, 0.012, 0.17), (lx, FRONT_Y - 0.004, lz), rust, bevel=0.006)
    for j, (dx, dz) in enumerate([(-0.04, 0.065), (0.04, 0.065), (-0.04, -0.065), (0.04, -0.065)]):
        cylinder(f"lock_rivet_{j}", 0.009, 0.008, (lx + dx, FRONT_Y - 0.01, lz + dz), worn, rot=(90, 0, 0),
                 segments=8, bevel=0)
    cylinder("keyhole", 0.014, 0.004, (lx, FRONT_Y - 0.0115, lz + 0.015), mortar, rot=(90, 0, 0), segments=10,
             bevel=0)
    box("keyhole_slot", (0.012, 0.004, 0.04), (lx, FRONT_Y - 0.0115, lz - 0.01), mortar, bevel=0)
