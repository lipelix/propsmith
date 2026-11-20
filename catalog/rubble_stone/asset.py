"""A heap of fallen dressed masonry, about 1.2 x 1.2 m and 0.6 m high: dark blue-grey crypt ashlar blocks and a
slab of coping lying tumbled and stacked on a low mound of grit, some whole, some broken with paler fresh faces, and
chips and grit spilled round the foot. Same stone palette as the crypt wall kit."""
import math
import random

from mathutils import Euler, Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

SPAN = 1.2  # footprint across x and y
H = 0.6  # height of the heap
MOUND_R = 0.56  # grit mound radius at the floor
MOUND_TOP_R = 0.2
MOUND_H = 0.15
SINK = 0.35  # how far (of the mound height under it) a block settles into the grit

# Crypt stone palette (shared with wall_crypt_* and pillar_stone): keep them equal.
STONE = (0.19, 0.195, 0.205)  # linear RGB: cool dark blue-grey ashlar
STONE_OLD = (0.145, 0.148, 0.155)
STONE_PALE = (0.24, 0.243, 0.25)
DAMP = (0.1, 0.11, 0.098)
COPING = (0.1, 0.104, 0.115)
BREAK = (0.29, 0.29, 0.288)  # fresh, paler broken stone
GRIT = (0.17, 0.162, 0.152)  # dust and grit, a little warmer than the stone

# The fallen blocks: (size x y z, centre x y, rotation degrees, material, rests on block index or None for the mound).
BLOCKS = [
    ((0.56, 0.32, 0.26), (-0.14, 0.12), (0, 2, 24), "stone", None),
    ((0.46, 0.3, 0.27), (0.26, -0.14), (17, 0, -34), "old", None),
    ((0.4, 0.26, 0.19), (-0.1, 0.06), (6, -9, 61), "pale", 0),
    ((0.3, 0.25, 0.22), (0.3, 0.33), (0, 24, 12), "break", None),
    ((0.28, 0.2, 0.18), (-0.38, -0.3), (-18, 9, 40), "damp", None),
    ((0.5, 0.27, 0.1), (0.02, -0.4), (0, 5, -12), "coping", None),
    ((0.26, 0.22, 0.2), (-0.41, 0.36), (11, -8, -25), "old", None),
    ((0.22, 0.16, 0.14), (0.18, 0.02), (25, 14, 70), "break", 1),
]


def _mats(prefix):
    return {
        "stone": material(f"{prefix}_stone", STONE, vary=0.22, scale=7, crevice=0.7),
        "old": material(f"{prefix}_stone_old", STONE_OLD, vary=0.25, scale=8, crevice=0.7),
        "pale": material(f"{prefix}_stone_pale", STONE_PALE, vary=0.2, scale=9, crevice=0.65),
        "damp": material(f"{prefix}_damp", DAMP, rough=0.6, vary=0.3, scale=5, crevice=0.75),
        "coping": material(f"{prefix}_coping", COPING, vary=0.22, scale=7, crevice=0.7),
        "break": material(f"{prefix}_break", BREAK, vary=0.3, scale=14, crevice=0.8),
        "grit": material(f"{prefix}_grit", GRIT, vary=0.35, scale=30, crevice=0.85),
    }


def _mound_h(x, y):
    """Height of the grit mound's surface at (x, y)."""
    r = math.hypot(x, y)
    if r <= MOUND_TOP_R:
        return MOUND_H
    return max(0.0, MOUND_H * (MOUND_R - r) / (MOUND_R - MOUND_TOP_R))


def _extent_z(size, rot):
    """Lowest and highest z of the corners of a box `size` centred on the origin, rotated by `rot` degrees (XYZ)."""
    e = Euler([math.radians(a) for a in rot])
    zs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                v = Vector((sx * size[0] / 2, sy * size[1] / 2, sz * size[2] / 2))
                v.rotate(e)
                zs.append(v.z)
    return min(zs), max(zs)


@prop
def rubble_stone():
    rnd = random.Random(62)
    mats = _mats("rubble_stone")
    cylinder("mound", MOUND_R, MOUND_H, (0, 0, 0), mats["grit"], r_top=MOUND_TOP_R, segments=11, bevel=0.03)

    tops = []
    for i, (size, (x, y), rot, mat, on) in enumerate(BLOCKS):
        lo, hi = _extent_z(size, rot)
        floor = _mound_h(x, y) * (1 - SINK) if on is None else tops[on] - 0.05
        z = max(floor - lo, -lo)  # never below the ground
        tops.append(z + hi)
        box(f"block_{i}", size, (x, y, z), mats[mat], rot=rot, bevel=rnd.uniform(0.016, 0.026))

    # Broken lumps of stone round the heap.
    for i in range(9):
        a = 2 * math.pi * i / 9 + rnd.uniform(-0.3, 0.3)
        d = rnd.uniform(0.42, 0.53)
        r = rnd.uniform(0.045, 0.08)
        x, y = d * math.cos(a), d * math.sin(a)
        blob(f"lump_{i}", r, (x, y, _mound_h(x, y) + r), rnd.choice([mats["break"], mats["stone"], mats["old"]]),
             squash=(1.1, 0.9, 0.75), subdiv=1, seed=rnd.randint(0, 9999), jitter=0.3)

    # Grit: small chips on the mound and spilled past it.
    for i in range(34):
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(0.15, 0.57)
        r = rnd.uniform(0.015, 0.032)
        x, y = d * math.cos(a), d * math.sin(a)
        blob(f"grit_{i}", r, (x, y, _mound_h(x, y) + r * 0.8), rnd.choice([mats["grit"], mats["break"], mats["pale"]]),
             squash=(1, 1, 0.6), subdiv=1, seed=rnd.randint(0, 9999), jitter=0.3)
