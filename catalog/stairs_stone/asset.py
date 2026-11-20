"""A flight of worn stone steps between two crypt side walls, 1.5 m wide and 3 m long, front (the way on) on -y.

stairs_stone_down: the flight seen from its head, going down into darkness. Nothing may sink below the ground, so the
descent is drawn the way the eye reads it: thin worn treads with dark shadow gaps that grow darker step by step, low
parapets beside the open head, then a roofed mouth whose lintels drop lower over every step and whose inside fades to
black.

stairs_stone_up: the same flight seen from its foot, rising (real risers) under a lintel to a dark opening at the top.
"""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box

MODULE = 1.5  # metres: the length wall and fence sections join at
W = MODULE  # overall width (x): one module
L = 2 * MODULE  # flight length (y): two modules
H = 3.0  # wall height including the coping, as the crypt wall kit
WALL_T = 0.25  # side wall thickness
IN = W / 2 - WALL_T  # half the clear width between the walls (0.5)
COPING_H = 0.1
COPING_OVER = 0.02
COURSES = 6
COURSE_H = (H - COPING_H) / COURSES
JOINT = 0.014
INSET = 0.03  # the mortar core sits behind the block faces
BLOCK = 0.8  # about how long a wall block is

# stairs_stone_down: a landing at the head, then treads running down to the deep end.
HEAD = 0.3  # landing depth at the head of the flight (-y)
DOWN_STEPS = 9
DOWN_TREAD = (L - HEAD) / DOWN_STEPS
TREAD_GAP = 0.035  # dark gap between treads, the shadow under each nosing
TREAD_TOP = 0.07  # the head landing's top; the treads thin out to TREAD_LOW at the deep end
TREAD_LOW = 0.02
DOWN_SOFFITS = (2.25, 1.9, 1.55, 1.2)  # undersides of the four ceiling lintels, dropping towards the deep end
DOWN_CEIL_Y = 0.0  # the ceiling starts here and runs to the deep end

# stairs_stone_up: real risers from the foot to a landing under the top lintel.
FOOT = 0.15  # floor margin before the first riser
UP_STEPS = 8
RISE = 0.18
UP_TREAD = 0.3
UP_TOP = UP_STEPS * RISE  # landing height (1.44)
UP_SOFFIT = UP_TOP + 1.1  # underside of the lintel over the top landing
UP_CEIL_Y = 0.45

VOID_T = 0.1  # the dark fill closing the far end

# Shared stone palette of the crypt wall set (wall_crypt_straight, _corner, _doorway): keep them equal.
STONE = (0.19, 0.195, 0.205)  # linear RGB: cool dark blue-grey ashlar
STONE_OLD = (0.145, 0.148, 0.155)
STONE_PALE = (0.24, 0.243, 0.25)
DAMP = (0.1, 0.11, 0.098)
MORTAR = (0.04, 0.04, 0.042)
COPING = (0.1, 0.104, 0.115)
# The steps: paler, foot-worn stone, fading into the dark.
STEP_LIT = (0.235, 0.232, 0.228)
STEP_DARK = (0.03, 0.03, 0.034)
SHADES = 5  # step materials from lit to dark
VOID = (0.012, 0.012, 0.015)  # the darkness beyond


def _lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _mats(prefix):
    mats = {
        "stone": material(f"{prefix}_stone", STONE, vary=0.22, scale=7, crevice=0.7),
        "old": material(f"{prefix}_stone_old", STONE_OLD, vary=0.25, scale=8, crevice=0.7),
        "pale": material(f"{prefix}_stone_pale", STONE_PALE, vary=0.2, scale=9, crevice=0.65),
        "damp": material(f"{prefix}_damp", DAMP, rough=0.6, vary=0.3, scale=5, crevice=0.75),
        "mortar": material(f"{prefix}_mortar", MORTAR, vary=0.12, scale=20, crevice=0.9),
        "coping": material(f"{prefix}_coping", COPING, vary=0.22, scale=7, crevice=0.7),
        "void": material(f"{prefix}_void", VOID, rough=1.0, vary=0.05, scale=4, crevice=0.2),
    }
    # Step shades, lit to dark: a gamma so the first few stay readable and the last ones sink fast.
    mats["steps"] = [
        material(f"{prefix}_step_{i}", _lerp(STEP_LIT, STEP_DARK, (i / (SHADES - 1)) ** 1.4), vary=0.2, scale=8,
                 crevice=0.75)
        for i in range(SHADES)
    ]
    return mats


