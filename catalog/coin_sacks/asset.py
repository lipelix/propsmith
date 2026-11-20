"""Three small tied cloth money sacks, about 0.65 m across and 0.35 m high: two standing plump and tied at the neck with
twine, the third tipped on its side in front (-y) with its neck open and gold coins spilling out of it onto the
floor."""
import math
import random

from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, cylinder, torus

# Overall dimensions (metres).
UP_R, UP_H = 0.15, 0.33  # a standing sack's body radius and height; neck and tuft bring it to about 0.38 m
LIE_L, LIE_R = 0.3, 0.12  # the tipped sack's body length and half-width
NECK_L, NECK_R = 0.06, 0.045
COIN_R, COIN_T = 0.017, 0.003
SPILL_COINS = 44

CLOTH = (0.3, 0.2, 0.1)  # linear RGB, a warm canvas brown
CLOTH_PALE = (0.36, 0.27, 0.15)
CLOTH_DARK = (0.18, 0.11, 0.06)  # the third sack and the patches
TWINE = (0.17, 0.12, 0.06)
GOLD = (0.5, 0.33, 0.09)  # as `treasure_pile`
GOLD_DARK = (0.26, 0.15, 0.04)


def _mats():
    return {
        "cloth": material("coin_sacks_cloth", CLOTH, rough=0.95, vary=0.22, scale=30, crevice=0.6),
        "pale": material("coin_sacks_cloth_pale", CLOTH_PALE, rough=0.95, vary=0.2, scale=30, crevice=0.6),
        "dark": material("coin_sacks_cloth_dark", CLOTH_DARK, rough=0.95, vary=0.2, scale=25, crevice=0.5),
        "twine": material("coin_sacks_twine", TWINE, rough=0.9, vary=0.2, scale=40, crevice=0.4),
        "gold": material("coin_sacks_gold", GOLD, rough=0.32, vary=0.25, scale=30, crevice=0.6, metal=0.9),
        "heap": material("coin_sacks_heap", GOLD_DARK, rough=0.4, vary=0.5, scale=60, crevice=0.75, metal=0.85),
    }


def _matrix(obj):
    return Matrix.Translation(obj.location) @ obj.rotation_euler.to_matrix().to_4x4()


def _put(obj, frame, at, rot=(0, 0, 0)):
    """Place `obj` at local `at` / rotation `rot` (degrees) inside the sack `frame` (a 4x4 matrix)."""
    world = frame @ Matrix.Translation(at) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
    obj.location = world.to_translation()
    obj.rotation_euler = world.to_euler()
    return obj


def _frame(at, yaw, pitch=0):
    return Matrix.Translation(at) @ Euler((0, math.radians(pitch), math.radians(yaw)), "ZYX").to_matrix().to_4x4()


def _slump(obj, down, k):
    """Flatten the half of a blob facing local `down` by `k`, so the sack sags onto what it stands on."""
    down = Vector(down).normalized()
    for v in obj.data.vertices:
        d = v.co.dot(down)
        if d > 0:
            v.co -= down * d * (1 - k)


def _settle(objs, z=0.0):
    """Shift `objs` so their lowest vertex sits at `z`."""
    low = min((_matrix(o) @ v.co).z for o in objs for v in o.data.vertices)
    for o in objs:
        o.location.z += z - low


def _sack(name, length, radius, frame, mats, seed, down, body, tied=True):
    """A sack along local +x (neck at +x), centred on the frame's origin. Returns its parts."""
    rnd = random.Random(seed)
    b = blob(f"{name}_body", radius, (0, 0, 0), mats[body], squash=(length / (2 * radius), 1, 1), subdiv=3,
             seed=seed, jitter=0.04)
    _slump(b, down, 0.5)
    parts = [_put(b, frame, (0, 0, 0), (rnd.uniform(-4, 4), 0, 0))]
    x0 = length / 2 * 0.78
    if tied:
        # Gathered neck, the twine round it and the frayed tuft above.
        parts.append(_put(cylinder(f"{name}_neck", NECK_R * 1.6, NECK_L, (0, 0, 0), mats[body], r_top=NECK_R * 0.8,
                                   segments=10, bevel=0.01), frame, (x0, 0, 0), (0, 90, 0)))
        parts.append(_put(torus(f"{name}_twine", NECK_R * 0.92, 0.009, (0, 0, 0), mats["twine"], major=14, minor=6),
                          frame, (x0 + NECK_L * 0.6, 0, 0), (0, 90, 0)))
        parts.append(_put(blob(f"{name}_tuft", 0.045, (0, 0, 0), mats[body], squash=(0.75, 1.25, 1.05), subdiv=2,
                               seed=seed + 1, jitter=0.25), frame, (x0 + NECK_L + 0.025, 0, 0)))
    else:
        # The neck untied and flared open, the twine slack round it.
        parts.append(_put(cylinder(f"{name}_neck", NECK_R * 1.4, NECK_L, (0, 0, 0), mats[body],
                                   r_top=NECK_R * 1.7, segments=12, bevel=0.01), frame, (x0, 0, 0), (0, 90, 0)))
        parts.append(_put(torus(f"{name}_twine", NECK_R * 1.45, 0.008, (0, 0, 0), mats["twine"], major=14, minor=6),
                          frame, (x0 + NECK_L * 0.25, 0, 0), (0, 80, 0)))
        # Coins showing in the open mouth.
        parts.append(_put(blob(f"{name}_mouth", NECK_R * 1.5, (0, 0, 0), mats["heap"], squash=(0.5, 1, 0.9),
                               subdiv=2, seed=seed + 3, jitter=0.1), frame, (x0 + NECK_L * 0.95, 0, -0.005)))
    a = math.radians(rnd.uniform(30, 60))
    at = (rnd.uniform(-0.2, 0.05) * length, -radius * 0.62 * math.cos(a), radius * 0.62 * math.sin(a))
    parts.append(_put(blob(f"{name}_patch", radius * 0.45, (0, 0, 0), mats["dark" if body != "dark" else "pale"],
                           squash=(1.2, 0.9, 0.9), subdiv=2, seed=seed + 2, jitter=0.04), frame, at))
    return parts


