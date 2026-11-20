"""A three-legged inn stool: a thick round seat of two joined boards on three splayed, tapered legs braced by a ring of
stretchers."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder

# Overall size: a seat about 0.36 m across, its top at 0.45 m.
H = 0.445  # seat top height
SEAT_R = 0.18  # seat radius
SEAT_T = 0.045  # seat thickness
LEGS = 3
LEG_TOP_R = 0.105  # leg tops sit this far from the centre, under the seat
LEG_FOOT_R = 0.2  # feet splay out to this radius
LEG_R_TOP, LEG_R_FOOT = 0.026, 0.02  # legs taper towards the foot
STR_Z = 0.17  # stretcher height
STR_R = 0.013
PEG_R = 0.014

WOOD = (0.21, 0.13, 0.068)  # linear RGB
WOOD_OLD = (0.17, 0.11, 0.065)
SEAT = (0.25, 0.165, 0.09)
PEG = (0.1, 0.065, 0.035)


def leg_point(a, z, top, foot, seat_z):
    """A point on the leg at angle `a` (rad) and height z: linear between the foot (z = 0) and the seat."""
    r = foot + (top - foot) * z / seat_z
    return r * math.cos(a), r * math.sin(a)


@prop
def stool_wood():
    rnd = random.Random(21)
    seat = material("stool_seat", SEAT, vary=0.28, scale=12)
    wood = material("stool_legs", WOOD, vary=0.25, scale=14)
    old = material("stool_legs_old", WOOD_OLD, vary=0.3, scale=11)
    peg = material("stool_pegs", PEG, vary=0.2, scale=10)

    seat_z = H - SEAT_T
    # The seat: two half-boards with a fine glue line, a touch out of level.
    for i, s in enumerate((-1, 1)):
        cylinder(f"seat_{i}", SEAT_R, SEAT_T, (0, 0, seat_z), seat if i == 0 else old, segments=24, bevel=0.012)
    box("seat_join", (2 * SEAT_R * 0.97, 0.004, 0.002), (0, 0.01, H + 0.0005), peg, rot=(0, 0, 8), bevel=0)

    dr = LEG_FOOT_R - LEG_TOP_R
    tilt = math.degrees(math.atan2(dr, seat_z))
    length = math.hypot(dr, seat_z) + 0.02  # a tenon into the seat
    angles = [2 * math.pi * i / LEGS + math.radians(90 + rnd.uniform(-4, 4)) for i in range(LEGS)]
    for i, a in enumerate(angles):
        # A tapered leg from its foot out at LEG_FOOT_R, leaning in to the seat; the foot lifted so its lowest edge is
        # on the ground.
        fx, fy = LEG_FOOT_R * math.cos(a), LEG_FOOT_R * math.sin(a)
        lift = LEG_R_FOOT * math.sin(math.radians(tilt))
        cylinder(f"leg_{i}", LEG_R_FOOT, length, (fx, fy, lift), wood if i != 1 else old, r_top=LEG_R_TOP,
                 segments=10, rot=(0, tilt, math.degrees(a) + 180), bevel=0.004)
        # The wedged tenon end showing on the seat top.
        tx, ty = LEG_TOP_R * math.cos(a), LEG_TOP_R * math.sin(a)
        cylinder(f"tenon_{i}", PEG_R * 1.3, 0.004, (tx, ty, H - 0.0035), peg, segments=10, bevel=0)

    # A ring of round stretchers between the legs.
    for i in range(LEGS):
        a0, a1 = angles[i], angles[(i + 1) % LEGS]
        z = STR_Z + rnd.uniform(-0.015, 0.015)
        x0, y0 = leg_point(a0, z, LEG_TOP_R, LEG_FOOT_R, seat_z)
        x1, y1 = leg_point(a1, z, LEG_TOP_R, LEG_FOOT_R, seat_z)
        span = math.hypot(x1 - x0, y1 - y0)
        heading = math.degrees(math.atan2(y1 - y0, x1 - x0))
        cylinder(f"stretcher_{i}", STR_R, span, (x0, y0, z), wood, segments=8, rot=(0, 90, heading), bevel=0.002)
