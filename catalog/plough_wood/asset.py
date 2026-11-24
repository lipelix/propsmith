"""A wooden plough, its hitch towards +x and the ploughman's end towards -x, mouldboard on the -y side: a long draw beam
from two splayed handles forward to an iron hitch ring, carried at the front on a small iron-tyred foot wheel in a fork;
below it a sole on the ground held by a standard, a pointed iron share at its nose, an iron coulter knife through the
beam ahead of the share, and a twisted plank mouldboard behind the share to turn the furrow."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall size: about 2.2 m long (x), 0.6 m across the handles (y), 1 m high at the grips.
SOLE_X0, SOLE_X1, SOLE_H = -0.5, 0.2, 0.08  # the sole on the ground
SHARE_L = 0.28
BEAM_A, BEAM_B = (-0.7, 0.0, 0.44), (1.0, 0.0, 0.56)  # the draw beam's rear and front ends
BEAM_W, BEAM_H = 0.08, 0.1
WHEEL_X, WHEEL_R, WHEEL_T = 0.84, 0.16, 0.05
HANDLE_FOOT = (-0.46, 0.07, 0.06)  # where a handle leaves the sole (y mirrored)
HANDLE_TOP = (-1.02, 0.25, 0.94)  # its grip end
COULTER_X = 0.34

WOOD = (0.2, 0.125, 0.065)  # linear RGB
WOOD_OLD = (0.16, 0.11, 0.07)
WOOD_WORN = (0.26, 0.19, 0.12)  # hand-polished grips
IRON = (0.06, 0.055, 0.05)
IRON_BRIGHT = (0.2, 0.19, 0.18)  # the share's worn edge
RUST = (0.17, 0.075, 0.035)
EARTH = (0.1, 0.07, 0.042)


def _norm(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def _rot(d):
    """Euler XYZ (degrees) turning local +z onto unit direction d."""
    a = math.degrees(math.acos(max(-1.0, min(1.0, d[2]))))
    c = math.degrees(math.atan2(d[0], -d[1]))
    return (a, 0, c)


def _beam(name, p, q, w, h, mat, bevel=0.01, extend=0.0):
    """A squared timber from p to q (lengthened by `extend` at each end), `w` across and `h` deep."""
    d = tuple(b - a for a, b in zip(p, q))
    length = math.sqrt(sum(c * c for c in d)) + 2 * extend
    mid = tuple((a + b) / 2 for a, b in zip(p, q))
    return box(name, (w, h, length), mid, mat, rot=_rot(_norm(d)), bevel=bevel)


def _rod(name, p, q, r, mat, segments=8, bevel=0.004, r_top=None):
    d = tuple(b - a for a, b in zip(p, q))
    length = math.sqrt(sum(c * c for c in d))
    return cylinder(name, r, length, p, mat, r_top=r_top, segments=segments, rot=_rot(_norm(d)), bevel=bevel)


def _lerp(p, q, t):
    return tuple(a + (b - a) * t for a, b in zip(p, q))


@prop
def plough_wood():
    rnd = random.Random(22)
    wood = material("plough_wood_wood", WOOD, vary=0.28, scale=10)
    old = material("plough_wood_wood_old", WOOD_OLD, vary=0.3, scale=9)
    worn = material("plough_wood_grip", WOOD_WORN, rough=0.55, vary=0.25, scale=14)
    iron = material("plough_wood_iron", IRON, rough=0.55, metal=0.8, vary=0.35, scale=25, crevice=0.8)
    bright = material("plough_wood_share_edge", IRON_BRIGHT, rough=0.35, metal=0.9, vary=0.2, scale=30)
    rust = material("plough_wood_rust", RUST, rough=0.9, metal=0.2, vary=0.4, scale=30)
    earth = material("plough_wood_earth", EARTH, rough=1.0, vary=0.35, scale=12)

    # The sole on the ground and the iron share at its nose, earth still clinging to it.
    box("sole", (SOLE_X1 - SOLE_X0, 0.09, SOLE_H), ((SOLE_X0 + SOLE_X1) / 2, 0, SOLE_H / 2), old, bevel=0.012)
    share = cylinder("share", 0.1, SHARE_L, (SOLE_X1 - 0.04, 0, 0.042), iron, r_top=0.004, segments=4,
                     rot=(0, 90, 0), bevel=0.003)
    share.scale = (0.4, 1.0, 1.0)
    box("share_socket", (0.12, 0.1, 0.06), (SOLE_X1 - 0.02, 0, 0.034), rust, bevel=0.006)
    _rod("share_edge", (SOLE_X1 + 0.02, -0.045, 0.012), (SOLE_X1 + SHARE_L - 0.03, -0.004, 0.012), 0.006, bright,
         segments=6, bevel=0)
    blob("earth_clod", 0.035, (SOLE_X1 + 0.05, -0.05, 0.025), earth, squash=(1.4, 0.8, 0.7), subdiv=1, seed=3)
    blob("earth_clod_1", 0.025, (SOLE_X0 + 0.1, -0.05, 0.02), earth, squash=(1.2, 1, 0.8), subdiv=1, seed=4)

    # The mouldboard: a twisted plank on the -y side, low and narrow at the share, high and out-turned behind.
    for i in range(3):
        t0, t1 = i / 3, (i + 1) / 3
        x0, x1 = SOLE_X1 - 0.02 - 0.5 * t0, SOLE_X1 - 0.02 - 0.5 * t1
        xm = (x0 + x1) / 2
        tm = (t0 + t1) / 2
        box(f"mouldboard_{i}", (0.18, 0.022, 0.1 + 0.12 * tm), (xm, -0.06 - 0.08 * tm, 0.065 + 0.06 * tm), wood,
            rot=(-10 - 35 * tm, 0, 18), bevel=0.006)

    # The standard from the sole up to the beam, and the draw beam with its pegs.
    _beam("standard", (0.02, 0, 0.04), _lerp(BEAM_A, BEAM_B, 0.4), 0.07, 0.09, wood, extend=0.02)
    _beam("beam", BEAM_A, BEAM_B, BEAM_W, BEAM_H, wood, bevel=0.014)
    for i, t in enumerate((0.12, 0.4)):
        p = _lerp(BEAM_A, BEAM_B, t)
        cylinder(f"peg_{i}", 0.014, 0.13, (p[0], -0.065, p[2]), old, segments=8, rot=(-90, 0, 0), bevel=0.003)
        box(f"strap_{i}", (0.05, BEAM_W + 0.012, BEAM_H + 0.012), (p[0] + 0.07, 0, p[2] + 0.008), iron,
            rot=(0, -4, 0), bevel=0.003)

    # The coulter: an iron knife through the beam, its point just ahead of the share.
    pc = _lerp(BEAM_A, BEAM_B, (COULTER_X - BEAM_A[0]) / (BEAM_B[0] - BEAM_A[0]))
    _beam("coulter", (pc[0], -0.005, pc[2] + 0.1), (SOLE_X1 + SHARE_L - 0.08, -0.01, 0.06), 0.018, 0.06, iron,
          bevel=0.004)
    box("coulter_wedge", (0.04, 0.03, 0.05), (pc[0] + 0.04, 0, pc[2] + BEAM_H / 2 + 0.01), old, bevel=0.004)

    # The handles from the sole's tail up and back, splayed, with a rung, a stay to the beam and worn grips.
    for s in (-1, 1):
        foot = (HANDLE_FOOT[0], s * HANDLE_FOOT[1], HANDLE_FOOT[2])
        top = (HANDLE_TOP[0], s * HANDLE_TOP[1], HANDLE_TOP[2])
        _beam(f"handle_{s}", foot, top, 0.05, 0.06, old if s < 0 else wood, extend=0.03)
        grip0 = _lerp(foot, top, 0.98)
        grip1 = (grip0[0] - 0.12, grip0[1] + s * 0.01, grip0[2] - 0.05)
        _rod(f"grip_{s}", grip0, grip1, 0.024, worn, segments=8, bevel=0.004)
        b = _lerp(BEAM_A, BEAM_B, 0.02)
        _rod(f"handle_stay_{s}", _lerp(foot, top, 0.45), (b[0], s * 0.03, b[2]), 0.015, iron, segments=6, bevel=0)
    r0 = _lerp(HANDLE_FOOT, HANDLE_TOP, 0.62)
    _rod("rung", (r0[0], -r0[1], r0[2]), r0, 0.02, old, segments=8, bevel=0.003)
    r2 = _lerp(HANDLE_FOOT, HANDLE_TOP, (BEAM_A[2] - HANDLE_FOOT[2]) / (HANDLE_TOP[2] - HANDLE_FOOT[2]))
    _rod("beam_bar", (r2[0], -r2[1] - 0.03, r2[2]), (r2[0], r2[1] + 0.03, r2[2]), 0.022, old, segments=8, bevel=0.003)
    r1 = _lerp(HANDLE_FOOT, HANDLE_TOP, 0.3)
    _rod("rung_low", (r1[0], -r1[1], r1[2]), r1, 0.022, old, segments=8, bevel=0.003)

    # The foot wheel in a fork under the beam's front, and the hitch ring.
    wz = WHEEL_R
    cylinder("wheel", WHEEL_R - 0.012, WHEEL_T, (WHEEL_X, WHEEL_T / 2, wz), old, segments=18, rot=(90, 0, 0),
             bevel=0.006)
    torus("tyre", WHEEL_R - 0.012, 0.013, (WHEEL_X, 0, wz), iron, rot=(90, 0, 0), major=24, minor=6).scale = (
        1, 1, 1.6)
    cylinder("hub", 0.04, WHEEL_T + 0.04, (WHEEL_X, WHEEL_T / 2 + 0.02, wz), wood, segments=10, rot=(90, 0, 0),
             bevel=0.005)
    cylinder("axle", 0.012, WHEEL_T + 0.12, (WHEEL_X, WHEEL_T / 2 + 0.06, wz), iron, segments=8, rot=(90, 0, 0),
             bevel=0)
    pb = _lerp(BEAM_A, BEAM_B, (WHEEL_X - BEAM_A[0]) / (BEAM_B[0] - BEAM_A[0]))
    for s in (-1, 1):
        _beam(f"fork_{s}", (WHEEL_X, s * 0.055, wz), (pb[0], s * 0.055, pb[2] + 0.02), 0.025, 0.05, wood,
              extend=0.02, bevel=0.005)
    box("fork_bolster", (0.07, 0.14, 0.04), (pb[0], 0, pb[2] - BEAM_H / 2 - 0.02), wood, bevel=0.006)
    end = BEAM_B
    box("hitch_cap", (0.06, BEAM_W + 0.012, BEAM_H + 0.012), (end[0] - 0.03, 0, end[2]), iron, rot=(0, -4, 0),
        bevel=0.003)
    torus("hitch_ring", 0.045, 0.01, (end[0] + 0.045, 0, end[2] - 0.01), iron, rot=(rnd.uniform(70, 80), 0, 0),
          major=16, minor=6)
