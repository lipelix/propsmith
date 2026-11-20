"""A young broadleaf sapling about 2 m high: a thin, slightly crooked grey-brown stem with a small root flare, a few
slender branches rising from it, and a loose, open crown of fresh green pointed leaves in small clusters round dark
leafy cores, sky showing through."""
import math
import random

from mathutils import Quaternion, Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall dimensions (metres), from the description.
H = 2.0  # total height, top leaves
SPREAD = 1.0  # crown width
STEM = [  # the stem axis: (x, y, z, radius), a little crooked
    (0.0, 0.0, 0.0, 0.035),
    (0.02, 0.01, 0.6, 0.028),
    (-0.01, -0.02, 1.25, 0.02),
    (0.01, 0.0, 1.82, 0.009),
]
ROOT_N, ROOT_L, ROOT_R = 3, 0.12, 0.024
BRANCHES = 8  # from BRANCH_Z0 up to BRANCH_Z1
BRANCH_Z0, BRANCH_Z1 = 0.6, 1.6
BRANCH_R = 0.011
REACH = 0.36  # how far out a branch tip reaches, at most
LEAF_L = (0.1, 0.15)  # leaf length range
LEAF_T = 0.004
CORE_R = 0.085  # dark leafy core in a cluster

BARK = (0.15, 0.115, 0.085)  # linear RGB, smooth young grey-brown bark
TWIG = (0.16, 0.09, 0.055)  # reddish new twigs
LEAF_DARK = (0.035, 0.07, 0.018)
LEAF = (0.08, 0.15, 0.032)  # fresh green
LEAF_LIT = (0.17, 0.25, 0.05)


def _mats():
    return {
        "bark": material("sapling_young_bark", BARK, rough=0.8, vary=0.25, scale=30, crevice=0.5),
        "twig": material("sapling_young_twigs", TWIG, rough=0.8, vary=0.25, scale=40, crevice=0.5),
        "core": material("sapling_young_leaves_core", LEAF_DARK, rough=0.9, vary=0.3, scale=20, crevice=0.6),
        "leaf": material("sapling_young_leaves", LEAF, rough=0.7, vary=0.3, scale=30, crevice=0.4),
        "lit": material("sapling_young_leaves_lit", LEAF_LIT, rough=0.7, vary=0.25, scale=30, crevice=0.3),
    }


def _rot(d):
    """Euler (degrees) turning local +z onto direction `d` (for `cylinder`)."""
    d = Vector(d).normalized()
    pitch = math.degrees(math.acos(max(-1.0, min(1.0, d.z))))
    yaw = math.degrees(math.atan2(d.y, d.x))
    return (0, pitch, yaw)


def _branch(name, a, b, r0, r1, mat, segments=6):
    """A tapered cylinder from point `a` to point `b`."""
    a, b = Vector(a), Vector(b)
    return cylinder(name, r0, (b - a).length, a, mat, r_top=r1, segments=segments, rot=_rot(b - a), bevel=0)


def _axis(z):
    """Point on the stem axis at height `z` and the stem radius there."""
    for (x0, y0, z0, r0), (x1, y1, z1, r1) in zip(STEM, STEM[1:]):
        if z <= z1:
            t = (z - z0) / (z1 - z0)
            return Vector((x0 + t * (x1 - x0), y0 + t * (y1 - y0), z)), r0 + t * (r1 - r0)
    x, y, z1, r = STEM[-1]
    return Vector((x, y, z1)), r


def _leaf(name, at, facing, spin, length, mat):
    """A thin pointed leaf (a rhombus card) whose broad face looks along `facing`."""
    obj = box(name, (length, length * 0.55, LEAF_T), at, mat, bevel=0)
    for v in obj.data.vertices:
        if (v.co.x > 0) == (v.co.y > 0):
            v.co.y = 0.0
        else:
            v.co.x = 0.0
        if v.co.x < 0:
            v.co.x *= 0.3  # the stalk end is short, the tip long
    q = Vector(facing).normalized().to_track_quat("Z", "Y") @ Quaternion((0, 0, 1), math.radians(spin))
    obj.rotation_euler = q.to_euler("XYZ")
    return obj


