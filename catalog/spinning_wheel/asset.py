"""A Saxony spinning wheel: a plank bench at stool height on three splayed legs, a spoked wheel between two uprights,
turned by a treadle and a footman rod on its crank; a drive band runs from the wheel to the flyer and bobbin held
between two maidens at the bench's +x end, beside them a distaff dressed with a cone of raw wool."""
import math
import random

import bpy
from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# About 1 x 0.5 x 1.1 m; the wheel turns in the x-z plane, the spinner sits at the front (-y).
BENCH_X0, BENCH_X1 = -0.44, 0.36
BENCH_W, BENCH_T = 0.2, 0.055
BENCH_TOP = 0.47
WHEEL_X, WHEEL_Z = -0.12, 0.79
WHEEL_R = 0.28  # to the rim's centre line
RIM_R = 0.022
SPOKES = 8
UP_Y = 0.05  # the wheel's uprights at +-UP_Y
FLYER_X, FLYER_Z = 0.25, 0.67
WHORL_R = 0.036
MAIDEN_Y0, MAIDEN_Y1 = -0.11, 0.045
DISTAFF_FOOT = (0.33, 0.055)
DISTAFF_TOP = Vector((0.4, 0.14, 0.93))

WOOD = (0.23, 0.14, 0.07)  # linear RGB: an oiled, turned wood
WOOD_DARK = (0.17, 0.1, 0.055)
BENCH = (0.25, 0.16, 0.085)
WOOL = (0.45, 0.375, 0.26)
YARN = (0.4, 0.35, 0.26)
BAND = (0.3, 0.25, 0.17)
IRON = (0.045, 0.045, 0.045)
RIBBON = (0.28, 0.08, 0.05)


def _settle(obj, z_min=0.0):
    """Move `obj` up or down so its lowest point is at `z_min`."""
    bpy.context.view_layer.update()
    lowest = min((obj.matrix_world @ v.co).z for v in obj.data.vertices)
    obj.location.z += z_min - lowest
    return obj


def _rod(name, r, a, b, mat, segments=8, bevel=0.004, r_top=None):
    """A round rod from point `a` to point `b`."""
    d = Vector(b) - Vector(a)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return cylinder(name, r, d.length, a, mat, r_top=r_top, segments=segments,
                    rot=tuple(math.degrees(x) for x in rot), bevel=bevel)


def _tangents(c1, r1, c2, r2):
    """The two outer tangent segments of two circles in the x-z plane, as point pairs."""
    dx, dz = c2[0] - c1[0], c2[1] - c1[1]
    theta, phi = math.atan2(dz, dx), math.acos((r1 - r2) / math.hypot(dx, dz))
    out = []
    for s in (-1, 1):
        a = theta + s * phi
        out.append(((c1[0] + r1 * math.cos(a), c1[1] + r1 * math.sin(a)),
                    (c2[0] + r2 * math.cos(a), c2[1] + r2 * math.sin(a))))
    return out


