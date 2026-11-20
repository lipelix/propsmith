"""A scholar's oak writing desk, the sitter's side on -y: a plank top on four turned-corner legs with a stretcher
frame, a shallow drawer with an iron ring pull, a low book rail along the back; on top, sheets of parchment and a half
unrolled scroll, a dark glass inkwell with a quill standing in it, a closed book and a tallow candle in an iron dish."""
import math
import random

from mathutils import Euler, Vector

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall size: 1.2 m wide (x), 0.6 m deep (y), the top at 0.76 m, the candle's wick at 0.9 m and the
# quill's tip at about 0.95 m.
W, D = 1.2, 0.6
TOP_Z = 0.76  # top surface
TOP_T = 0.04
PLANKS = 3
LEG = 0.06
LEG_X = W / 2 - 0.06
LEG_Y = D / 2 - 0.06
APRON_H, APRON_T = 0.1, 0.025
STRETCHER_Z, STRETCHER_H = 0.12, 0.04
DRAWER_W, DRAWER_H = 0.46, 0.075
RAIL_H, RAIL_T = 0.05, 0.025  # book rail at the back of the top

CANDLE_AT = (-0.44, 0.17)
CANDLE_R, CANDLE_H = 0.024, 0.1
DISH_R, DISH_H = 0.06, 0.012
INKWELL_AT = (0.36, 0.14)
QUILL_L = 0.22

OAK = (0.2, 0.12, 0.062)  # linear RGB
OAK_OLD = (0.155, 0.095, 0.052)
OAK_TOP = (0.23, 0.14, 0.072)
IRON = (0.045, 0.043, 0.04)
PARCHMENT = (0.45, 0.37, 0.24)
PARCHMENT_OLD = (0.38, 0.29, 0.17)
INK = (0.07, 0.055, 0.045)
GLASS = (0.04, 0.06, 0.07)  # dark inkwell glass
WAX = (0.42, 0.38, 0.3)  # tallow
WICK = (0.05, 0.04, 0.035)
FEATHER = (0.4, 0.38, 0.34)
LEATHER = (0.14, 0.08, 0.045)


def tilted(base, rot, dist):
    """The point `dist` along the local +z of something standing on `base` turned by `rot` degrees."""
    e = Euler([math.radians(a) for a in rot])
    return tuple(Vector(base) + e.to_matrix() @ Vector((0, 0, dist)))


