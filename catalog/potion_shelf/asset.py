"""An apothecary's narrow wall shelf, open front on -y: two plank sides with a shaped top, a back of vertical boards,
four shelves with a lip rail, crowded with stoppered glass bottles and flasks in dull greens, ambers and reds, squat
clay jars with tied cloth covers and a few small lidded pots."""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder

# Overall size: about 1 m wide (x), 0.3 m deep (y), 1.5 m high. The back is on +y.
W, D, H = 1.0, 0.3, 1.45  # carcass; the crest on the sides reaches about 1.5 m
SIDE_T = 0.03
BACK_T = 0.018
BACK_BOARDS = 5
SHELF_T = 0.025
SHELF_Z = (0.08, 0.42, 0.76, 1.1)  # top surfaces of the four shelves
TOP_T = 0.035
LIP_H = 0.035  # the small rail along each shelf's front edge
INNER_W = W - 2 * SIDE_T
FRONT_Y = -D / 2
BACK_Y = D / 2

WOOD = (0.2, 0.12, 0.062)  # linear RGB
WOOD_OLD = (0.15, 0.095, 0.055)
GLASS = ((0.12, 0.27, 0.1), (0.42, 0.2, 0.05), (0.34, 0.07, 0.05), (0.1, 0.17, 0.32), (0.3, 0.32, 0.24))
CORK = (0.3, 0.2, 0.11)
WAX = (0.22, 0.05, 0.04)
CLAY = (0.38, 0.17, 0.08)
CLAY_PALE = (0.4, 0.3, 0.18)
CLOTH = (0.32, 0.27, 0.19)


def bottle(name, x, y, z, kind, glass, seal, rnd):
    """A glass bottle: a round flask, a tall bottle or a squat phial, each with a stopper."""
    if kind == 0:  # round-bellied flask with a long neck
        r = rnd.uniform(0.04, 0.05)
        cylinder(f"{name}_body", r * 0.7, r * 0.9, (x, y, z), glass, r_top=r, segments=8, bevel=0)
        cylinder(f"{name}_neck", r, r * 0.9 + 0.05, (x, y, z + r * 0.9), glass, r_top=0.011, segments=8, bevel=0)
        top = z + r * 1.8 + 0.05
    elif kind == 1:  # tall bottle with a short neck
        r = rnd.uniform(0.028, 0.034)
        h = rnd.uniform(0.15, 0.19)
        cylinder(f"{name}_body", r, h, (x, y, z), glass, r_top=r * 0.95, segments=8, bevel=0)
        cylinder(f"{name}_neck", r * 0.95, 0.06, (x, y, z + h - 0.002), glass, r_top=0.011, segments=8, bevel=0)
        top = z + h + 0.058
    else:  # squat phial
        r = rnd.uniform(0.022, 0.028)
        h = rnd.uniform(0.07, 0.09)
        cylinder(f"{name}_body", r, h, (x, y, z), glass, r_top=r * 0.5, segments=6, bevel=0)
        top = z + h
    cylinder(f"{name}_stopper", 0.012, 0.022, (x, y, top - 0.006), seal, r_top=0.015, segments=6, bevel=0)


def jar(name, x, y, z, r, h, clay, cloth):
    """A squat clay jar with a cloth cover tied over its mouth."""
    cylinder(f"{name}_belly", r * 0.8, h * 0.6, (x, y, z), clay, r_top=r, segments=10, bevel=0)
    cylinder(f"{name}_shoulder", r, h * 0.3, (x, y, z + h * 0.6 - 0.002), clay, r_top=r * 0.7, segments=10, bevel=0)
    cylinder(f"{name}_cover", r * 0.76, h * 0.14, (x, y, z + h * 0.88), cloth, r_top=r * 0.6, segments=10,
             bevel=0)


def pot(name, x, y, z, r, h, clay, wood):
    """A small straight-sided pot with a wooden lid."""
    cylinder(f"{name}_body", r, h, (x, y, z), clay, r_top=r * 0.92, segments=8, bevel=0)
    cylinder(f"{name}_lid", r * 0.98, 0.014, (x, y, z + h - 0.002), wood, r_top=r * 0.6, segments=8, bevel=0)


