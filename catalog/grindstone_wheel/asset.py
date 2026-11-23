"""A sharpening grindstone: a thick sandstone wheel on an iron axle in a timber frame of two rails on four splayed legs,
the axle turned by an iron crank with a wooden grip at the front (-y), the bottom of the wheel dipping into a plank
water trough that rests on bearers under it."""
import math
import random

import bpy
from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder

# About 1 x 0.5 x 1 m; the wheel turns in the x-z plane, its face to the front.
RAIL_X = 0.48  # the rails run to +-RAIL_X
RAIL_Y = 0.16  # rail centres
RAIL_TOP = 0.55
LEG_X = 0.36
LEG_FOOT_Y = 0.22  # the legs splay out to this at the ground
WHEEL_R, WHEEL_T = 0.33, 0.1
AXLE_Z = 0.6
AXLE_R = 0.018
CRANK_Y = -0.23  # the crank arm, in front of the frame
TROUGH_X, TROUGH_Y = 0.32, 0.12  # trough half-length and half-width (outside)
TROUGH_Z0, TROUGH_Z1 = 0.16, 0.32
WATER_Z = 0.3
LOW_Z = 0.12  # the lower rails that carry the trough bearers

WOOD = (0.2, 0.12, 0.062)  # linear RGB
WOOD_OLD = (0.16, 0.105, 0.062)
WOOD_WET = (0.11, 0.075, 0.045)
GRIP = (0.25, 0.165, 0.09)
SANDSTONE = (0.36, 0.27, 0.17)
SANDSTONE_WORN = (0.3, 0.23, 0.15)
IRON = (0.045, 0.045, 0.045)
IRON_RUST = (0.09, 0.05, 0.03)
WATER = (0.05, 0.075, 0.07)


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


