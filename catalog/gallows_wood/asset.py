"""A wooden gallows: a plank platform on a frame of posts with cross braces, a trapdoor in its deck with iron strap
hinges and a release lever, a steep flight of steps with a handrail up its +x side, and over the trapdoor two tall
uprights carrying a cross beam on knee braces, one rope wound round the beam and hanging to a coiled noose."""
import math
import random

from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall dimensions (metres): about 3 m wide (x) with the steps, 2.5 m deep, 4 m high.
DX0, DX1 = -1.5, 0.4  # the deck, along x
DY = 1.1  # the deck, either side of the middle
DECK = 1.4  # top of the deck
PLANK_T = 0.045
POST = 0.15  # posts under the deck
UPRIGHT = 0.2  # the gallows uprights
GX = -0.6  # the uprights and the trapdoor, along x
GY = 0.85  # the uprights, either side
BEAM_Z = 3.77  # underside of the cross beam
BEAM = (0.2, 2 * GY + 0.5, 0.17)  # cross beam: x, y, z
TRAP = 0.85  # the square trapdoor
STEPS = 7  # rises from the ground to the deck
STAIR_X = 1.5  # foot of the steps
STAIR_Y = -0.45  # the steps' centre line
STAIR_W = 0.95
NOOSE_Z = 2.95  # centre of the noose loop

OAK = (0.17, 0.11, 0.065)  # linear RGB, weathered
OAK_OLD = (0.14, 0.10, 0.07)
OAK_DARK = (0.11, 0.072, 0.045)
ROPE = (0.34, 0.27, 0.16)
IRON = (0.045, 0.044, 0.042)
IRON_WORN = (0.1, 0.092, 0.082)


def _rot_to(d):
    """Rotation (degrees, XYZ) that turns local +z onto direction `d`."""
    q = Vector((0, 0, 1)).rotation_difference(Vector(d).normalized())
    return tuple(math.degrees(a) for a in q.to_euler("XYZ"))


def _strut(name, a, b, w, mat, bevel=0.01):
    """A square timber `w` thick from `a` to `b`."""
    a, b = Vector(a), Vector(b)
    d = b - a
    return box(name, (w, w, d.length), tuple((a + b) / 2), mat, rot=_rot_to(d), bevel=bevel)


