"""A tall plank bookcase for a wall, open front on -y: two thick sides on a plinth, a back of vertical boards, four
shelves and a moulded top, packed with uneven rows of worn leather books, some leaning, a few lying in small stacks,
and a handful of rolled scrolls."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder

# Overall size: 1.2 m wide (x), 0.4 m deep (y), 2 m high. Centred on the origin, the back on +y goes to the wall.
W, D, H = 1.2, 0.38, 2.0
SIDE_T = 0.045  # plank sides
BACK_T = 0.02
BACK_BOARDS = 5
SHELF_T = 0.035
SHELF_Z = (0.1, 0.48, 0.86, 1.24, 1.6)  # top surfaces of the bottom board and the four shelves
TOP_Z = 1.93  # underside of the top board
TOP_T = 0.035
CORNICE_H = 0.035  # moulding on top, overhanging
PLINTH_H = 0.085
INNER_W = W - 2 * SIDE_T
BACK_Y = D / 2
FRONT_Y = -D / 2
SHELF_D = D - BACK_T - 0.015
SHELF_Y = BACK_Y - BACK_T - SHELF_D / 2

WOOD = (0.19, 0.11, 0.055)  # linear RGB, darkened oak
WOOD_OLD = (0.15, 0.088, 0.045)
WOOD_TOP = (0.21, 0.125, 0.064)
# Book covers: dull dyed leathers and cloth.
COVERS = (
    (0.24, 0.06, 0.04),  # oxblood
    (0.14, 0.08, 0.045),  # brown calf
    (0.07, 0.12, 0.08),  # bottle green
    (0.08, 0.08, 0.14),  # faded indigo
    (0.3, 0.2, 0.1),  # tan vellum
    (0.2, 0.14, 0.08),  # tawny
    (0.1, 0.06, 0.04),  # dark
)
GILT = (0.42, 0.29, 0.09)
PARCHMENT = (0.45, 0.37, 0.24)
CORD = (0.28, 0.06, 0.04)


def book(name, size, at, mat, rot):
    """A book: a box with a one-segment bevel (many of them, so they stay cheap)."""
    obj = box(name, size, at, mat, rot=rot, bevel=0.004)
    obj.modifiers["bevel"].segments = 1
    return obj


def book_row(name, x0, x1, z, rnd, covers, gilt, gaps=()):
    """Books standing along a shelf from x0 to x1 on z; the last one may lean. `gaps` are x ranges left empty."""
    x = x0
    i = 0
    while True:
        t = rnd.uniform(0.03, 0.065)
        h = rnd.uniform(0.19, 0.29)
        d = rnd.uniform(0.17, 0.25)
        if x + t > x1:
            break
        if any(a <= x <= b for a, b in gaps):
            x += 0.01
            continue
        mat = covers[rnd.randrange(len(covers))]
        y = FRONT_Y + 0.03 + d / 2 + rnd.uniform(0, 0.015)
        book(f"{name}_{i}", (t, d, h), (x + t / 2, y, z + h / 2), mat, rot=(0, rnd.uniform(-1.5, 1.5), 0))
        # A gilt band on the spine of some books.
        if rnd.random() < 0.35:
            box(f"{name}_{i}_band", (t * 0.8, 0.004, 0.012), (x + t / 2, y - d / 2 - 0.001, z + h * 0.78), gilt,
                bevel=0)
        x += t + rnd.uniform(0.0, 0.004)
        i += 1
    return x


def leaning(name, x, z, side, rnd, covers, lean=14):
    """One book whose top leans on a neighbour's face at x: `side` -1 leans to -x, +1 to +x."""
    t, h, d = 0.04, 0.26, 0.22
    a = math.radians(lean)
    cx = x - side * (t / 2 * math.cos(a) + h / 2 * math.sin(a))
    cz = z + h / 2 * math.cos(a) + t / 2 * math.sin(a)
    book(name, (t, d, h), (cx, FRONT_Y + 0.035 + d / 2, cz), covers[rnd.randrange(len(covers))],
         rot=(0, side * lean, 0))


def flat_stack(name, x, z, n, rnd, covers):
    """Books lying flat, each a little turned."""
    for k in range(n):
        t = rnd.uniform(0.035, 0.055)
        w, d = rnd.uniform(0.17, 0.21), rnd.uniform(0.15, 0.2)
        book(f"{name}_{k}", (w, d, t), (x + rnd.uniform(-0.01, 0.01), FRONT_Y + 0.035 + d / 2, z + t / 2),
             covers[rnd.randrange(len(covers))], rot=(0, 0, rnd.uniform(-6, 6)))
        z += t
    return z


def scroll(name, x, y, z, length, r, rot, parch):
    """A rolled scroll lying along `rot` (a cylinder grows along its local +z)."""
    cylinder(name, r, length, (x, y, z), parch, rot=rot, segments=10, bevel=0.003)


