"""A ridge tent of worn, patched canvas: two sloping sides from a ridge pole on two uprights down to pegged hems, a
closed back gable, and at the front (+x) the +y door flap hanging shut and the -y one rolled back and tied, so a bedroll
with a rolled pillow and a blanket shows on the ground sheet inside."""
import math
import random

import bpy
from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# About 2.5 x 2 x 1.7 m; the ridge runs along x, the door is on +x.
L = 2.3  # length of the canvas
HW = 0.92  # half width of the canvas at the ground
RH = 1.58  # height of the canvas at the ridge
T = 0.02  # canvas thickness
POLE_R = 0.032
POLE_TOP = 1.69
POLE_X = L / 2 + 0.06
PEG_XS = (-0.98, -0.33, 0.33, 0.98)
BED = (1.75, 0.62, 0.045)  # bedroll mat x, y, z
BED_Y = -0.3

CANVAS = (0.3, 0.26, 0.18)  # linear RGB: weathered undyed canvas
CANVAS_DARK = (0.22, 0.19, 0.13)  # stained, damp at the hem
PATCHES = ((0.2, 0.15, 0.09), (0.26, 0.18, 0.1), (0.17, 0.16, 0.12), (0.34, 0.3, 0.22))
POLE = (0.17, 0.1, 0.052)
POLE_CUT = (0.3, 0.2, 0.11)
ROPE = (0.3, 0.24, 0.14)
SHEET = (0.12, 0.11, 0.08)  # oiled ground sheet
WOOL = (0.15, 0.055, 0.042)  # dull red blanket
CLOAK = (0.09, 0.1, 0.07)

SLOPE = math.degrees(math.atan2(RH, HW))
SLOPE_LEN = math.hypot(HW, RH)


def _frame(side):
    """Unit vectors along the slope (up from the hem) and out of it for the canvas side `side` (-1 is -y)."""
    up = Vector((0, -side * HW, RH)).normalized()
    out = Vector((0, side * RH, HW)).normalized()
    return up, out


def _on_slope(side, x, u, lift):
    """The point at `x` on the canvas side `side`, `u` of the way up from the hem, `lift` out from its inner face."""
    up, out = _frame(side)
    return Vector((x, side * HW, 0)) + up * (u * SLOPE_LEN) + out * lift


def _triangle(name, x, a, b, c, mat, t=T, bevel=0.006):
    """A flat triangular panel `t` thick in the y-z plane at `x`, with corners `a`, `b`, `c` given as (y, z)."""
    obj = cylinder(name, 1.0, t, (0, 0, 0), mat, segments=3, bevel=bevel)
    pts = (a, b, c)
    for v in obj.data.vertices:
        k = round(math.degrees(math.atan2(v.co.y, v.co.x)) % 360 / 120) % 3
        v.co = Vector((x + v.co.z - t / 2, pts[k][0], pts[k][1]))
    return obj


def _rod(name, r, a, b, mat, segments=8, bevel=0.004, r_top=None):
    """A round rod from point `a` to point `b`."""
    d = Vector(b) - Vector(a)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return cylinder(name, r, d.length, a, mat, r_top=r_top, segments=segments,
                    rot=tuple(math.degrees(x) for x in rot), bevel=bevel)