def _cluster(name, at, out, n, mats, rnd, core=True):
    """A cluster of `n` leaves round point `at`, facing up and outwards along `out`, round a small dark core."""
    at = Vector(at)
    out = Vector(out)
    if core:
        blob(f"{name}_core", CORE_R * rnd.uniform(0.8, 1.1), at, mats["core"], squash=(1, 1, 0.75), subdiv=2,
             seed=rnd.randrange(1000), jitter=0.2)
    for i in range(n):
        a = math.radians(137.5 * i + rnd.uniform(-20, 20))
        rho = CORE_R * rnd.uniform(0.7, 1.7)
        dz = rnd.uniform(-0.6, 0.9) * CORE_R
        p = at + Vector((rho * math.cos(a), rho * math.sin(a), dz))
        radial = Vector((math.cos(a), math.sin(a), 0))
        facing = Vector((0, 0, 1)) + radial * rnd.uniform(0.3, 0.9) + out * 0.3
        mat = mats["lit"] if dz > 0 and rnd.random() < 0.65 else mats["leaf"] if rnd.random() < 0.8 else mats["core"]
        _leaf(f"{name}_leaf_{i}", p, facing, rnd.uniform(0, 360), rnd.uniform(*LEAF_L), mat)


@prop
def sapling_young():
    rnd = random.Random(7)
    mats = _mats()
    for i, (a, b) in enumerate(zip(STEM, STEM[1:])):
        _branch(f"sapling_young_stem_{i}", a[:3], (b[0], b[1], b[2] + 0.02), a[3], b[3],
                mats["bark" if i < 2 else "twig"], segments=10 if i < 2 else 6)
    for i in range(ROOT_N):
        yaw = 120 * i + rnd.uniform(-20, 20)
        tilt = rnd.uniform(105, 112)
        dz = math.cos(math.radians(tilt))
        flat = math.sqrt(1 - dz * dz)
        z0 = max(0.003 + 1.1 * 0.008 * flat - ROOT_L * dz, 0.003 + 1.1 * ROOT_R * flat)
        cylinder(f"sapling_young_root_{i}", ROOT_R, ROOT_L, (0, 0, z0), mats["bark"], r_top=0.008, segments=6,
                 rot=(tilt, 0, yaw), bevel=0)

    turn = rnd.uniform(0, 360)
    for i in range(BRANCHES):
        u = i / (BRANCHES - 1)
        z = BRANCH_Z0 + (BRANCH_Z1 - BRANCH_Z0) * u
        c, r = _axis(z)
        a = math.radians(turn + 137.5 * i + rnd.uniform(-12, 12))
        out = Vector((math.cos(a), math.sin(a), 0))
        reach = REACH * (1 - 0.4 * u) * rnd.uniform(0.85, 1.05)
        elbow = c + out * reach * 0.55 + Vector((0, 0, reach * 0.55))
        tip = c + out * reach + Vector((0, 0, reach * rnd.uniform(0.6, 0.85)))
        br = BRANCH_R * (1 - 0.3 * u)
        _branch(f"sapling_young_branch_{i}_a", c, elbow, br, br * 0.7, mats["twig"])
        _branch(f"sapling_young_branch_{i}_b", elbow, tip, br * 0.7, 0.003, mats["twig"], segments=5)
        _cluster(f"sapling_young_tip_{i}", tip, out, 26, mats, rnd)
        if u < 0.7:
            _cluster(f"sapling_young_mid_{i}", elbow + Vector((0, 0, 0.02)), out, 12, mats, rnd, core=False)
    top, _ = _axis(STEM[-1][2])
    _cluster("sapling_young_top", top + Vector((0, 0, 0.02)), Vector((0, 0, 0)), 28, mats, rnd)
