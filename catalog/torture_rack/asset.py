"""A torture rack: a long timber frame on four braced legs with a plank bed, a roller across each end turning in the
side beams, ropes wound on the rollers running along the bed to wrist and ankle loops, capstan bars through the head
roller and a toothed iron ratchet wheel with its pawl on the foot roller."""
import math
import random

from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall dimensions (metres): about 2.4 m long (x), 1 m wide, 1 m high.
L = 2.4  # side beams, end to end
BEAM_Y = 0.38  # side beam centres, either side
BEAM = (0.12, 0.16)  # side beam width (y) and height
TOP = 0.8  # top of the side beams
LEG = 0.12
LEG_X = 1.1  # leg centres
ROLL_X = 0.98  # roller axes, either end
ROLL_Z = TOP - 0.02  # rollers turn in the beams' top edge, standing proud of them
ROLL_R = 0.07
ROLL_L = 1.0  # roller length, past both beams
BED = (1.6, 2 * BEAM_Y - BEAM[0], 0.04)  # the plank bed between the beams
WHEEL_R = 0.17  # ratchet wheel, outside the -y beam at the foot (+x)
ROPE_R = 0.013
ROPE_Y = 0.13  # the two ropes either side of the middle

OAK = (0.2, 0.12, 0.062)  # linear RGB
OAK_OLD = (0.155, 0.095, 0.052)
OAK_DARK = (0.11, 0.072, 0.045)
ROPE = (0.34, 0.27, 0.16)
IRON = (0.045, 0.044, 0.042)
IRON_WORN = (0.1, 0.092, 0.082)
RUST = (0.1, 0.055, 0.033)


def _rot_to(d):
    """Rotation (degrees, XYZ) that turns local +z onto direction `d`."""
    q = Vector((0, 0, 1)).rotation_difference(Vector(d).normalized())
    return tuple(math.degrees(a) for a in q.to_euler("XYZ"))


def _rope(name, a, b, mat, r=ROPE_R):
    d = Vector(b) - Vector(a)
    return cylinder(name, r, d.length, a, mat, segments=8, rot=_rot_to(d), bevel=0)


