"""A small plank footbridge about 4 × 1.6 × 1.4 m: weathered planks with uneven gaps laid across two stringers that
rise in a gentle hump from the ground at both ends, held up in the middle by two low trestles of splayed round legs
on flat stones under a cap beam. Square posts bolted to the stringers carry a handrail and a middle rail on both sides
(plan 3, item 17)."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box as _box, cylinder

# Overall dimensions (metres): the bridge runs along x, its ends resting on the ground.
L = 4.0
Z_MID = 0.6  # deck top over the middle
FLAT = 0.5  # half-length of the level middle of the deck
PLANK_T = 0.045
PLANK_LEN = 1.32
PLANK_W = (0.17, 0.22)
GAP = (0.01, 0.03)
STR_W, STR_H = 0.11, 0.15  # stringers
STR_Y = 0.62
STR_X = (-2.0, -1.45, -0.9, -FLAT, FLAT, 0.9, 1.45, 2.0)  # stringer break points
POST = 0.085  # square handrail posts
POST_Y = STR_Y + STR_W / 2 + POST / 2
POST_X = (-1.88, -0.95, 0.0, 0.95, 1.88)
RAIL_H = 0.77  # top of the handrail above the deck
RAIL_W, RAIL_D = 0.075, 0.07
TRESTLE_X = 0.8
CAP_W, CAP_H, CAP_LEN = 0.13, 0.12, 1.5
LEG_R = 0.06
LEG_FOOT_Y = 0.66
PAD = (0.26, 0.2, 0.06)  # flat stones under the legs

WOOD = (0.24, 0.205, 0.16)  # sun-greyed planks
WOOD_OLD = (0.18, 0.15, 0.115)
FRAME = (0.17, 0.125, 0.085)
RAIL = (0.21, 0.165, 0.11)
STONE = (0.27, 0.26, 0.235)
IRON = (0.05, 0.047, 0.044)

Z_END = PLANK_T + STR_H + 0.006  # deck top at the very ends: the stringers' feet just reach the ground


def box(*args, **kwargs):
    """A box with a one-segment bevel (a chamfer): enough at this size, and half the triangles."""
    obj = _box(*args, **kwargs)
    if obj.modifiers:
        obj.modifiers[0].segments = 1
    return obj


def _deck(x):
    """Height of the deck top at x: level in the middle, easing down to the ground at both ends."""
    u = max(0.0, abs(x) - FLAT) / (L / 2 - FLAT)
    return Z_END + (Z_MID - Z_END) * 0.5 * (1 + math.cos(math.pi * min(1.0, u)))


def _slope(x, h=0.01):
    return math.degrees(math.atan2(_deck(x + h) - _deck(x - h), 2 * h))


def _beam(name, p, q, w, h, mat, extra=0.0, bevel=0.012):
    """A box from p to q (its length along pq, plus `extra`), `w` wide and `h` high."""
    d = [q[i] - p[i] for i in range(3)]
    length = math.sqrt(sum(c * c for c in d))
    yaw = math.degrees(math.atan2(d[1], d[0]))
    pitch = math.degrees(math.atan2(d[2], math.hypot(d[0], d[1])))
    mid = tuple((p[i] + q[i]) / 2 for i in range(3))
    return box(name, (length + extra, w, h), mid, mat, rot=(0, -pitch, yaw), bevel=bevel)


@prop
def bridge_wood_small():
    rnd = random.Random(1719)
    wood = material("bridge_wood_small_planks", WOOD, vary=0.3, scale=14)
    wood_old = material("bridge_wood_small_planks_old", WOOD_OLD, vary=0.34, scale=14)
    frame = material("bridge_wood_small_frame", FRAME, vary=0.28, scale=10)
    rail = material("bridge_wood_small_rail", RAIL, vary=0.28, scale=12)
    stone = material("bridge_wood_small_stone", STONE, vary=0.3, scale=8, crevice=0.65)
    iron = material("bridge_wood_small_iron", IRON, rough=0.55, vary=0.3, scale=20, metal=0.6)

    def str_z(x):  # stringer centre line
        return _deck(x) - PLANK_T - STR_H / 2

    # Two stringers in segments following the hump; the end segments end with their feet on the ground.
    for s in (-1, 1):
        for k in range(len(STR_X) - 1):
            a, b = STR_X[k], STR_X[k + 1]
            inset = 0.03 if k == 0 else 0.0
            inset_b = 0.03 if k == len(STR_X) - 2 else 0.0
            a, b = a + inset, b - inset_b
            ext = 0.0 if inset or inset_b else 0.05
            _beam(f"stringer_{s}_{k}", (a, s * STR_Y, str_z(a)), (b, s * STR_Y, str_z(b)), STR_W, STR_H, frame,
                  extra=ext, bevel=0.014)

    # Planks across the stringers, following the deck, uneven widths and gaps.
    x = -L / 2 + 0.01
    n = 0
    while True:
        w = rnd.uniform(*PLANK_W)
        if x + w > L / 2 - 0.01:
            break
        cx = x + w / 2
        length = PLANK_LEN - rnd.uniform(0.0, 0.06)
        z = _deck(cx) - PLANK_T / 2 + rnd.uniform(-0.003, 0.004)
        box(f"plank_{n}", (w, length, PLANK_T), (cx, rnd.uniform(-0.02, 0.02), z),
            wood_old if rnd.random() < 0.35 else wood,
            rot=(rnd.uniform(-0.6, 0.6), -_slope(cx), rnd.uniform(-1.5, 1.5)), bevel=0.008)
        n += 1
        x += w + rnd.uniform(*GAP)

    # Two trestles: a cap beam under the stringers on two pairs of splayed round legs standing on flat stones.
    for t, tx in enumerate((-TRESTLE_X, TRESTLE_X)):
        cap_top = str_z(tx) - STR_H / 2 * math.cos(math.radians(_slope(tx))) - 0.005
        box(f"cap_{t}", (CAP_W, CAP_LEN, CAP_H), (tx, 0, cap_top - CAP_H / 2), frame,
            rot=(0, 0, rnd.uniform(-1.0, 1.0)), bevel=0.015)
        for s in (-1, 1):
            for dx in (-0.035, 0.035):
                foot_y = s * (LEG_FOOT_Y + rnd.uniform(-0.01, 0.01))
                if dx < 0:
                    box(f"pad_{t}_{s}", PAD, (tx, foot_y, PAD[2] / 2), stone, rot=(0, 0, rnd.uniform(-12, 12)),
                        bevel=0.015)
            p = (tx, foot_y, PAD[2] - 0.005)
            q = (tx, s * (CAP_LEN / 2 - 0.12), cap_top - CAP_H + 0.02)
            d = [q[i] - p[i] for i in range(3)]
            length = math.sqrt(sum(c * c for c in d))
            tilt = math.degrees(math.acos(d[2] / length))
            yaw = math.degrees(math.atan2(d[1], d[0]))
            cylinder(f"leg_{t}_{s}", LEG_R, length, p, frame, r_top=LEG_R * 0.92, segments=10,
                     rot=(tilt, 0, yaw + 90), bevel=0.008)

    # Handrail posts bolted to the outside of the stringers, a top rail and a middle rail between them.
    tops = {-1: [], 1: []}
    for s in (-1, 1):
        for k, px in enumerate(POST_X):
            px += rnd.uniform(-0.02, 0.02)
            bottom = max(0.004, str_z(px) - STR_H / 2 - 0.02)
            top = _deck(px) + RAIL_H - RAIL_D / 2
            box(f"post_{s}_{k}", (POST, POST, top - bottom), (px, s * POST_Y, (top + bottom) / 2), rail,
                rot=(rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0), bevel=0.012)
            cylinder(f"bolt_{s}_{k}", 0.016, 0.02, (px, s * (POST_Y + POST / 2 - 0.004), str_z(px)), iron,
                     segments=8, rot=(-90 * s, 0, 0), bevel=0.003)
            tops[s].append((px, top))
        for k in range(len(POST_X) - 1):
            (xa, za), (xb, zb) = tops[s][k], tops[s][k + 1]
            y = s * POST_Y
            _beam(f"rail_{s}_{k}", (xa, y, za + RAIL_D / 2 - 0.01), (xb, y, zb + RAIL_D / 2 - 0.01), RAIL_W, RAIL_D,
                  rail, extra=0.09 if k in (0, len(POST_X) - 2) else 0.06, bevel=0.012)
            ma, mb = (za + _deck(xa)) / 2, (zb + _deck(xb)) / 2
            _beam(f"midrail_{s}_{k}", (xa, y + s * 0.02, ma), (xb, y + s * 0.02, mb), 0.045, 0.06, frame,
                  extra=0.04, bevel=0.01)
