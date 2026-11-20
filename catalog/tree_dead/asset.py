"""A bare dead snag about 5 m high: a leaning grey trunk stripped of most of its bark, with flared roots, the last
dark bark clinging to its foot, long cracks in the silvered wood, a jagged splintered top where the crown broke off,
two crooked bare limbs reaching up with forked twigs, three snapped limb stubs with pale breaks, woodpecker holes and a
few shelf fungi."""
import math
import random

from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall dimensions (metres), from the description.
H = 5.0  # total height, tip of the highest limb
TRUNK = [  # the trunk axis: (x, y, z, radius), leaning a little, to the broken top
    (0.0, 0.0, 0.01, 0.27),  # lifted: the tilted first segment's base would dip
    (0.04, 0.02, 1.3, 0.22),
    (0.1, -0.02, 2.6, 0.17),
    (0.08, -0.06, 3.7, 0.13),
]
BARK_H = 0.9  # the last bark clings up to about here
ROOT_N, ROOT_L, ROOT_R = 6, 0.6, 0.15
SPLINTERS = 9  # jagged splinters round the broken top
SPLINTER_L = (0.15, 0.55)
LIMBS = [  # crooked bare limbs: start height, direction (degrees), and the bend points (x, y, z) from the trunk out
    (2.4, [(-0.35, 0.1, 3.1), (-0.62, 0.22, 3.9), (-0.7, 0.3, 4.95)]),
    (2.0, [(0.5, -0.25, 2.35), (0.85, -0.42, 2.8), (0.92, -0.55, 3.35)]),
    (3.15, [(0.0, 0.42, 3.55), (-0.08, 0.78, 3.8)]),
]
LIMB_R = 0.085  # limb radius where it leaves the trunk
STUBS = [(1.55, 200, 0.075, 0.3), (2.85, 320, 0.06, 0.22), (3.3, 80, 0.05, 0.35)]  # height, yaw, radius, length

WOOD = (0.28, 0.255, 0.22)  # linear RGB, silvered weathered wood
WOOD_DARK = (0.15, 0.14, 0.125)
BARK = (0.07, 0.055, 0.042)  # the last dark bark
CRACK = (0.04, 0.036, 0.032)
BREAK = (0.36, 0.3, 0.21)  # paler wood in a fresher break
ROT = (0.1, 0.075, 0.05)  # rotten heart wood
FUNGUS = (0.3, 0.22, 0.13)
FUNGUS_RIM = (0.42, 0.37, 0.28)


def _mats():
    return {
        "wood": material("tree_dead_wood", WOOD, rough=0.95, vary=0.35, scale=12, crevice=0.8),
        "dark": material("tree_dead_wood_dark", WOOD_DARK, rough=0.95, vary=0.35, scale=14, crevice=0.8),
        "bark": material("tree_dead_bark", BARK, rough=1.0, vary=0.4, scale=18, crevice=0.85),
        "crack": material("tree_dead_crack", CRACK, rough=1.0, vary=0.2, scale=20),
        "break": material("tree_dead_break", BREAK, rough=0.95, vary=0.3, scale=16, crevice=0.6),
        "rot": material("tree_dead_rot", ROT, rough=1.0, vary=0.35, scale=14, crevice=0.7),
        "fungus": material("tree_dead_fungus", FUNGUS, rough=0.85, vary=0.3, scale=30, crevice=0.6),
        "rim": material("tree_dead_fungus_rim", FUNGUS_RIM, rough=0.85, vary=0.25, scale=30),
    }


def _roughen(obj, rnd, amount, ridges=0.0):
    """Seeded radial jitter of the vertices; with `ridges`, alternate vertices pushed in: furrows."""
    for i, v in enumerate(obj.data.vertices):
        r = math.hypot(v.co.x, v.co.y)
        if r > 1e-4:
            k = 1 + rnd.uniform(-amount, amount) - (ridges if i % 2 else 0)
            v.co.x *= k
            v.co.y *= k


def _rot(d):
    """Euler (degrees) turning local +z onto direction `d` (for `cylinder`)."""
    d = Vector(d).normalized()
    pitch = math.degrees(math.acos(max(-1.0, min(1.0, d.z))))
    yaw = math.degrees(math.atan2(d.y, d.x))
    return (0, pitch, yaw)


def _branch(name, a, b, r0, r1, mat, rnd, segments=8, rough=0.07, ridges=0.0):
    """A tapered cylinder from point `a` to point `b`."""
    a, b = Vector(a), Vector(b)
    c = cylinder(name, r0, (b - a).length, a, mat, r_top=r1, segments=segments, rot=_rot(b - a), bevel=0)
    _roughen(c, rnd, rough, ridges)
    return c