@prop
def tent_canvas():
    rnd = random.Random(112)
    canvas = material("tent_canvas_canvas", CANVAS, rough=0.95, vary=0.3, scale=5, crevice=0.6)
    dark = material("tent_canvas_canvas_dark", CANVAS_DARK, rough=0.95, vary=0.3, scale=7, crevice=0.6)
    patches = [material(f"tent_canvas_patch_{i}", c, rough=0.95, vary=0.3, scale=12, crevice=0.6)
               for i, c in enumerate(PATCHES)]
    pole = material("tent_canvas_pole", POLE, rough=0.85, vary=0.3, scale=16, crevice=0.6)
    pole_cut = material("tent_canvas_pole_cut", POLE_CUT, vary=0.25, scale=24)
    rope = material("tent_canvas_rope", ROPE, rough=0.95, vary=0.25, scale=40)
    sheet = material("tent_canvas_sheet", SHEET, rough=0.7, vary=0.25, scale=8, crevice=0.5)
    wool = material("tent_canvas_wool", WOOL, rough=0.98, vary=0.3, scale=14, crevice=0.65)
    cloak = material("tent_canvas_cloak", CLOAK, rough=0.97, vary=0.3, scale=10, crevice=0.6)

    # The two canvas sides, each in three slightly sagging bays, and a darker damp band along the hem.
    bays = 3
    for side in (-1, 1):
        up, out = _frame(side)
        for k in range(bays):
            x0 = -L / 2 + L * k / bays
            w = L / bays + (0.01 if k < bays - 1 else 0)
            c = _on_slope(side, x0 + w / 2, 0.5, T / 2 + 0.003 * k)
            box(f"side_{side}_{k}", (w, SLOPE_LEN, T), tuple(c), canvas,
                rot=(-side * SLOPE, 0, 0), bevel=0.006)
        c = _on_slope(side, 0, 0.06, T + 0.002)
        box(f"hem_{side}", (L + 0.01, SLOPE_LEN * 0.12, 0.006), tuple(c), dark, rot=(-side * SLOPE, 0, 0),
            bevel=0.002)

    # Patches sewn on where the canvas wore through.
    spots = [(-1, -0.7, 0.55, 0.34, 0.26), (-1, 0.25, 0.3, 0.42, 0.3), (-1, 0.65, 0.72, 0.24, 0.2),
             (-1, -0.2, 0.82, 0.3, 0.18), (1, -0.5, 0.4, 0.36, 0.3), (1, 0.4, 0.66, 0.3, 0.24)]
    for i, (side, x, u, pw, ph) in enumerate(spots):
        c = _on_slope(side, x, u, T + 0.004)
        box(f"patch_{i}", (pw, ph, 0.006), tuple(c), patches[i % len(patches)],
            rot=(-side * SLOPE, 0, rnd.uniform(-6, 6)), bevel=0.002)

    # Ridge: a pole under a canvas fold, resting on two uprights just outside the gables.
    _rod("ridge_pole", POLE_R * 0.9, (-POLE_X - 0.01, 0, RH - 0.01), (POLE_X + 0.01, 0, RH - 0.01), pole, segments=10)
    _rod("ridge_fold", 0.034, (-L / 2 - 0.005, 0, RH), (L / 2 + 0.005, 0, RH), canvas, segments=10, bevel=0.004)
    for s in (-1, 1):
        x = s * POLE_X
        cylinder(f"upright_{s}", POLE_R, POLE_TOP - 0.02, (x, 0, 0), pole, segments=10, bevel=0.006)
        cylinder(f"upright_{s}_top", POLE_R * 0.9, 0.02, (x, 0, POLE_TOP - 0.02), pole_cut, segments=10, bevel=0.004)
        torus(f"lashing_{s}", POLE_R + 0.006, 0.007, (x, 0, RH - 0.03), rope, major=10, minor=5)

    # Back gable: one closed triangle, with a patch.
    xb = -L / 2 + 0.03
    _triangle("gable_back", xb, (-HW + 0.02, 0.002), (0, RH - 0.01), (HW - 0.02, 0.002), canvas)
    _triangle("gable_back_patch", xb - T / 2 - 0.003, (-0.4, 0.25), (-0.1, 0.75), (0.05, 0.3), patches[0], t=0.006,
              bevel=0.002)

    # Front: the +y door flap hangs shut, the -y one is rolled back against the side and tied.
    xf = L / 2 - 0.03
    _triangle("flap_shut", xf, (-0.06, 0.002), (-0.04, RH - 0.02), (HW - 0.02, 0.002), canvas)
    for i in range(4):
        z = 0.25 + 0.3 * i
        y = -0.05 + z * 0.03 / RH
        box(f"toggle_{i}", (0.02, 0.05, 0.018), (xf + T / 2 + 0.008, y, z), pole, rot=(rnd.uniform(-10, 10), 0, 0),
            bevel=0.003)
    a = _on_slope(-1, L / 2 - 0.08, 0.04, 0.055)
    b = _on_slope(-1, L / 2 - 0.08, 0.9, 0.04)
    _rod("flap_roll", 0.055, a, b, dark, segments=10, r_top=0.035, bevel=0.01)
    for i, u in enumerate((0.3, 0.62)):
        c = a + (b - a) * u
        d = (b - a).normalized()
        rot = Vector((0, 0, 1)).rotation_difference(d).to_euler()
        torus(f"flap_tie_{i}", 0.052 - 0.012 * u, 0.008, tuple(c), rope,
              rot=tuple(math.degrees(r) for r in rot), major=12, minor=5)

    # Pegs along both hems, each with a short rope loop to the canvas.
    for side in (-1, 1):
        for i, x in enumerate(PEG_XS):
            px = x + rnd.uniform(-0.04, 0.04)
            peg_base = Vector((px, side * (HW + 0.05), 0))
            peg_top = peg_base + Vector((0, side * 0.02, 0.1))
            _rod(f"peg_{side}_{i}", 0.014, peg_base, peg_top, pole, segments=6, bevel=0.003)
            _rod(f"loop_{side}_{i}", 0.006, _on_slope(side, px, 0.05, T), peg_top - Vector((0, 0, 0.02)), rope,
                 segments=5, bevel=0)

    # Inside: a ground sheet and a bedroll, head to the back, a rolled cloak for a pillow and a blanket.
    box("ground_sheet", (L - 0.1, 2 * HW - 0.25, 0.008), (0, 0, 0.004), sheet, bevel=0.002)
    bx = 0.05
    box("bed_mat", BED, (bx, BED_Y, 0.008 + BED[2] / 2), canvas, rot=(0, 0, 1.5), bevel=0.015)
    box("bed_blanket", (BED[0] * 0.6, BED[1] + 0.06, 0.03), (bx + BED[0] * 0.18, BED_Y, 0.008 + BED[2] + 0.012),
        wool, rot=(0, 0, -2), bevel=0.012)
    box("bed_fold", (0.12, BED[1] + 0.04, 0.035), (bx - BED[0] * 0.12, BED_Y, 0.008 + BED[2] + 0.017), wool,
        rot=(0, 0, -2), bevel=0.014)
    _rod("bed_pillow", 0.07, (bx - BED[0] / 2 + 0.12, BED_Y - 0.27, 0.008 + BED[2] + 0.06),
         (bx - BED[0] / 2 + 0.12, BED_Y + 0.27, 0.008 + BED[2] + 0.06), cloak, segments=12, bevel=0.012)
    pack = blob("pack", 0.16, (-0.75, 0.4, 0.15), dark, squash=(0.9, 0.75, 1.0), subdiv=2, seed=9, jitter=0.1)
    bpy.context.view_layer.update()
    pack.location.z += 0.008 - min((pack.matrix_world @ v.co).z for v in pack.data.vertices)
