"""A square crypt pillar of dark dressed stone, about 0.7 x 0.7 x 3 m: a two-step moulded base, a square shaft of
five stacked drums with worn joints, and a capital of a chamfered bell under a broad square abacus. Same cool blue-grey
ashlar as the crypt wall kit, damp-darkened near the floor."""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder

W = 0.7  # footprint of the plinth and the abacus (x and y)
H = 3.0  # overall height
SHAFT = 0.46  # shaft width
PLINTH_H = 0.16
STEP_W = 0.62  # second, narrower plinth course
STEP_H = 0.1
TORUS_H = 0.08  # chamfered step between plinth and shaft
NECK_H = 0.05  # band round the top of the shaft
BELL_H = 0.14  # chamfered bell under the abacus
ABACUS_H = 0.16
DRUMS = 5
JOINT = 0.012  # gap between drums, the dark core shows through
SQRT2 = 2**0.5

# Crypt stone palette (shared with wall_crypt_* and pillar_stone_broken): keep them equal.
STONE = (0.19, 0.195, 0.205)  # linear RGB: cool dark blue-grey ashlar
STONE_OLD = (0.145, 0.148, 0.155)
STONE_PALE = (0.24, 0.243, 0.25)
DAMP = (0.1, 0.11, 0.098)  # stone darkened by damp, a little green
MORTAR = (0.04, 0.04, 0.042)
CAP = (0.165, 0.17, 0.182)


def _mats(prefix):
    return {
        "stone": material(f"{prefix}_stone", STONE, vary=0.22, scale=7, crevice=0.7),
        "old": material(f"{prefix}_stone_old", STONE_OLD, vary=0.25, scale=8, crevice=0.7),
        "pale": material(f"{prefix}_stone_pale", STONE_PALE, vary=0.2, scale=9, crevice=0.65),
        "damp": material(f"{prefix}_damp", DAMP, rough=0.6, vary=0.3, scale=5, crevice=0.75),
        "mortar": material(f"{prefix}_mortar", MORTAR, vary=0.12, scale=20, crevice=0.9),
        "cap": material(f"{prefix}_cap", CAP, vary=0.22, scale=7, crevice=0.7),
    }


def _square(name, w_bottom, w_top, h, z, mat, twist=0.0):
    """A square frustum (a 4-sided cylinder turned 45 deg), `w_*` its side lengths, standing on z."""
    return cylinder(name, w_bottom / SQRT2, h, (0, 0, z), mat, r_top=w_top / SQRT2, segments=4, rot=(0, 0, 45 + twist),
                    bevel=0.014)


def base(rnd, mats):
    """Plinth and chamfered step; returns the height the shaft starts at."""
    box("plinth", (W, W, PLINTH_H), (0, 0, PLINTH_H / 2), mats["damp"], rot=(0, 0, rnd.uniform(-0.6, 0.6)), bevel=0.022)
    box("plinth_step", (STEP_W, STEP_W, STEP_H), (0, 0, PLINTH_H + STEP_H / 2), mats["damp"],
        rot=(0, 0, rnd.uniform(-0.6, 0.6)), bevel=0.018)
    z = PLINTH_H + STEP_H
    _square("base_chamfer", SHAFT + 0.12, SHAFT + 0.01, TORUS_H, z, mats["old"], rnd.uniform(-0.5, 0.5))
    return z + TORUS_H


def drum(rnd, mats, i, z0, h, prefix="drum"):
    """One shaft drum, a slightly uneven ashlar block standing on z0."""
    mat = mats["damp"] if i == 0 else rnd.choice([mats["stone"], mats["stone"], mats["old"], mats["pale"]])
    w = SHAFT * rnd.uniform(0.985, 1.0)
    box(f"{prefix}_{i}", (w, w, h - JOINT), (rnd.uniform(-0.004, 0.004), rnd.uniform(-0.004, 0.004), z0 + h / 2), mat,
        rot=(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(-1.0, 1.0)), bevel=rnd.uniform(0.018, 0.026))


@prop
def pillar_stone():
    rnd = random.Random(52)
    mats = _mats("pillar_stone")
    z = base(rnd, mats)
    top = H - ABACUS_H - BELL_H - NECK_H
    # The dark core behind the joints.
    box("core", (SHAFT - 0.04, SHAFT - 0.04, top - z), (0, 0, (z + top) / 2), mats["mortar"], bevel=0)
    h = (top - z) / DRUMS
    for i in range(DRUMS):
        drum(rnd, mats, i, z + i * h, h)
    box("neck", (SHAFT + 0.04, SHAFT + 0.04, NECK_H), (0, 0, top + NECK_H / 2), mats["cap"],
        rot=(0, 0, rnd.uniform(-0.6, 0.6)), bevel=0.014)
    _square("bell", SHAFT + 0.01, W - 0.06, BELL_H, top + NECK_H, mats["cap"], rnd.uniform(-0.5, 0.5))
    box("abacus", (W, W, ABACUS_H), (0, 0, H - ABACUS_H / 2), mats["cap"], rot=(0, 0, rnd.uniform(-0.6, 0.6)),
        bevel=0.022)