def _axis(z):
    """Point on the trunk axis at height `z` and the trunk radius there."""
    for (x0, y0, z0, r0), (x1, y1, z1, r1) in zip(TRUNK, TRUNK[1:]):
        if z <= z1:
            t = (z - z0) / (z1 - z0)
            return Vector((x0 + t * (x1 - x0), y0 + t * (y1 - y0), z)), r0 + t * (r1 - r0)
    x, y, z1, r = TRUNK[-1]
    return Vector((x, y, z1)), r


def _surface(z, yaw, inset=0.0):
    """Point on the trunk surface at height `z`, `yaw` degrees round, and its outward direction."""
    c, r = _axis(z)
    a = math.radians(yaw)
    n = Vector((math.cos(a), math.sin(a), 0))
    return c + n * (r - inset), n


def _trunk(mats, rnd):
    for i, (a, b) in enumerate(zip(TRUNK, TRUNK[1:])):
        _branch(f"tree_dead_trunk_{i}", a[:3], (b[0], b[1], b[2] + (0.05 if i < 2 else 0)), a[3], b[3], mats["wood"],
                rnd, segments=14, rough=0.05, ridges=0.07)
    # The last bark at the foot, frayed into tongues upwards.
    sleeve = cylinder("tree_dead_bark", TRUNK[0][3] * 1.08, BARK_H, (0, 0, 0), mats["bark"],
                      r_top=_axis(BARK_H)[1] * 1.04, segments=14, bevel=0)
    _roughen(sleeve, rnd, 0.05, ridges=0.08)
    for i in range(7):
        yaw = 51 * i + rnd.uniform(-12, 12)
        z = BARK_H + rnd.uniform(0.1, 0.45)
        p, n = _surface(z, yaw, inset=-0.004)
        h = rnd.uniform(0.3, 0.8)
        box(f"tree_dead_bark_tongue_{i}", (0.028, rnd.uniform(0.06, 0.12), h), p, mats["bark"], rot=(0, 0, yaw),
            bevel=0.006)
    # Long cracks in the bare wood.
    for i in range(9):
        yaw = 40 * i + rnd.uniform(-15, 15)
        z = rnd.uniform(BARK_H + 0.3, 3.2)
        p, n = _surface(z, yaw, inset=0.004)
        box(f"tree_dead_crack_{i}", (0.02, 0.018, rnd.uniform(0.4, 1.1)), p, mats["crack"], rot=(0, 0, yaw), bevel=0)
    # Flared roots sloping down to the ground.
    for i in range(ROOT_N):
        yaw = 360 * i / ROOT_N + rnd.uniform(-18, 18)
        tilt = rnd.uniform(103, 110)
        length = ROOT_L * rnd.uniform(0.85, 1.2)
        r, r_top = ROOT_R * rnd.uniform(0.85, 1.1), 0.03
        dz = math.cos(math.radians(tilt))
        flat = math.sqrt(1 - dz * dz)
        z0 = max(0.004 + 1.2 * r_top * flat - length * dz, 0.004 + 1.2 * r * flat)
        root = cylinder(f"tree_dead_root_{i}", r, length, (0, 0, z0), mats["bark" if i % 2 else "dark"], r_top=r_top,
                        segments=8, rot=(tilt, 0, yaw), bevel=0)
        _roughen(root, rnd, 0.1)


def _top(mats, rnd):
    """The broken top: a rotten hollow heart ringed by tall jagged splinters of pale and grey wood."""
    c, r = _axis(TRUNK[-1][2])
    blob("tree_dead_top_heart", r * 0.75, c + Vector((0, 0, 0.0)), mats["rot"], squash=(1, 1, 0.5), subdiv=2, seed=5,
         jitter=0.1)
    for k in range(SPLINTERS):
        a = math.radians(360 * k / SPLINTERS + rnd.uniform(-12, 12))
        n = Vector((math.cos(a), math.sin(a), 0))
        base = c + n * r * 0.72 - Vector((0, 0, 0.08))
        ln = rnd.uniform(*SPLINTER_L) * (1.4 if k == 2 else 1.0)
        d = Vector((0, 0, 1)) + n * rnd.uniform(0.05, 0.25)
        mat = mats["break"] if k % 3 == 0 else mats["dark"] if k % 3 == 1 else mats["wood"]
        _branch(f"tree_dead_splinter_{k}", base, base + d.normalized() * ln, r * 0.38, 0.006, mat, rnd, segments=4,
                rough=0.15)


