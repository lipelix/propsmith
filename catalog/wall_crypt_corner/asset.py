"""An L-shaped corner of crypt wall: two half-sections, arms running 0.75 m to +x and to +y from a square corner pier at
the origin, in the dark dressed ashlar of wall_crypt_straight: long quoins alternating between the arms so the joints
stagger round the corner, a recessed near black mortar core, a proud footing course, a plain coping, worn arrises and a
little damp staining."""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box

MODULE = 1.5  # metres: the length wall and fence sections join at
EDGE = MODULE / 2  # the arms end half a module out, where straight sections centred a module away begin
T = 0.6  # wall thickness
H = 3.0  # overall height including the coping
COPING_H = 0.1
COPING_OVER = 0.02
COURSES = 9
COURSE_H = (H - COPING_H) / COURSES
FOOT_OVER = 0.025  # the footing course stands proud of both faces
JOINT = 0.014
INSET = 0.035  # how far the mortar core sits behind the faces
QUOIN = 0.75  # length of the corner quoin that ties the arms, from the outer face of the pier

# Shared stone palette of the crypt wall set (wall_crypt_straight, _corner, _doorway): keep them equal.
STONE = (0.19, 0.195, 0.205)
STONE_OLD = (0.145, 0.148, 0.155)
STONE_PALE = (0.24, 0.243, 0.25)
DAMP = (0.1, 0.11, 0.098)
MORTAR = (0.04, 0.04, 0.042)
COPING = (0.1, 0.104, 0.115)


def _mats(prefix):
    return {
        "stone": material(f"{prefix}_stone", STONE, vary=0.22, scale=7, crevice=0.7),
        "old": material(f"{prefix}_stone_old", STONE_OLD, vary=0.25, scale=8, crevice=0.7),
        "pale": material(f"{prefix}_stone_pale", STONE_PALE, vary=0.2, scale=9, crevice=0.65),
        "damp": material(f"{prefix}_damp", DAMP, rough=0.6, vary=0.3, scale=5, crevice=0.75),
        "mortar": material(f"{prefix}_mortar", MORTAR, vary=0.12, scale=20, crevice=0.9),
        "coping": material(f"{prefix}_coping", COPING, vary=0.22, scale=7, crevice=0.7),
    }


def _pick(rnd, mats, course):
    damp = (0.65, 0.3, 0.06)[min(course, 2)]
    if rnd.random() < damp:
        return mats["damp"]
    r = rnd.random()
    return mats["stone"] if r < 0.55 else mats["old"] if r < 0.85 else mats["pale"]


def _block(rnd, name, along, a, b, depth, z0, h, mat, bevel=None):
    """A block from `a` to `b` along `along` ("x" or "y"), `depth` thick across the wall, standing on `z0`."""
    bh = h * rnd.uniform(0.985, 1.0)
    d = depth * rnd.uniform(0.985, 1.0)
    across = rnd.uniform(-0.004, 0.004)
    if along == "x":
        size, at = (b - a, d, bh), ((a + b) / 2, across, z0 + bh / 2)
    else:
        size, at = (d, b - a, bh), (across, (a + b) / 2, z0 + bh / 2)
    box(name, size, at, mat, rot=(0, 0, rnd.uniform(-0.4, 0.4)), bevel=bevel or rnd.uniform(0.022, 0.032))


@prop
def wall_crypt_corner():
    rnd = random.Random(37)
    mats = _mats("wall_crypt_corner")
    body_h = COURSES * COURSE_H
    core = T - 2 * INSET
    box("core_x", (EDGE + core / 2, core, body_h), ((EDGE - core / 2) / 2, 0, body_h / 2), mats["mortar"], bevel=0)
    box("core_y", (core, EDGE - core / 2, body_h), (0, (EDGE + core / 2) / 2, body_h / 2), mats["mortar"], bevel=0)

    for c in range(COURSES):
        z0 = c * COURSE_H + JOINT / 2
        h = COURSE_H - JOINT
        depth = T + (2 * FOOT_OVER if c == 0 else 0)
        back = -T / 2 - (FOOT_OVER if c == 0 else 0)  # outer face of the pier
        q_end = -T / 2 + QUOIN * rnd.uniform(0.94, 1.02)
        mat = _pick(rnd, mats, c)
        # The quoin runs through the pier along one arm, the other arm butts against it; they swap every course.
        first, second = ("x", "y") if c % 2 == 0 else ("y", "x")
        _block(rnd, f"quoin_{c}", first, back, q_end - JOINT / 2, depth, z0, h, mat, bevel=0.03)
        _block(rnd, f"block_{first}_{c}", first, q_end + JOINT / 2, EDGE - JOINT / 4, depth, z0, h,
               _pick(rnd, mats, c))
        _block(rnd, f"block_{second}_{c}", second, T / 2 + JOINT / 2, EDGE - JOINT / 4, depth, z0, h,
               _pick(rnd, mats, c))

    # Coping: a square slab over the pier, then one slab out along each arm.
    cw = T + 2 * COPING_OVER
    zc = body_h + COPING_H / 2
    box("coping_corner", (cw, cw, COPING_H), (0, 0, zc), mats["coping"], rot=(0, 0, rnd.uniform(-0.4, 0.4)),
        bevel=0.022)
    a, b = cw / 2 + JOINT / 2, EDGE - JOINT / 4
    hc = COPING_H * rnd.uniform(0.94, 1.0)
    box("coping_x", (b - a, cw, hc), ((a + b) / 2, 0, zc), mats["coping"], rot=(0, 0, rnd.uniform(-0.4, 0.4)),
        bevel=0.022)
    box("coping_y", (cw, b - a, hc), (0, (a + b) / 2, zc), mats["coping"], rot=(0, 0, rnd.uniform(-0.4, 0.4)),
        bevel=0.022)
