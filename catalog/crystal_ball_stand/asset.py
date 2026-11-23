"""A seer's crystal ball on a small round table: a turned oak pedestal on three splayed feet, a round top with a dark
velvet cloth, and on it a wrought iron stand, a ring foot on three ball feet with three curved claws gripping a pale
blue glass orb."""
import math
import random

from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, cylinder, torus

# Overall size: about 0.6 m across the table's feet, the top at 0.72 m, the orb's crown at about 1.1 m.
TOP_R, TOP_Z, TOP_T = 0.28, 0.72, 0.04
COLUMN_R = 0.05
FOOT_REACH = 0.26  # how far the feet splay from the centre
CLOTH_R = 0.24
STAND_R = 0.09  # the iron stand's ring foot
ORB_LIFT = 0.08  # the orb's lowest point above the cloth
ORB_R = 0.13
CLAWS = 3

OAK = (0.19, 0.115, 0.06)  # linear RGB
OAK_OLD = (0.145, 0.09, 0.05)
VELVET = (0.12, 0.04, 0.09)  # dark plum
FRINGE = (0.38, 0.27, 0.08)
IRON = (0.045, 0.043, 0.04)
ORB = (0.22, 0.3, 0.42)


def _rod(name, r, a, b, mat, segments=8, bevel=0.003, r_top=None):
    """A round rod from point `a` to point `b`."""
    d = Vector(b) - Vector(a)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return cylinder(name, r, d.length, a, mat, r_top=r_top, segments=segments,
                    rot=tuple(math.degrees(x) for x in rot), bevel=bevel)


@prop
def crystal_ball_stand():
    rnd = random.Random(17)
    oak = material("crystal_ball_stand_oak", OAK, vary=0.25, scale=14)
    old = material("crystal_ball_stand_oak_old", OAK_OLD, vary=0.3, scale=11)
    velvet = material("crystal_ball_stand_velvet", VELVET, rough=0.95, vary=0.2, scale=20, crevice=0.6)
    fringe = material("crystal_ball_stand_fringe", FRINGE, rough=0.7, vary=0.25, scale=40, metal=0.3)
    iron = material("crystal_ball_stand_iron", IRON, rough=0.5, vary=0.12, scale=20, metal=0.6)
    orb = material("crystal_ball_stand_orb", ORB, rough=0.04, vary=0.35, scale=5, crevice=0.15)

    # The table: three splayed feet, a turned pedestal and a round top with a moulded edge.
    for i in range(3):
        a = math.radians(120 * i)
        foot = (FOOT_REACH * math.cos(a), FOOT_REACH * math.sin(a), 0.025)
        _rod(f"foot_{i}", 0.03, (0.6 * COLUMN_R * math.cos(a), 0.6 * COLUMN_R * math.sin(a), 0.14), foot, old,
             segments=8, r_top=0.022, bevel=0.006)
        cylinder(f"foot_pad_{i}", 0.032, 0.025, (foot[0], foot[1], 0), old, r_top=0.028, segments=10, bevel=0.005)
    cylinder("column_base", COLUMN_R * 1.5, 0.08, (0, 0, 0.1), oak, r_top=COLUMN_R, segments=14, bevel=0.008)
    cylinder("column", COLUMN_R, TOP_Z - TOP_T - 0.24, (0, 0, 0.18), oak, r_top=COLUMN_R * 0.85, segments=14,
             bevel=0.006)
    torus("column_ring", COLUMN_R * 0.95, 0.012, (0, 0, 0.36), old, major=14, minor=6)
    cylinder("column_head", COLUMN_R * 0.85, 0.06, (0, 0, TOP_Z - TOP_T - 0.06), oak, r_top=COLUMN_R * 1.6,
             segments=14, bevel=0.006)
    cylinder("top", TOP_R, TOP_T, (0, 0, TOP_Z - TOP_T), oak, r_top=TOP_R - 0.008, segments=32, bevel=0.01)
    torus("top_edge", TOP_R - 0.004, 0.012, (0, 0, TOP_Z - TOP_T * 0.6), old, major=32, minor=6)

    # A round velvet cloth on the top with a little gold fringe, slightly off centre.
    cx, cy = 0.01, -0.01
    cylinder("cloth", CLOTH_R, 0.006, (cx, cy, TOP_Z - 0.001), velvet, segments=24, bevel=0.002)
    torus("cloth_fringe", CLOTH_R, 0.005, (cx, cy, TOP_Z + 0.004), fringe, major=24, minor=4)
    cloth_top = TOP_Z + 0.005

    # The iron stand: a ring foot on three ball feet, a short socket and three claws curling round the orb.
    ring_z = cloth_top + 0.022
    torus("stand_ring", STAND_R, 0.011, (cx, cy, ring_z), iron, major=20, minor=6)
    for i in range(CLAWS):
        a = math.radians(30 + 120 * i)
        blob(f"stand_ball_{i}", 0.016, (cx + STAND_R * math.cos(a), cy + STAND_R * math.sin(a), cloth_top + 0.013),
             iron, subdiv=1, seed=5 + i, jitter=0.02)
        _rod(f"stand_spoke_{i}", 0.007, (cx + STAND_R * math.cos(a), cy + STAND_R * math.sin(a), ring_z),
             (cx, cy, ring_z + 0.045), iron, segments=6, bevel=0)
    cylinder("stand_socket", 0.022, 0.04, (cx, cy, ring_z + 0.03), iron, r_top=0.045, segments=12, bevel=0.004)

    orb_c = Vector((cx, cy, cloth_top + ORB_LIFT + ORB_R))  # the orb sits in the socket's cup
    for i in range(CLAWS):
        a = math.radians(90 + 120 * i + rnd.uniform(-3, 3))
        # The claw: from the socket outwards and up round the orb, the tip bending in over its shoulder.
        pts = []
        for k, (ang, off) in enumerate(((-70, 0.004), (-35, 0.012), (0, 0.016), (30, 0.014), (52, 0.008))):
            e = math.radians(ang)
            d = ORB_R + off
            pts.append(orb_c + Vector((d * math.cos(e) * math.cos(a), d * math.cos(e) * math.sin(a), d * math.sin(e))))
        pts.insert(0, Vector((cx, cy, ring_z + 0.06)) + Vector((0.02 * math.cos(a), 0.02 * math.sin(a), 0)))
        for k in range(len(pts) - 1):
            r0 = 0.014 - 0.0018 * k
            _rod(f"claw_{i}_{k}", r0, pts[k], pts[k + 1], iron, segments=6, r_top=r0 - 0.0015, bevel=0)
            blob(f"claw_{i}_knuckle_{k}", r0 * 1.05, pts[k + 1], iron, subdiv=1, seed=40 + 6 * i + k, jitter=0.02)

    # The orb: pale blue glass, clouded.
    blob("orb", ORB_R, tuple(orb_c), orb, subdiv=3, seed=1, jitter=0)