def _limbs(mats, rnd):
    """Crooked bare limbs, each a chain of tapering segments, with a few forked twigs."""
    for i, (z, points) in enumerate(LIMBS):
        c, r = _axis(z)
        chain = [c] + [Vector(p) for p in points]
        radii = [LIMB_R * (1 - 0.8 * j / (len(chain) - 1)) for j in range(len(chain))]
        for j, (a, b) in enumerate(zip(chain, chain[1:])):
            _branch(f"tree_dead_limb_{i}_{j}", a, b, radii[j], radii[j + 1] * 0.95, mats["wood"], rnd)
            if j:
                blob(f"tree_dead_limb_{i}_knee_{j}", radii[j] * 1.05, a, mats["wood"], subdiv=1, seed=30 + 3 * i + j,
                     jitter=0.05)
        # Twigs forking off the outer segments, thin and crooked.
        for j in range(1, len(chain) - 1):
            a, b = chain[j], chain[j + 1]
            p = a.lerp(b, 0.5)
            side = (b - a).cross(Vector((0, 0, 1)))
            side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
            s = 1 if (i + j) % 2 else -1
            t1 = p + side * s * 0.3 + Vector((0, 0, 0.35))
            t2 = t1 + side * s * 0.12 + Vector((0, 0, 0.2))
            _branch(f"tree_dead_twig_{i}_{j}_a", p, t1, radii[j] * 0.45, 0.012, mats["dark"], rnd, segments=5)
            _branch(f"tree_dead_twig_{i}_{j}_b", t1, t2, 0.012, 0.004, mats["dark"], rnd, segments=4)
        tip = chain[-1]
        _branch(f"tree_dead_limb_{i}_tip", tip, tip + (chain[-1] - chain[-2]).normalized() * 0.04, radii[-1] * 0.95,
                0.004, mats["break"], rnd, segments=5)


def _stubs(mats, rnd):
    """Snapped limb stubs pointing out and a little up, each with a pale break and two splinters."""
    for i, (z, yaw, r0, ln) in enumerate(STUBS):
        base, n = _surface(z, yaw, inset=0.05)
        d = (n + Vector((0, 0, 0.45))).normalized()
        _branch(f"tree_dead_stub_{i}", base, base + d * ln, r0, r0 * 0.8, mats["wood"], rnd)
        tip = base + d * ln
        cylinder(f"tree_dead_stub_{i}_break", r0 * 0.7, 0.012, tip - d * 0.006, mats["break"], segments=8,
                 rot=_rot(d), bevel=0)
        for k in range(2):
            a = math.radians(140 * k + rnd.uniform(0, 60))
            side = d.cross(Vector((0, 0, 1))).normalized()
            up = side.cross(d)
            off = (side * math.cos(a) + up * math.sin(a)) * r0 * 0.4
            _branch(f"tree_dead_stub_{i}_splinter_{k}", tip + off - d * 0.01, tip + off + d * rnd.uniform(0.05, 0.1),
                    r0 * 0.35, 0.003, mats["break" if k else "wood"], rnd, segments=4, rough=0.1)


def _details(mats, rnd):
    """Woodpecker holes and shelf fungi."""
    for i, (z, yaw) in enumerate(((2.15, 285), (3.0, 250))):
        p, n = _surface(z, yaw, inset=0.012)
        cylinder(f"tree_dead_hole_{i}", 0.04, 0.03, p, mats["crack"], segments=10, rot=_rot(n), bevel=0)
    for i, (z, yaw) in enumerate(((0.95, 300), (1.12, 320), (1.75, 30), (1.55, 15))):
        p, n = _surface(z, yaw, inset=0.04)
        r = rnd.uniform(0.07, 0.11)
        blob(f"tree_dead_fungus_{i}", r, p + n * r * 0.45, mats["fungus"], squash=(1.0, 1.25, 0.28), subdiv=2,
             seed=60 + i, jitter=0.06).rotation_euler = (0, 0, math.radians(yaw))
        blob(f"tree_dead_fungus_{i}_rim", r * 0.85, p + n * r * 0.55 + Vector((0, 0, r * 0.08)), mats["rim"],
             squash=(1.0, 1.25, 0.2), subdiv=2, seed=70 + i, jitter=0.05).rotation_euler = (0, 0, math.radians(yaw))


@prop
def tree_dead():
    rnd = random.Random(31)
    mats = _mats()
    _trunk(mats, rnd)
    _top(mats, rnd)
    _limbs(mats, rnd)
    _stubs(mats, rnd)
    _details(mats, rnd)