@prop
def desk_writing():
    rnd = random.Random(31)
    oak = material("desk_writing_oak", OAK, vary=0.25, scale=14)
    old = material("desk_writing_oak_old", OAK_OLD, vary=0.3, scale=11)
    top_mat = material("desk_writing_top", OAK_TOP, vary=0.28, scale=12)
    iron = material("desk_writing_iron", IRON, rough=0.55, vary=0.12, scale=20, metal=0.6)
    parch = material("desk_writing_parchment", PARCHMENT, rough=0.95, vary=0.18, scale=16, crevice=0.4)
    parch_old = material("desk_writing_parchment_old", PARCHMENT_OLD, rough=0.95, vary=0.22, scale=14, crevice=0.5)
    ink = material("desk_writing_ink", INK, rough=0.9, vary=0.2, scale=40)
    glass = material("desk_writing_glass", GLASS, rough=0.15, vary=0.1, scale=20)
    wax = material("desk_writing_wax", WAX, rough=0.6, vary=0.12, scale=18, crevice=0.3)
    wick = material("desk_writing_wick", WICK, rough=0.9, vary=0.1, scale=20)
    feather = material("desk_writing_feather", FEATHER, rough=0.9, vary=0.2, scale=30)
    leather = material("desk_writing_leather", LEATHER, rough=0.75, vary=0.3, scale=18, crevice=0.65)

    # The top: planks along x with hairline gaps, slightly uneven.
    pw = D / PLANKS
    for i in range(PLANKS):
        y = -D / 2 + pw / 2 + i * pw
        box(f"plank_{i}", (W - rnd.uniform(0, 0.012), pw - 0.004, TOP_T - rnd.uniform(0, 0.003)),
            (rnd.uniform(-0.004, 0.004), y, TOP_Z - TOP_T / 2), old if i == 1 else top_mat,
            rot=(0, 0, rnd.uniform(-0.2, 0.2)), bevel=0.01)
    under = TOP_Z - TOP_T

    # Four legs with a chamfered foot, an apron below the top and a low stretcher frame.
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        x, y = sx * LEG_X, sy * LEG_Y
        box(f"leg_{i}", (LEG, LEG, under), (x, y, under / 2), oak if i % 2 else old,
            rot=(0, 0, rnd.uniform(-1, 1)), bevel=0.012)
    for s in (-1, 1):
        box(f"apron_side_{s}", (APRON_T, 2 * LEG_Y - LEG, APRON_H), (s * LEG_X, 0, under - APRON_H / 2), oak,
            bevel=0.006)
        box(f"stretcher_side_{s}", (APRON_T + 0.01, 2 * LEG_Y - LEG, STRETCHER_H), (s * LEG_X, 0, STRETCHER_Z),
            old, bevel=0.008)
    box("apron_back", (2 * LEG_X - LEG, APRON_T, APRON_H), (0, LEG_Y, under - APRON_H / 2), oak, bevel=0.006)
    box("stretcher_mid", (2 * LEG_X - LEG, 0.045, STRETCHER_H), (0, 0, STRETCHER_Z), oak, bevel=0.008)
    # The front apron in two halves around the drawer.
    side_w = (2 * LEG_X - LEG - DRAWER_W) / 2
    for s in (-1, 1):
        box(f"apron_front_{s}", (side_w, APRON_T, APRON_H), (s * (DRAWER_W / 2 + side_w / 2), -LEG_Y,
                                                             under - APRON_H / 2), oak, bevel=0.006)
    box("apron_front_top", (DRAWER_W, APRON_T, APRON_H - DRAWER_H - 0.008),
        (0, -LEG_Y, under - (APRON_H - DRAWER_H - 0.008) / 2), oak, bevel=0.004)
    dz = under - APRON_H + DRAWER_H / 2 + 0.004
    box("drawer_body", (DRAWER_W - 0.01, D * 0.6, DRAWER_H - 0.006), (0, -LEG_Y + D * 0.3 - 0.01, dz), old,
        bevel=0.004)
    box("drawer_front", (DRAWER_W - 0.008, 0.022, DRAWER_H - 0.004), (0, -LEG_Y - 0.008, dz), top_mat, bevel=0.006)
    cylinder("drawer_plate", 0.018, 0.004, (0, -LEG_Y - 0.019, dz), iron, rot=(90, 0, 0), segments=12, bevel=0)
    torus("drawer_ring", 0.016, 0.0035, (0, -LEG_Y - 0.025, dz - 0.016), iron, rot=(90, 0, 0), major=14, minor=5)

    # A low rail along the back edge of the top to keep books from falling off.
    box("rail", (W - 0.08, RAIL_T, RAIL_H), (0, D / 2 - RAIL_T / 2 - 0.01, TOP_Z + RAIL_H / 2), oak, bevel=0.008)
    for s in (-1, 1):
        box(f"rail_end_{s}", (0.03, 0.08, RAIL_H + 0.015), (s * (W / 2 - 0.055), D / 2 - 0.05,
                                                            TOP_Z + (RAIL_H + 0.015) / 2), old, bevel=0.008)

    # Sheets of parchment fanned in front of the sitter, lines of writing on the top one.
    z = TOP_Z
    for i in range(3):
        t = 0.0025
        box(f"sheet_{i}", (0.24, 0.32, t), (0.02 + i * 0.03, -0.09 + rnd.uniform(-0.01, 0.01), z + t / 2),
            parch if i != 1 else parch_old, rot=(0, 0, rnd.uniform(-12, 12)), bevel=0)
        z += t
    top_rot = 8
    for row in range(10):
        length = 0.17 * rnd.uniform(0.6, 1.0)
        e = Euler((0, 0, math.radians(top_rot)))
        off = e.to_matrix() @ Vector((-0.085 + length / 2, 0.12 - row * 0.024, 0))
        box(f"text_{row}", (length, 0.004, 0.0015), (0.08 + off.x, -0.09 + off.y, z + 0.0033), ink,
            rot=(0, 0, top_rot), bevel=0)
    box("sheet_top", (0.22, 0.3, 0.0025), (0.08, -0.09, z + 0.00125), parch, rot=(0, 0, top_rot), bevel=0)

    # A half unrolled scroll to the left: a flat unrolled tongue and the roll at its end.
    box("scroll_flat", (0.2, 0.18, 0.003), (-0.27, -0.1, TOP_Z + 0.0015), parch_old, rot=(0, 0, -5), bevel=0)
    for k, x in enumerate((-0.385, -0.155)):
        cylinder(f"scroll_roll_{k}", 0.022, 0.2, (x, -0.0, TOP_Z + 0.022), parch_old if k else parch,
                 rot=(90, 0, -5), segments=10, bevel=0.003)

    # A closed book lying at the back right against the rail.
    box("book_cover", (0.24, 0.17, 0.05), (0.14, 0.17, TOP_Z + 0.025), leather, rot=(0, 0, 4), bevel=0.006)
    box("book_pages", (0.232, 0.162, 0.042), (0.143, 0.168, TOP_Z + 0.025), parch, rot=(0, 0, 4), bevel=0.004)

    # The inkwell: a squat dark glass pot with a narrow neck, a quill standing in it.
    ix, iy = INKWELL_AT
    cylinder("inkwell", 0.04, 0.045, (ix, iy, TOP_Z), glass, r_top=0.032, segments=14, bevel=0.006)
    cylinder("inkwell_neck", 0.016, 0.018, (ix, iy, TOP_Z + 0.045), glass, segments=10, bevel=0.003)
    cylinder("inkwell_ink", 0.013, 0.002, (ix, iy, TOP_Z + 0.062), ink, segments=10, bevel=0)
    rot = (-20, 46, 0)  # leaning well over, away from the candle
    base = (ix, iy, TOP_Z + 0.02)
    cylinder("quill_shaft", 0.0035, QUILL_L, base, feather, rot=rot, segments=6, bevel=0)
    vane_c = tilted(base, rot, QUILL_L * 0.68)
    box("quill_vane", (0.028, 0.003, QUILL_L * 0.55), vane_c, feather, rot=rot, bevel=0)
    box("quill_vane_tip", (0.018, 0.003, 0.05), tilted(base, rot, QUILL_L * 0.98), feather, rot=rot, bevel=0)

    # The candle: an iron dish with a ring handle, a tallow candle with drips, the wick.
    cx, cy = CANDLE_AT
    cylinder("dish", DISH_R, DISH_H, (cx, cy, TOP_Z), iron, r_top=DISH_R + 0.008, segments=16, bevel=0.003)
    cylinder("dish_cup", 0.03, 0.025, (cx, cy, TOP_Z + DISH_H), iron, segments=12, bevel=0.003)
    torus("dish_handle", 0.022, 0.004, (cx + DISH_R + 0.012, cy, TOP_Z + DISH_H - 0.002), iron, major=14, minor=5)
    cz = TOP_Z + DISH_H + 0.01
    cylinder("candle", CANDLE_R, CANDLE_H, (cx, cy, cz), wax, r_top=CANDLE_R * 0.92, segments=12, bevel=0.004)
    for k in range(3):
        a = math.radians(70 + 120 * k)
        blob(f"drip_{k}", 0.008, (cx + math.cos(a) * CANDLE_R, cy + math.sin(a) * CANDLE_R,
                                  cz + CANDLE_H * (0.55 + 0.12 * k)), wax, squash=(0.7, 0.7, 2.4), subdiv=1,
             seed=40 + k, jitter=0.1)
    top = cz + CANDLE_H
    cylinder("wick", 0.003, 0.014, (cx, cy, top - 0.003), wick, segments=6, bevel=0)

    anchor("light:candle", (cx, cy, top + 0.025))
    anchor("fire:candle", (cx, cy, top + 0.008), size=(0.01, 0.01, 0.04))