@prop
def bookshelf_wood():
    rnd = random.Random(42)
    wood = material("bookshelf_wood_wood", WOOD, vary=0.25, scale=14)
    old = material("bookshelf_wood_wood_old", WOOD_OLD, vary=0.3, scale=11)
    top_mat = material("bookshelf_wood_top", WOOD_TOP, vary=0.25, scale=12)
    covers = [material(f"bookshelf_wood_cover_{i}", c, rough=0.75, vary=0.25, scale=18, crevice=0.6)
              for i, c in enumerate(COVERS)]
    gilt = material("bookshelf_wood_gilt", GILT, rough=0.4, vary=0.2, scale=20, metal=0.8)
    parch = material("bookshelf_wood_parchment", PARCHMENT, rough=0.95, vary=0.2, scale=16, crevice=0.4)
    cord = material("bookshelf_wood_cord", CORD, rough=0.9, vary=0.2, scale=30)

    # Two thick plank sides from the floor to the top board.
    for i, s in enumerate((-1, 1)):
        box(f"side_{i}", (SIDE_T, D, TOP_Z), (s * (W / 2 - SIDE_T / 2), 0, TOP_Z / 2), old if i else wood,
            rot=(0, 0, rnd.uniform(-0.2, 0.2)), bevel=0.01)

    # The back: vertical boards, a little uneven.
    bw = INNER_W / BACK_BOARDS
    for i in range(BACK_BOARDS):
        x = -INNER_W / 2 + bw / 2 + i * bw
        box(f"back_{i}", (bw - 0.004, BACK_T, TOP_Z - 0.005 - rnd.uniform(0, 0.01)),
            (x, BACK_Y - BACK_T / 2, TOP_Z / 2), old if i % 2 else wood, bevel=0.005)

    # Plinth board across the front under the bottom shelf.
    box("plinth", (INNER_W, 0.03, PLINTH_H), (0, FRONT_Y + 0.025, PLINTH_H / 2), old, bevel=0.006)

    # Bottom board and four shelves.
    for i, z in enumerate(SHELF_Z):
        box(f"shelf_{i}", (INNER_W + 0.002, SHELF_D, SHELF_T), (0, SHELF_Y, z - SHELF_T / 2),
            old if i % 2 else wood, rot=(rnd.uniform(-0.3, 0.3), 0, 0), bevel=0.008)

    # The top board and a cornice moulding overhanging front and sides.
    box("top", (W, D, TOP_T), (0, 0, TOP_Z + TOP_T / 2), top_mat, bevel=0.01)
    box("cornice", (W + 0.04, D + 0.02, CORNICE_H), (0, -0.01, H - CORNICE_H / 2), wood, bevel=0.012)
    box("frieze", (INNER_W, 0.025, 0.1), (0, FRONT_Y + 0.0125, TOP_Z - 0.05), top_mat, bevel=0.008)

    x0, x1 = -INNER_W / 2 + 0.005, INNER_W / 2 - 0.005

    # Bottom: big folios, a gap with a flat stack and two scrolls lying at the right.
    z = SHELF_Z[0]
    end = book_row("books_0", x0, 0.12, z, rnd, covers, gilt)
    leaning("lean_0", end, z, -1, rnd, covers, lean=18)
    flat_stack("stack_0", 0.38, z, 3, rnd, covers)

    # Second: a full row with one book pulled forward-leaning to the left at its end.
    z = SHELF_Z[1]
    book_row("books_1", x0 + 0.02, x1, z, rnd, covers, gilt, gaps=((-0.2, -0.12),))

    # Third: books on the left, a pile of scrolls on the right.
    z = SHELF_Z[2]
    end = book_row("books_2", x0, 0.05, z, rnd, covers, gilt)
    leaning("lean_2", end, z, -1, rnd, covers, lean=22)
    for k, (dx, dz, ang, ln) in enumerate(((0.3, 0.033, 2, 0.3), (0.37, 0.033, -3, 0.32), (0.44, 0.033, 4, 0.28),
                                            (0.335, 0.09, -1, 0.3), (0.405, 0.09, 3, 0.31))):
        scroll(f"scroll_{k}", dx, SHELF_Y + ln / 2 - 0.02, z + dz, ln, 0.033, (90, 0, ang), parch)
        cylinder(f"scroll_{k}_tie", 0.035, 0.012, (dx, SHELF_Y - 0.02, z + dz), cord,
                 rot=(90, 0, ang), segments=10, bevel=0)

    # Fourth: a flat stack on the left, then a row leaning against the right side.
    z = SHELF_Z[3]
    flat_stack("stack_3", -0.44, z, 4, rnd, covers)
    leaning("lean_3", -0.16, z, 1, rnd, covers, lean=16)
    book_row("books_3", -0.16, x1, z, rnd, covers, gilt)

    # Top shelf: a short row, a lone scroll and a gap.
    z = SHELF_Z[4]
    end = book_row("books_4", x0, -0.05, z, rnd, covers, gilt)
    leaning("lean_4", end, z, -1, rnd, covers, lean=25)
    scroll("scroll_top", 0.07, SHELF_Y - 0.03, z + 0.033, 0.25, 0.033, (0, 90, 4), parch)
    flat_stack("stack_4", 0.44, z, 2, rnd, covers)
