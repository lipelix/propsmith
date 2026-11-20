"""A slender white birch about 6 m high: a thin, gently curving chalk-white trunk with black horizontal bark marks and
a dark fissured foot, thin ascending branches that arch out at the tips, and a narrow airy crown of small
yellow-green leaf clumps with sky between them, some hanging from the branch tips."""
import math
import random

from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall dimensions (metres), from the description.
H = 6.0  # total height, top of the crown
SPREAD = 2.0  # crown width
TRUNK = [  # the trunk axis: (x, y, z, radius); a gentle S curve
    (0.0, 0.0, 0.0, 0.15),
    (0.03, -0.02, 1.2, 0.125),
    (0.0, -0.05, 2.5, 0.1),
    (-0.06, -0.02, 3.7, 0.075),
    (-0.04, 0.03, 4.8, 0.05),
    (0.0, 0.02, 5.55, 0.025),
]
FOOT_H = 0.5  # height of the dark fissured bark at the foot
ROOT_N, ROOT_L, ROOT_R = 4, 0.35, 0.09
MARKS = 46  # black lenticel marks on the white bark
BRANCHES = 12  # main branches, from BRANCH_Z0 up to BRANCH_Z1
BRANCH_Z0, BRANCH_Z1 = 2.3, 5.0
BRANCH_R = 0.04  # branch radius where it leaves the trunk
REACH = 0.78  # how far out a branch tip reaches, at most
CLUMP_R = 0.29  # radius of a leaf clump

BARK = (0.5, 0.48, 0.43)  # linear RGB, chalky off-white birch bark
BARK_SHADE = (0.36, 0.34, 0.3)
MARK = (0.035, 0.032, 0.03)  # the black horizontal marks
FOOT = (0.075, 0.068, 0.06)  # dark fissured bark at the foot
TWIG = (0.12, 0.08, 0.06)  # thin red-brown twigs
LEAF_DARK = (0.055, 0.085, 0.022)
LEAF = (0.12, 0.17, 0.04)  # light yellow-green birch leaves
LEAF_LIT = (0.3, 0.33, 0.07)


def _mats():
    return {
        "bark": material("birch_tree_bark", BARK, rough=0.85, vary=0.2, scale=8, crevice=0.6),
        "shade": material("birch_tree_bark_shade", BARK_SHADE, rough=0.9, vary=0.25, scale=10, crevice=0.6),
        "mark": material("birch_tree_marks", MARK, rough=0.9, vary=0.2, scale=20),
        "foot": material("birch_tree_foot", FOOT, rough=1.0, vary=0.4, scale=18, crevice=0.85),
        "twig": material("birch_tree_twigs", TWIG, rough=0.9, vary=0.3, scale=14, crevice=0.6),
        "core": material("birch_tree_leaves_core", LEAF_DARK, rough=0.9, vary=0.3, scale=9, crevice=0.7),
        "leaf": material("birch_tree_leaves", LEAF, rough=0.85, vary=0.35, scale=12, crevice=0.55),
        "lit": material("birch_tree_leaves_lit", LEAF_LIT, rough=0.8, vary=0.3, scale=12, crevice=0.45),
    }


def _roughen(obj, rnd, amount, ridges=0.0):
    """Seeded radial jitter of the vertices; with `ridges`, alternate vertices pushed in: bark fissures."""
    for i, v in enumerate(obj.data.vertices):
        r = math.hypot(v.co.x, v.co.y)
        if r > 1e-4:
            k = 1 + rnd.uniform(-amount, amount) - (ridges if i % 2 else 0)
            v.co.x *= k
            v.co.y *= k


def _branch(name, a, b, r0, r1, mat, rnd, segments=6, rough=0.06):
    """A tapered cylinder from point `a` to point `b`."""
    d = [b[i] - a[i] for i in range(3)]
    length = math.sqrt(sum(c * c for c in d))
    pitch = math.degrees(math.acos(max(-1.0, min(1.0, d[2] / length))))
    yaw = math.degrees(math.atan2(d[1], d[0]))
    c = cylinder(name, r0, length, a, mat, r_top=r1, segments=segments, rot=(0, pitch, yaw), bevel=0)
    _roughen(c, rnd, rough)
    return c


def _axis(z):
    """Point on the trunk axis at height `z` and the trunk radius there."""
    for (x0, y0, z0, r0), (x1, y1, z1, r1) in zip(TRUNK, TRUNK[1:]):
        if z <= z1:
            t = (z - z0) / (z1 - z0)
            return Vector((x0 + t * (x1 - x0), y0 + t * (y1 - y0), z)), r0 + t * (r1 - r0)
    x, y, z1, r = TRUNK[-1]
    return Vector((x, y, z1)), r


def _trunk(mats, rnd):
    for i, (a, b) in enumerate(zip(TRUNK, TRUNK[1:])):
        _branch(f"birch_tree_trunk_{i}", a[:3], (b[0], b[1], b[2] + 0.04), a[3], b[3], mats["bark"], rnd,
                segments=12 if i < 3 else 8, rough=0.025)
    # The dark, deeply fissured foot, a sleeve over the white bark that frays upwards.
    foot = cylinder("birch_tree_foot", TRUNK[0][3] * 1.12, FOOT_H, (0, 0, 0), mats["foot"], r_top=TRUNK[0][3] * 0.98,
                    segments=14, bevel=0)
    _roughen(foot, rnd, 0.05, ridges=0.08)
    for i in range(8):
        a = math.radians(45 * i + rnd.uniform(-20, 20))
        z = FOOT_H + rnd.uniform(-0.05, 0.12)
        c, r = _axis(z)
        h = rnd.uniform(0.18, 0.4)
        p = (c.x + r * math.cos(a), c.y + r * math.sin(a), z)
        box(f"birch_tree_fissure_{i}", (0.022, 0.05, h), p, mats["foot"], rot=(0, 0, math.degrees(a)), bevel=0.004)
    for i in range(ROOT_N):
        yaw = 360 * i / ROOT_N + rnd.uniform(-20, 20)
        tilt = rnd.uniform(100, 106)
        length = ROOT_L * rnd.uniform(0.8, 1.15)
        r, r_top = ROOT_R * rnd.uniform(0.85, 1.1), 0.03
        dz = math.cos(math.radians(tilt))
        flat = math.sqrt(1 - dz * dz)
        z0 = max(0.003 + 1.1 * r_top * flat - length * dz, 0.003 + 1.1 * r * flat)
        root = cylinder(f"birch_tree_root_{i}", r, length, (0, 0, z0), mats["foot"], r_top=r_top, segments=8,
                        rot=(tilt, 0, yaw), bevel=0)
        _roughen(root, rnd, 0.1)


