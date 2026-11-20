"""An open spiked pit, 1.5 m square, its rim at floor level: a border of crypt floor flags whose inner edge is broken
away into jagged chunks, some tipped into the hole, round a square opening about 1 m across. Nothing may sink below
the ground, so the depth is drawn the way the eye reads it (as stairs_stone_down does): two stepped dark ledges inside
the rim, darker each step, down to a near-black floor bristling with rusty iron spikes. Same stone palette as the crypt
wall kit."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

S = 1.5  # overall footprint (square)
BORDER = 0.22  # nominal width of the floor flags round the hole
HOLE = S - 2 * BORDER  # the opening (1.06)
BED_H = 0.02
TOP = 0.08  # top of the rim flags: the floor level
JOINT = 0.02
LEDGE_W = 0.045  # width of each dark ledge stepping down inside the rim
LEDGE_TOPS = (0.055, 0.03)  # the two ledges, darker as they go down
FLOOR_H = 0.006  # the pit floor
SPIKE_ROWS = 5
SPIKE_R = 0.02
SPIKE_H = (0.05, 0.075)  # spike heights: the tips stay under the rim

# Crypt stone palette (shared with wall_crypt_* and ritual_circle_floor): keep them equal.
STONE = (0.19, 0.195, 0.205)  # linear RGB: cool dark blue-grey
STONE_OLD = (0.145, 0.148, 0.155)
STONE_PALE = (0.24, 0.243, 0.25)
DAMP = (0.1, 0.11, 0.098)
SHADE_1 = (0.06, 0.062, 0.066)  # the first ledge in the rim's shadow
SHADE_2 = (0.03, 0.031, 0.034)
VOID = (0.015, 0.015, 0.017)  # the pit floor: nearly black
IRON = (0.05, 0.047, 0.044)
RUST = (0.09, 0.055, 0.035)
IRON_WORN = (0.13, 0.115, 0.1)  # rubbed points that catch the light


def _ring(name, outer, inner, top, mat):
    """A square frame of four boxes from the ground up to `top`, `outer` and `inner` its outer and inner sides."""
    w = (outer - inner) / 2
    c = (outer + inner) / 4
    box(f"{name}_s", (outer, w, top), (0, -c, top / 2), mat, bevel=0)
    box(f"{name}_n", (outer, w, top), (0, c, top / 2), mat, bevel=0)
    box(f"{name}_w", (w, inner + 0.002, top), (-c, 0, top / 2), mat, bevel=0)
    box(f"{name}_e", (w, inner + 0.002, top), (c, 0, top / 2), mat, bevel=0)


@prop
def pit_open_spiked():
    rnd = random.Random(67)
    stone = material("pit_open_spiked_stone", STONE, vary=0.22, scale=7, crevice=0.7)
    old = material("pit_open_spiked_stone_old", STONE_OLD, vary=0.25, scale=8, crevice=0.7)
    pale = material("pit_open_spiked_stone_pale", STONE_PALE, vary=0.2, scale=9, crevice=0.65)
    damp = material("pit_open_spiked_damp", DAMP, rough=0.6, vary=0.3, scale=5, crevice=0.75)
    shade1 = material("pit_open_spiked_shade_1", SHADE_1, vary=0.2, scale=9, crevice=0.8)
    shade2 = material("pit_open_spiked_shade_2", SHADE_2, vary=0.15, scale=9, crevice=0.85)
    void = material("pit_open_spiked_void", VOID, vary=0.1, scale=20, crevice=0.9)
    iron = material("pit_open_spiked_iron", IRON, rough=0.55, vary=0.25, scale=18, metal=0.6)
    worn = material("pit_open_spiked_iron_worn", IRON_WORN, rough=0.45, vary=0.25, scale=20, crevice=0.3, metal=0.6)
    rust = material("pit_open_spiked_rust", RUST, rough=0.8, vary=0.3, scale=24, metal=0.3)
    flags = [stone, old, pale, damp]
    weights = [6, 3, 2, 1]

    # The inside: floor, two ledges stepping up to just under the rim's broken edge.
    box("floor", (S - 0.01, S - 0.01, FLOOR_H), (0, 0, FLOOR_H / 2), void, bevel=0)
    _ring("ledge_1", HOLE + 0.04, HOLE - 2 * LEDGE_W, LEDGE_TOPS[0], shade1)
    _ring("ledge_2", HOLE - 2 * LEDGE_W + 0.01, HOLE - 4 * LEDGE_W, LEDGE_TOPS[1], shade2)

    # Rim flags: four strips cut into flags; the inner edge of each flag is broken back by a random amount.
    h = TOP - BED_H + 0.006
    half = S / 2
    inner = half - BORDER
    strips = [
        ("s", (-half, half), -1, "x"),
        ("n", (-half, half), 1, "x"),
        ("w", (-inner, inner), -1, "y"),
        ("e", (-inner, inner), 1, "y"),
    ]
    k = 0
    for side, (a, b), sign, axis in strips:
        n = 3 if axis == "x" else 2
        cuts = [a] + sorted(a + (b - a) * (i + rnd.uniform(-0.12, 0.12)) / n for i in range(1, n)) + [b]
        for i in range(n):
            lo, hi = cuts[i] + JOINT / 2, cuts[i + 1] - JOINT / 2
            mid = (lo + hi) / 2
            # Broken back from the hole: the flag keeps 60 to 100 % of its width, its outer edge stays on the border.
            w = (BORDER - JOINT) * rnd.uniform(0.6, 1.0)
            c = sign * (half - JOINT / 2 - w / 2)
            dh = rnd.uniform(-0.004, 0.003)
            size = (hi - lo, w, h + dh) if axis == "x" else (w, hi - lo, h + dh)
            at = (mid, c, BED_H - 0.006 + (h + dh) / 2) if axis == "x" else (c, mid, BED_H - 0.006 + (h + dh) / 2)
            mat = rnd.choices(flags, weights)[0]
            box(f"flag_{side}_{k}", size, at, mat, rot=(0, 0, rnd.uniform(-1, 1)), bevel=rnd.uniform(0.008, 0.014))
            # Where a flag broke back, a jagged chunk or two of it still clings to the edge or has tipped in.
            if w < (BORDER - JOINT) * 0.9:
                for j in range(rnd.choice([1, 2])):
                    t = rnd.uniform(lo + 0.06, hi - 0.06)
                    d = half - JOINT / 2 - w - rnd.uniform(0.02, 0.05)
                    x, y = (t, sign * d) if axis == "x" else (sign * d, t)
                    ch = rnd.uniform(0.035, 0.05)
                    tilt = rnd.uniform(10, 25)
                    rot = (sign * tilt, 0, rnd.uniform(0, 40)) if axis == "x" else (0, -sign * tilt, rnd.uniform(0, 40))
                    box(f"chunk_{k}_{j}", (rnd.uniform(0.07, 0.12), rnd.uniform(0.05, 0.08), ch),
                        (x, y, TOP - ch / 2 - 0.012), mat, rot=rot, bevel=0.008)
            k += 1
    # The bed under the rim flags (the joints show it).
    _ring("bed", S - 0.01, HOLE + 0.03, BED_H, void)

    # Spikes: rows of rusty iron points on the pit floor, a few leaning or bent.
    span = HOLE - 4 * LEDGE_W - 0.08
    for r in range(SPIKE_ROWS):
        for c in range(SPIKE_ROWS):
            x = -span / 2 + span * c / (SPIKE_ROWS - 1) + rnd.uniform(-0.02, 0.02) + (0.03 if r % 2 else -0.03)
            y = -span / 2 + span * r / (SPIKE_ROWS - 1) + rnd.uniform(-0.02, 0.02)
            if abs(x) > span / 2 + 0.01:
                x = math.copysign(span / 2, x)
            sh = rnd.uniform(*SPIKE_H)
            lean = rnd.uniform(0, 6) if rnd.random() > 0.15 else rnd.uniform(14, 22)
            cylinder(f"spike_{r}_{c}", SPIKE_R, sh, (x, y, FLOOR_H - 0.002), rnd.choice([worn, worn, rust, iron]),
                     r_top=0.0015, segments=6, rot=(lean, 0, rnd.uniform(0, 360)), bevel=0)
            # A square foot collar where the spike is driven into the floor.
            box(f"spike_foot_{r}_{c}", (0.034, 0.034, 0.008), (x, y, FLOOR_H + 0.002), rust,
                rot=(0, 0, rnd.uniform(0, 90)), bevel=0.002)

    # Rubble that fell in with the broken edge.
    for i in range(7):
        a = rnd.uniform(0, 2 * math.pi)
        d = HOLE / 2 - 2 * LEDGE_W - rnd.uniform(0.04, 0.12)
        x, y = d * math.cos(a), d * math.sin(a)
        r = rnd.uniform(0.025, 0.045)
        blob(f"rubble_{i}", r, (x, y, FLOOR_H + r * 0.55), rnd.choice([old, stone, damp]), squash=(1.1, 0.9, 0.65),
             subdiv=1, seed=300 + i)
