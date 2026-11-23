"""A floor candelabra of wrought iron: three splayed legs with curled toes, a slightly twisted square stem with a knop,
and at the top four arms in a cross, each bending up to a drip pan with an ivory candle, round a taller centre candle,
with small scrolls under the arms."""
import math
import random

from mathutils import Vector

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall size: about 0.45 m across the arms and the feet, the centre flame at about 1.7 m.
HUB_Z = 0.24  # where the legs meet the stem
LEG_REACH = 0.22  # leg tip distance from the axis
LEG_T = 0.022
STEM_T = 0.026
STEM_SEGMENTS = 12
STEM_TWIST = 11  # degrees per segment
ARM_Z = 1.3  # height of the arms' horizontal run
ARM_REACH = 0.21  # distance of the outer candles from the axis
ARM_RISE = 0.09  # the arms bend up this far to their pans
CENTRE_PAN_Z = 1.46
PAN_R, PAN_H = 0.045, 0.018
CANDLE_R = 0.022
CANDLE_H = 0.15
CENTRE_CANDLE_H = 0.17
WICK_H = 0.015

IRON = (0.045, 0.045, 0.045)  # linear RGB
IRON_WORN = (0.1, 0.092, 0.085)
WAX = (0.5, 0.44, 0.32)
WICK = (0.06, 0.05, 0.04)
FLAME = (0.5, 0.3, 0.06)


def _rod(name, r, a, b, mat, segments=8, bevel=0.003):
    """A round rod from point `a` to point `b`."""
    d = Vector(b) - Vector(a)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return cylinder(name, r, d.length, a, mat, segments=segments, rot=tuple(math.degrees(x) for x in rot),
                    bevel=bevel)


@prop
def candelabra_standing():
    rnd = random.Random(17)
    iron = material("candelabra_standing_iron", IRON, rough=0.55, vary=0.25, scale=22, metal=0.6)
    worn = material("candelabra_standing_iron_worn", IRON_WORN, rough=0.4, vary=0.3, scale=30, metal=0.7)
    wax = material("candelabra_standing_wax", WAX, rough=0.5, vary=0.08, scale=10, crevice=0.12)
    wick = material("candelabra_standing_wick", WICK, rough=0.9, vary=0.1, scale=20)
    flame = material("candelabra_standing_flame", FLAME, rough=0.5, vary=0.3, scale=10, crevice=0.1)

    # Three splayed legs with a pad on the ground and a curled toe.
    for i in range(3):
        az = 30 + i * 120 + rnd.uniform(-3, 3)
        a = math.radians(az)
        c, s = math.cos(a), math.sin(a)
        _rod(f"leg_{i}", LEG_T / 2 + 0.002, (0.02 * c, 0.02 * s, HUB_Z - 0.02), (LEG_REACH * c, LEG_REACH * s, 0.03),
             iron)
        cylinder(f"pad_{i}", 0.03, 0.016, (LEG_REACH * c, LEG_REACH * s, 0), worn, segments=10, bevel=0.003)
        cr = LEG_REACH - 0.035
        torus(f"toe_{i}", 0.028, 0.008, (cr * c, cr * s, 0.075), iron, rot=(90, 0, az), major=12, minor=5)

    cylinder("hub", 0.04, 0.05, (0, 0, HUB_Z - 0.04), worn, r_top=0.026, segments=12, bevel=0.005)

    # The twisted square stem with a knop halfway up.
    stem_bottom, stem_top = HUB_Z, ARM_Z - 0.03
    seg = (stem_top - stem_bottom) / STEM_SEGMENTS
    for i in range(STEM_SEGMENTS):
        box(f"stem_{i}", (STEM_T, STEM_T, seg + 0.004), (0, 0, stem_bottom + (i + 0.5) * seg), iron,
            rot=(0, 0, 20 + i * STEM_TWIST), bevel=0.004)
    knop_z = (stem_bottom + stem_top) / 2
    blob("knop", 0.034, (0, 0, knop_z), worn, squash=(1, 1, 0.75), subdiv=1, seed=11, jitter=0.05)
    blob("knop_upper", 0.03, (0, 0, stem_top - 0.02), worn, squash=(1, 1, 0.8), subdiv=1, seed=12, jitter=0.05)

    # The arm boss and four arms: out, then up to a pan; a scroll braces each arm under it.
    cylinder("boss", 0.038, 0.05, (0, 0, ARM_Z - 0.025), worn, segments=12, bevel=0.005)
    candles = []
    for k in range(4):
        a = math.radians(45 + 90 * k)
        c, s = math.cos(a), math.sin(a)
        elbow = (ARM_REACH * c, ARM_REACH * s, ARM_Z)
        _rod(f"arm_{k}", 0.009, (0.03 * c, 0.03 * s, ARM_Z), elbow, iron)
        blob(f"elbow_{k}", 0.012, elbow, iron, subdiv=1, seed=30 + k, jitter=0.02)
        _rod(f"riser_{k}", 0.009, elbow, (elbow[0], elbow[1], ARM_Z + ARM_RISE), iron)
        torus(f"brace_{k}", 0.045, 0.006, (0.09 * c, 0.09 * s, ARM_Z - 0.045), worn, rot=(90, 0, 45 + 90 * k),
              major=12, minor=4)
        candles.append((elbow[0], elbow[1], ARM_Z + ARM_RISE, CANDLE_H * rnd.uniform(0.75, 1.0)))
    _rod("centre_riser", 0.012, (0, 0, ARM_Z), (0, 0, CENTRE_PAN_Z), iron)
    candles.append((0, 0, CENTRE_PAN_Z, CENTRE_CANDLE_H))

    # Pans, candles, drips, wicks and small flames.
    for k, (x, y, z, h) in enumerate(candles):
        cylinder(f"pan_{k}", PAN_R - 0.012, PAN_H, (x, y, z), iron, r_top=PAN_R, segments=12, bevel=0)
        base = z + PAN_H - 0.004
        cylinder(f"candle_{k}", CANDLE_R, h, (x, y, base), wax, segments=8, bevel=0)
        top = base + h
        a = rnd.uniform(0, 2 * math.pi)
        blob(f"drip_{k}", 0.009, (x + CANDLE_R * math.cos(a), y + CANDLE_R * math.sin(a), top - 0.03), wax,
             squash=(0.8, 0.8, 1.8), subdiv=1, seed=50 + k, jitter=0.1)
        cylinder(f"wick_{k}", 0.003, WICK_H, (x, y, top - 0.003), wick, segments=6, bevel=0)
        blob(f"flame_{k}", 0.011, (x, y, top + WICK_H + 0.008), flame, squash=(1, 1, 2.2), subdiv=1, seed=60 + k,
             jitter=0.05)

    x, y, z, h = candles[-1]
    anchor("light:candle", (0, 0, z + PAN_H + h + WICK_H))
