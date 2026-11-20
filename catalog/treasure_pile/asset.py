"""A heap of gold coins about 1.2 m across and 0.5 m high: a lumpy mound of gold strewn with loose coins, a goblet
standing half buried near the top, a crown tipped on the front (-y) slope, a few cut gems and coins spilt round its
foot."""
import math
import random

import bpy

from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall dimensions (metres).
MOUND_R = 0.5  # footprint radius of the heap
MOUND_H = 0.31  # height of the heap itself; the goblet rises above it
SPILL_R = 0.6  # loose coins lie out to here
COIN_R = 0.021  # a large gold coin
COIN_T = 0.004
SURFACE_COINS = 130
SPILL_COINS = 24
STACKS = ((0.47, -0.3, 6), (-0.5, -0.12, 4), (0.12, 0.52, 5))  # coin stacks at the foot: x, y, coins

GOLD = (0.5, 0.33, 0.09)  # linear RGB, a warm, slightly dull gold
GOLD_DARK = (0.26, 0.15, 0.04)  # the body of the heap, coins in shadow
RUBY = (0.32, 0.025, 0.035)
SAPPHIRE = (0.03, 0.06, 0.3)
EMERALD = (0.03, 0.22, 0.07)
VELVET = (0.22, 0.03, 0.04)  # the crown's cap


def _mats():
    return {
        "gold": material("treasure_pile_gold", GOLD, rough=0.32, vary=0.25, scale=30, crevice=0.6, metal=0.9),
        "heap": material("treasure_pile_heap", GOLD_DARK, rough=0.4, vary=0.5, scale=60, crevice=0.75, metal=0.85),
        "ruby": material("treasure_pile_ruby", RUBY, rough=0.15, vary=0.2, scale=20, crevice=0.3),
        "sapphire": material("treasure_pile_sapphire", SAPPHIRE, rough=0.15, vary=0.2, scale=20, crevice=0.3),
        "emerald": material("treasure_pile_emerald", EMERALD, rough=0.15, vary=0.2, scale=20, crevice=0.3),
        "velvet": material("treasure_pile_velvet", VELVET, rough=0.95, vary=0.2, scale=25, crevice=0.6),
    }


def _matrix(obj):
    return Matrix.Translation(obj.location) @ obj.rotation_euler.to_matrix().to_4x4()


def _set(obj, m):
    obj.location = m.to_translation()
    obj.rotation_euler = m.to_euler()
    return obj


def _tilt(normal):
    """A rotation turning local +z onto `normal`."""
    return Vector((0, 0, 1)).rotation_difference(Vector(normal)).to_matrix().to_4x4()


def _mound(mats):
    """The heap: a squashed blob whose underside is pressed flat onto the ground. Returns it and a ray tree."""
    m = blob("treasure_pile_mound", MOUND_R, (0, 0, 0), mats["heap"], squash=(1, 0.96, MOUND_H / MOUND_R), subdiv=3,
             seed=7, jitter=0.07)
    rnd = random.Random(8)
    lumps = [(rnd.uniform(0, 6.3), rnd.uniform(0.15, 0.4), rnd.uniform(0.04, 0.08)) for _ in range(7)]
    for v in m.data.vertices:
        if v.co.z < 0:
            v.co.z *= 0.02
            continue
        # A heap, not a bun: sloped sides and a rounded peak, with a few slipped lumps on the flanks.
        r = min(1.0, math.hypot(v.co.x, v.co.y) / MOUND_R)
        v.co.z *= 0.55 + 0.45 * (1 - r) ** 0.6
        for a, d, h in lumps:
            dx, dy = v.co.x - d * math.cos(a), v.co.y - d * math.sin(a)
            v.co.z += h * math.exp(-(dx * dx + dy * dy) / 0.012) * (1 - r * 0.5)
    m.data.set_sharp_from_angle(angle=math.pi)  # one smooth heap, no creases
    low = min(v.co.z for v in m.data.vertices)
    m.location.z = -low
    w = _matrix(m)
    tree = BVHTree.FromPolygons([w @ v.co for v in m.data.vertices], [p.vertices for p in m.data.polygons])
    return m, tree


def _surface(tree, x, y):
    """Where a ray from above meets the heap at (x, y): (point, normal), or None off the heap."""
    hit = tree.ray_cast(Vector((x, y, 2.0)), Vector((0, 0, -1)))
    if hit[0] is None:
        return None
    n = hit[1] if hit[1].z > 0 else -hit[1]
    return hit[0], n


def _coin(name, at, normal, spin, mat, sink=0.0015):
    c = cylinder(name, COIN_R, COIN_T, (0, 0, 0), mat, segments=8, bevel=0)
    m = Matrix.Translation(Vector(at) - Vector(normal) * sink) @ _tilt(normal) @ Matrix.Rotation(spin, 4, "Z")
    return _set(c, m)


