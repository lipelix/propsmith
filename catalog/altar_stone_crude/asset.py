"""A crude altar of rough unhewn stone, about 1.5 x 0.9 m and 1 m high: two rough uprights of dark crypt stone under
a thick flattish capstone boulder, packed with smaller stones between them, every face broken by faceted lumps, the top and the front
streaked with old dark stains that ran down the faces and dried in a pool at its foot. Same stone palette as the
crypt wall kit."""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box

L, W, H = 1.5, 0.9, 1.0  # overall length (x), depth (y), height
CORE_X, CORE_Y = 0.62, 0.33  # half extents of the stone under the lumps
UP_X, UP_W = 0.42, 0.4  # uprights: centre x (each side) and width
CAP_R, CAP_SQUASH = 0.72, (1.0, 0.6, 0.2)  # the capstone boulder: radius and squash
CAP_JITTER = 0.05
CAP_HX, CAP_HY, CAP_HZ = (CAP_R * s for s in CAP_SQUASH)  # its half extents before jitter
CAP_C = H - 0.012 - CAP_HZ * (1 + CAP_JITTER)  # centre height of the capstone
CAP_Z = CAP_C - CAP_HZ * 0.55  # where the uprights end, inside the capstone
JITTER = 0.15  # blob jitter: a lump reaches (1 + JITTER) times its radius

STONE = (0.19, 0.195, 0.205)  # linear RGB: cool dark blue-grey (crypt wall kit)
STONE_OLD = (0.145, 0.148, 0.155)
STONE_PALE = (0.24, 0.243, 0.25)
DAMP = (0.1, 0.11, 0.098)
GRIT = (0.17, 0.162, 0.152)
STAIN = (0.034, 0.017, 0.015)  # old dried blood, nearly black
STAIN_RUN = (0.048, 0.022, 0.018)


def _cap_top(x, y):
    """Height of the capstone's (unjittered) top surface at (x, y)."""
    q = 1 - (x / CAP_HX) ** 2 - (y / CAP_HY) ** 2
    return CAP_C + CAP_HZ * max(q, 0) ** 0.5


def _mats(prefix):
    return {
        "stone": material(f"{prefix}_stone", STONE, vary=0.3, scale=4, crevice=0.75),
        "old": material(f"{prefix}_stone_old", STONE_OLD, vary=0.3, scale=5, crevice=0.75),
        "pale": material(f"{prefix}_stone_pale", STONE_PALE, vary=0.25, scale=6, crevice=0.7),
        "damp": material(f"{prefix}_damp", DAMP, rough=0.6, vary=0.3, scale=5, crevice=0.75),
        "grit": material(f"{prefix}_grit", GRIT, vary=0.35, scale=30, crevice=0.85),
        "stain": material(f"{prefix}_stain", STAIN, rough=0.4, vary=0.3, scale=9, crevice=0.3),
        "run": material(f"{prefix}_stain_run", STAIN_RUN, rough=0.45, vary=0.35, scale=12, crevice=0.3),
    }


def _lump(name, r, at, mat, squash, seed, subdiv=1, yaw=0.0, jitter=JITTER):
    """A faceted lump of stone, squashed along its axes as given (blob's own random yaw is replaced by `yaw`)."""
    obj = blob(name, r, at, mat, squash=squash, subdiv=subdiv, seed=seed, jitter=jitter)
    obj.rotation_euler = (0, 0, yaw)
    return obj


