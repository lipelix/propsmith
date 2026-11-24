"""Three shallow slatted crates of vegetables standing on the ground: green cabbages on straw and a heap of red and
yellow apples side by side at the back, carrots with their green tops in front; a cabbage and two apples have rolled
out onto the ground."""
import math
import random

from mathutils import Euler, Matrix, Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# About 1.2 x 0.8 m, side by side so every load shows: two crates at the back, one in front.
CL, CW, CH = 0.54, 0.36, 0.19  # one crate: length (x), width (y), height
POST = 0.035  # corner posts
SLAT_T = 0.014
GAP = 0.012  # between the two slats of a side
# Where the crates stand: (x, y, z of the bottom, yaw in degrees).
CABBAGE_AT = (-0.3, 0.205, 0.0, 3)
APPLE_AT = (0.3, 0.21, 0.0, -3)
CARROT_AT = (-0.05, -0.2, 0.0, 4)

WOOD = (0.25, 0.165, 0.09)  # linear RGB: pale crate slats
WOOD_OLD = (0.2, 0.14, 0.085)
POST_WOOD = (0.15, 0.095, 0.05)
INSIDE = (0.08, 0.055, 0.035)
STRAW = (0.35, 0.27, 0.12)
CABBAGE = (0.22, 0.3, 0.1)
LEAF = (0.12, 0.22, 0.06)
APPLE = (0.36, 0.06, 0.035)
APPLE_YELLOW = (0.38, 0.27, 0.06)
STALK = (0.1, 0.06, 0.03)
CARROT = (0.45, 0.15, 0.03)
TOPS = (0.07, 0.17, 0.04)


def _frame(at):
    """The matrix that places a crate's local frame (origin at its base centre) at `at`."""
    x, y, z, yaw = at
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")


def _put(obj, m, local, rot=(0, 0, 0)):
    """Place `obj` at `local` in the frame `m`, its rotation `rot` (degrees) turned by the frame's yaw."""
    obj.location = m @ Vector(local)
    e = (Matrix.Rotation(m.to_euler().z, 4, "Z") @ Euler([math.radians(v) for v in rot]).to_matrix().to_4x4()).to_euler()
    obj.rotation_euler = e
    return obj


def _crate(prefix, at, rnd, mats):
    """A shallow crate of two slats per side on four corner posts and a plank bottom; returns its frame."""
    wood, old, post, inside = mats
    m = _frame(at)
    hx, hy = CL / 2, CW / 2
    _put(box(f"{prefix}_bottom", (CL - 0.01, CW - 0.01, 0.014), (0, 0, 0), old, bevel=0.004), m, (0, 0, 0.007))
    _put(box(f"{prefix}_inside", (CL - 2 * SLAT_T - 0.01, CW - 2 * SLAT_T - 0.01, 0.004), (0, 0, 0), inside, bevel=0),
         m, (0, 0, 0.016))
    for sx in (-1, 1):
        for sy in (-1, 1):
            _put(box(f"{prefix}_post_{sx}_{sy}", (POST, POST, CH), (0, 0, 0), post, bevel=0.005), m,
                 (sx * (hx - POST / 2), sy * (hy - POST / 2), CH / 2), (0, 0, rnd.uniform(-1.5, 1.5)))
    sh = (CH - GAP - 0.012) / 2  # slat height
    for k in range(2):
        z = 0.012 + sh * (k + 0.5) + GAP * k
        for s in (-1, 1):
            _put(box(f"{prefix}_long_{k}_{s}", (CL + 0.004, SLAT_T, sh), (0, 0, 0), (wood, old)[rnd.random() < 0.3],
                     bevel=0.004), m, (rnd.uniform(-0.004, 0.004), s * (hy + SLAT_T / 2 - 0.002), z),
                 (rnd.uniform(-0.6, 0.6), 0, 0))
            _put(box(f"{prefix}_end_{k}_{s}", (SLAT_T, CW - 2 * POST + 0.008, sh), (0, 0, 0), wood, bevel=0.004), m,
                 (s * (hx - SLAT_T / 2), 0, z), (0, rnd.uniform(-0.6, 0.6), 0))
    return m


def _heap(lx, ly, rise):
    """Height of a crate's heaped load above its rim at (lx, ly): highest in the middle."""
    u, v = lx / (CL / 2), ly / (CW / 2)
    return rise * max(0.0, 1 - u * u) * max(0.0, 1 - v * v)