def _shade(mats, t):
    """The step material for a depth `t` in 0..1 along the flight into the dark."""
    return mats["steps"][min(SHADES - 1, int(t * SHADES))]


def _wall_block(rnd, mats, course, dark):
    """Damp on the footing, darker blocks towards the dark end of the flight."""
    if course == 0 and rnd.random() < 0.6:
        return mats["damp"]
    if rnd.random() < dark:
        return mats["old"] if rnd.random() < 0.5 else mats["mortar"]
    r = rnd.random()
    return mats["stone"] if r < 0.55 else mats["old"] if r < 0.85 else mats["pale"]


def _splits(rnd, y0, y1, course):
    """Block joints along y for one course of a wall run: blocks about BLOCK long, staggered course to course."""
    n = max(1, round((y1 - y0) / BLOCK))
    step = (y1 - y0) / n
    if course % 2 == 1 and n > 1:
        inner = [y0 + step * (i + 0.5) for i in range(n)]
    else:
        inner = [y0 + step * i for i in range(1, n)]
    return [y0] + [y + rnd.uniform(-0.06, 0.06) for y in inner] + [y1]


def _side_walls(rnd, mats, runs):
    """Two ashlar walls along y, their inner faces at x = ±IN, in `runs` of (y0, y1, courses): low parapets where the
    flight is open, the full 3 m where it is roofed. Blocks darken towards +y, the dark end."""
    for side in (-1, 1):
        cx = side * (IN + WALL_T / 2)
        for r, (y0, y1, courses) in enumerate(runs):
            body_h = courses * COURSE_H
            box(f"core_{side}_{r}", (WALL_T - 2 * INSET, y1 - y0, body_h), (cx, (y0 + y1) / 2, body_h / 2),
                mats["mortar"], bevel=0)
            for c in range(courses):
                z0 = c * COURSE_H
                ys = _splits(rnd, y0, y1, c + r)
                for i in range(len(ys) - 1):
                    a = ys[i] + (JOINT / 4 if i == 0 else JOINT / 2)
                    b = ys[i + 1] - (JOINT / 4 if i == len(ys) - 2 else JOINT / 2)
                    t = ((a + b) / 2 + L / 2) / L  # 0 at the open end, 1 at the dark end
                    bh = (COURSE_H - JOINT) * rnd.uniform(0.985, 1.0)
                    box(f"block_{side}_{r}_{c}_{i}", (WALL_T * rnd.uniform(0.985, 1.0), b - a, bh),
                        (cx, (a + b) / 2, z0 + JOINT / 2 + bh / 2), _wall_block(rnd, mats, c, 0.6 * t * t),
                        rot=(0, rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3)), bevel=rnd.uniform(0.02, 0.028))
            a = y0 + JOINT / 4
            b = y1 - JOINT / 4
            cw = WALL_T + 2 * COPING_OVER - 0.005
            box(f"coping_{side}_{r}", (cw, b - a, COPING_H * rnd.uniform(0.94, 1.0)),
                (side * (W / 2 - cw / 2), (a + b) / 2, body_h + COPING_H / 2), mats["coping"],
                rot=(0, 0, rnd.uniform(-0.2, 0.2)), bevel=0.02)


def _ceiling(rnd, mats, spans):
    """Lintels between the wall tops over the given (y0, y1, soffit) spans, each with a fill course above it."""
    top = H
    for i, (y0, y1, soffit) in enumerate(spans):
        d = y1 - y0 - JOINT
        yc = (y0 + y1) / 2
        t = (yc + L / 2) / L
        lintel_h = 0.36
        box(f"lintel_{i}", (2 * IN + 0.04, d, lintel_h), (0, yc, soffit + lintel_h / 2),
            mats["old"] if t > 0.6 else mats["stone"], rot=(rnd.uniform(-0.3, 0.3), 0, 0), bevel=0.025)
        fill_h = top - soffit - lintel_h - JOINT
        if fill_h > 0.05:
            box(f"fill_{i}", (2 * IN + 0.02, d, fill_h), (0, yc, top - fill_h / 2), mats["coping"], bevel=0.022)


