"""The snapped stump of the square crypt pillar (pillar_stone): its stepped base and the lowest drums, the next drum
broken off in a ragged, paler fresh break about 1.4 m up. The fallen drum lies on its side beside it on +x, one end
broken, with chips and grit scattered between them. The stump stands on the origin, so it replaces a pillar in place."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# The pillar's dimensions: keep them equal to pillar_stone's.
W = 0.7  # footprint of the plinth (x and y)
H = 3.0  # the whole pillar's height, for the drum height
SHAFT = 0.46
PLINTH_H = 0.16
STEP_W = 0.62
STEP_H = 0.1
TORUS_H = 0.08
NECK_H = 0.05
BELL_H = 0.14
ABACUS_H = 0.16
DRUMS = 5
JOINT = 0.012
SQRT2 = 2**0.5

STANDING = 2  # whole drums still standing
SNAP_H = 0.08  # the snapped drum's stub under the ragged break
BREAK_H = 0.12  # the slanted slab of the break
BREAK_TILT = 14  # degrees the break slopes
FALLEN_STUB = 0.22  # the stub of the next drum still on the fallen one
FALLEN_X = 0.62  # centre of the fallen piece (x, y)
FALLEN_Y = -0.04
FALLEN_TURN = 10  # degrees the fallen piece lies turned about z

# Crypt stone palette (shared with wall_crypt_* and pillar_stone): keep them equal.
STONE = (0.19, 0.195, 0.205)  # linear RGB: cool dark blue-grey ashlar
STONE_OLD = (0.145, 0.148, 0.155)
STONE_PALE = (0.24, 0.243, 0.25)
DAMP = (0.1, 0.11, 0.098)  # stone darkened by damp, a little green
MORTAR = (0.04, 0.04, 0.042)
BREAK = (0.29, 0.29, 0.288)  # the fresher, paler stone of the break


def _mats(prefix):
    return {
        "stone": material(f"{prefix}_stone", STONE, vary=0.22, scale=7, crevice=0.7),
        "old": material(f"{prefix}_stone_old", STONE_OLD, vary=0.25, scale=8, crevice=0.7),
        "pale": material(f"{prefix}_stone_pale", STONE_PALE, vary=0.2, scale=9, crevice=0.65),
        "damp": material(f"{prefix}_damp", DAMP, rough=0.6, vary=0.3, scale=5, crevice=0.75),
        "mortar": material(f"{prefix}_mortar", MORTAR, vary=0.12, scale=20, crevice=0.9),
        "break": material(f"{prefix}_break", BREAK, vary=0.3, scale=14, crevice=0.8),
    }


def _square(name, w_bottom, w_top, h, z, mat, twist=0.0):
    """A square frustum (a 4-sided cylinder turned 45 deg), `w_*` its side lengths, standing on z."""
    return cylinder(name, w_bottom / SQRT2, h, (0, 0, z), mat, r_top=w_top / SQRT2, segments=4, rot=(0, 0, 45 + twist),
                    bevel=0.014)


def _drum_h():
    shaft_bottom = PLINTH_H + STEP_H + TORUS_H
    shaft_top = H - ABACUS_H - BELL_H - NECK_H
    return (shaft_top - shaft_bottom) / DRUMS


def _rot(x, y, deg):
    a = math.radians(deg)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def stump(rnd, mats):
    box("plinth", (W, W, PLINTH_H), (0, 0, PLINTH_H / 2), mats["damp"], rot=(0, 0, rnd.uniform(-0.6, 0.6)), bevel=0.022)
    box("plinth_step", (STEP_W, STEP_W, STEP_H), (0, 0, PLINTH_H + STEP_H / 2), mats["damp"],
        rot=(0, 0, rnd.uniform(-0.6, 0.6)), bevel=0.018)
    z = PLINTH_H + STEP_H
    _square("base_chamfer", SHAFT + 0.12, SHAFT + 0.01, TORUS_H, z, mats["old"], rnd.uniform(-0.5, 0.5))
    z += TORUS_H
    h = _drum_h()
    top = z + STANDING * h + SNAP_H
    box("core", (SHAFT - 0.04, SHAFT - 0.04, top - z), (0, 0, (z + top) / 2), mats["mortar"], bevel=0)
    for i in range(STANDING):
        mat = mats["damp"] if i == 0 else mats["stone"]
        w = SHAFT * rnd.uniform(0.985, 1.0)
        box(f"drum_{i}", (w, w, h - JOINT), (0, 0, z + i * h + h / 2), mat,
            rot=(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(-1.0, 1.0)), bevel=0.022)
    # The stub of the snapped drum, its top a slanted break rising to the back (-x, +y), jagged shards on the high side.
    z0 = z + STANDING * h + JOINT / 2
    box("snap_stub", (SHAFT * 0.995, SHAFT * 0.995, SNAP_H), (0, 0, z0 + SNAP_H / 2), mats["old"],
        rot=(0, 0, rnd.uniform(-1.0, 1.0)), bevel=0.02)
    box("break_slope", (SHAFT * 0.96, SHAFT * 0.96, BREAK_H), (0, 0, z0 + SNAP_H + BREAK_H / 2 - 0.05), mats["break"],
        rot=(-BREAK_TILT * 0.6, -BREAK_TILT, rnd.uniform(-3, 3)), bevel=0.012)
    shards = [(-0.12, 0.11, 0.12, 0.05), (-0.13, -0.07, 0.1, 0.03), (0.04, 0.13, 0.09, 0.02), (-0.03, 0.01, 0.07, 0.0)]
    for i, (sx, sy, r, up) in enumerate(shards):
        blob(f"shard_{i}", r, (sx, sy, z0 + SNAP_H + BREAK_H / 2 + up), mats["break"], squash=(0.9, 0.9, 0.8),
             subdiv=1, seed=rnd.randint(0, 9999), jitter=0.3)
    return z0 + SNAP_H


def fallen(rnd, mats):
    """The fallen piece on its side, its length along y and turned a little: a whole drum and the snapped stub of the
    next one, a dark joint between them and a jagged break at the stub's end (-y)."""
    h = _drum_h() - JOINT
    total = h + JOINT + FALLEN_STUB
    cx, cy = FALLEN_X, FALLEN_Y

    def at(v, u=0.0, z=SHAFT / 2):
        ox, oy = _rot(u, v, FALLEN_TURN)
        return cx + ox, cy + oy, z

    y0 = total / 2  # the whole drum at +y, the broken stub towards -y
    box("fallen_core", (SHAFT - 0.04, total - 0.04, SHAFT - 0.04), at(0), mats["mortar"], rot=(0, 0, FALLEN_TURN),
        bevel=0)
    box("fallen_drum", (SHAFT, h, SHAFT), at(y0 - h / 2), mats["stone"], rot=(0, 0, FALLEN_TURN), bevel=0.022)
    box("fallen_stub", (SHAFT * 0.99, FALLEN_STUB, SHAFT * 0.99), at(y0 - h - JOINT - FALLEN_STUB / 2), mats["old"],
        rot=(0, 0, FALLEN_TURN + 0.8), bevel=0.02)
    end = -total / 2
    for i, (u, w, r, out) in enumerate([(-0.12, 0.1, 0.12, 0.05), (0.1, 0.12, 0.1, 0.03), (0.02, -0.07, 0.1, 0.04)]):
        blob(f"fallen_shard_{i}", r, at(end - out + r * 0.5, u, SHAFT / 2 + w), mats["break"],
             squash=(1.0, 0.7, 1.0), subdiv=1, seed=rnd.randint(0, 9999), jitter=0.3)


