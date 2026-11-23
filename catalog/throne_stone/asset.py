"""A high-backed carved stone throne on a two-step dais, its front on -y: two steps of jointed grey slabs, a solid
seat block with a carved front panel and a dull red cushion, heavy arms ending in rolled scrolls, a tall back slab
with a framed carved roundel, a pointed gable crest with a ball finial, and two round columns with ball finials
flanking the back."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall size: the dais 1.4 x 1.4 m, the crest's finial at 2.4 m.
STEP1 = (1.4, 1.4, 0.15)  # lower step: x, y, height
STEP2 = (1.1, 1.05, 0.15)  # upper step, flush toward the back
STEP2_BACK = 0.62  # y of the upper step's back edge
DAIS_Z = STEP1[2] + STEP2[2]  # top of the dais
PLINTH_H = 0.08
SEAT_W, SEAT_Y0, SEAT_Y1 = 0.66, -0.23, 0.39  # seat block width, front and back (the back slab's face)
SEAT_Z = 0.74  # top of the stone seat
ARM_W, ARM_Z = 0.13, 1.05  # arm block width and top
BACK_W, BACK_T, BACK_Z = 0.78, 0.16, 1.94  # back slab width, thickness, top (where the gable starts)
CREST_T = 0.13
FINIAL_TOP = 2.385
COL_R, COL_X, COL_TOP = 0.065, 0.47, 2.0

STONE = (0.31, 0.30, 0.275)  # linear RGB
STONE_OLD = (0.26, 0.25, 0.225)
STONE_PALE = (0.37, 0.355, 0.32)  # carved mouldings
CARVE = (0.12, 0.115, 0.105)  # recesses of the carving
CLOTH = (0.17, 0.04, 0.032)  # dull madder red
GOLD = (0.42, 0.3, 0.1)


@prop
def throne_stone():
    rnd = random.Random(404)
    stone = material("throne_stone_stone", STONE, rough=0.85, vary=0.22, scale=7, crevice=0.65)
    old = material("throne_stone_stone_old", STONE_OLD, rough=0.9, vary=0.25, scale=9, crevice=0.7)
    pale = material("throne_stone_pale", STONE_PALE, rough=0.8, vary=0.18, scale=10, crevice=0.6)
    carve = material("throne_stone_carve", CARVE, rough=0.9, vary=0.2, scale=12, crevice=0.4)
    cloth = material("throne_stone_cushion", CLOTH, rough=0.95, vary=0.22, scale=14, crevice=0.4)
    gold = material("throne_stone_tassel", GOLD, rough=0.6, vary=0.25, scale=20, crevice=0.3, metal=0.4)

    # The dais: two steps, each a row of jointed slabs with a few millimetres of jitter.
    def step(name, sx, sy, yc, z0, h, n):
        w = sx / n
        for i in range(n):
            x = -sx / 2 + (i + 0.5) * w
            dh = rnd.uniform(-0.006, 0.004)
            box(f"{name}_{i}", (w - 0.006, sy, h + dh), (x, yc + rnd.uniform(-0.004, 0.004), z0 + (h + dh) / 2),
                stone if i % 2 else old, rot=(0, 0, rnd.uniform(-0.4, 0.4)), bevel=0.018)

    step("step_low", STEP1[0], STEP1[1], 0, 0, STEP1[2], 4)
    step("step_high", STEP2[0], STEP2[1], STEP2_BACK - STEP2[1] / 2, STEP1[2] - 0.01, STEP2[2] + 0.01, 3)
    # A pale moulded nosing along the front of each step.
    box("nosing_low", (STEP1[0] - 0.02, 0.05, 0.035), (0, -STEP1[1] / 2 + 0.02, STEP1[2] - 0.012), pale, bevel=0.01)
    box("nosing_high", (STEP2[0] - 0.02, 0.05, 0.035), (0, STEP2_BACK - STEP2[1] + 0.02, DAIS_Z - 0.012), pale,
        bevel=0.01)

    # Plinth under the throne.
    depth = 0.55 + 0.02 - (SEAT_Y0 - 0.04)
    box("plinth", (0.98, depth, PLINTH_H), (0, (0.57 + SEAT_Y0 - 0.04) / 2, DAIS_Z + PLINTH_H / 2 - 0.005), old,
        bevel=0.015)
    base = DAIS_Z + PLINTH_H - 0.01

    # The seat block with a recessed carved panel on its front and a lip under the cushion.
    seat_d = SEAT_Y1 - SEAT_Y0
    yc = (SEAT_Y0 + SEAT_Y1) / 2
    box("seat", (SEAT_W, seat_d, SEAT_Z - base), (0, yc, (base + SEAT_Z) / 2), stone, bevel=0.015)
    box("seat_lip", (SEAT_W + 0.04, 0.07, 0.05), (0, SEAT_Y0 + 0.02, SEAT_Z - 0.02), pale, bevel=0.01)
    pz = (base + SEAT_Z - 0.05) / 2
    box("seat_panel", (SEAT_W - 0.14, 0.02, 0.2), (0, SEAT_Y0 - 0.002, pz), carve, bevel=0.004)
    box("seat_boss", (0.09, 0.09, 0.02), (0, SEAT_Y0 - 0.012, pz), pale, rot=(90, 45, 0), bevel=0.006)
    for s in (-1, 1):
        box(f"seat_leaf_{s}", (0.13, 0.03, 0.035), (s * 0.12, SEAT_Y0 - 0.01, pz), pale, rot=(0, s * 18, 0),
            bevel=0.008)

    # The cushion, plump, with gold tassels at its front corners.
    box("cushion", (SEAT_W - 0.06, seat_d - 0.06, 0.08), (0, yc - 0.01, SEAT_Z + 0.035), cloth, bevel=0.03)
    for s in (-1, 1):
        blob(f"tassel_{s}", 0.022, (s * (SEAT_W / 2 - 0.04), SEAT_Y0 + 0.02, SEAT_Z + 0.02), gold,
             squash=(0.8, 0.8, 1.4), subdiv=1, seed=10 + s, jitter=0.08)

    # Arms: solid stone sides with a moulded rest and a rolled scroll at the front.
    for s in (-1, 1):
        x = s * (SEAT_W / 2 + ARM_W / 2 - 0.01)
        box(f"arm_{s}", (ARM_W, seat_d + 0.02, ARM_Z - base), (x, yc, (base + ARM_Z) / 2), old, bevel=0.015)
        box(f"arm_rest_{s}", (ARM_W + 0.04, seat_d + 0.06, 0.06), (x, yc - 0.03, ARM_Z + 0.02), pale, bevel=0.012)
        cylinder(f"scroll_{s}", 0.075, ARM_W + 0.05, (x - (ARM_W + 0.05) / 2, SEAT_Y0 - 0.04, ARM_Z - 0.04), pale,
                 segments=14, rot=(0, 90, 0), bevel=0.01)
        cylinder(f"scroll_eye_{s}", 0.04, 0.012, (x + s * (ARM_W / 2 + 0.025), SEAT_Y0 - 0.04, ARM_Z - 0.04), carve,
                 segments=10, rot=(0, s * 90, 0), bevel=0.003)
        box(f"arm_panel_{s}", (0.02, seat_d - 0.18, 0.12), (x + s * ARM_W / 2, yc, (base + SEAT_Z) / 2), carve,
            bevel=0.004)

    # The back slab with a framed panel and a carved roundel.
    by = SEAT_Y1 + BACK_T / 2
    box("back", (BACK_W, BACK_T, BACK_Z - base), (0, by, (base + BACK_Z) / 2), stone, bevel=0.015)
    face = SEAT_Y1 - 0.008
    z0, z1 = SEAT_Z + 0.12, BACK_Z - 0.1
    fw = BACK_W - 0.14
    for k, z in enumerate((z0, z1)):
        box(f"frame_h_{k}", (fw, 0.025, 0.045), (0, face, z), pale, bevel=0.008)
    for s in (-1, 1):
        box(f"frame_v_{s}", (0.045, 0.025, z1 - z0 + 0.045), (s * (fw / 2 - 0.0225), face, (z0 + z1) / 2), pale,
            bevel=0.008)
    box("panel", (fw - 0.09, 0.012, z1 - z0 - 0.045), (0, SEAT_Y1 - 0.002, (z0 + z1) / 2), old, bevel=0.003)
    rz = z1 - 0.3
    cylinder("roundel", 0.17, 0.02, (0, SEAT_Y1 - 0.004, rz), carve, segments=24, rot=(90, 0, 0), bevel=0.004)
    torus("roundel_ring", 0.17, 0.018, (0, SEAT_Y1 - 0.02, rz), pale, rot=(90, 0, 0), major=24, minor=6)
    for k in range(8):
        a = k * 45
        r = 0.07
        box(f"ray_{k}", (0.1, 0.02, 0.028),
            (r * math.cos(math.radians(a)), SEAT_Y1 - 0.022, rz + r * math.sin(math.radians(a))), pale,
            rot=(0, -a, 0), bevel=0)
    blob("roundel_boss", 0.04, (0, SEAT_Y1 - 0.03, rz), pale, squash=(1, 0.6, 1), subdiv=1, seed=5, jitter=0.05)
    box("lower_band", (fw, 0.02, 0.05), (0, face, (SEAT_Z + 0.04 + z0) / 2 + 0.03), carve, bevel=0.005)

    # The pointed gable crest: a square block turned 45 degrees about y, its lower half hidden in the slab, with pale
    # coping along both slopes and a ball finial.
    half = BACK_W / 2
    box("crest", (half * math.sqrt(2), CREST_T, half * math.sqrt(2)), (0, by, BACK_Z), stone, rot=(0, 45, 0),
        bevel=0.015)
    apex = BACK_Z + half
    slope = half * math.sqrt(2) + 0.04
    for s in (-1, 1):
        box(f"coping_{s}", (slope, BACK_T + 0.03, 0.05), (s * half / 2, by, BACK_Z + half / 2 + 0.025), pale,
            rot=(0, s * 45, 0), bevel=0.01)
    cylinder("finial_neck", 0.04, 0.03, (0, by, apex - 0.01), pale, segments=10, bevel=0.005)
    blob("finial", 0.045, (0, by, FINIAL_TOP - 0.045), pale, subdiv=1, seed=8, jitter=0.04)

    # Columns flanking the back, each on a square base with a capital and a ball finial.
    for s in (-1, 1):
        x = s * COL_X
        cy = by + 0.01
        box(f"col_base_{s}", (0.17, 0.17, 0.08), (x, cy, base + 0.04), old, bevel=0.012)
        cylinder(f"col_{s}", COL_R, COL_TOP - base - 0.14, (x, cy, base + 0.07), stone, r_top=COL_R * 0.9,
                 segments=12, bevel=0.008)
        for k in range(3):
            torus(f"col_ring_{s}_{k}", COL_R + 0.004, 0.012, (x, cy, base + 0.35 + k * 0.5), pale, major=12,
                  minor=4)
        box(f"col_cap_{s}", (0.16, 0.16, 0.07), (x, cy, COL_TOP - 0.05), pale, bevel=0.012)
        blob(f"col_ball_{s}", 0.07, (x, cy, COL_TOP + 0.05), pale, subdiv=2, seed=20 + s, jitter=0.04)