def _shadow(mats, y0, soffit):
    """The dark inside a roofed flight: linings on both inner wall faces, the mortar dark from `y0`, then near black
    deeper in, so the light fades out under the ceiling instead of reaching the far end."""
    for k, (start, mat) in enumerate(((y0 + 0.12, mats["mortar"]), (y0 + 0.5, mats["void"]))):
        for side in (-1, 1):
            box(f"shadow_{k}_{side}", (0.01, L / 2 - start, soffit), (side * (IN - 0.005 + 0.001 * k),
                                                                      (start + L / 2) / 2, soffit / 2), mat, bevel=0)


@prop
def stairs_stone_down():
    rnd = random.Random(61)
    mats = _mats("stairs_stone")
    # Low parapets beside the open head of the flight, full walls where the ceiling roofs it.
    _side_walls(rnd, mats, [(-L / 2, DOWN_CEIL_Y, 1), (DOWN_CEIL_Y, L / 2, COURSES)])

    # The dark under the flight: seen through the gaps between treads and at the deep end.
    box("pit", (2 * IN - 0.01, L - HEAD, 0.01), (0, HEAD / 2, 0.005), mats["void"], bevel=0)
    box("head", (2 * IN - 0.01, HEAD - TREAD_GAP / 2, TREAD_TOP), (0, -L / 2 + (HEAD - TREAD_GAP / 2) / 2,
                                                                    TREAD_TOP / 2), mats["steps"][0], bevel=0.018)
    for i in range(DOWN_STEPS):
        t = (i + 1) / DOWN_STEPS
        y0 = -L / 2 + HEAD + i * DOWN_TREAD + TREAD_GAP / 2
        d = DOWN_TREAD - TREAD_GAP
        h = TREAD_TOP + (TREAD_LOW - TREAD_TOP) * t
        # Worn: each tread a touch narrower or askew, its front rounded off by feet.
        box(f"tread_{i}", ((2 * IN - 0.03) * rnd.uniform(0.97, 1.0), d, h),
            (rnd.uniform(-0.01, 0.01), y0 + d / 2, h / 2), _shade(mats, t * 0.999),
            rot=(0, 0, rnd.uniform(-0.6, 0.6)), bevel=min(0.02, h * 0.45))

    n = len(DOWN_SOFFITS)
    span = (L / 2 - DOWN_CEIL_Y) / n
    _ceiling(rnd, mats, [(DOWN_CEIL_Y + i * span, DOWN_CEIL_Y + (i + 1) * span, s) for i, s in enumerate(DOWN_SOFFITS)])
    _shadow(mats, DOWN_CEIL_Y, DOWN_SOFFITS[0])
    # The deep end: nothing but dark under the last lintel.
    box("void", (2 * IN, VOID_T, DOWN_SOFFITS[-1]), (0, L / 2 - VOID_T / 2, DOWN_SOFFITS[-1] / 2), mats["void"],
        bevel=0)


@prop
def stairs_stone_up():
    rnd = random.Random(62)
    mats = _mats("stairs_stone")
    # Parapets that climb with the flight, then full walls where the lintel roofs its head.
    third = (UP_CEIL_Y + L / 2) / 3
    _side_walls(rnd, mats, [(-L / 2, -L / 2 + third, 1), (-L / 2 + third, -L / 2 + 2 * third, 2),
                            (-L / 2 + 2 * third, UP_CEIL_Y, 3), (UP_CEIL_Y, L / 2, COURSES)])

    for i in range(UP_STEPS):
        y0 = -L / 2 + FOOT + i * UP_TREAD
        top = (i + 1) * RISE
        t = i / UP_STEPS
        # Each step a block from its riser to the back, so the flight is solid; the nosings worn round.
        box(f"step_{i}", ((2 * IN - 0.02) * rnd.uniform(0.98, 1.0), L / 2 - VOID_T - y0, top * rnd.uniform(0.995, 1.0)),
            (rnd.uniform(-0.008, 0.008), (y0 + L / 2 - VOID_T) / 2, top / 2), _shade(mats, t),
            rot=(0, 0, rnd.uniform(-0.4, 0.4)) if i == 0 else (0, 0, 0), bevel=0.02)

    _ceiling(rnd, mats, [(UP_CEIL_Y, L / 2, UP_SOFFIT)])
    _shadow(mats, UP_CEIL_Y, UP_SOFFIT)
    # The dark opening at the head of the flight.
    box("void", (2 * IN, VOID_T, UP_SOFFIT), (0, L / 2 - VOID_T / 2, UP_SOFFIT / 2), mats["void"], bevel=0)