@prop
def torture_rack():
    rnd = random.Random(5)
    oak = material("torture_rack_oak", OAK, vary=0.25, scale=14)
    old = material("torture_rack_oak_old", OAK_OLD, vary=0.3, scale=12)
    dark = material("torture_rack_oak_dark", OAK_DARK, vary=0.3, scale=12)
    rope = material("torture_rack_rope", ROPE, vary=0.3, scale=40)
    iron = material("torture_rack_iron", IRON, rough=0.55, vary=0.25, scale=18, metal=0.6)
    worn = material("torture_rack_iron_worn", IRON_WORN, rough=0.5, vary=0.25, scale=22, metal=0.7)
    rust = material("torture_rack_rust", RUST, rough=0.85, vary=0.3, scale=24, metal=0.25)

    bw, bh = BEAM
    # Legs, low stretchers along and across, the side beams and an end rail at each end.
    for i, sx in enumerate((-1, 1)):
        for j, sy in enumerate((-1, 1)):
            box(f"leg_{i}_{j}", (LEG, LEG, TOP - 0.02), (sx * LEG_X, sy * BEAM_Y, (TOP - 0.02) / 2), oak,
                rot=(rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), 0), bevel=0.014)
        box(f"stretch_x_{i}", (0.08, 2 * BEAM_Y, 0.09), (sx * LEG_X, 0, 0.2), old, bevel=0.01)
        box(f"end_rail_{i}", (0.1, 2 * BEAM_Y + bw, 0.1), (sx * (L / 2 - 0.05), 0, TOP - 0.05 - bh - 0.02), dark,
            bevel=0.012)
    for j, sy in enumerate((-1, 1)):
        box(f"stretch_y_{j}", (2 * LEG_X, 0.08, 0.09), (0, sy * BEAM_Y, 0.2), old,
            rot=(0, 0, rnd.uniform(-0.3, 0.3)), bevel=0.01)
        box(f"beam_{j}", (L, bw, bh), (0, sy * BEAM_Y, TOP - bh / 2), oak, rot=(rnd.uniform(-0.4, 0.4), 0, 0),
            bevel=0.016)
        # Iron bearing plates where the rollers pass through the beams.
        for i, sx in enumerate((-1, 1)):
            box(f"bearing_{i}_{j}", (0.2, 0.012, 0.13), (sx * ROLL_X, sy * (BEAM_Y + bw / 2 + 0.006), ROLL_Z),
                iron, bevel=0.003)
            for k, dx in enumerate((-0.07, 0.07)):
                cylinder(f"bearing_nail_{i}_{j}_{k}", 0.01, 0.008, (sx * ROLL_X + dx, sy * (BEAM_Y + bw / 2 + 0.01),
                         ROLL_Z + 0.04), worn, segments=6, rot=(-sy * 90, 0, 0), bevel=0)

    # The plank bed between the beams, on two cross bearers.
    for k, x in enumerate((-0.5, 0.5)):
        box(f"bearer_{k}", (0.08, BED[1] + 0.02, 0.06), (x, 0, TOP - 0.08), dark, bevel=0.008)
    n = 4
    for k in range(n):
        y = -BED[1] / 2 + BED[1] * (k + 0.5) / n
        box(f"bed_plank_{k}", (BED[0] * rnd.uniform(0.97, 1.0), BED[1] / n - 0.01, BED[2]),
            (rnd.uniform(-0.02, 0.02), y, TOP - 0.05 + BED[2] / 2), old if k % 2 else oak,
            rot=(0, 0, rnd.uniform(-0.3, 0.3)), bevel=0.008)
    bed_top = TOP - 0.05 + BED[2]  # the ropes lie on it

    # Rollers across both ends, with rope wound on them and square ends through the beams.
    for i, sx in enumerate((-1, 1)):
        x = sx * ROLL_X
        cylinder(f"roller_{i}", ROLL_R, ROLL_L, (x, -ROLL_L / 2, ROLL_Z), dark, segments=12, rot=(-90, 0, 0),
                 bevel=0.006)
        for j, sy in enumerate((-1, 1)):
            for k in range(3):
                torus(f"coil_{i}_{j}_{k}", ROLL_R + ROPE_R * 0.8, ROPE_R, (x, sy * ROPE_Y + (k - 1) * 0.024, ROLL_Z),
                      rope, rot=(90, 0, k * 20), major=14, minor=6)

    # Capstan bars through the head roller (-x), outside the -y beam.
    fy = -ROLL_L / 2 + 0.04
    torus("capstan_hub", ROLL_R + 0.01, 0.018, (-ROLL_X, fy, ROLL_Z), iron, rot=(90, 0, 0), major=14, minor=6)
    for k, a in enumerate((20, 110)):
        r = math.radians(a)
        d = Vector((math.cos(r), 0, math.sin(r)))
        c = Vector((-ROLL_X, fy, ROLL_Z))
        h = 0.2
        cylinder(f"capstan_bar_{k}", 0.02, 2 * h, tuple(c - d * h), old, segments=8, rot=_rot_to(d), bevel=0)

    # Ratchet wheel on the foot roller (+x), outside the -y beam: a disc, a ring of sloped teeth and a pawl.
    wy = -(BEAM_Y + bw / 2 + 0.045)
    wx = ROLL_X
    cylinder("wheel", WHEEL_R - 0.02, 0.04, (wx, wy - 0.02, ROLL_Z), iron, segments=20, rot=(-90, 0, 0),
             bevel=0.004)
    cylinder("wheel_hub", 0.05, 0.07, (wx, wy - 0.04, ROLL_Z), worn, segments=10, rot=(-90, 0, 0), bevel=0.004)
    teeth = 14
    for k in range(teeth):
        a = 2 * math.pi * k / teeth
        box(f"tooth_{k}", (0.055, 0.038, 0.035),
            (wx + (WHEEL_R - 0.01) * math.cos(a), wy, ROLL_Z + (WHEEL_R - 0.01) * math.sin(a)),
            iron if k % 4 else rust, rot=(0, -math.degrees(a) + 30, 0), bevel=0)
    # The pawl hangs from a pin in the side beam and drops onto the teeth.
    px, pz = wx - 0.27, TOP - 0.05
    cylinder("pawl_pin", 0.016, 0.06, (px, wy - 0.01, pz), worn, segments=8, rot=(-90, 0, 0), bevel=0)
    tip = Vector((wx + WHEEL_R * math.cos(math.radians(150)), wy, ROLL_Z + WHEEL_R * math.sin(math.radians(150))))
    d = tip - Vector((px, wy, pz))
    box("pawl", (0.03, 0.025, d.length), tuple(Vector((px, wy, pz)) + d / 2), iron, rot=_rot_to(d), bevel=0.004)

    # Ropes from the rollers along the bed: two to wrist loops near the head, two to ankle loops near the foot.
    for i, (sx, end) in enumerate(((-1, -0.62), (1, 0.38))):
        for j, sy in enumerate((-1, 1)):
            y = sy * ROPE_Y
            a = (sx * ROLL_X - sx * 0.01, y, ROLL_Z + ROLL_R + ROPE_R)
            b = (end, y + sy * 0.02 * rnd.uniform(0.5, 1.5), bed_top + ROPE_R)
            _rope(f"rope_{i}_{j}", a, b, rope)
            torus(f"loop_{i}_{j}", 0.05, ROPE_R, (end - sx * 0.05, b[1], bed_top + ROPE_R), rope,
                  rot=(0, 0, rnd.uniform(0, 60)), major=12, minor=6)
