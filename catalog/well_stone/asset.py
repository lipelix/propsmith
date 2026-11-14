"""A round drystone well with a plank roof, a winch and a bucket (hand-written, Phase 12 Task 0)."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

STONE = (0.31, 0.265, 0.205)
STONE_DARK = (0.12, 0.11, 0.10)
WOOD = (0.17, 0.095, 0.05)
ROOF = (0.13, 0.075, 0.042)
ROPE = (0.42, 0.33, 0.20)
WATER = (0.015, 0.035, 0.04)
IRON = (0.05, 0.05, 0.05)


@prop
def well_stone():
    rnd = random.Random(7)
    stone = material("well_stone", STONE, vary=0.28, scale=9)
    dark = material("well_shaft", STONE_DARK, vary=0.1)
    wood = material("well_wood", WOOD, vary=0.25, scale=14)
    roof = material("well_roof", ROOF, vary=0.3, scale=10)
    rope = material("well_rope", ROPE, vary=0.15, scale=40)

    # Wall: five courses of rough blocks, every other course turned half a block.
    R_out, R_in, courses, per = 0.62, 0.44, 4, 10
    mid = (R_out + R_in) / 2
    for c in range(courses):
        h = 0.18
        for i in range(per):
            a = 2 * math.pi * (i + (0.5 if c % 2 else 0) + rnd.uniform(-0.06, 0.06)) / per
            w = 2 * math.pi * mid / per - 0.025
            box(
                f"block_{c}_{i}",
                (w * rnd.uniform(0.9, 1.0), (R_out - R_in) * rnd.uniform(0.92, 1.05), h * rnd.uniform(0.85, 1.0)),
                (mid * math.cos(a), mid * math.sin(a), h * c + h / 2),
                stone,
                rot=(rnd.uniform(-2, 2), rnd.uniform(-2, 2), math.degrees(a) + 90),
                bevel=0.022,
            )
    top = courses * 0.18
    caps = 8  # fewer, longer capstones than blocks: the triangle budget
    for i in range(caps):
        a = 2 * math.pi * (i + 0.25) / caps
        box(
            f"cap_{i}",
            (2 * math.pi * mid / caps - 0.02, R_out - R_in + 0.06, 0.07),
            (mid * math.cos(a), mid * math.sin(a), top + 0.035),
            stone,
            rot=(0, 0, math.degrees(a) + 90),
            bevel=0.018,
        )
    cylinder("shaft", R_in + 0.02, top - 0.02, (0, 0, 0.01), dark, segments=16, bevel=0, caps=False)
    cylinder("water", R_in, 0.01, (0, 0, top - 0.32), material("well_water", WATER, rough=0.05, vary=0.05, crevice=0), bevel=0)

    # Frame: two posts on the rim, a ridge beam and a winch roller with a crank.
    post_h = 2.05 - top
    for s in (-1, 1):
        box(f"post_{s}", (0.1, 0.1, post_h), (s * mid, 0, top + post_h / 2), wood, bevel=0.012)
        box(f"brace_{s}", (0.06, 0.32, 0.06), (s * mid, 0, top + 0.25), wood, rot=(35 * s, 0, 0), bevel=0.008)
    cylinder("roller", 0.055, 2 * mid - 0.1, (-(mid - 0.05), 0, 1.38), wood, segments=12, rot=(0, 90, 0), bevel=0.006)
    cylinder("rope_coil", 0.075, 0.24, (-0.12, 0, 1.38), rope, segments=12, rot=(0, 90, 0), bevel=0)
    box("crank_arm", (0.04, 0.04, 0.22), (mid + 0.1, 0, 1.31), material("well_iron", IRON, rough=0.5, metal=0.8), bevel=0)
    box("crank_grip", (0.16, 0.035, 0.035), (mid + 0.17, 0, 1.21), wood, bevel=0.006)

    # Rope down to a bucket hanging over the shaft.
    cylinder("rope", 0.012, 0.42, (0, 0, 0.96), rope, segments=8, bevel=0)
    cylinder("bucket", 0.13, 0.22, (0, 0, 0.74), wood, r_top=0.15, segments=16, bevel=0.006)
    torus("bucket_hoop", 0.145, 0.012, (0, 0, 0.92), material("well_iron", IRON, rough=0.5, metal=0.8), major=16, minor=6)
    torus("bucket_handle", 0.14, 0.008, (0, 0, 0.96), material("well_iron", IRON), rot=(90, 0, 0), major=16, minor=6)

    # Roof: two plank slopes over a ridge beam.
    ridge_z, eave_z, half = 2.2, 1.82, 0.62
    box("ridge", (1.5, 0.09, 0.09), (0, 0, ridge_z), wood, bevel=0.01)
    slope = math.atan2(ridge_z - eave_z, half)
    length = math.hypot(ridge_z - eave_z, half) + 0.08
    for s in (-1, 1):
        planks = 5
        for p in range(planks):
            x = -0.7 + (p + 0.5) * 1.4 / planks
            box(
                f"roof_{s}_{p}",
                (1.4 / planks - 0.012, length * rnd.uniform(0.97, 1.03), 0.035),
                (x, s * half / 2, (ridge_z + eave_z) / 2 + 0.02),
                roof,
                rot=(-math.degrees(slope) * s, rnd.uniform(-1.5, 1.5), 0),
                bevel=0.008,
            )
