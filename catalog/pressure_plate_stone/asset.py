"""A stone pressure plate, 1.5 m square and a few centimetres high: one big worn flagstone standing a little proud of a
border of crypt floor flags, with a dark open gap all round it where it sinks when stepped on, and a little grit in
the gap. Same stone palette as the crypt wall kit."""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box

S = 1.5  # overall footprint (square)
BORDER = 0.2  # width of the floor flags round the plate
GAP = 0.04  # the dark gap between the border and the plate
PLATE = S - 2 * BORDER - 2 * GAP  # the plate's side (1.02)
BED_H = 0.02  # dark bed under everything; the gap shows it
TOP = 0.045  # top of the border flags (the floor level of ritual_circle_floor)
PLATE_TOP = 0.07  # the plate stands about 2.5 cm proud of the floor
JOINT = 0.02

# Crypt stone palette (shared with wall_crypt_* and ritual_circle_floor): keep them equal.
STONE = (0.19, 0.195, 0.205)  # linear RGB: cool dark blue-grey
STONE_OLD = (0.145, 0.148, 0.155)
STONE_PALE = (0.24, 0.243, 0.25)
DAMP = (0.1, 0.11, 0.098)
VOID = (0.02, 0.02, 0.022)  # the gap: nearly black
PLATE_STONE = (0.215, 0.212, 0.205)  # the plate: a touch warmer and paler, rubbed by feet


@prop
def pressure_plate_stone():
    rnd = random.Random(66)
    stone = material("pressure_plate_stone_stone", STONE, vary=0.22, scale=7, crevice=0.7)
    old = material("pressure_plate_stone_stone_old", STONE_OLD, vary=0.25, scale=8, crevice=0.7)
    pale = material("pressure_plate_stone_stone_pale", STONE_PALE, vary=0.2, scale=9, crevice=0.65)
    damp = material("pressure_plate_stone_damp", DAMP, rough=0.6, vary=0.3, scale=5, crevice=0.75)
    void = material("pressure_plate_stone_void", VOID, vary=0.1, scale=20, crevice=0.9)
    plate = material("pressure_plate_stone_plate", PLATE_STONE, vary=0.2, scale=6, crevice=0.75)
    flags = [stone, old, pale, damp]
    weights = [6, 3, 2, 1]

    box("bed", (S - 0.01, S - 0.01, BED_H), (0, 0, BED_H / 2), void, bevel=0)

    # Border flags: the -y and +y strips run the full width, the side strips fit between them; each strip is cut into
    # two or three flags with a little jitter.
    h = TOP - BED_H + 0.006
    z = BED_H - 0.006 + h / 2
    inner = S / 2 - BORDER  # where the gap starts
    strips = [
        ("s", (-S / 2, S / 2), -S / 2 + BORDER / 2, "x"),
        ("n", (-S / 2, S / 2), S / 2 - BORDER / 2, "x"),
        ("w", (-inner, inner), -S / 2 + BORDER / 2, "y"),
        ("e", (-inner, inner), S / 2 - BORDER / 2, "y"),
    ]
    k = 0
    for side, (a, b), c, axis in strips:
        n = 3 if axis == "x" else 2
        cuts = [a] + sorted(a + (b - a) * (i + rnd.uniform(-0.12, 0.12)) / n for i in range(1, n)) + [b]
        for i in range(n):
            lo, hi = cuts[i] + JOINT / 2, cuts[i + 1] - JOINT / 2
            length = hi - lo
            mid = (lo + hi) / 2
            w = BORDER - JOINT
            dh = rnd.uniform(-0.003, 0.003)
            size = (length, w, h + dh) if axis == "x" else (w, length, h + dh)
            at = (mid, c, z + dh / 2) if axis == "x" else (c, mid, z + dh / 2)
            mat = rnd.choices(flags, weights)[0]
            box(f"flag_{side}_{k}", size, at, mat, rot=(0, 0, rnd.uniform(-0.8, 0.8)),
                bevel=rnd.uniform(0.008, 0.014))
            k += 1

    # The plate: one big slab, a hair out of square, its edges rounded by wear.
    ph = PLATE_TOP - BED_H + 0.004
    box("plate", (PLATE, PLATE, ph), (0.004, -0.003, BED_H - 0.004 + ph / 2), plate, rot=(0.25, -0.2, 1.1),
        bevel=0.022)
    # A darker worn stain in the middle where feet land.
    box("plate_wear", (PLATE * 0.55, PLATE * 0.48, 0.004), (0.03, -0.04, PLATE_TOP - 0.0005), old,
        rot=(0.25, -0.2, 8), bevel=0.0015)

    # Grit lodged in the gap.
    for i in range(14):
        side = rnd.randrange(4)
        t = rnd.uniform(-inner + 0.05, inner - 0.05)
        d = inner - GAP / 2 + 0.003
        x, y = [(t, -d), (t, d), (-d, t), (d, t)][side]
        r = rnd.uniform(0.012, 0.02)
        blob(f"grit_{i}", r, (x, y, BED_H + r * 0.5), rnd.choice([old, damp, stone]), squash=(1, 1, 0.7), subdiv=1,
             seed=200 + i)
