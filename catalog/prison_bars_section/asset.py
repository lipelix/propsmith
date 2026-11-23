"""A 1.5 m section of prison bars, floor to lintel: round iron bars set in a dressed stone sill and a heavy stone
lintel, held by a flat iron rail on the sill, one under the lintel and a riveted cross band on both faces. The sill,
the lintel and the rails run the full 1.5 m and the bars keep one pitch across the joint, so sections (and
`prison_bars_door`) join side by side along x."""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder

# Overall dimensions (metres): 1.5 m long (x), 0.4 m deep, 2.4 m high.
W = 1.5
D = 0.4  # sill and lintel depth
H = 2.4
SILL_H = 0.18
LINTEL_H = 0.28
JOINT = 0.012  # mortar joint between stones
BAR_R = 0.017
PITCH = 0.15  # bar spacing; bars sit at ±PITCH/2, ±3 PITCH/2, ... so it carries across joins
RAIL = (0.016, 0.07)  # flat rail on the sill and under the lintel: thickness (z), width (y)
BAND = (0.016, 0.06)  # cross band on each face: thickness (y), height (z)
BAND_Z = 1.15

STONE = (0.32, 0.305, 0.28)  # linear RGB: cold grey dungeon stone
STONE_OLD = (0.24, 0.23, 0.205)
IRON = (0.045, 0.044, 0.042)
IRON_WORN = (0.1, 0.092, 0.082)
RUST = (0.1, 0.055, 0.033)


@prop
def prison_bars_section():
    rnd = random.Random(5)
    stone = material("prison_bars_section_stone", STONE, vary=0.28, scale=8, crevice=0.7)
    old = material("prison_bars_section_stone_old", STONE_OLD, vary=0.3, scale=9, crevice=0.7)
    iron = material("prison_bars_section_iron", IRON, rough=0.55, vary=0.25, scale=18, metal=0.6)
    worn = material("prison_bars_section_iron_worn", IRON_WORN, rough=0.5, vary=0.25, scale=22, metal=0.7)
    rust = material("prison_bars_section_rust", RUST, rough=0.85, vary=0.3, scale=24, metal=0.25)

    # Stone sill of two blocks and a single lintel block, joints half a joint in from each end.
    half = (W - JOINT) / 2
    for k, s in enumerate((-1, 1)):
        box(f"sill_{k}", (half - JOINT, D * rnd.uniform(0.97, 1.0), SILL_H), (s * (W / 4), 0, SILL_H / 2),
            rnd.choice((stone, old)), rot=(0, 0, rnd.uniform(-0.4, 0.4)), bevel=0.02)
    box("lintel", (W - JOINT, D, LINTEL_H - JOINT / 2), (0, 0, H - (LINTEL_H - JOINT / 2) / 2), stone, bevel=0.022)
    box("lintel_bed", (W - 0.02, D - 0.06, JOINT), (0, 0, H - LINTEL_H + JOINT / 2), old, bevel=0)

    # Iron rails along the sill and under the lintel.
    z0, z1 = SILL_H, H - LINTEL_H
    box("rail_sill", (W - 0.004, RAIL[1], RAIL[0]), (0, 0, z0 + RAIL[0] / 2), iron, bevel=0.004)
    box("rail_lintel", (W - 0.004, RAIL[1], RAIL[0]), (0, 0, z1 - RAIL[0] / 2), iron, bevel=0.004)

    # Bars from the sill into the lintel, a few rusted, a lead-sealed collar at the foot of each.
    n = round(W / PITCH)
    for i in range(n):
        x = -W / 2 + PITCH * (i + 0.5)
        mat = rust if rnd.random() < 0.25 else iron
        cylinder(f"bar_{i}", BAR_R, z1 - z0, (x, 0, z0), mat, segments=10,
                 rot=(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0), bevel=0)
        cylinder(f"collar_{i}", BAR_R + 0.008, 0.03, (x, 0, z0 + RAIL[0]), worn, segments=10, bevel=0.003)

    # Cross band on both faces with a rivet through each bar.
    for f in (-1, 1):
        y = f * (BAR_R + BAND[0] / 2)
        box(f"band_{f}", (W - 0.004, BAND[0], BAND[1]), (0, y, BAND_Z), iron, bevel=0.004)
    for i in range(n):
        x = -W / 2 + PITCH * (i + 0.5)
        cylinder(f"rivet_{i}", 0.014, 2 * (BAR_R + BAND[0]) + 0.012, (x, BAR_R + BAND[0] + 0.006, BAND_Z), worn,
                 segments=8, rot=(90, 0, 0), bevel=0.003)
