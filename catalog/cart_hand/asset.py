"""A two-wheeled wooden handcart with sacks, parked on a stand (hand-written, Phase 12 Task 0)."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

WOOD = (0.2, 0.115, 0.058)
WOOD_OLD = (0.16, 0.11, 0.075)
IRON = (0.045, 0.045, 0.045)
SACK = (0.42, 0.33, 0.2)


@prop
def cart_hand():
    rnd = random.Random(3)
    wood = material("cart_wood", WOOD, vary=0.25, scale=14)
    old = material("cart_boards", WOOD_OLD, vary=0.3, scale=11)
    iron = material("cart_iron", IRON, rough=0.45, metal=0.8)
    sack = material("cart_sack", SACK, vary=0.18, scale=30, rough=1.0)

    # The bed: centred on the footprint; y is the long axis, the handles point to +y.
    bed_z, bed_x, bed_y, y0 = 0.52, 0.9, 1.25, -0.4
    for i in range(5):
        w = bed_x / 5
        box(f"floor_{i}", (w - 0.01, bed_y, 0.04), (-bed_x / 2 + w * (i + 0.5), y0, bed_z), old, bevel=0.006)
    for s in (-1, 1):
        for k in range(3):
            box(
                f"side_{s}_{k}",
                (0.035, bed_y, 0.095),
                (s * (bed_x / 2 - 0.018), y0, bed_z + 0.07 + k * 0.1),
                old,
                rot=(rnd.uniform(-0.6, 0.6), 0, 0),
                bevel=0.006,
            )
        box(f"stake_{s}_f", (0.05, 0.05, 0.36), (s * (bed_x / 2 + 0.01), y0 + bed_y / 2 - 0.05, bed_z + 0.16), wood, bevel=0.008)
        box(f"stake_{s}_b", (0.05, 0.05, 0.36), (s * (bed_x / 2 + 0.01), y0 - bed_y / 2 + 0.05, bed_z + 0.16), wood, bevel=0.008)
    for e in (-1, 1):
        for k in range(2):
            box(f"end_{e}_{k}", (bed_x, 0.035, 0.095), (0, y0 + e * (bed_y / 2 - 0.018), bed_z + 0.07 + k * 0.1), old, bevel=0.006)

    # Shafts run under the bed and out as handles; a stand holds the front up.
    for s in (-1, 1):
        x = s * 0.3
        box(f"shaft_{s}", (0.06, 2.0, 0.07), (x, y0 + 0.37, bed_z - 0.055), wood, bevel=0.01)
        box(f"leg_{s}", (0.06, 0.06, bed_z - 0.09), (x, y0 + bed_y / 2 - 0.08, (bed_z - 0.09) / 2), wood, bevel=0.008)
    box("handle_bar", (0.68, 0.045, 0.045), (0, y0 + 1.33, bed_z - 0.055), wood, bevel=0.008)

    # Wheels on an axle under the back half.
    R, axle_y = 0.4, y0 - 0.2
    cylinder("axle", 0.035, bed_x + 0.3, (-(bed_x + 0.3) / 2, axle_y, R), iron, rot=(0, 90, 0), bevel=0)
    for s in (-1, 1):
        x = s * (bed_x / 2 + 0.09)
        torus(f"rim_{s}", R - 0.03, 0.035, (x, axle_y, R), wood, rot=(0, 90, 0), major=40, minor=8)
        torus(f"tyre_{s}", R - 0.005, 0.012, (x, axle_y, R), iron, rot=(0, 90, 0), major=40, minor=6)
        cylinder(f"hub_{s}", 0.07, 0.12, (x - 0.06, axle_y, R), wood, rot=(0, 90, 0), segments=12, bevel=0.01)
        for k in range(8):
            a = 360 * k / 8 + 11
            box(
                f"spoke_{s}_{k}",
                (0.03, 0.03, R - 0.07),
                (x, axle_y + math.sin(math.radians(a)) * (R / 2), R + math.cos(math.radians(a)) * (R / 2)),
                wood,
                rot=(-a, 0, 0),
                bevel=0,
            )

    # Load: two grain sacks and a small crate.
    blob("sack_a", 0.22, (-0.18, y0 - 0.25, bed_z + 0.2), sack, squash=(1.0, 1.3, 0.75), seed=1, jitter=0.08)
    blob("sack_b", 0.2, (0.2, y0 - 0.05, bed_z + 0.19), sack, squash=(1.05, 1.25, 0.72), seed=2, jitter=0.08)
    box("crate", (0.34, 0.3, 0.26), (0.05, y0 + 0.38, bed_z + 0.15), material("cart_crate", (0.24, 0.15, 0.08), vary=0.3, scale=12), rot=(0, 0, 8), bevel=0.012)