@prop
def vegetable_crates():
    rnd = random.Random(17)
    wood = material("vegetable_crates_wood", WOOD, vary=0.25, scale=14)
    old = material("vegetable_crates_wood_old", WOOD_OLD, vary=0.3, scale=11)
    post = material("vegetable_crates_posts", POST_WOOD, vary=0.25, scale=12)
    inside = material("vegetable_crates_inside", INSIDE, vary=0.1, scale=4, crevice=0.2)
    straw = material("vegetable_crates_straw", STRAW, rough=0.95, vary=0.35, scale=30, crevice=0.6)
    cabbage = material("vegetable_crates_cabbage", CABBAGE, rough=0.6, vary=0.3, scale=18, crevice=0.7)
    leaf = material("vegetable_crates_leaf", LEAF, rough=0.6, vary=0.3, scale=14, crevice=0.6)
    apple = material("vegetable_crates_apple", APPLE, rough=0.45, vary=0.3, scale=16, crevice=0.5)
    yellow = material("vegetable_crates_apple_yellow", APPLE_YELLOW, rough=0.45, vary=0.3, scale=16, crevice=0.5)
    stalk = material("vegetable_crates_stalk", STALK, vary=0.2, scale=20)
    carrot = material("vegetable_crates_carrot", CARROT, rough=0.7, vary=0.25, scale=30, crevice=0.6)
    tops = material("vegetable_crates_tops", TOPS, rough=0.7, vary=0.3, scale=20, crevice=0.5)
    mats = (wood, old, post, inside)

    # The cabbage crate on the ground at the back: four heads on a bed of straw.
    m = _crate("cabbage_crate", CABBAGE_AT, rnd, mats)
    _put(blob("cabbage_straw", 0.24, (0, 0, 0), straw, squash=(1.05, 0.68, 0.25), subdiv=2, seed=2, jitter=0.15), m,
         (0, 0, CH - 0.07))
    for i, (lx, ly) in enumerate([(-0.13, -0.075), (0.12, -0.07), (-0.12, 0.075), (0.13, 0.08)]):
        r = rnd.uniform(0.078, 0.088)
        _put(blob(f"cabbage_{i}", r, (0, 0, 0), cabbage, squash=(1, 1, 0.88), subdiv=2, seed=10 + i, jitter=0.07), m,
             (lx, ly, CH - 0.07 + r * 0.6))
        _put(blob(f"cabbage_leaf_{i}", r * 0.8, (0, 0, 0), leaf, squash=(1.25, 1.1, 0.45), subdiv=1, seed=20 + i,
                  jitter=0.15), m, (lx, ly, CH - 0.07 + r * 0.25), (rnd.uniform(-10, 10), rnd.uniform(-10, 10), 0))

    # The apple crate beside the cabbages: a heap of red and a few yellow apples.
    m = _crate("apple_crate", APPLE_AT, rnd, mats)
    _put(blob("apple_fill", 0.24, (0, 0, 0), straw, squash=(1.05, 0.66, 0.2), subdiv=2, seed=3, jitter=0.06), m,
         (0, 0, CH - 0.06))
    rows = [(-0.2, -0.1), (-0.07, -0.1), (0.07, -0.1), (0.2, -0.1), (-0.14, 0.0), (0.0, 0.0), (0.14, 0.0),
            (-0.2, 0.1), (-0.07, 0.1), (0.07, 0.1), (0.2, 0.1), (-0.07, 0.04), (0.07, -0.04)]
    for i, (lx, ly) in enumerate(rows):
        lx += rnd.uniform(-0.012, 0.012)
        ly += rnd.uniform(-0.01, 0.01)
        r = rnd.uniform(0.034, 0.04)
        z = CH - 0.01 + _heap(lx, ly, 0.04) + (0.03 if i >= 11 else 0)
        mat = yellow if i in (2, 8, 12) else apple
        _put(blob(f"apple_{i}", r, (0, 0, 0), mat, squash=(1, 1, 0.9), subdiv=2, seed=40 + i, jitter=0.02), m,
             (lx, ly, z))
        if i % 3 == 0:
            _put(cylinder(f"apple_stalk_{i}", 0.003, 0.014, (0, 0, 0), stalk, segments=4, bevel=0), m,
                 (lx, ly, z + r * 0.8), (rnd.uniform(-20, 20), 0, 0))

    # The carrot crate in front: carrots lying roughly lengthwise on a heap, green tops towards the ends.
    m = _crate("carrot_crate", CARROT_AT, rnd, mats)
    _put(blob("carrot_fill", 0.24, (0, 0, 0), carrot, squash=(1.08, 0.66, 0.22), subdiv=2, seed=4, jitter=0.1), m,
         (0, 0, CH - 0.05))
    for i in range(14):
        row, col = divmod(i, 2)
        ly = -0.125 + row * 0.04 + rnd.uniform(-0.008, 0.008)
        side = 1 if (col + row) % 2 else -1
        lx = side * rnd.uniform(0.02, 0.06)
        length = rnd.uniform(0.15, 0.19)
        z = CH - 0.02 + _heap(lx, ly, 0.05) + 0.012
        yaw = rnd.uniform(-12, 12)
        # A carrot lies along x: its thick end at the outside, tapering towards the middle.
        root = cylinder(f"carrot_{i}", 0.017, length, (0, 0, 0), carrot, r_top=0.004, segments=6, bevel=0)
        _put(root, m, (lx + side * length * 0.5, ly, z), (0, -side * 90 + rnd.uniform(-8, 8), yaw))
        tuft = cylinder(f"carrot_top_{i}", 0.012, 0.07, (0, 0, 0), tops, r_top=0.022, segments=5, bevel=0)
        _put(tuft, m, (lx + side * (length * 0.5 + 0.005), ly, z + 0.004), (0, side * 90 + rnd.uniform(-15, 15), yaw))

    # A cabbage and two apples rolled out onto the ground.
    blob("stray_cabbage", 0.08, (0.43, -0.27, 0.07), cabbage, squash=(1, 1, 0.88), subdiv=2, seed=60, jitter=0.07)
    blob("stray_cabbage_leaf", 0.065, (0.43, -0.27, 0.025), leaf, squash=(1.25, 1.1, 0.4), subdiv=1, seed=61,
         jitter=0.15)
    for i, (x, y, mat) in enumerate([(-0.47, -0.22, apple), (-0.4, -0.31, yellow)]):
        blob(f"stray_apple_{i}", 0.037, (x, y, 0.033), mat, squash=(1, 1, 0.9), subdiv=2, seed=70 + i, jitter=0.02)
