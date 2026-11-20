"""A ritual circle set flush in a round patch of crypt flagstones, about 3.5 m across and a few centimetres high: a
ring of curved kerb stones round worn square flags on a dark grout bed, and a dark-painted sigil over them, two
concentric rings with rune marks between them, a five-pointed star with a small ring at each point, and a dark disc
at the centre. Same stone palette as the crypt wall kit."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

D = 3.5  # overall diameter
R = D / 2
KERB_W = 0.24  # radial width of the kerb ring
KERBS = 20
FLAG = 0.5  # nominal flagstone pitch
JOINT = 0.022
BED_H = 0.02  # dark grout bed under the stones
TOP = 0.045  # top of every stone (the floor is level)
PAINT_T = 0.006  # thickness of the painted sigil, standing 2 mm proud of the stones
RING_OUT = 1.38  # sigil outer ring radius
RING_IN = 1.12  # sigil inner ring radius (the star's points touch it)
STROKE = 0.055  # width of a painted line

# Crypt stone palette (shared with wall_crypt_* and pillar_stone): keep them equal.
STONE = (0.19, 0.195, 0.205)  # linear RGB: cool dark blue-grey
STONE_OLD = (0.145, 0.148, 0.155)
STONE_PALE = (0.24, 0.243, 0.25)
DAMP = (0.1, 0.11, 0.098)
MORTAR = (0.04, 0.04, 0.042)
COPING = (0.1, 0.104, 0.115)
PAINT = (0.045, 0.014, 0.013)  # old dark red-brown paint, nearly black


def _mats(prefix):
    return {
        "stone": material(f"{prefix}_stone", STONE, vary=0.22, scale=7, crevice=0.7),
        "old": material(f"{prefix}_stone_old", STONE_OLD, vary=0.25, scale=8, crevice=0.7),
        "pale": material(f"{prefix}_stone_pale", STONE_PALE, vary=0.2, scale=9, crevice=0.65),
        "damp": material(f"{prefix}_damp", DAMP, rough=0.6, vary=0.3, scale=5, crevice=0.75),
        "mortar": material(f"{prefix}_mortar", MORTAR, vary=0.12, scale=20, crevice=0.9),
        "kerb": material(f"{prefix}_kerb", COPING, vary=0.22, scale=7, crevice=0.7),
        "paint": material(f"{prefix}_paint", PAINT, rough=0.55, vary=0.35, scale=11, crevice=0.4),
    }


def _stroke(name, a, b, mat, w=STROKE):
    """A straight painted line from point a to point b (x, y) on top of the stones."""
    (ax, ay), (bx, by) = a, b
    length = math.hypot(bx - ax, by - ay)
    ang = math.degrees(math.atan2(by - ay, bx - ax))
    box(name, (length, w, PAINT_T), ((ax + bx) / 2, (ay + by) / 2, TOP + PAINT_T / 2 - 0.002), mat,
        rot=(0, 0, ang), bevel=0)


def _ring(name, radius, mat, w=STROKE, major=52):
    """A painted ring: a torus flattened onto the floor."""
    obj = torus(name, radius, w / 2, (0, 0, TOP + 0.001), mat, major=major, minor=4)
    obj.scale = (1, 1, PAINT_T / w)
    return obj


@prop
def ritual_circle_floor():
    rnd = random.Random(63)
    mats = _mats("ritual_circle_floor")
    cylinder("bed", R - 0.01, BED_H, (0, 0, 0), mats["mortar"], segments=40, bevel=0)

    # Kerb ring: curved stones approximated by tangential blocks.
    inner = R - KERB_W
    step = 2 * math.pi / KERBS
    for i in range(KERBS):
        a = step * i + step / 2
        rc = R - KERB_W / 2 - 0.006
        h = TOP - BED_H + 0.01 + (0.003 if i % 2 else 0)  # neighbours overlap a little inside: no coplanar tops
        mat = rnd.choices([mats["kerb"], mats["old"], mats["damp"]], [5, 2, 1])[0]
        box(f"kerb_{i}", (KERB_W - 0.012, 2 * rc * math.sin(step / 2) - JOINT, h), (rc * math.cos(a), rc * math.sin(a), BED_H - 0.01 + h / 2),
            mat, rot=(0, 0, math.degrees(a)), bevel=0.012)

    # Square flags inside the kerb, offset every other row, kept clear of it.
    n = int(math.ceil(inner / FLAG)) + 1
    k = 0
    for row in range(-n, n + 1):
        y0 = row * FLAG
        off = FLAG / 2 if row % 2 else 0
        for col in range(-n - 1, n + 1):
            x0 = col * FLAG + off
            w = FLAG - JOINT
            # Keep a flag only when all its corners sit inside the kerb; trim the ones that stick out.
            corners = [(x0 + sx * w / 2, y0 + sy * w / 2) for sx in (-1, 1) for sy in (-1, 1)]
            if all(math.hypot(x, y) <= inner - 0.012 for x, y in corners):
                sx, sy, cx, cy = w, w, x0, y0
            else:
                # Shrink toward the centre until it fits, then drop slivers.
                sx = sy = w
                cx, cy = x0, y0
                for _ in range(12):
                    corners = [(cx + ex * sx / 2, cy + ey * sy / 2) for ex in (-1, 1) for ey in (-1, 1)]
                    worst = max(corners, key=lambda c: math.hypot(*c))
                    if math.hypot(*worst) <= inner - 0.012:
                        break
                    if abs(worst[0]) > abs(worst[1]):
                        sx -= 0.04
                        cx -= math.copysign(0.02, worst[0])
                    else:
                        sy -= 0.04
                        cy -= math.copysign(0.02, worst[1])
                else:
                    continue
                if min(sx, sy) < 0.12:
                    continue
            h = TOP - BED_H + 0.008
            mat = rnd.choices([mats["stone"], mats["old"], mats["pale"], mats["damp"]], [6, 3, 2, 1])[0]
            box(f"flag_{k}", (sx, sy, h), (cx, cy, BED_H - 0.008 + h / 2), mat,
                rot=(0, 0, rnd.uniform(-1.2, 1.2)), bevel=rnd.uniform(0.008, 0.014))
            k += 1

    # The sigil.
    paint = mats["paint"]
    _ring("ring_outer", RING_OUT, paint)
    _ring("ring_inner", RING_IN, paint, w=STROKE * 0.8)
    _ring("ring_border", inner - 0.06, paint, w=STROKE * 0.5, major=56)
    pts = [(RING_IN * math.cos(math.pi / 2 + 2 * math.pi * i / 5), RING_IN * math.sin(math.pi / 2 + 2 * math.pi * i / 5))
           for i in range(5)]
    for i in range(5):
        _stroke(f"star_{i}", pts[i], pts[(i + 2) % 5], paint)
    for i, (x, y) in enumerate(pts):
        a = math.atan2(y, x)
        rp = (RING_IN + RING_OUT) / 2
        obj = torus(f"point_ring_{i}", 0.09, 0.016, (rp * math.cos(a), rp * math.sin(a), TOP + 0.001), paint,
                    major=16, minor=4)
        obj.scale = (1, 1, PAINT_T / 0.032)
    # Rune marks between the rings: a short bar across the band and a tick or two beside it.
    for i in range(15):
        if i % 3 == 0:
            continue  # the point rings stand here
        a = math.pi / 2 + 2 * math.pi * i / 15 + rnd.uniform(-0.04, 0.04)
        r0, r1 = RING_IN + 0.06, RING_OUT - 0.06
        c, s = math.cos(a), math.sin(a)
        _stroke(f"rune_{i}_bar", (r0 * c, r0 * s), (r1 * c, r1 * s), paint, w=0.03)
        t = a + rnd.choice([-1, 1]) * 0.05
        rm = (r0 + r1) / 2 + rnd.uniform(-0.03, 0.03)
        _stroke(f"rune_{i}_tick", (rm * c, rm * s), ((rm + 0.06) * math.cos(t), (rm + 0.06) * math.sin(t)), paint,
                w=0.026)
        if rnd.random() < 0.5:
            _stroke(f"rune_{i}_hook", (r1 * c, r1 * s), ((r1 - 0.05) * math.cos(2 * a - t), (r1 - 0.05) * math.sin(2 * a - t)),
                    paint, w=0.026)
    cylinder("centre", 0.16, PAINT_T, (0, 0, TOP - 0.002), paint, segments=20, bevel=0)
