"""A four-wheeled covered wagon: a plank box bed on two axles with tall spoked rear wheels and smaller front ones, a
canvas tilt stretched over wooden hoops and closed at the back, open at the front over the driver's bench and
footboard, a load of a barrel, sacks and a crate inside, and a draw pole with a swingletree bar resting on the ground
in front (+x)."""
import math
import random

import bpy
from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# About 4 x 1.8 x 2.6 m; the front (bench and draw pole) is on +x.
BED_X0, BED_X1 = -1.75, 0.95  # the box bed's back and front
BED_HW = 0.6  # half width of the bed
BED_Z = 0.95  # top of the bed floor
SIDE_H = 0.4  # height of the side boards above the floor
REAR_X, REAR_R = -1.15, 0.62  # rear axle and wheel radius
FRONT_X, FRONT_R = 0.55, 0.5
TRACK = 0.79  # wheel planes at +-TRACK
TILT_X0, TILT_X1 = -1.8, 0.82  # canvas ends
TILT_HW = 0.68  # half width of the tilt at its lower edge
TILT_Z = BED_Z + SIDE_H - 0.08  # lower edge of the tilt
TILT_H = 1.2  # rise of the tilt above its lower edge
TILT_SEGS = 14
T = 0.022  # canvas thickness
HOOPS = (-1.72, -1.05, -0.38, 0.29, 0.76)
POLE_TIP = 1.94

WOOD = (0.2, 0.115, 0.058)  # linear RGB
WOOD_OLD = (0.16, 0.11, 0.075)
WOOD_DARK = (0.11, 0.065, 0.035)
IRON = (0.045, 0.045, 0.045)
CANVAS = (0.36, 0.32, 0.23)  # weathered off-white tilt
CANVAS_DARK = (0.25, 0.22, 0.15)
SACK = (0.38, 0.3, 0.18)
BARREL = (0.19, 0.11, 0.055)
CRATE = (0.24, 0.15, 0.08)


def _ellipse(t, hw=TILT_HW, h=TILT_H, z=TILT_Z):
    """The point (y, z) at angle `t` (0 at +y, pi at -y) on the tilt's arch."""
    return Vector((hw * math.cos(t), z + h * math.sin(t)))


def _arch(name, x, width, thick, inset, mat, bevel, hw=TILT_HW, h=TILT_H):
    """Boxes `width` along x and `thick` deep following the arch at `x`, `inset` in from the canvas' inner face."""
    parts = []
    for k in range(TILT_SEGS):
        p0 = _ellipse(math.pi * k / TILT_SEGS, hw, h)
        p1 = _ellipse(math.pi * (k + 1) / TILT_SEGS, hw, h)
        d = p1 - p0
        theta = math.atan2(d.y, d.x)
        out = Vector((math.sin(theta), -math.cos(theta)))  # away from the arch's centre
        mid = (p0 + p1) / 2 + out * (thick / 2 - inset)
        parts.append(box(f"{name}_{k}", (width, d.length + 0.012, thick), (x, mid.x, mid.y), mat,
                         rot=(math.degrees(theta), 0, 0), bevel=bevel))
    return parts


def _rod(name, r, a, b, mat, segments=8, bevel=0.004, r_top=None):
    """A round rod from point `a` to point `b`."""
    d = Vector(b) - Vector(a)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return cylinder(name, r, d.length, a, mat, r_top=r_top, segments=segments,
                    rot=tuple(math.degrees(x) for x in rot), bevel=bevel)


def _wheel(name, x, y, r, wood, iron, rnd):
    """A spoked wheel of radius `r` in the x-z plane at (`x`, `y`), standing on the ground."""
    torus(f"{name}_felloe", r - 0.055, 0.042, (x, y, r), wood, rot=(90, 0, 0), major=20, minor=5)
    torus(f"{name}_tyre", r - 0.012, 0.012, (x, y, r), iron, rot=(90, 0, 0), major=20, minor=4)
    hub = 0.2
    s = 1 if y > 0 else -1
    cylinder(f"{name}_hub", 0.085, hub, (x, y - s * hub / 2, r), wood, rot=(-s * 90, 0, 0), segments=10,
             bevel=0.012)
    cylinder(f"{name}_cap", 0.05, 0.03, (x, y + s * hub / 2, r), iron, rot=(-s * 90, 0, 0), segments=10,
             bevel=0)
    spokes = 12 if r > 0.55 else 10
    length = r - 0.1 - 0.06
    off = rnd.uniform(0, 360)
    for k in range(spokes):
        a = math.radians(off + 360 * k / spokes)
        c = 0.07 + length / 2
        box(f"{name}_spoke_{k}", (0.04, 0.03, length), (x + math.sin(a) * c, y, r + math.cos(a) * c), wood,
            rot=(0, math.degrees(a), 0), bevel=0)