def _marks(mats, rnd):
    """Black horizontal lenticel dashes wrapping part way round the white trunk, denser low down."""
    for i in range(MARKS):
        z = FOOT_H + 0.15 + (4.6 - FOOT_H) * (rnd.random() ** 1.4)
        c, r = _axis(z)
        a = rnd.uniform(0, 2 * math.pi)
        w = min(r * rnd.uniform(0.5, 1.0), 0.09)
        h = rnd.uniform(0.012, 0.03)
        p = (c.x + r * math.cos(a), c.y + r * math.sin(a), z)
        box(f"birch_tree_mark_{i}", (0.014, w, h), p, mats["mark"], rot=(0, 0, math.degrees(a)), bevel=0)
    # A few greyed, peeling patches.
    for i in range(6):
        z = rnd.uniform(1.0, 3.8)
        c, r = _axis(z)
        a = rnd.uniform(0, 2 * math.pi)
        p = (c.x + r * 0.96 * math.cos(a), c.y + r * 0.96 * math.sin(a), z)
        box(f"birch_tree_patch_{i}", (0.012, r * 0.9, rnd.uniform(0.08, 0.16)), p, mats["shade"],
            rot=(0, 0, math.degrees(a)), bevel=0.003)


def _clump(name, at, r, mats, rnd, seed, hang=False):
    """A small leaf clump: a dark core, a mid-green lump beside it and a lit lump on top; hanging ones are longer."""
    sq = (0.85, 0.85, 1.45) if hang else (1, 1, 0.8)
    blob(f"{name}_core", r, at, mats["core"], squash=sq, subdiv=2, seed=seed, jitter=0.16)
    x, y, z = at
    d = math.hypot(x, y) or 1.0
    ox, oy = x / d, y / d
    blob(f"{name}_leaf", r * 0.7, (x - oy * r * 0.4, y + ox * r * 0.4, z - r * 0.1), mats["leaf"], squash=sq,
         subdiv=1, seed=seed + 1, jitter=0.22)
    blob(f"{name}_lit", r * 0.7, (x + ox * r * 0.25, y + oy * r * 0.25, z + r * (0.55 if hang else 0.35)),
         mats["lit"], squash=sq, subdiv=1, seed=seed + 2, jitter=0.22)


@prop
def birch_tree():
    rnd = random.Random(23)
    mats = _mats()
    _trunk(mats, rnd)
    _marks(mats, rnd)

    turn = rnd.uniform(0, 360)
    n = 0
    for i in range(BRANCHES):
        u = i / (BRANCHES - 1)
        z = BRANCH_Z0 + (BRANCH_Z1 - BRANCH_Z0) * u
        c, r = _axis(z)
        a = math.radians(turn + 137.5 * i + rnd.uniform(-15, 15))
        ca, sa = math.cos(a), math.sin(a)
        reach = REACH * (1 - 0.45 * u) * rnd.uniform(0.85, 1.05)
        start = (c.x + ca * r * 0.4, c.y + sa * r * 0.4, z)
        # Ascending, then arching out and a little down at the tip.
        elbow = (c.x + ca * reach * 0.55, c.y + sa * reach * 0.55, z + reach * rnd.uniform(0.75, 1.0))
        tip = (c.x + ca * reach, c.y + sa * reach, elbow[2] + rnd.uniform(-0.12, 0.05))
        br = BRANCH_R * (1 - 0.4 * u)
        _branch(f"birch_tree_branch_{i}_a", start, elbow, br, br * 0.6, mats["bark"], rnd)
        _branch(f"birch_tree_branch_{i}_b", elbow, tip, br * 0.6, 0.008, mats["twig"], rnd, segments=5)
        cr = CLUMP_R * (1 - 0.3 * u) * rnd.uniform(0.85, 1.05)
        _clump(f"birch_tree_clump_{n}", elbow, cr * 0.9, mats, rnd, 100 + 3 * n)
        n += 1
        if u < 0.8:
            _clump(f"birch_tree_clump_{n}", (tip[0], tip[1], tip[2] - cr * 0.6), cr, mats, rnd, 100 + 3 * n,
                   hang=True)
            n += 1
    # Clumps hugging the upper trunk fill the narrow crown, and one tops it.
    for i in range(6):
        z = 3.0 + 0.45 * i
        c, r = _axis(z)
        a = math.radians(turn + 70 + 150 * i)
        d = 0.18 + rnd.uniform(0, 0.1)
        _clump(f"birch_tree_clump_{n}", (c.x + d * math.cos(a), c.y + d * math.sin(a), z), CLUMP_R * 0.85, mats, rnd,
               100 + 3 * n)
        n += 1
    top, _ = _axis(5.55)
    _clump("birch_tree_top", (top.x, top.y, H - CLUMP_R * 0.75 - 0.05), CLUMP_R * 0.75, mats, rnd, 400)