def debris(rnd, mats):
    """Chips and grit on the floor round the break, most of it between stump and drum."""
    spots = [(0.42, -0.42), (0.38, 0.4), (0.86, -0.4), (0.84, 0.44), (-0.1, -0.44), (0.25, -0.5), (-0.5, 0.2)]
    for i, (x, y) in enumerate(spots):
        s = rnd.uniform(0.07, 0.12)
        d = rnd.uniform(0.05, 0.1)
        box(f"chip_{i}", (s, d, s * 0.6), (x, y, s * 0.3), rnd.choice([mats["break"], mats["stone"], mats["old"]]),
            rot=(0, 0, rnd.uniform(0, 90)), bevel=0.01)
    for i in range(16):
        x, y = rnd.uniform(-0.55, 0.88), rnd.uniform(-0.5, 0.5)
        if abs(x) < W / 2 + 0.02 and abs(y) < W / 2 + 0.02:
            continue  # not on the plinth
        r = rnd.uniform(0.018, 0.035)
        blob(f"grit_{i}", r, (x, y, r * 0.5), rnd.choice([mats["break"], mats["pale"]]), squash=(1, 1, 0.5), subdiv=1,
             seed=rnd.randint(0, 9999), jitter=0.25)


@prop
def pillar_stone_broken():
    rnd = random.Random(53)
    mats = _mats("pillar_stone_broken")
    stump(rnd, mats)
    fallen(rnd, mats)
    debris(rnd, mats)
