"""A carved wooden temple lectern, its reading face on -y: a cross-shaped foot of two moulded beams with scrolled
ends, a stout square post with a carved collar and a ring of fluting, a bracket head carrying a sloping desk with
carved rosette side panels and a book ledge, and a heavy open book with a red ribbon lying on the desk."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall size: about 0.6 m wide (x), 0.55 m deep (y), 1.25 m high to the top of the desk.
W, D = 0.6, 0.5
FOOT_L = 0.52  # each foot beam
FOOT_T = 0.07  # foot beam height
POST = 0.11  # square post
DESK_W = 0.56
DESK_D = 0.42  # along the slope
DESK_T = 0.03
SLOPE = 24  # degrees; the low edge is on -y
DESK_Z = 1.08  # height of the desk's centre
BOOK_W, BOOK_D = 0.44, 0.3  # open book, both pages

WOOD = (0.17, 0.095, 0.05)  # linear RGB, dark oiled oak
WOOD_OLD = (0.13, 0.075, 0.042)
WOOD_CARVE = (0.21, 0.125, 0.065)  # the carved, rubbed parts
LEATHER = (0.12, 0.05, 0.03)
PAGE = (0.46, 0.4, 0.29)
INK = (0.07, 0.055, 0.045)
RIBBON = (0.3, 0.05, 0.04)
BRASS = (0.35, 0.24, 0.1)


@prop
def lectern_wood():
    rnd = random.Random(18)
    wood = material("lectern_wood_wood", WOOD, vary=0.22, scale=14)
    old = material("lectern_wood_wood_old", WOOD_OLD, vary=0.28, scale=11)
    carve = material("lectern_wood_carve", WOOD_CARVE, vary=0.2, scale=18, crevice=0.8)
    leather = material("lectern_wood_leather", LEATHER, rough=0.7, vary=0.3, scale=16)
    page = material("lectern_wood_page", PAGE, rough=0.95, vary=0.12, scale=30, crevice=0.3)
    ink = material("lectern_wood_ink", INK, rough=0.9, vary=0.2, scale=40)
    ribbon = material("lectern_wood_ribbon", RIBBON, rough=0.8, vary=0.2, scale=20)
    brass = material("lectern_wood_brass", BRASS, rough=0.4, vary=0.2, scale=20, metal=0.8)

    # Foot: two crossed beams with rounded scroll ends lifting slightly off the ground on pads.
    box("foot_x", (FOOT_L, 0.09, FOOT_T), (0, 0, FOOT_T / 2), wood, bevel=0.014)
    box("foot_y", (0.09, FOOT_L, FOOT_T), (0, 0, FOOT_T / 2 + 0.002), old, bevel=0.014)
    for i, (x, y) in enumerate([(-1, 0), (1, 0), (0, -1), (0, 1)]):
        cx, cy = x * (FOOT_L / 2 - 0.035), y * (FOOT_L / 2 - 0.035)
        rot = (90, 0, 0) if x else (0, 90, 0)
        cylinder(f"foot_scroll_{i}", 0.045, 0.1, (cx + (0 if x else -0.05), cy + (0.05 if x else 0), 0.045), carve,
                 rot=rot, segments=12, bevel=0.008)
    box("foot_block", (0.17, 0.17, 0.06), (0, 0, FOOT_T + 0.03), carve, bevel=0.012)

    # Post: a square shaft with a carved collar, a fluted band and a capital.
    z0 = FOOT_T + 0.06
    post_top = DESK_Z - 0.17
    box("post", (POST, POST, post_top - z0), (0, 0, (post_top + z0) / 2), wood, bevel=0.012)
    for k, z in enumerate((z0 + 0.04, z0 + 0.36, post_top - 0.05)):
        box(f"collar_{k}", (POST + 0.035, POST + 0.035, 0.035), (0, 0, z), carve if k != 1 else old, bevel=0.01)
    # Fluting: shallow raised ribs on every face of the post's middle.
    for f in range(4):
        a = math.radians(90 * f)
        for r in (-1, 0, 1):
            off = r * 0.032
            x = math.cos(a) * (POST / 2 + 0.004) - math.sin(a) * off
            y = math.sin(a) * (POST / 2 + 0.004) + math.cos(a) * off
            box(f"flute_{f}_{r}", (0.012, 0.012, 0.26), (x, y, z0 + 0.2 + 0.0 * r), carve, rot=(0, 0, 90 * f),
                bevel=0.004)
    cylinder("capital", 0.08, 0.04, (0, 0, post_top - 0.02), carve, r_top=0.11, segments=16, bevel=0.008)

    # Bracket head carrying the desk: two side cheeks shaped to the slope.
    tilt = math.radians(SLOPE)
    head_z = post_top + 0.02
    box("head", (0.2, 0.16, 0.07), (0, 0, head_z + 0.035), wood, bevel=0.01)
    for s in (-1, 1):
        box(f"cheek_{s}", (0.03, 0.3, 0.1), (s * 0.08, 0, head_z + 0.08), old, rot=(SLOPE, 0, 0), bevel=0.008)

    # The desk: a sloping board with a raised rim on the sides, carved side panels and a ledge on the low edge.
    desk_z = DESK_Z
    box("desk", (DESK_W, DESK_D, DESK_T), (0, 0, desk_z), wood, rot=(SLOPE, 0, 0), bevel=0.01)

    def on_desk(u, v, h):
        """A point on the desk: u along x, v along the slope (+ up the slope, toward +y), h above its top face."""
        n = DESK_T / 2 + h
        return (u, v * math.cos(tilt) - n * math.sin(tilt), desk_z + v * math.sin(tilt) + n * math.cos(tilt))

    for s in (-1, 1):
        # The side panels hang under the desk edge, deeper at the back (+y).
        box(f"side_panel_{s}", (0.025, DESK_D * 0.92, 0.12), (s * (DESK_W / 2 - 0.02), 0.015, desk_z - 0.075), old,
            rot=(SLOPE, 0, 0), bevel=0.008)
        # A carved rosette on each side panel's outer face: a disc with petals and a raised boss.
        rx = s * (DESK_W / 2 - 0.004)
        ry, rz = 0.03, desk_z - 0.07
        cylinder(f"rosette_{s}", 0.045, 0.012, (rx - s * 0.006, ry, rz), carve, rot=(0, s * 90, 0), segments=16,
                 bevel=0.004)
        for p in range(6):
            a = math.radians(60 * p + 30)
            box(f"rosette_{s}_petal_{p}", (0.012, 0.03, 0.014),
                (rx + s * 0.004, ry + math.cos(a) * 0.028, rz + math.sin(a) * 0.028), carve,
                rot=(math.degrees(a) + 90, 0, 0), bevel=0.003)
        blob(f"rosette_{s}_boss", 0.013, (rx + s * 0.008, ry, rz), carve, subdiv=1, seed=3 + s, jitter=0.05)
        # Rails along the desk's side edges.
        box(f"rim_{s}", (0.025, DESK_D, 0.022), on_desk(s * (DESK_W / 2 - 0.0125), 0, 0.011), carve,
            rot=(SLOPE, 0, 0), bevel=0.006)
    box("ledge", (DESK_W, 0.035, 0.045), on_desk(0, -DESK_D / 2 + 0.0175, 0.022), carve, rot=(SLOPE, 0, 0),
        bevel=0.008)
    box("crest", (DESK_W * 0.6, 0.03, 0.05), on_desk(0, DESK_D / 2 - 0.015, 0.025), carve, rot=(SLOPE, 0, 0),
        bevel=0.01)
    for s in (-1, 1):
        blob(f"crest_knob_{s}", 0.022, on_desk(s * DESK_W * 0.3, DESK_D / 2 - 0.015, 0.05), carve, subdiv=1,
             seed=8 + s, jitter=0.06)

    # The open book: two covers in a shallow V, a thick block of pages on each, ruled lines of text and a ribbon.
    half = BOOK_W / 2
    v0 = -0.015
    for s in (-1, 1):
        cx = s * half / 2
        box(f"cover_{s}", (half + 0.012, BOOK_D + 0.02, 0.012), on_desk(cx, v0, 0.006), leather,
            rot=(SLOPE, s * -4, 0), bevel=0.004)
        box(f"pages_{s}", (half - 0.02, BOOK_D - 0.01, 0.03), on_desk(cx - s * 0.002, v0, 0.012 + 0.015 + 0.004 *
            (1 - abs(cx) / half)), page, rot=(SLOPE, s * -4, 0), bevel=0.008)
        # Lines of writing: thin dark bars on the page face, a darker illuminated initial on the left page.
        for row in range(9):
            length = (half - 0.08) * rnd.uniform(0.75, 1.0)
            box(f"text_{s}_{row}", (length, 0.005, 0.002),
                on_desk(cx - s * 0.005, v0 + BOOK_D / 2 - 0.05 - row * 0.024, 0.045 + 0.003 *
                        (1 - abs(cx) / half)), ink, rot=(SLOPE, s * -4, 0), bevel=0)
    box("initial", (0.035, 0.035, 0.003), on_desk(-half + 0.06, v0 + BOOK_D / 2 - 0.055, 0.049), ribbon,
        rot=(SLOPE, 4, 0), bevel=0)
    box("spine", (0.03, BOOK_D + 0.02, 0.02), on_desk(0, v0, 0.008), leather, rot=(SLOPE, 0, 0), bevel=0.006)
    # The ribbon falls from the spine over the ledge and hangs in front of it.
    low_y = -DESK_D / 2 * math.cos(tilt) - 0.03
    low_z = desk_z - DESK_D / 2 * math.sin(tilt) + 0.02
    box("ribbon", (0.012, 0.004, 0.15), (0.012, low_y, low_z - 0.075), ribbon, rot=(0, 4, 0), bevel=0)
    for s in (-1, 1):
        for v in (-1, 1):
            box(f"corner_{s}_{v}", (0.03, 0.03, 0.014),
                on_desk(s * (BOOK_W / 2 - 0.009), v0 + v * (BOOK_D / 2 - 0.004), 0.006), brass,
                rot=(SLOPE, s * -4, 0), bevel=0.003)