@prop
def coin_sacks():
    rnd = random.Random(5)
    mats = _mats()

    # Two standing at the back: local +x (neck) points up, the -x end slumps on the floor.
    for i, (x, y, yaw, scale, body, seed) in enumerate([(-0.17, 0.13, 20, 1.0, "cloth", 10),
                                                         (0.13, 0.14, -35, 0.88, "pale", 20)]):
        parts = _sack(f"coin_sacks_up{i}", UP_H * scale, UP_R * scale, _frame((x, y, 0), yaw, -90), mats, seed,
                      (-1, 0, 0), body)
        _settle(parts)

    # The third tipped on its side in front, its open neck towards +x, -y.
    yaw = -12
    lie = _frame((-0.17, -0.12, 0), yaw)
    parts = _sack("coin_sacks_tipped", LIE_L, LIE_R, lie, mats, 30, (0, 0, -1), "dark", tied=False)
    _settle(parts)

    # Coins pouring out of the mouth: a low tongue of gold and loose coins fanning out over the floor.
    mouth = lie @ Vector((LIE_L / 2 * 0.78 + NECK_L * 1.2, 0, 0))
    out = Vector((math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0))
    side = Vector((-out.y, out.x, 0))
    tongue = blob("coin_sacks_spill", 0.11, (mouth.x + out.x * 0.07, mouth.y + out.y * 0.07, 0), mats["heap"],
                  squash=(1.4, 0.95, 0.4), subdiv=2, seed=41, jitter=0.2)
    tongue.rotation_euler = (0, 0, math.radians(yaw))
    for v in tongue.data.vertices:  # pressed flat onto the floor
        if v.co.z < 0:
            v.co.z *= 0.03
    tongue.location.z = -min(v.co.z for v in tongue.data.vertices)
    w = _matrix(tongue)
    tree = BVHTree.FromPolygons([w @ v.co for v in tongue.data.vertices], [p.vertices for p in tongue.data.polygons])
    tongue.data.set_sharp_from_angle(angle=math.pi)
    for i in range(SPILL_COINS):
        d = rnd.uniform(0.02, 0.3)
        w = rnd.uniform(-1, 1) * (0.03 + d * 0.45)
        p = mouth + out * d + side * w
        if abs(p.x) > 0.37 or abs(p.y) > 0.27:
            continue
        # On the tongue of coins they lie tipped on its surface; past it flat on the floor.
        c = cylinder(f"coin_sacks_coin_{i}", COIN_R, COIN_T, (0, 0, 0), mats["gold"], segments=8, bevel=0)
        hit = tree.ray_cast(Vector((p.x, p.y, 1.0)), Vector((0, 0, -1)))
        if hit[0] is not None:
            n = hit[1] if hit[1].z > 0 else -hit[1]
            n = (n + Vector((rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), 0))).normalized()
            m = Matrix.Translation(hit[0] - n * 0.002) @ Vector((0, 0, 1)).rotation_difference(n).to_matrix().to_4x4()
        else:
            m = Matrix.Translation((p.x, p.y, 0))
        m = m @ Matrix.Rotation(rnd.uniform(0, 6.3), 4, "Z")
        c.location, c.rotation_euler = m.to_translation(), m.to_euler()
        low = min((_matrix(c) @ v.co).z for v in c.data.vertices)
        if low < 0:  # a coin tipped at the tongue's edge rests on the floor, not through it
            c.location.z -= low
    for j in range(4):  # a little stack someone was counting
        cylinder(f"coin_sacks_stack_{j}", COIN_R, COIN_T, (0.3 + rnd.uniform(-0.002, 0.002), -0.02, j * COIN_T),
                 mats["gold"], segments=8, bevel=0)