@prop
def grindstone_wheel():
    rnd = random.Random(17)
    wood = material("grindstone_wheel_wood", WOOD, vary=0.28, scale=14)
    old = material("grindstone_wheel_wood_old", WOOD_OLD, vary=0.3, scale=11)
    wet = material("grindstone_wheel_wood_wet", WOOD_WET, rough=0.6, vary=0.3, scale=12)
    grip = material("grindstone_wheel_grip", GRIP, rough=0.6, vary=0.2, scale=16)
    stone = material("grindstone_wheel_stone", SANDSTONE, rough=0.95, vary=0.25, scale=22, crevice=0.6)
    worn = material("grindstone_wheel_stone_worn", SANDSTONE_WORN, rough=0.7, vary=0.3, scale=30, crevice=0.5)
    iron = material("grindstone_wheel_iron", IRON, rough=0.55, vary=0.2, scale=14, metal=0.6, crevice=0.6)
    rust = material("grindstone_wheel_rust", IRON_RUST, rough=0.8, vary=0.3, scale=16, metal=0.3)
    water = material("grindstone_wheel_water", WATER, rough=0.08, vary=0.15, scale=6, crevice=0.1)

    # The frame: two rails on four legs splayed outward, lower rails and two bearers under the trough.
    tilt = math.degrees(math.atan2(LEG_FOOT_Y - RAIL_Y, RAIL_TOP))
    for sx in (-1, 1):
        for sy in (-1, 1):
            leg = box(f"leg_{sx}_{sy}", (0.065, 0.065, RAIL_TOP / math.cos(math.radians(tilt)) - 0.04),
                      (sx * LEG_X, sy * (LEG_FOOT_Y + RAIL_Y) / 2, RAIL_TOP / 2 - 0.03),
                      old if (sx, sy) == (1, -1) else wood, rot=(sy * tilt, 0, rnd.uniform(-3, 3)), bevel=0.01)
            _settle(leg)
    for sy in (-1, 1):
        box(f"rail_{sy}", (2 * RAIL_X, 0.07, 0.08), (0, sy * RAIL_Y, RAIL_TOP - 0.04), wood,
            rot=(0, rnd.uniform(-0.6, 0.6), 0), bevel=0.012)
        ly = sy * (LEG_FOOT_Y - (LEG_FOOT_Y - RAIL_Y) * (LOW_Z + 0.025) / RAIL_TOP)
        box(f"low_rail_{sy}", (2 * LEG_X + 0.04, 0.05, 0.05), (0, ly, LOW_Z + 0.025), old, bevel=0.008)
    for sx in (-1, 1):
        box(f"bearer_{sx}", (0.06, 2 * LEG_FOOT_Y - 0.04, 0.04), (sx * (TROUGH_X - 0.08), 0, LOW_Z + 0.07), wood,
            bevel=0.008)
        # A pegged cross-tie between the rails at each end.
        box(f"tie_{sx}", (0.06, 2 * RAIL_Y + 0.06, 0.05), (sx * (RAIL_X - 0.06), 0, RAIL_TOP + 0.025), wood,
            bevel=0.01)

    # The trough: a plank box on the bearers, full of murky water.
    tz = LOW_Z + 0.09
    box("trough_floor", (2 * TROUGH_X, 2 * TROUGH_Y, 0.025), (0, 0, tz + 0.0125), wet, bevel=0.006)
    h = TROUGH_Z1 - tz
    for sy in (-1, 1):
        box(f"trough_side_{sy}", (2 * TROUGH_X, 0.022, h), (0, sy * (TROUGH_Y - 0.011), tz + h / 2), wet,
            rot=(0, 0, rnd.uniform(-0.6, 0.6)), bevel=0.006)
    for sx in (-1, 1):
        box(f"trough_end_{sx}", (0.03, 2 * TROUGH_Y + 0.02, h + 0.015), (sx * (TROUGH_X - 0.005), 0, tz + h / 2),
            old, bevel=0.006)
    box("water", (2 * TROUGH_X - 0.05, 2 * TROUGH_Y - 0.04, WATER_Z - tz - 0.025), (0, 0, (WATER_Z + tz + 0.025) / 2),
        water, bevel=0)

    # The wheel: a thick sandstone disc on a square iron hub, its rim worn smoother than its faces.
    cylinder("wheel", WHEEL_R, WHEEL_T, (0, WHEEL_T / 2, AXLE_Z), stone, segments=28, rot=(90, 0, 0), bevel=0.02)
    cylinder("wheel_rim", WHEEL_R + 0.002, WHEEL_T * 0.6, (0, WHEEL_T * 0.3, AXLE_Z), worn, segments=28,
             rot=(90, 0, 0), bevel=0.004)
    for sy in (-1, 1):
        box(f"hub_{sy}", (0.1, 0.014, 0.1), (0, sy * (WHEEL_T / 2 + 0.007), AXLE_Z), iron, rot=(0, 12, 0),
            bevel=0.004)
        box(f"wedge_{sy}", (0.03, 0.03, 0.02), (0.06, sy * (WHEEL_T / 2 + 0.012), AXLE_Z + 0.03), old,
            rot=(0, 40, 0), bevel=0.004)

    # The axle in two bearing blocks on the rails, the crank in front.
    _rod("axle", AXLE_R, (0, RAIL_Y + 0.06, AXLE_Z), (0, CRANK_Y - 0.01, AXLE_Z), iron, segments=10)
    for sy in (-1, 1):
        box(f"bearing_{sy}", (0.1, 0.08, 0.07), (0, sy * RAIL_Y, RAIL_TOP + 0.035), old, bevel=0.01)
        box(f"bearing_cap_{sy}", (0.1, 0.085, 0.03), (0, sy * RAIL_Y, AXLE_Z + AXLE_R + 0.012), iron, bevel=0.005)
    elbow = Vector((0.15, CRANK_Y, AXLE_Z - 0.08))
    _rod("crank_arm", 0.016, (0, CRANK_Y, AXLE_Z), elbow, rust, segments=8)
    _rod("crank_pin", 0.011, elbow, elbow + Vector((0, -0.1, 0)), iron, segments=8)
    _rod("crank_grip", 0.022, elbow + Vector((0, -0.015, 0)), elbow + Vector((0, -0.09, 0)), grip, segments=10,
         bevel=0.006)