@prop
def altar_stone_crude():
    rnd = random.Random(631)
    m = _mats("altar_stone_crude")
    rock = ["stone", "old", "damp", "pale"]

    # Two rough uprights: a boulder each round a flat-footed core, with the packing between them.
    for side in (-1, 1):
        h = 0.22  # a flat footing under the boulder
        box(f"upright_{side}_foot", (UP_W - 0.04, 2 * CORE_Y - 0.06, h), (side * UP_X, 0, h / 2),
            m["old" if side > 0 else "stone"], rot=(0, 0, side * 2.5), bevel=0.05)
        r = 0.5
        sz = 0.82
        _lump(f"upright_{side}", r, (side * UP_X, 0, r * sz * (1 + JITTER) - 0.02), m["stone" if side > 0 else "old"],
              (UP_W / 2 / r * 1.0, CORE_Y / r * 1.0, sz), rnd.randint(0, 9999), subdiv=2, yaw=side * 0.05)
    box("infill", (2 * (UP_X - UP_W / 2) + 0.06, 2 * CORE_Y - 0.14, CAP_Z), (0, 0.04, CAP_Z / 2), m["damp"],
        bevel=0.04)
    for j in range(4):
        r = rnd.uniform(0.09, 0.11)
        z = 0.12 + j * 0.15
        _lump(f"pack_{j}", r, (rnd.uniform(-0.1, 0.1), -CORE_Y + 0.09, z), m[rnd.choice(rock)], (1.2, 0.6, 0.8),
              rnd.randint(0, 9999))
    # A few faceted lumps on the ends and fronts break the outline further.
    for side in (-1, 1):
        for j in range(2):
            r = rnd.uniform(0.13, 0.16)
            _lump(f"end_{side}_{j}", r, (side * (CORE_X - 0.08), rnd.uniform(-0.15, 0.15), 0.2 + j * 0.3),
                  m[rnd.choice(rock)], (0.5, 1.1, 0.85), rnd.randint(0, 9999))
            _lump(f"face_{side}_{j}", r * 0.9, (side * (UP_X + rnd.uniform(-0.06, 0.06)), -(CORE_Y - 0.06),
                  0.18 + j * 0.34), m[rnd.choice(rock)], (1.1, 0.5, 0.85), rnd.randint(0, 9999))

    # The capstone: a broad, flattish boulder, a few lumps on its rim.
    _lump("capstone", CAP_R, (0, 0, CAP_C), m["stone"], CAP_SQUASH, 4, subdiv=3, yaw=0.03, jitter=CAP_JITTER)
    for j, (x, y) in enumerate([(-0.5, -0.24), (0.15, -0.36), (0.55, 0.22), (-0.3, 0.33)]):
        _lump(f"cap_lump_{j}", 0.1, (x, y, CAP_C), m[rnd.choice(["old", "pale"])], (1.3, 0.8, 0.7),
              rnd.randint(0, 9999))

    # Old stains: dark splashes on the top, short runs over the capstone's front rim, long drips down the uprights'
    # fronts (-y) and a dried pool at the foot.
    for j in range(9):
        x, y = rnd.uniform(-0.3, 0.3), rnd.uniform(-0.24, 0.1)
        r = rnd.uniform(0.05, 0.12)
        _lump(f"stain_top_{j}", r, (x, y, _cap_top(x, y) + 0.003), m["stain" if j % 3 else "run"], (1.3, 0.8, 0.12),
              rnd.randint(0, 9999), subdiv=2, yaw=rnd.uniform(0, 3))
    for j, x in enumerate([-0.12, 0.08, 0.3]):
        y = -CAP_HY * (1 - (x / CAP_HX) ** 2) ** 0.5
        _lump(f"stain_run_{j}", 0.035, (x, y - 0.004, CAP_C), m["run"], (0.8, 0.3, 2.2), rnd.randint(0, 9999))
    for j, (x, length) in enumerate([(-0.36, 0.42), (0.3, 0.5), (0.48, 0.3)]):
        _lump(f"stain_drip_{j}", 0.035, (x, -CORE_Y * 1.1, CAP_Z - length / 2), m["run"], (0.8, 0.3, length / 0.07),
              rnd.randint(0, 9999))
    for j, (x, y, r) in enumerate([(0.3, -0.4, 0.09), (0.16, -0.42, 0.07), (0.38, -0.36, 0.06), (-0.36, -0.4, 0.06)]):
        _lump(f"stain_pool_{j}", r, (x, y, 0.003), m["stain"], (1.3, 0.8, 0.05), rnd.randint(0, 9999), subdiv=2,
              yaw=rnd.uniform(0, 3), jitter=0.3)

    # Grit and chips round the foot.
    for j in range(14):
        x = rnd.uniform(-0.7, 0.7)
        y = rnd.choice([-1, 1]) * rnd.uniform(0.37, 0.42)
        r = rnd.uniform(0.02, 0.04)
        blob(f"grit_{j}", r, (x, y, r * 0.55), m[rnd.choice(["grit", "pale", "old"])], squash=(1, 1, 0.6), subdiv=1,
             seed=rnd.randint(0, 9999), jitter=0.3)
