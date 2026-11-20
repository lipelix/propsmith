"""A scribe's pigeonhole rack for a wall, open front on -y: a plank case on a low plinth divided into a grid of square
cells, most holding rolled scrolls of parchment lying with their ends to the front, some tied with a cord or sealed,
a few cells empty, one with a leather scroll case."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder

# Overall size: 0.9 m wide (x), 0.3 m deep (y), 1.2 m high. Centred on the origin, the back on +y goes to the wall.
W, D, H = 0.9, 0.3, 1.2
COLS, ROWS = 5, 5
OUTER_T = 0.03  # sides, top and bottom
DIV_T = 0.014  # pigeonhole dividers
BACK_T = 0.012
PLINTH_H = 0.1
CAP_H = 0.03  # moulded cap on the top, overhanging a little
BOX_Z0 = PLINTH_H  # the case starts on the plinth
BOX_Z1 = H - CAP_H
CELL_W = (W - 2 * OUTER_T - (COLS - 1) * DIV_T) / COLS
CELL_H = (BOX_Z1 - BOX_Z0 - 2 * OUTER_T - (ROWS - 1) * DIV_T) / ROWS
FRONT_Y = -D / 2
POKE = 0.015  # how far scroll ends stand out of the front

WOOD = (0.19, 0.115, 0.058)  # linear RGB
WOOD_OLD = (0.15, 0.09, 0.047)
WOOD_INSIDE = (0.11, 0.065, 0.035)  # darker back and cell floors
PARCHMENT = (0.45, 0.37, 0.24)
PARCHMENT_OLD = (0.38, 0.29, 0.17)
PARCHMENT_PALE = (0.48, 0.42, 0.31)
CORD = (0.28, 0.06, 0.04)
CORD_GREEN = (0.08, 0.14, 0.08)
SEAL = (0.3, 0.03, 0.03)
LEATHER = (0.14, 0.08, 0.045)


def scroll(name, x, z, r, length, mat, core, rot_z):
    """A rolled scroll lying front to back with its axis at height z, the rolled-up core showing on its front end."""
    y0 = FRONT_Y - POKE
    # A cylinder grows along its local +z; turned by 90 deg about x it grows toward -y, so stand it at the back end.
    # No bevel: there are some sixty of them and the core disc already marks the end.
    cylinder(name, r, length, (x, y0 + length, z), mat, rot=(90, 0, rot_z), segments=8, bevel=0)
    cylinder(f"{name}_core", r * 0.4, 0.006, (x, y0 + 0.004, z), core, rot=(90, 0, rot_z), segments=6, bevel=0)


@prop
def scroll_rack():
    rnd = random.Random(12)
    wood = material("scroll_rack_wood", WOOD, vary=0.25, scale=14)
    old = material("scroll_rack_wood_old", WOOD_OLD, vary=0.3, scale=11)
    inside = material("scroll_rack_inside", WOOD_INSIDE, vary=0.25, scale=12)
    parch = [material(f"scroll_rack_parchment_{i}", c, rough=0.95, vary=0.2, scale=16, crevice=0.45)
             for i, c in enumerate((PARCHMENT, PARCHMENT_OLD, PARCHMENT_PALE))]
    cords = [material("scroll_rack_cord", CORD, rough=0.9, vary=0.2, scale=30),
             material("scroll_rack_cord_green", CORD_GREEN, rough=0.9, vary=0.2, scale=30)]
    seal = material("scroll_rack_seal", SEAL, rough=0.5, vary=0.2, scale=30)
    leather = material("scroll_rack_leather", LEATHER, rough=0.75, vary=0.3, scale=18, crevice=0.65)

    # The case: plinth, two sides, bottom, top, back and the moulded cap.
    box("plinth", (W - 0.04, D - 0.03, PLINTH_H), (0, 0.01, PLINTH_H / 2), old, bevel=0.008)
    for i, s in enumerate((-1, 1)):
        box(f"side_{i}", (OUTER_T, D, BOX_Z1 - BOX_Z0), (s * (W / 2 - OUTER_T / 2), 0, (BOX_Z0 + BOX_Z1) / 2),
            wood if i else old, bevel=0.008)
    for name, z in (("bottom", BOX_Z0 + OUTER_T / 2), ("top", BOX_Z1 - OUTER_T / 2)):
        box(name, (W - 2 * OUTER_T + 0.002, D, OUTER_T), (0, 0, z), wood, bevel=0.008)
    box("back", (W - 2 * OUTER_T + 0.002, BACK_T, BOX_Z1 - BOX_Z0 - 2 * OUTER_T + 0.002),
        (0, D / 2 - BACK_T / 2, (BOX_Z0 + BOX_Z1) / 2), inside, bevel=0.003)
    box("cap", (W + 0.03, D + 0.015, CAP_H), (0, -0.0075, H - CAP_H / 2), wood, bevel=0.01)

    # The pigeonholes: vertical dividers and horizontal shelves, a little uneven.
    x_in = -W / 2 + OUTER_T
    z_in = BOX_Z0 + OUTER_T
    inner_h = BOX_Z1 - BOX_Z0 - 2 * OUTER_T
    for c in range(1, COLS):
        x = x_in + c * (CELL_W + DIV_T) - DIV_T / 2
        box(f"divider_{c}", (DIV_T, D - BACK_T, inner_h + 0.002), (x, -BACK_T / 2, z_in + inner_h / 2),
            old if c % 2 else wood, rot=(0, rnd.uniform(-0.3, 0.3), 0), bevel=0.004)
    for r in range(1, ROWS):
        z = z_in + r * (CELL_H + DIV_T) - DIV_T / 2
        box(f"shelf_{r}", (W - 2 * OUTER_T + 0.002, D - BACK_T, DIV_T), (0, -BACK_T / 2, z),
            wood if r % 2 else old, bevel=0.004)

    # Scrolls in the cells: one, two or three side by side, sometimes one more lying on the hollow between two.
    empty = {(1, 3), (4, 1), (2, 0)}
    case_cell = (3, 3)
    for r in range(ROWS):
        for c in range(COLS):
            if (c, r) in empty:
                continue
            cx = x_in + c * (CELL_W + DIV_T) + CELL_W / 2
            floor = z_in + r * (CELL_H + DIV_T)
            name = f"cell_{c}_{r}"
            if (c, r) == case_cell:
                # A leather scroll case with a capped end and a strap ring.
                rc = 0.042
                cylinder(f"{name}_case", rc, D - 0.03, (cx, FRONT_Y + D - 0.03 - POKE, floor + rc), leather,
                         rot=(90, 0, 3), segments=10, bevel=0.004)
                cylinder(f"{name}_case_cap", rc + 0.004, 0.04, (cx, FRONT_Y + 0.04 - POKE - 0.002, floor + rc),
                         old, rot=(90, 0, 3), segments=10, bevel=0.004)
                continue
            n = rnd.choice((1, 2, 2, 3, 3))
            r_s = rnd.uniform(0.026, 0.034) if n < 3 else 0.026
            gap = (CELL_W - 2 * r_s * n) / (n + 1)
            xs = [cx - CELL_W / 2 + gap + r_s + k * (2 * r_s + gap) for k in range(n)]
            for k, x in enumerate(xs):
                rs = r_s * rnd.uniform(0.9, 1.0)
                length = rnd.uniform(0.22, D - 0.03)
                mat = parch[rnd.randrange(3)]
                scroll(f"{name}_{k}", x, floor + rs, rs, length, mat, parch[1], rnd.uniform(-4, 4))
                if rnd.random() < 0.35:
                    # Tied with a cord a little way back from the front end.
                    cylinder(f"{name}_{k}_cord", rs + 0.003, 0.012, (x, FRONT_Y + 0.07, floor + rs),
                             cords[rnd.randrange(2)], rot=(90, 0, 0), segments=8, bevel=0)
                elif rnd.random() < 0.2:
                    # A wax seal on the front end of the roll's top.
                    cylinder(f"{name}_{k}_seal", 0.012, 0.006, (x, FRONT_Y + 0.03, floor + 2 * rs - 0.001), seal,
                             segments=8, bevel=0.002)
            # A scroll lying on top, in the hollow between two.
            if n >= 2 and rnd.random() < 0.6:
                x = (xs[0] + xs[1]) / 2
                d = xs[1] - xs[0]
                rt = 0.026
                lift = math.sqrt(max((r_s + rt) ** 2 - (d / 2) ** 2, 0.0))
                if floor + r_s + lift + rt < floor + CELL_H - 0.005:
                    scroll(f"{name}_top", x, floor + r_s + lift, rt, rnd.uniform(0.2, 0.26), parch[2], parch[1],
                           rnd.uniform(-3, 3))