@prop
def wagon_covered():
    rnd = random.Random(410)
    wood = material("wagon_covered_wood", WOOD, vary=0.25, scale=14, crevice=0.6)
    old = material("wagon_covered_boards", WOOD_OLD, vary=0.3, scale=11, crevice=0.6)
    dark = material("wagon_covered_wood_dark", WOOD_DARK, vary=0.3, scale=14, crevice=0.6)
    iron = material("wagon_covered_iron", IRON, rough=0.5, vary=0.2, scale=20, metal=0.7)
    canvas = material("wagon_covered_canvas", CANVAS, rough=0.95, vary=0.3, scale=4, crevice=0.6)
    canvas_dark = material("wagon_covered_canvas_dark", CANVAS_DARK, rough=0.95, vary=0.3, scale=8, crevice=0.6)
    sack = material("wagon_covered_sack", SACK, rough=1.0, vary=0.2, scale=30)
    barrel = material("wagon_covered_barrel", BARREL, vary=0.25, scale=14)
    crate = material("wagon_covered_crate", CRATE, vary=0.3, scale=12)

    # Running gear: wheels, axle trees, bolsters up to the bed and a reach pole between the axles.
    for ax, r, tag in ((REAR_X, REAR_R, "rear"), (FRONT_X, FRONT_R, "front")):
        for s in (-1, 1):
            _wheel(f"wheel_{tag}_{s}", ax, s * TRACK, r, wood, iron, rnd)
        box(f"axle_{tag}", (0.11, 2 * TRACK + 0.04, 0.1), (ax, 0, r), dark, bevel=0)
        under = BED_Z - 0.05
        box(f"bolster_{tag}", (0.14, 2 * BED_HW - 0.1, under - r - 0.05), (ax, 0, (under + r + 0.05) / 2), wood,
            bevel=0)
    box("reach", (FRONT_X - REAR_X + 0.3, 0.09, 0.08), ((FRONT_X + REAR_X) / 2, 0, REAR_R + 0.1), dark, bevel=0)

    # The box bed: floor, three side boards a side, end boards, stakes and iron corner straps.
    length = BED_X1 - BED_X0
    cx = (BED_X0 + BED_X1) / 2
    box("floor", (length, 2 * BED_HW, 0.05), (cx, 0, BED_Z - 0.025), old, bevel=0)
    plank = SIDE_H / 3
    for s in (-1, 1):
        for k in range(3):
            box(f"side_{s}_{k}", (length, 0.035, plank - 0.006), (cx, s * (BED_HW - 0.018),
                BED_Z + plank * (k + 0.5)), old if (k + s) % 2 else wood, rot=(rnd.uniform(-0.8, 0.8), 0, 0),
                bevel=0.006)
        for i, x in enumerate(HOOPS):
            box(f"stake_{s}_{i}", (0.06, 0.04, SIDE_H + 0.04), (min(max(x, BED_X0 + 0.04), BED_X1 - 0.04),
                s * (BED_HW + 0.012), BED_Z + SIDE_H / 2 - 0.02), wood, bevel=0)
        for x in (BED_X0 + 0.03, BED_X1 - 0.03):
            box(f"strap_{s}_{x:.2f}", (0.07, 0.008, SIDE_H - 0.04), (x, s * (BED_HW + 0.034), BED_Z + SIDE_H / 2),
                iron, bevel=0)
    for e, x in (("back", BED_X0 + 0.018), ("front", BED_X1 - 0.018)):
        for k in range(3):
            box(f"end_{e}_{k}", (0.035, 2 * BED_HW, plank - 0.006), (x, 0, BED_Z + plank * (k + 0.5)), old,
                bevel=0)

    # The tilt: canvas over the arch, a darker seam over every hoop, the back closed, the front hoop showing.
    _arch("tilt", (TILT_X0 + TILT_X1) / 2, TILT_X1 - TILT_X0, T, 0, canvas, 0)
    for i, x in enumerate(HOOPS[1:-1]):
        _arch(f"seam_{i}", x, 0.05, 0.008, -T, canvas_dark, 0)
    _arch("hoop_front", HOOPS[-1] + 0.04, 0.05, 0.04, 0.04, wood, 0)
    back = cylinder("tilt_back", 1.0, T, (0, 0, 0), canvas, segments=TILT_SEGS * 2, bevel=0)
    for v in back.data.vertices:
        y, z = v.co.x * TILT_HW, max(v.co.y, 0) * TILT_H
        v.co = Vector((TILT_X0 + T / 2 - v.co.z, y, TILT_Z + z))
    _arch("hem_back", TILT_X0 + 0.02, 0.06, 0.01, -T, canvas_dark, 0)
    _arch("hem_front", TILT_X1 - 0.02, 0.06, 0.01, -T, canvas_dark, 0)
    for s in (-1, 1):  # lashing cords from the tilt's lower edge to the side boards
        for i, x in enumerate(HOOPS[1:-1]):
            _rod(f"cord_{s}_{i}", 0.007, (x + 0.2, s * (TILT_HW + 0.012), TILT_Z + 0.03),
                 (x + 0.24, s * (BED_HW + 0.04), BED_Z + SIDE_H * 0.4), canvas_dark, segments=5, bevel=0)

    # Load, seen through the open front.
    cylinder("barrel", 0.24, 0.62, (0.25, 0.28, BED_Z), barrel, segments=16, bevel=0.015)
    for k, z in enumerate((0.08, 0.54)):
        torus(f"barrel_hoop_{k}", 0.243, 0.01, (0.25, 0.28, BED_Z + z), iron, major=16, minor=4)
    blob("sack_a", 0.24, (0.2, -0.25, BED_Z + 0.2), sack, squash=(0.9, 1.0, 0.85), subdiv=1, seed=1, jitter=0.08)
    blob("sack_b", 0.2, (-0.25, -0.3, BED_Z + 0.4), sack, squash=(1.1, 0.9, 0.8), subdiv=1, seed=2, jitter=0.08)
    box("crate", (0.5, 0.5, 0.42), (-0.35, 0.22, BED_Z + 0.21), crate, rot=(0, 0, 7), bevel=0.014)

    # Driver's bench at the front, on two uprights, with a sloping footboard over the front end.
    seat_z = BED_Z + 0.42
    for s in (-1, 1):
        box(f"bench_leg_{s}", (0.06, 0.06, seat_z - BED_Z - 0.03), (0.78, s * 0.45, (seat_z + BED_Z) / 2 - 0.015),
            wood, bevel=0)
    box("bench_seat", (0.32, 2 * BED_HW - 0.04, 0.05), (0.78, 0, seat_z), old, rot=(0, -3, 0), bevel=0.012)
    box("footboard", (0.34, 2 * BED_HW - 0.1, 0.035), (BED_X1 + 0.12, 0, BED_Z + 0.08), old, rot=(0, -35, 0),
        bevel=0.008)
    for s in (-1, 1):
        _rod(f"foot_brace_{s}", 0.015, (BED_X1, s * 0.45, BED_Z - 0.03), (BED_X1 + 0.24, s * 0.45, BED_Z + 0.15),
             iron, segments=6)

    # The draw pole from the front axle to the ground, a swingletree bar across it and a ring at the tip.
    root = Vector((FRONT_X - 0.05, 0, FRONT_R + 0.02))
    tip = Vector((POLE_TIP - 0.05, 0, 0.065))
    _rod("pole", 0.045, root, tip, wood, segments=10, r_top=0.035, bevel=0.008)
    for s in (-1, 1):
        _rod(f"hound_{s}", 0.025, (FRONT_X, s * 0.4, FRONT_R), root + (tip - root) * 0.28, dark, segments=8)
    bar = root + (tip - root) * 0.7
    box("swingletree", (0.07, 0.95, 0.06), (bar.x, 0, bar.z + 0.075), wood, bevel=0.01)
    for s in (-1, 1):
        torus(f"trace_ring_{s}", 0.025, 0.007, (bar.x, s * 0.47, bar.z + 0.075), iron, rot=(0, 90, 0), major=10,
              minor=4)
    torus("pole_ring", 0.04, 0.01, (POLE_TIP - 0.03, 0, 0.08), iron, rot=(90, 0, 0), major=12, minor=5)

    bpy.context.view_layer.update()
