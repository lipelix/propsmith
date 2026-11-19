"""A straight 1.5 m section of crypt wall: dark, cool dressed ashlar in regular staggered courses over a recessed near
black mortar core, a slightly proud footing course, a plain coping course on top, worn rounded arrises and a little
damp staining: most footing blocks, and a seep of darkened blocks running down from one joint."""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box

MODULE = 1.5  # metres: the length wall and fence sections join at
L = MODULE  # wall length along x: one module so sections join end to end
T = 0.6  # wall thickness (y)
H = 3.0  # overall height including the coping
COPING_H = 0.1
COPING_OVER = 0.02  # coping overhang on each face
COURSES = 9
COURSE_H = (H - COPING_H) / COURSES
FOOT_OVER = 0.025  # the footing course stands proud of both faces
JOINT = 0.014  # mortar joint between blocks
INSET = 0.035  # how far the mortar core sits behind the faces
SEEP_X = 0.38  # where damp seeps down the wall from a joint
SEEP_TOP = 4  # the seep darkens the blocks under it up to this course

# Shared stone palette of the crypt wall set (wall_crypt_straight, _corner, _doorway): keep them equal.
STONE = (0.19, 0.195, 0.205)  # linear RGB: cool dark blue-grey ashlar
STONE_OLD = (0.145, 0.148, 0.155)
STONE_PALE = (0.24, 0.243, 0.25)
DAMP = (0.1, 0.11, 0.098)  # stone darkened by damp, a little green
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


def _pick(rnd, mats, course, seep=False):
    """Damp low down: most footing blocks, some of the next course, a rare one higher up, and the blocks of a seep."""
    damp = 0.85 if seep else (0.65, 0.3, 0.06)[min(course, 2)]
    if rnd.random() < damp:
        return mats["damp"]
    r = rnd.random()
    return mats["stone"] if r < 0.55 else mats["old"] if r < 0.85 else mats["pale"]


def _splits(rnd, course):
    """Block joints along x for a course: two long blocks, then three (half, long, half), so joints stagger."""
    half = L / 2
    if course % 2 == 0:
        return [-half, rnd.uniform(-0.08, 0.08), half]
    q = L / 4
    return [-half, -q + rnd.uniform(-0.05, 0.05), q + rnd.uniform(-0.05, 0.05), half]


@prop
def wall_crypt_straight():
    rnd = random.Random(31)
    mats = _mats("wall_crypt_straight")
    body_h = COURSES * COURSE_H
    box("core", (L, T - 2 * INSET, body_h), (0, 0, body_h / 2), mats["mortar"], bevel=0)

    for c in range(COURSES):
        z0 = c * COURSE_H
        h = COURSE_H - JOINT
        depth = T + (2 * FOOT_OVER if c == 0 else 0)
        xs = _splits(rnd, c)
        for i in range(len(xs) - 1):
            a, b = xs[i] + JOINT / 2, xs[i + 1] - JOINT / 2
            # Blocks at a section end reach to it, so sections join with one joint's gap.
            if i == 0:
                a = xs[0] + JOINT / 4
            if i == len(xs) - 2:
                b = xs[-1] - JOINT / 4
            bh = h * rnd.uniform(0.985, 1.0)
            seep = a <= SEEP_X <= b and c < SEEP_TOP
            box(f"block_{c}_{i}", (b - a, depth * rnd.uniform(0.985, 1.0), bh),
                ((a + b) / 2, rnd.uniform(-0.004, 0.004), z0 + JOINT / 2 + bh / 2), _pick(rnd, mats, c, seep),
                rot=(rnd.uniform(-0.3, 0.3), 0, rnd.uniform(-0.4, 0.4)), bevel=rnd.uniform(0.022, 0.032))

    # Coping: flat slabs a little proud of both faces.
    zc = body_h + COPING_H / 2
    xs = [-L / 2, -0.25 + rnd.uniform(-0.05, 0.05), 0.3 + rnd.uniform(-0.05, 0.05), L / 2]
    for i in range(len(xs) - 1):
        a = xs[i] + (JOINT / 4 if i == 0 else JOINT / 2)
        b = xs[i + 1] - (JOINT / 4 if i == len(xs) - 2 else JOINT / 2)
        box(f"coping_{i}", (b - a, T + 2 * COPING_OVER, COPING_H * rnd.uniform(0.94, 1.0)), ((a + b) / 2, 0, zc),
            mats["coping"], rot=(0, 0, rnd.uniform(-0.4, 0.4)), bevel=0.022)