@prop
def potion_shelf():
    rnd = random.Random(29)
    wood = material("potion_shelf_wood", WOOD, vary=0.25, scale=14)
    old = material("potion_shelf_wood_old", WOOD_OLD, vary=0.3, scale=11)
    glasses = [material(f"potion_shelf_glass_{i}", c, rough=0.15, vary=0.1, scale=12, crevice=0.3)
               for i, c in enumerate(GLASS)]
    cork = material("potion_shelf_cork", CORK, vary=0.3, scale=40, rough=0.9)
    wax = material("potion_shelf_wax", WAX, vary=0.15, scale=20, rough=0.5)
    clay = material("potion_shelf_clay", CLAY, vary=0.2, scale=8, rough=0.9)
    clay_pale = material("potion_shelf_clay_pale", CLAY_PALE, vary=0.2, scale=8, rough=0.9)
    cloth = material("potion_shelf_cloth", CLOTH, vary=0.2, scale=22, rough=0.95, crevice=0.4)

    # Two plank sides with a stepped crest, a back of vertical boards, a top and four shelves with lip rails.
    for i, s in enumerate((-1, 1)):
        x = s * (W - SIDE_T) / 2
        box(f"side_{i}", (SIDE_T, D, H), (x, 0, H / 2), wood if i else old, bevel=0.008)
        box(f"crest_{i}", (SIDE_T, D * 0.6, 0.05), (x, BACK_Y - D * 0.3, H + 0.025), old, bevel=0.008)
    bw = INNER_W / BACK_BOARDS
    for k in range(BACK_BOARDS):
        x = -INNER_W / 2 + bw * (k + 0.5)
        box(f"back_{k}", (bw - 0.003, BACK_T, H - 0.01), (x, BACK_Y - BACK_T / 2, (H - 0.01) / 2),
            old if k % 2 else wood, rot=(0, rnd.uniform(-0.3, 0.3), 0), bevel=0.004)
    box("top", (W + 0.03, D + 0.02, TOP_T), (0, 0.01, H - TOP_T / 2), wood, bevel=0.01)
    for j, z in enumerate(SHELF_Z):
        box(f"shelf_{j}", (INNER_W + 0.004, D - BACK_T, SHELF_T), (0, -BACK_T / 2, z - SHELF_T / 2),
            wood if j % 2 else old, rot=(0, rnd.uniform(-0.3, 0.3), 0), bevel=0.005)
        box(f"lip_{j}", (INNER_W + 0.004, 0.014, LIP_H), (0, FRONT_Y + 0.007, z + LIP_H / 2 - 0.004), old,
            bevel=0.003)
    box("plinth", (INNER_W, 0.02, SHELF_Z[0] - SHELF_T), (0, FRONT_Y + 0.03, (SHELF_Z[0] - SHELF_T) / 2), old,
        bevel=0.004)

    # The goods: each shelf filled left to right with a seeded mix of bottles, jars and pots, two rows deep.
    limit = (0.29, 0.29, 0.29, H - TOP_T - SHELF_Z[3] - 0.01)
    n = 0
    for j, z in enumerate(SHELF_Z):
        for row, y in enumerate((0.05, -0.06)):
            x = -INNER_W / 2 + 0.05 + rnd.uniform(0, 0.03) + row * 0.04
            while x < INNER_W / 2 - 0.05:
                pick = rnd.random()
                yy = y + rnd.uniform(-0.012, 0.012)
                if j == 0 and row == 0 and pick < 0.5:
                    r = rnd.uniform(0.06, 0.07)
                    if x + r > INNER_W / 2 - 0.01:
                        break
                    jar(f"jar_{n}", x + r - 0.04, yy, z, r, min(0.17, limit[j]), clay_pale if n % 2 else clay,
                        cloth)
                    x += 2 * r + 0.015
                elif pick < 0.12:
                    r = rnd.uniform(0.035, 0.045)
                    pot(f"pot_{n}", x, yy, z, r, rnd.uniform(0.06, 0.08), clay_pale if n % 2 else clay, old)
                    x += 2 * r + 0.02
                elif pick < 0.22:
                    x += rnd.uniform(0.04, 0.08)  # a gap where something was sold
                    continue
                else:
                    kind = rnd.choice((0, 1, 1, 2, 2)) if limit[j] > 0.25 else 2
                    bottle(f"bottle_{n}", x, yy, z, kind, rnd.choice(glasses), wax if rnd.random() < 0.3 else cork, rnd)
                    x += (0.11 if kind == 0 else 0.075 if kind == 1 else 0.06) + rnd.uniform(0, 0.02)
                n += 1
