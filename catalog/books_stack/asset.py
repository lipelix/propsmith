"""A leaning stack of seven worn books of different sizes, each a little turned and shifted so the pile slants, with a
heavy book lying open on top: leather covers with raised spine bands and brass corners on the big ones, pale page
edges, and two pages of written lines and a ribbon on the open one."""
import math
import random

from mathutils import Euler, Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box

# Overall size: about 0.4 × 0.4 m, the open book on top at about 0.38 m.
BOOKS = 7
BOARD = 0.006  # cover board thickness
LEAN = 0.014  # how far each book shifts along x from the one below
OPEN_W, OPEN_D = 0.36, 0.25  # the open book, both pages
OPEN_T = 0.024  # a page block of the open book
OPEN_V = 5  # degrees each half rises toward the spine

COVERS = (
    (0.24, 0.06, 0.04),  # oxblood
    (0.14, 0.08, 0.045),  # brown calf
    (0.07, 0.12, 0.08),  # bottle green
    (0.08, 0.08, 0.14),  # faded indigo
    (0.3, 0.2, 0.1),  # tan vellum
    (0.1, 0.06, 0.04),  # dark
)
PAGE = (0.44, 0.38, 0.27)
PAGE_OLD = (0.38, 0.3, 0.19)
INK = (0.07, 0.055, 0.045)
BRASS = (0.35, 0.24, 0.1)
RIBBON = (0.3, 0.05, 0.04)


def part(name, size, centre, rot, local, mat, bevel):
    """A box at `local` offset in a frame centred on `centre` and turned by `rot` (degrees, XYZ)."""
    e = Euler([math.radians(a) for a in rot])
    at = Vector(centre) + e.to_matrix() @ Vector(local)
    return box(name, size, tuple(at), mat, rot=rot, bevel=bevel)


def closed_book(name, w, d, t, centre, rz, cover, page, brass, rnd):
    """A closed book lying flat: two boards, a spine on local -y and an inset page block. Spine bands and, on the
    big ones, brass corners."""
    rot = (0, 0, rz)
    part(f"{name}_bottom", (w, d, BOARD), centre, rot, (0, 0, -t / 2 + BOARD / 2), cover, 0.003)
    part(f"{name}_top", (w, d, BOARD), centre, rot, (0, 0, t / 2 - BOARD / 2), cover, 0.003)
    part(f"{name}_spine", (w, 0.012, t), centre, rot, (0, -d / 2 + 0.006, 0), cover, 0.004)
    part(f"{name}_pages", (w - 0.012, d - 0.014, t - 2 * BOARD + 0.002), centre, rot, (0, 0.001, 0), page, 0.003)
    for k in (-1, 1):
        part(f"{name}_band_{k}", (0.008, 0.004, t + 0.002), centre, rot, (k * w * 0.28, -d / 2 - 0.001, 0), cover,
             0)
    if w > 0.26:
        for k in (-1, 1):
            part(f"{name}_corner_{k}", (0.03, 0.03, 0.003), centre, rot, (k * (w / 2 - 0.013), d / 2 - 0.013,
                                                                          t / 2 + 0.0005), brass, 0.001)


@prop
def books_stack():
    rnd = random.Random(23)
    covers = [material(f"books_stack_cover_{i}", c, rough=0.75, vary=0.3, scale=18, crevice=0.65)
              for i, c in enumerate(COVERS)]
    page = material("books_stack_page", PAGE, rough=0.95, vary=0.15, scale=30, crevice=0.3)
    page_old = material("books_stack_page_old", PAGE_OLD, rough=0.95, vary=0.2, scale=26, crevice=0.4)
    ink = material("books_stack_ink", INK, rough=0.9, vary=0.2, scale=40)
    brass = material("books_stack_brass", BRASS, rough=0.4, vary=0.2, scale=20, metal=0.8)
    ribbon = material("books_stack_ribbon", RIBBON, rough=0.8, vary=0.2, scale=20)

    # The stack: biggest at the bottom, each shifted a little further along x so the pile slants.
    z = 0.0
    x0 = -0.04
    for i in range(BOOKS):
        w = 0.32 - i * 0.017 + rnd.uniform(-0.015, 0.015)
        d = 0.24 - i * 0.01 + rnd.uniform(-0.01, 0.01)
        t = rnd.uniform(0.035, 0.06)
        rz = rnd.uniform(-9, 9) + (180 if i % 3 == 2 else 0)
        centre = (x0 + i * LEAN + rnd.uniform(-0.005, 0.005), rnd.uniform(-0.01, 0.01), z + t / 2)
        closed_book(f"book_{i}", w, d, t, centre, rz, covers[(i * 4 + 1) % len(covers)],
                    page_old if i % 2 else page, brass, rnd)
        z += t

    # The open book on top, turned across the stack: two halves rising to a sunken spine.
    rz = 14
    cx, cy = 0.0, -0.015
    half = OPEN_W / 2
    cover = covers[0]
    for s in (-1, 1):
        ry = s * -OPEN_V
        hx = s * half / 2  # the frame turns with the half, so the outer edge rises by itself
        c = (cx, cy, z)
        part(f"open_cover_{s}", (half, OPEN_D + 0.014, BOARD), c, (0, ry, rz),
             (hx, 0, BOARD / 2), cover, 0.003)
        part(f"open_pages_{s}", (half - 0.012, OPEN_D, OPEN_T), c, (0, ry, rz),
             (hx - s * 0.004, 0, BOARD + OPEN_T / 2), page, 0.006)
        # Lines of writing on the page.
        for row in range(8):
            length = (half - 0.06) * rnd.uniform(0.7, 1.0)
            part(f"text_{s}_{row}", (length, 0.004, 0.002), c, (0, ry, rz),
                 (hx - s * 0.004, OPEN_D / 2 - 0.035 - row * 0.022, BOARD + OPEN_T + 0.0008), ink, 0)
    part("open_spine", (0.03, OPEN_D + 0.014, 0.012), (cx, cy, z), (0, 0, rz), (0, 0, 0.006), cover, 0.004)
    # The ribbon lies across the right page from the spine and hangs over its lower edge.
    top = BOARD + OPEN_T + 0.003
    part("ribbon_lying", (0.01, 0.11, 0.002), (cx, cy, z), (0, 0, rz), (0.02, -OPEN_D / 2 + 0.055, top), ribbon, 0)
    part("ribbon_hanging", (0.01, 0.002, 0.07), (cx, cy, z), (0, 0, rz), (0.02, -OPEN_D / 2 - 0.002, top - 0.035),
         ribbon, 0)