@prop
def gallows_wood():
    rnd = random.Random(17)
    oak = material("gallows_wood_oak", OAK, vary=0.3, scale=12)
    old = material("gallows_wood_oak_old", OAK_OLD, vary=0.3, scale=12)
    dark = material("gallows_wood_oak_dark", OAK_DARK, vary=0.3, scale=12)
    rope = material("gallows_wood_rope", ROPE, vary=0.3, scale=40)
    iron = material("gallows_wood_iron", IRON, rough=0.55, vary=0.25, scale=18, metal=0.6)
    worn = material("gallows_wood_iron_worn", IRON_WORN, rough=0.5, vary=0.25, scale=22, metal=0.7)

    # Posts under the deck on a 3 × 3 grid (the middle one left out under the trapdoor), girts under the deck edge.
    xs = (DX0 + POST / 2, (DX0 + DX1) / 2, DX1 - POST / 2)
    ys = (-DY + POST / 2, 0, DY - POST / 2)
    top = DECK - PLANK_T
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            if i == 1 and j == 1:
                continue
            box(f"post_{i}_{j}", (POST, POST, top), (x, y, top / 2), oak,
                rot=(rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), 0), bevel=0.012)
    gh = 0.14
    for j, y in enumerate((ys[0], ys[2])):
        box(f"girt_x_{j}", (DX1 - DX0, 0.1, gh), ((DX0 + DX1) / 2, y, top - gh / 2), old, bevel=0.01)
    for i, x in enumerate((xs[0], xs[2])):
        box(f"girt_y_{i}", (0.1, 2 * DY, gh), (x, 0, top - gh / 2), old, bevel=0.01)
    # Joists along y carry the planks.
    for k, x in enumerate((DX0 + 0.5, DX1 - 0.5)):
        box(f"joist_{k}", (0.1, 2 * DY - 0.2, 0.12), (x, 0, top - 0.06), dark, bevel=0.008)
    # Cross braces on the front (-y) and the +x faces, low rails at knee height.
    lo, hi = 0.15, top - gh - 0.02
    for k in range(2):
        xa, xb = xs[k], xs[k + 1]
        y = ys[0] - 0.02
        _strut(f"brace_front_{k}", (xa + 0.06, y, lo), (xb - 0.06, y, hi), 0.08, old)
        _strut(f"brace_front_b_{k}", (xa + 0.06, y - 0.08, hi), (xb - 0.06, y - 0.08, lo), 0.08, oak)
    for k in range(2):
        ya, yb = ys[k], ys[k + 1]
        x = xs[2] + 0.02
        _strut(f"brace_side_{k}", (x, ya + 0.06, lo), (x, yb - 0.06, hi), 0.08, old)
    box("rail_back", (DX1 - DX0, 0.08, 0.1), ((DX0 + DX1) / 2, ys[2], 0.35), dark, bevel=0.008)
    box("rail_left", (0.08, 2 * DY, 0.1), (xs[0], 0, 0.35), dark, bevel=0.008)

    # Deck planks along y.
    n = 10
    pw = (DX1 - DX0) / n
    for i in range(n):
        x = DX0 + pw * (i + 0.5)
        box(f"plank_{i}", (pw - 0.01, 2 * DY * rnd.uniform(0.98, 1.0), PLANK_T + rnd.uniform(-0.004, 0.004)),
            (x, rnd.uniform(-0.015, 0.015), DECK - PLANK_T / 2), old if i % 3 == 1 else oak,
            rot=(0, 0, rnd.uniform(-0.4, 0.4)), bevel=0.008)

    # The trapdoor: a dark frame, two leaves of planks with strap hinges, the bolt bar and the lever beside it.
    t2 = TRAP / 2
    fz = DECK + 0.004
    for k, (sx, sy, x, y) in enumerate(((TRAP + 0.06, 0.03, GX, -t2 - 0.015), (TRAP + 0.06, 0.03, GX, t2 + 0.015),
                                        (0.03, TRAP, GX - t2 - 0.015, 0), (0.03, TRAP, GX + t2 + 0.015, 0))):
        box(f"trap_frame_{k}", (sx, sy, 0.012), (x, y, fz), dark, bevel=0)
    for k, s in enumerate((-1, 1)):
        box(f"trap_leaf_{k}", (TRAP / 2 - 0.01, TRAP, 0.02), (GX + s * TRAP / 4, 0, DECK + 0.01), dark,
            rot=(0, 0, rnd.uniform(-0.3, 0.3)), bevel=0.006)
        for j, y in enumerate((-0.25, 0.25)):
            box(f"trap_hinge_{k}_{j}", (0.3, 0.05, 0.008), (GX + s * (t2 - 0.15), y, DECK + 0.024), iron, bevel=0)
    box("trap_bolt", (0.6, 0.04, 0.03), (GX, -t2 + 0.12, DECK + 0.035), worn, bevel=0.004)
    lx, ly = GX + t2 + 0.22, -t2 + 0.12
    box("lever_block", (0.16, 0.12, 0.1), (lx, ly, DECK + 0.05), dark, bevel=0.01)
    _strut("lever", (lx, ly, DECK + 0.08), (lx - 0.12, ly, DECK + 0.95), 0.045, oak, bevel=0.006)
    cylinder("lever_pin", 0.016, 0.16, (lx, ly - 0.08, DECK + 0.07), worn, segments=8, rot=(-90, 0, 0), bevel=0)

    # The uprights from the ground through the deck, the cross beam and knee braces under it.
    for k, s in enumerate((-1, 1)):
        y = s * GY
        box(f"upright_{k}", (UPRIGHT, UPRIGHT, BEAM_Z), (GX, y, BEAM_Z / 2), oak,
            rot=(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0), bevel=0.018)
        _strut(f"knee_{k}", (GX, y - s * (UPRIGHT / 2 - 0.03), BEAM_Z - 0.62),
               (GX, y - s * 0.62, BEAM_Z + 0.03), 0.12, old)
        box(f"beam_strap_{k}", (UPRIGHT + 0.014, 0.06, 0.3), (GX, y, BEAM_Z), iron, bevel=0.003)
    bx, by, bz = BEAM
    box("beam", (bx, by, bz), (GX, 0, BEAM_Z + bz / 2), oak, rot=(0.6, 0, 0), bevel=0.018)

    # The rope: wraps round the beam, a straight drop, the coils of the knot and the loop.
    for k in range(3):
        o = torus(f"wrap_{k}", 0.11, 0.018, (GX, -0.04 + k * 0.04, BEAM_Z + bz / 2), rope, rot=(90, 0, 0),
                  major=12, minor=6)
        o.scale = (1.0, 1.0, 0.95)
    coil_top = NOOSE_Z + 0.4
    cylinder("drop", 0.016, BEAM_Z - coil_top + 0.02, (GX, 0, coil_top - 0.01), rope, segments=8, bevel=0)
    for k in range(6):
        torus(f"coil_{k}", 0.028, 0.016, (GX, 0, coil_top - 0.02 - k * 0.03), rope, rot=(0, 0, k * 25), major=10,
              minor=6)
    lr = 0.13
    torus("noose", lr, 0.018, (GX, 0, coil_top - 0.18 - lr), rope, rot=(0, 90, 0), major=18, minor=6)

    # The steps up the +x side: two stringers, treads and a handrail on posts.
    run = STAIR_X - DX1
    rise = DECK / STEPS
    tread = run / STEPS
    for k, s in enumerate((-1, 1)):
        y = STAIR_Y + s * (STAIR_W / 2 - 0.03)
        _strut(f"stringer_{k}", (STAIR_X - 0.04, y, 0.06), (DX1 - 0.02, y, DECK - 0.1), 0.07, oak)
    for i in range(STEPS - 1):
        z = rise * (i + 1)
        x = STAIR_X - tread * (i + 1) + 0.02
        box(f"tread_{i}", (tread + 0.06, STAIR_W - 0.02 * rnd.random(), 0.04), (x, STAIR_Y, z - 0.02),
            old if i % 2 else oak, rot=(0, 0, rnd.uniform(-1, 1)), bevel=0.008)
    hy = STAIR_Y - STAIR_W / 2 - 0.02
    for k, (x, h) in enumerate(((STAIR_X - 0.06, 1.0), (DX1 + 0.04, DECK + 0.55))):
        box(f"rail_post_{k}", (0.07, 0.07, h), (x, hy, h / 2), oak, bevel=0.008)
    _strut("handrail", (STAIR_X - 0.06, hy, 0.95), (DX1 + 0.04, hy, DECK + 0.5), 0.06, old, bevel=0.008)