@prop
def spinning_wheel():
    rnd = random.Random(29)
    wood = material("spinning_wheel_wood", WOOD, rough=0.55, vary=0.25, scale=16)
    dark = material("spinning_wheel_wood_dark", WOOD_DARK, rough=0.6, vary=0.25, scale=14)
    bench = material("spinning_wheel_bench", BENCH, vary=0.28, scale=12)
    wool = material("spinning_wheel_wool", WOOL, rough=1.0, vary=0.25, scale=30, crevice=0.6)
    yarn = material("spinning_wheel_yarn", YARN, rough=0.95, vary=0.2, scale=50, crevice=0.5)
    band = material("spinning_wheel_band", BAND, rough=0.95, vary=0.1, scale=30, crevice=0.2)
    iron = material("spinning_wheel_iron", IRON, rough=0.5, vary=0.2, scale=14, metal=0.6)
    ribbon = material("spinning_wheel_ribbon", RIBBON, rough=0.8, vary=0.2, scale=20)

    # The bench on three splayed legs: two at the wheel end, one under the flyer end.
    bz = BENCH_TOP - BENCH_T
    box("bench", (BENCH_X1 - BENCH_X0, BENCH_W, BENCH_T), ((BENCH_X0 + BENCH_X1) / 2, 0, bz + BENCH_T / 2), bench,
        rot=(0, 0, 0.8), bevel=0.012)
    for i, (foot, top) in enumerate([((-0.47, -0.2), (-0.36, -0.06)), ((-0.47, 0.2), (-0.36, 0.06)),
                                     ((0.47, 0.0), (0.3, 0.0))]):
        leg = _rod(f"leg_{i}", 0.02, (foot[0], foot[1], 0), (top[0], top[1], bz + 0.03), wood, segments=10,
                   r_top=0.026)
        _settle(leg)

    # The treadle on a hinge bar between the front legs, and the footman rod up to the crank.
    box("treadle_bar", (0.035, 0.36, 0.035), (-0.44, 0, 0.06), dark, bevel=0.006)
    box("treadle", (0.36, 0.13, 0.025), (-0.27, 0, 0.075), bench, rot=(0, -6, 0), bevel=0.008)
    crank_y = UP_Y + 0.04
    crank_pin = Vector((WHEEL_X + 0.06, crank_y, WHEEL_Z - 0.04))
    _rod("footman", 0.011, (-0.1, crank_y, 0.09), crank_pin, wood, segments=8)
    box("footman_link", (0.03, 0.03, 0.04), (-0.1, crank_y - 0.01, 0.09), iron, bevel=0.004)

    # The wheel's uprights, axle and crank.
    for s in (-1, 1):
        _rod(f"upright_{s}", 0.024, (WHEEL_X, s * UP_Y, bz + 0.02), (WHEEL_X, s * UP_Y, WHEEL_Z + 0.08), wood,
             segments=10, r_top=0.019)
        blob(f"upright_knob_{s}", 0.024, (WHEEL_X, s * UP_Y, WHEEL_Z + 0.09), dark, subdiv=1, seed=3 + s,
             jitter=0.02)
    _rod("axle", 0.009, (WHEEL_X, -UP_Y - 0.03, WHEEL_Z), (WHEEL_X, crank_y + 0.01, WHEEL_Z), iron, segments=8,
         bevel=0)
    _rod("crank", 0.008, (WHEEL_X, crank_y, WHEEL_Z), crank_pin, iron, segments=6, bevel=0)

    # The wheel: a torus rim, a turned hub and spokes.
    torus("rim", WHEEL_R, RIM_R, (WHEEL_X, 0, WHEEL_Z), dark, rot=(90, 0, 0), major=40, minor=6)
    _rod("hub", 0.04, (WHEEL_X, -0.035, WHEEL_Z), (WHEEL_X, 0.035, WHEEL_Z), wood, segments=12, r_top=0.032)
    off = rnd.uniform(0, 360 / SPOKES)
    for i in range(SPOKES):
        a = math.radians(off + 360 * i / SPOKES)
        u = Vector((math.cos(a), 0, math.sin(a)))
        c = Vector((WHEEL_X, 0, WHEEL_Z))
        _rod(f"spoke_{i}", 0.011, c + u * 0.035, c + u * (WHEEL_R - RIM_R * 0.6), wood, segments=6, r_top=0.008,
             bevel=0)

    # The mother-of-all: a post on the bench, a cross bar and two maidens holding the flyer, bobbin and whorl.
    _rod("mother_post", 0.028, (FLYER_X, 0, bz + 0.02), (FLYER_X, 0, FLYER_Z - 0.12), dark, segments=10)
    box("mother_bar", (0.06, MAIDEN_Y1 - MAIDEN_Y0 + 0.08, 0.05), (FLYER_X, (MAIDEN_Y0 + MAIDEN_Y1) / 2,
                                                                     FLYER_Z - 0.12), wood, bevel=0.01)
    for name, y in (("front", MAIDEN_Y0), ("back", MAIDEN_Y1)):
        _rod(f"maiden_{name}", 0.017, (FLYER_X, y, FLYER_Z - 0.1), (FLYER_X, y, FLYER_Z + 0.07), wood,
             segments=8, r_top=0.013)
        blob(f"maiden_knob_{name}", 0.018, (FLYER_X, y, FLYER_Z + 0.08), dark, subdiv=1, seed=11, jitter=0.02)
    _rod("flyer_shaft", 0.007, (FLYER_X, MAIDEN_Y0 - 0.04, FLYER_Z), (FLYER_X, MAIDEN_Y1 + 0.01, FLYER_Z), iron,
         segments=6, bevel=0)
    _rod("orifice", 0.012, (FLYER_X, MAIDEN_Y0 - 0.045, FLYER_Z), (FLYER_X, MAIDEN_Y0 - 0.01, FLYER_Z), iron,
         segments=8, bevel=0)
    _rod("whorl", WHORL_R, (FLYER_X, -0.008, FLYER_Z), (FLYER_X, 0.012, FLYER_Z), dark, segments=12, bevel=0.003)
    _rod("bobbin_yarn", 0.032, (FLYER_X, -0.075, FLYER_Z), (FLYER_X, -0.022, FLYER_Z), yarn, segments=12,
         bevel=0.006)
    for y in (-0.08, -0.022):
        _rod(f"bobbin_flange_{y:.2f}", 0.04, (FLYER_X, y, FLYER_Z), (FLYER_X, y + 0.008, FLYER_Z), wood, segments=12,
             bevel=0.002)
    box("flyer_yoke", (0.02, 0.012, 0.13), (FLYER_X, MAIDEN_Y0 + 0.02, FLYER_Z), wood, bevel=0.003)
    for s in (-1, 1):
        box(f"flyer_arm_{s}", (0.014, 0.075, 0.012), (FLYER_X, MAIDEN_Y0 + 0.055, FLYER_Z + s * 0.058), wood,
            bevel=0.003)

    # The drive band from the wheel's rim to the whorl.
    for i, (p, q) in enumerate(_tangents((WHEEL_X, WHEEL_Z), WHEEL_R, (FLYER_X, FLYER_Z), WHORL_R)):
        _rod(f"band_{i}", 0.003, (p[0], 0.002, p[1]), (q[0], 0.002, q[1]), band, segments=4, bevel=0)

    # The distaff: a staff from the bench, dressed with a cone of wool tied with a ribbon.
    foot = Vector((DISTAFF_FOOT[0], DISTAFF_FOOT[1], bz + 0.02))
    _rod("distaff", 0.013, foot, DISTAFF_TOP, dark, segments=8, r_top=0.009)
    wool_c = foot.lerp(DISTAFF_TOP, 0.8)
    cone = blob("distaff_wool", 0.075, tuple(wool_c), wool, squash=(1, 1, 1.7), subdiv=2, seed=6, jitter=0.2)
    cone.rotation_euler = (math.radians(10), math.radians(4), 0)
    torus("distaff_ribbon", 0.066, 0.009, tuple(wool_c + Vector((0, 0, -0.03))), ribbon, rot=(10, 4, 0),
          major=16, minor=5)
    blob("distaff_tuft", 0.05, tuple(wool_c + Vector((0.02, 0.0, -0.11))), wool, squash=(0.8, 0.8, 1.2), subdiv=1,
         seed=8, jitter=0.2)
