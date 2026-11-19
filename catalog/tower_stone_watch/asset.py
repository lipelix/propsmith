"""A round stone watchtower: three stepped drystone drums with string courses, a crenellated parapet, a red
conical roof, slit windows and a plank door (hand-written, from the tower isle diorama)."""
import math
import random

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall dimensions (metres): a small village lookout, about 4.3 m across and 12 m to the finial.
DRUMS = ((2.1, 3.0), (1.9, 2.8), (1.72, 2.6))  # (radius, height) from the ground up
COURSE_TUBE = 0.09  # string course between drums
MERLONS = 14
MERLON = (0.42, 0.32, 0.5)  # width, depth, height
ROOF_R, ROOF_H = 1.4, 2.6
DOOR_W, DOOR_H = 1.0, 2.0
SLIT_W, SLIT_H = 0.24, 0.8

STONE = (0.31, 0.29, 0.26)  # linear RGB
STONE_OLD = (0.25, 0.235, 0.21)
STONE_DARK = (0.12, 0.11, 0.10)
ROOF = (0.33, 0.085, 0.05)
WOOD = (0.17, 0.095, 0.05)
IRON = (0.05, 0.05, 0.05)
GLOW = (0.5, 0.33, 0.12)


@prop
def tower_stone_watch():
    rnd = random.Random(11)
    stones = [
        material("tower_stone", STONE, vary=0.3, scale=5),
        material("tower_stone_old", STONE_OLD, vary=0.32, scale=4),
    ]
    dark = material("tower_course", STONE_DARK, vary=0.15, scale=8)
    roof = material("tower_roof", ROOF, vary=0.3, scale=6)
    wood = material("tower_door", WOOD, vary=0.25, scale=14)
    iron = material("tower_iron", IRON, rough=0.5, metal=0.8, vary=0.3, scale=20)
    glow = material("tower_window", GLOW, rough=0.4, vary=0.1, crevice=0)

    # Drums: each a slightly tapered cylinder, the next one stepped in and resting on a string course.
    z = 0.0
    for i, (r, h) in enumerate(DRUMS):
        cylinder(f"drum_{i}", r, h, (0, 0, z), stones[i % 2], r_top=r * 0.97, segments=28, bevel=0.03)
        z += h
        torus(f"course_{i}", r * 0.97 + COURSE_TUBE * 0.4, COURSE_TUBE, (0, 0, z), dark, major=28, minor=6)
    top_r = DRUMS[-1][0] * 0.97

    # Parapet: a floor slab and a ring of merlons with seeded wear.
    cylinder("parapet_floor", top_r + 0.12, 0.18, (0, 0, z), dark, segments=28, bevel=0.025)
    z += 0.18
    for k in range(MERLONS):
        a = 360 * k / MERLONS + rnd.uniform(-1.5, 1.5)
        ar = math.radians(a)
        rr = top_r - MERLON[1] / 2 + 0.06
        box(
            f"merlon_{k}",
            (MERLON[1], MERLON[0] * rnd.uniform(0.92, 1.0), MERLON[2] * rnd.uniform(0.9, 1.0)),
            (rr * math.cos(ar), rr * math.sin(ar), z + MERLON[2] / 2),
            stones[k % 2],
            rot=(0, 0, a),
            bevel=0.02,
        )

    # Roof: a steep red cone inside the parapet, the merlons showing around it, with an iron finial.
    roof_z = z + MERLON[2] * 0.55
    cylinder("roof_post", top_r * 0.55, roof_z - z + 0.1, (0, 0, z), wood, segments=16, bevel=0.01)
    cylinder("roof", ROOF_R, ROOF_H, (0, 0, roof_z), roof, r_top=0.04, segments=28, bevel=0.02)
    cylinder("finial", 0.05, 0.35, (0, 0, roof_z + ROOF_H - 0.05), iron, segments=8, bevel=0.005)

    # Door on the -y face, in a dark recess, with two iron bands.
    r0 = DRUMS[0][0]
    box("door_recess", (DOOR_W + 0.24, 0.3, DOOR_H + 0.14), (0, -r0 + 0.08, (DOOR_H + 0.14) / 2), dark, bevel=0.03)
    box("door", (DOOR_W, 0.08, DOOR_H), (0, -r0 - 0.04, DOOR_H / 2), wood, bevel=0.015)
    for b, bz in enumerate((0.45, 1.55)):
        box(f"door_band_{b}", (DOOR_W * 0.9, 0.03, 0.07), (0, -r0 - 0.095, bz), iron, bevel=0.006)
    box("door_step", (DOOR_W + 0.5, 0.55, 0.14), (0, -r0 - 0.15, 0.07), stones[1], bevel=0.02)

    # Slit windows, lit warm, two per upper drum and one high on the ground drum.
    z0 = 0.0
    slits = ((0, (200, 340)), (1, (250, 30, 150)), (2, (290, 70, 190)))
    for i, angles in slits:
        r, h = DRUMS[i]
        zc = z0 + h * (0.72 if i == 0 else 0.55)
        for a in angles:
            ar = math.radians(a)
            rr = r * 0.985 - 0.06
            box(f"slit_{i}_{a}", (0.16, SLIT_W, SLIT_H), (rr * math.cos(ar), rr * math.sin(ar), zc), glow, rot=(0, 0, a), bevel=0.01)
            box(
                f"sill_{i}_{a}",
                (0.2, SLIT_W + 0.14, 0.08),
                ((rr + 0.04) * math.cos(ar), (rr + 0.04) * math.sin(ar), zc - SLIT_H / 2 - 0.04),
                dark,
                rot=(0, 0, a),
                bevel=0.01,
            )
        z0 += h

    # A lamp glow inside the top drum, behind its windows.
    anchor("light:window", (0, 0, DRUMS[0][1] + DRUMS[1][1] + DRUMS[2][1] * 0.55))
