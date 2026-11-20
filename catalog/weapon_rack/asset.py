"""A merchant's timber weapon rack, front on -y: two footed uprights joined by a bottom board, a slotted middle rail and
a slotted top rail; three spears stand through both rails, a sword hangs by its crossguard and a bearded axe leans in
the middle rail."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall size: about 1.2 m wide (x), 0.4 m deep (y), 1.5 m high to the spear points.
W = 1.2
FOOT_L, FOOT = 0.39, 0.08  # feet along y under each upright
POST = 0.075
POST_X = W / 2 - 0.05
POST_H = 1.25  # top of the uprights
BOARD_Z, BOARD_T = 0.1, 0.03  # bottom board the butts stand on (top surface at BOARD_Z)
RAIL_T, RAIL_H = 0.03, 0.06  # each of the paired slot rails
GAP = 0.06  # slot between the front and back rail
MID_Z = 0.82  # top of the middle rail pair
TOP_Z = 1.17  # top of the top rail pair
SPEAR_L = 1.38  # butt to point
SPEAR_R = 0.016
SPEAR_HEAD = 0.2
SPEARS = (-0.44, -0.3, 0.42)  # x of each spear
SWORD_X = -0.1
BLADE_L, BLADE_W, BLADE_T = 0.7, 0.05, 0.008
AXE_X = 0.18
AXE_L = 0.9  # haft length

TIMBER = (0.2, 0.125, 0.065)  # linear RGB
TIMBER_OLD = (0.15, 0.1, 0.06)
SHAFT = (0.24, 0.16, 0.085)
STEEL = (0.2, 0.2, 0.21)
IRON = (0.05, 0.05, 0.05)
LEATHER = (0.13, 0.07, 0.035)
BRASS = (0.3, 0.22, 0.09)


def spear(n, x, rnd, shaft, steel, iron):
    lean = rnd.uniform(-1.5, 1.5)
    z0 = BOARD_Z
    shaft_l = SPEAR_L - SPEAR_HEAD
    cylinder(f"spear_{n}_shaft", SPEAR_R, shaft_l, (x, 0, z0), shaft, r_top=SPEAR_R * 0.85, segments=8,
             rot=(0, lean, 0), bevel=0.002)
    # The socket, a leaf head (a flattened four-sided point) and a butt cap; follow the lean.
    a = math.radians(lean)
    sx, sz = x + math.sin(a) * shaft_l, z0 + math.cos(a) * shaft_l
    cylinder(f"spear_{n}_socket", SPEAR_R * 1.1, 0.07, (x + math.sin(a) * (shaft_l - 0.05), 0,
             z0 + math.cos(a) * (shaft_l - 0.05)), iron, r_top=SPEAR_R * 0.75, segments=8, rot=(0, lean, 0),
             bevel=0.002)
    head = cylinder(f"spear_{n}_head", 0.04, SPEAR_HEAD - 0.02, (sx, 0, sz), steel, r_top=0.002,
                    segments=4, rot=(0, lean, 0), bevel=0.002)
    head.scale = (1.0, 0.25, 1.0)
    cylinder(f"spear_{n}_butt", SPEAR_R * 1.05, 0.04, (x, 0, z0), iron, segments=8, rot=(0, lean, 0), bevel=0.002)


@prop
def weapon_rack():
    rnd = random.Random(17)
    timber = material("weapon_rack_timber", TIMBER, vary=0.28, scale=10)
    old = material("weapon_rack_timber_old", TIMBER_OLD, vary=0.3, scale=9)
    shaft = material("weapon_rack_shaft", SHAFT, vary=0.22, scale=18)
    steel = material("weapon_rack_steel", STEEL, rough=0.35, metal=0.85, vary=0.15, scale=30)
    iron = material("weapon_rack_iron", IRON, rough=0.5, metal=0.8, vary=0.3, scale=20)
    leather = material("weapon_rack_leather", LEATHER, rough=0.7, vary=0.25, scale=30)
    brass = material("weapon_rack_brass", BRASS, rough=0.4, metal=0.7, vary=0.2, scale=25)

    # Frame: a foot under each upright, the uprights, the bottom board and two pairs of slot rails.
    for i, s in enumerate((-1, 1)):
        x = s * POST_X
        box(f"foot_{i}", (FOOT, FOOT_L, FOOT), (x, 0, FOOT / 2), old, rot=(0, 0, rnd.uniform(-1, 1)), bevel=0.012)
        box(f"post_{i}", (POST, POST, POST_H - FOOT + 0.005), (x, 0, FOOT + (POST_H - FOOT) / 2 - 0.0025), timber,
            rot=(0, 0, rnd.uniform(-1.5, 1.5)), bevel=0.01)
        cylinder(f"post_cap_{i}", POST * 0.42, 0.03, (x, 0, POST_H - 0.004), timber, r_top=POST * 0.2,
                 segments=8, bevel=0.004)
        # Angled braces from the foot up to the upright, front and back.
        for j, t in enumerate((-1, 1)):
            box(f"brace_{i}_{j}", (0.045, 0.2, 0.045), (x, t * 0.1, FOOT + 0.06), old, rot=(t * 40, 0, 0),
                bevel=0.006)
    span = 2 * POST_X + POST
    box("board", (span - 0.02, 0.26, BOARD_T), (0, 0, BOARD_Z - BOARD_T / 2), old, bevel=0.008)
    for name, z in (("mid", MID_Z), ("top", TOP_Z)):
        for j, t in enumerate((-1, 1)):
            box(f"rail_{name}_{j}", (span + 0.02, RAIL_T, RAIL_H), (0, t * (GAP + RAIL_T) / 2, z - RAIL_H / 2),
                timber if j else old, rot=(0, 0, rnd.uniform(-0.3, 0.3)), bevel=0.008)
    # Spacer blocks close the slots between the weapons.
    for name, z, xs in (("mid", MID_Z, (-0.37, -0.2, 0.04, 0.32)), ("top", TOP_Z, (-0.37, -0.1, 0.18))):
        for k, x in enumerate(xs):
            box(f"spacer_{name}_{k}", (0.05, GAP + 0.004, RAIL_H - 0.01), (x, 0, z - RAIL_H / 2), old, bevel=0.005)

    # Three spears standing in both rails.
    for n, x in enumerate(SPEARS):
        spear(n, x, rnd, shaft, steel, iron)

    # A sword hanging point down through the middle rail, its crossguard resting on the rails.
    guard_z = MID_Z + 0.012
    tilt = rnd.uniform(-1, 1)
    box("sword_blade", (BLADE_W, BLADE_T, BLADE_L - 0.06), (SWORD_X, 0, guard_z - (BLADE_L - 0.06) / 2), steel,
        rot=(0, tilt, 0), bevel=0.002)
    tip = cylinder("sword_tip", BLADE_W * 0.5, 0.08, (SWORD_X, 0, guard_z - BLADE_L + 0.08), steel, r_top=0.002,
                   segments=4, rot=(180, tilt, 0), bevel=0.001)
    tip.scale = (1.0, 0.16, 1.0)
    box("sword_guard", (0.2, 0.024, 0.022), (SWORD_X, 0, guard_z + 0.011), iron, bevel=0.005)
    cylinder("sword_grip", 0.014, 0.12, (SWORD_X, 0, guard_z + 0.02), leather, segments=8, bevel=0.002)
    for k in range(3):
        torus(f"sword_wrap_{k}", 0.0145, 0.002, (SWORD_X, 0, guard_z + 0.05 + k * 0.03), brass, major=10, minor=4)
    cylinder("sword_pommel", 0.026, 0.035, (SWORD_X, 0, guard_z + 0.14), brass, r_top=0.018, segments=10,
             bevel=0.006)

    # A bearded axe leaning back in the middle rail, its head up and blade to +x.
    lean = -4.0
    a = math.radians(lean)
    cylinder("axe_haft", 0.017, AXE_L, (AXE_X, 0, BOARD_Z), shaft, r_top=0.014, segments=8, rot=(0, lean, 0),
             bevel=0.002)
    hx, hz = AXE_X + math.sin(a) * (AXE_L - 0.1), BOARD_Z + math.cos(a) * (AXE_L - 0.1)
    box("axe_eye", (0.055, 0.035, 0.07), (hx, 0, hz), iron, rot=(0, lean, 0), bevel=0.006)
    box("axe_neck", (0.09, 0.02, 0.05), (hx + 0.06, 0, hz + 0.005), iron, rot=(0, lean, 0), bevel=0.004)
    box("axe_beard", (0.08, 0.014, 0.19), (hx + 0.12, 0, hz - 0.025), steel, rot=(0, lean + 8, 0), bevel=0.004)
    box("axe_butt", (0.03, 0.03, 0.04), (hx - 0.035, 0, hz), iron, rot=(0, lean, 0), bevel=0.004)
    cylinder("axe_knob", 0.019, 0.03, (AXE_X, 0, BOARD_Z), shaft, segments=8, rot=(0, lean, 0), bevel=0.003)