def _goblet(mats, at, normal):
    """A footed goblet, its foot buried in the heap; parts built standing on the origin, then tilted onto `at`."""
    g = mats["gold"]
    parts = [
        cylinder("treasure_pile_goblet_foot", 0.05, 0.018, (0, 0, -0.03), g, r_top=0.035, segments=14, bevel=0.004),
        cylinder("treasure_pile_goblet_stem", 0.012, 0.09, (0, 0, -0.012), g, segments=10, bevel=0.002),
        torus("treasure_pile_goblet_knop", 0.016, 0.008, (0, 0, 0.035), g, major=12, minor=6),
        cylinder("treasure_pile_goblet_bowl_base", 0.014, 0.03, (0, 0, 0.075), g, r_top=0.048, segments=14,
                 bevel=0.003),
        cylinder("treasure_pile_goblet_bowl", 0.048, 0.07, (0, 0, 0.105), g, r_top=0.058, segments=14, bevel=0.003),
        torus("treasure_pile_goblet_rim", 0.057, 0.005, (0, 0, 0.175), g, major=16, minor=6),
        box("treasure_pile_goblet_jewel", (0.016, 0.01, 0.022), (0, -0.05, 0.135), mats["ruby"], rot=(-6, 0, 45),
            bevel=0.003),
    ]
    frame = Matrix.Translation(at) @ _tilt(normal.lerp(Vector((0, 0, 1)), 0.6)) @ Matrix.Rotation(0.4, 4, "Z")
    for p in parts:
        _set(p, frame @ _matrix(p))


def _crown(mats, at, normal):
    """An open gold circlet with five points and a velvet cap, tipped on its side down the slope."""
    g = mats["gold"]
    r, h = 0.1, 0.055
    parts = [
        cylinder("treasure_pile_crown_band", r, h, (0, 0, 0), g, segments=16, bevel=0.003),
        cylinder("treasure_pile_crown_cap", r - 0.006, h + 0.025, (0, 0, 0.004), mats["velvet"], r_top=r * 0.55,
                 segments=12, bevel=0.01),
        torus("treasure_pile_crown_rim", r + 0.002, 0.005, (0, 0, 0.004), g, major=20, minor=6),
    ]
    for i in range(5):
        a = 2 * math.pi * i / 5
        parts.append(cylinder(f"treasure_pile_crown_point_{i}", 0.02, 0.05, (r * math.cos(a), r * math.sin(a), h - 0.004),
                              g, r_top=0.003, segments=6, bevel=0.002))
        parts.append(blob(f"treasure_pile_crown_gem_{i}", 0.011, (1.03 * r * math.cos(a), 1.03 * r * math.sin(a),
                                                                 h * 0.5), mats["ruby" if i % 2 else "emerald"],
                          subdiv=1, seed=40 + i, jitter=0.05))
    # Lying on its side: the band's axis turned towards -y and down the slope.
    frame = Matrix.Translation(at) @ _tilt(normal) @ Matrix.Rotation(math.radians(-70), 4, "X") @ \
        Matrix.Translation((0, 0, -r * 0.35))
    for p in parts:
        _set(p, frame @ _matrix(p))


@prop
def treasure_pile():
    rnd = random.Random(3)
    mats = _mats()
    _, tree = _mound(mats)

    # Coins strewn over the heap, tilted to its surface; an even spread from a jittered spiral.
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(SURFACE_COINS):
        rr = MOUND_R * 0.95 * math.sqrt((i + 0.5) / SURFACE_COINS) + rnd.uniform(-0.02, 0.02)
        a = i * golden + rnd.uniform(-0.2, 0.2)
        hit = _surface(tree, rr * math.cos(a), rr * math.sin(a))
        if hit is None:
            continue
        p, n = hit
        n = (n + Vector((rnd.uniform(-0.45, 0.45), rnd.uniform(-0.45, 0.45), 0))).normalized()
        _coin(f"treasure_pile_coin_{i}", p, n, rnd.uniform(0, 6.3), mats["gold"], sink=0.003)

    # Coins spilt round the foot, flat on the ground or propped on the heap's edge.
    for i in range(SPILL_COINS):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(MOUND_R * 0.98, SPILL_R - COIN_R)
        c = cylinder(f"treasure_pile_spill_{i}", COIN_R, COIN_T, (rr * math.cos(a), rr * math.sin(a), 0),
                     mats["gold"], segments=8, bevel=0, rot=(0, 0, rnd.uniform(0, 360)))
        c.location.y *= 0.97
    for k, (x, y, n) in enumerate(STACKS):
        for j in range(n):
            cylinder(f"treasure_pile_stack_{k}_{j}", COIN_R, COIN_T, (x + rnd.uniform(-0.003, 0.003),
                     y + rnd.uniform(-0.003, 0.003), j * COIN_T), mats["gold"], segments=8, bevel=0)

    # The goblet half buried just behind the top, the crown on the front slope.
    p, n = _surface(tree, 0.0, 0.1)
    _goblet(mats, p - Vector((0, 0, 0.014)), n)
    p, n = _surface(tree, 0.16, -0.27)
    _crown(mats, p, n)

    # A few cut gems lying on the heap.
    for i, (x, y, gem, r) in enumerate([(0.22, -0.18, "ruby", 0.034), (-0.3, 0.12, "sapphire", 0.036),
                                        (0.08, -0.36, "emerald", 0.03), (0.3, 0.2, "sapphire", 0.028),
                                        (-0.08, 0.3, "ruby", 0.03), (0.36, -0.02, "emerald", 0.026)]):
        p, n = _surface(tree, x, y)
        g = blob(f"treasure_pile_gem_{i}", r, (0, 0, 0), mats[gem], squash=(1.2, 0.9, 0.7), subdiv=1, seed=60 + i,
                 jitter=0.08)
        _set(g, Matrix.Translation(p + n * r * 0.3) @ _tilt(n) @ Matrix.Rotation(rnd.uniform(0, 6.3), 4, "Z"))

    # Nothing dips under the floor: lift any coin or trinket tipped through it at the heap's foot.
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            low = min((_matrix(o) @ v.co).z for v in o.data.vertices)
            if low < 0:
                o.location.z -= low
