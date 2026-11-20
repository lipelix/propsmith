"""The catalogue's oak chest (`chest_wood`) with its domed lid thrown back on the hinges and the box heaped with gold
coins: the same planks, iron corner bands, straps and ring handles; the hasp hangs open from the lid and the padlock is
gone."""
import math
import random

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall dimensions (metres), a real-world chest.
W, D, H = 0.9, 0.54, 0.6  # lid width (x), lid depth (y), total height (z)
BW, BD = W - 0.02, D - 0.02  # body, inset under the lid band
BODY_H = 0.40  # top of the box body
BODY_PLANKS = 4
BAND_H = 0.08  # straight lid band below the dome
RIM_Z = BODY_H + BAND_H  # where the dome starts
SAG = H - RIM_Z  # dome rise
R = (D * D / 4 + SAG * SAG) / (2 * SAG)  # dome radius from chord D and rise SAG
CZ = H - R  # dome axis height
TH_MAX = math.asin(D / 2 / R)  # half angle of the dome
LID_PLANKS = 5
LID_T = 0.13  # radial depth of a dome plank (fills the dome solid)

IRON_T = 0.007  # strap and band thickness
CORNER_W = 0.06  # corner band leg width
STRAP_W = 0.05
STRAP_X = (-0.26, 0.26)

OAK = (0.2, 0.12, 0.062)  # linear RGB
OAK_OLD = (0.155, 0.095, 0.052)
OAK_LID = (0.185, 0.112, 0.058)
IRON = (0.04, 0.038, 0.036)
LOCK = (0.06, 0.05, 0.042)  # a slightly rusty iron



# The open chest.
SOLID_COURSES = 3  # the lower plank courses are solid; above them the box is four walls round the coins
WALL_T = 0.035
OPEN_DEG = 105  # the lid swings back past upright and rests on its hinge straps
HINGE = (D / 2, BODY_H)  # hinge line along x: y, z
COIN_RISE = 0.05  # how far the heap of coins bulges over the rim
COIN_R, COIN_T = 0.021, 0.004
TOP_COINS = 44

GOLD = (0.5, 0.33, 0.09)  # linear RGB, as `treasure_pile`
GOLD_HEAP = (0.36, 0.22, 0.055)  # the coin bed, less metallic so it does not mirror the dark room
RUBY = (0.32, 0.025, 0.035)
EMERALD = (0.03, 0.22, 0.07)


def _matrix(obj):
    return Matrix.Translation(obj.location) @ obj.rotation_euler.to_matrix().to_4x4()


def _set(obj, m):
    obj.location = m.to_translation()
    obj.rotation_euler = m.to_euler()
    return obj


def _tilt(normal):
    return Vector((0, 0, 1)).rotation_difference(Vector(normal)).to_matrix().to_4x4()


def _lid(rnd, oak, old, lidw, iron):
    """The lid as `chest_wood` builds it, closed; returns its parts to swing open."""
    parts = [box("lid_band", (W, D, BAND_H), (0, 0, BODY_H + BAND_H / 2), lidw, bevel=0.012)]
    step = 2 * TH_MAX / LID_PLANKS
    pw = 2 * R * math.tan(step / 2)
    angles = [-TH_MAX + step * (i + 0.5) for i in range(LID_PLANKS)]
    for i, th in enumerate(angles):
        r = R - LID_T / 2 - rnd.uniform(0, 0.003)
        parts.append(box(f"lid_plank_{i}", (W - rnd.uniform(0, 0.008), pw, LID_T),
                         (0, r * math.sin(th), CZ + r * math.cos(th)), rnd.choice((lidw, lidw, old)),
                         rot=(-math.degrees(th) + rnd.uniform(-0.4, 0.4), 0, 0), bevel=0.01))
    for sx in (-1, 1):
        for sy in (-1, 1):
            zc = (BODY_H + RIM_Z) / 2
            parts.append(box(f"corner_band_{sx}_{sy}_y", (CORNER_W, IRON_T, BAND_H),
                             (sx * (W / 2 - CORNER_W / 2 + 0.002), sy * (D / 2 + IRON_T / 2), zc), iron, bevel=0.003))
            parts.append(box(f"corner_band_{sx}_{sy}_x", (IRON_T, CORNER_W, BAND_H),
                             (sx * (W / 2 + IRON_T / 2), sy * (D / 2 - CORNER_W / 2 + 0.002), zc), iron, bevel=0.003))
    for k, x in enumerate(STRAP_X):
        for sy in (-1, 1):
            parts.append(box(f"strap_band_{k}_{sy}", (STRAP_W, IRON_T, BAND_H),
                             (x, sy * (D / 2 + IRON_T / 2), BODY_H + BAND_H / 2), iron, bevel=0.003))
        for i, th in enumerate(angles):
            r = R + IRON_T / 2 - 0.001
            parts.append(box(f"strap_lid_{k}_{i}", (STRAP_W, pw + 0.004, IRON_T),
                             (x, r * math.sin(th), CZ + r * math.cos(th)), iron, rot=(-math.degrees(th), 0, 0),
                             bevel=0.003))
    # The hasp hangs from the front of the lid band, open now.
    parts.append(box("hasp", (0.065, 0.008, 0.13), (0, -D / 2 - IRON_T - 0.002, RIM_Z - 0.06), iron, bevel=0.003))
    return parts


def _coins(rnd, gold, heap, gems):
    """The box heaped with coins: a squared-off mound sunk into the walls, coins strewn on it, a few gems."""
    ix, iy = BW / 2 - WALL_T * 0.5, BD / 2 - WALL_T * 0.5  # reaches into the walls so no gap shows at the rim
    depth = BODY_H - BODY_H / BODY_PLANKS * SOLID_COURSES
    # A level bed of coins just over the rim, with a few slipping mounds on it.
    parts = [box("coins_bed", (2 * ix, 2 * iy, depth + 0.012), (0, 0, BODY_H + 0.012 - (depth + 0.012) / 2), heap,
                 bevel=0)]
    for i, (x, y, r, h) in enumerate([(-0.2, 0.03, 0.24, 0.05), (0.15, -0.02, 0.26, 0.06), (0.3, 0.1, 0.16, 0.04),
                                      (-0.05, 0.12, 0.2, 0.05)]):
        lump = blob(f"coins_mound_{i}", r, (x, y, BODY_H), heap, squash=(1.1, 0.75, h / r), subdiv=1,
                    seed=80 + i, jitter=0.1)
        lump.data.set_sharp_from_angle(angle=math.pi)
        parts.append(lump)
    verts, polys = [], []
    for o in parts:
        w = _matrix(o)
        polys += [[i + len(verts) for i in p.vertices] for p in o.data.polygons]
        verts += [w @ v.co for v in o.data.vertices]
    tree = BVHTree.FromPolygons(verts, polys)

    def surface(x, y):
        hit = tree.ray_cast(Vector((x, y, 2.0)), Vector((0, 0, -1)))
        return (hit[0], hit[1] if hit[1].z > 0 else -hit[1]) if hit[0] is not None else None

    golden = math.pi * (3 - math.sqrt(5))
    for i in range(TOP_COINS):
        f = math.sqrt((i + 0.5) / TOP_COINS)
        a = i * golden
        x, y = f * (ix - 0.02) * math.cos(a), f * (iy - 0.02) * math.sin(a)
        hit = surface(x, y)
        if hit is None:
            continue
        p, n = hit
        n = (n + Vector((rnd.uniform(-0.45, 0.45), rnd.uniform(-0.45, 0.45), 0))).normalized()
        c = cylinder(f"coin_{i}", COIN_R, COIN_T, (0, 0, 0), gold, segments=8, bevel=0)
        _set(c, Matrix.Translation(p - n * 0.003) @ _tilt(n) @ Matrix.Rotation(rnd.uniform(0, 6.3), 4, "Z"))
    for i, (x, y, mat, r) in enumerate([(0.18, -0.08, gems[0], 0.03), (-0.22, 0.06, gems[1], 0.028),
                                        (0.02, 0.12, gems[0], 0.025), (-0.33, -0.12, gems[1], 0.024)]):
        p, n = surface(x, y)
        g = blob(f"gem_{i}", r, (0, 0, 0), mat, squash=(1.2, 0.9, 0.7), subdiv=1, seed=70 + i, jitter=0.08)
        _set(g, Matrix.Translation(p + n * r * 0.3) @ _tilt(n) @ Matrix.Rotation(rnd.uniform(0, 6.3), 4, "Z"))
    # A few coins spilt over the front onto the floor, one small stack.
    for i in range(5):
        x, y = rnd.uniform(-0.38, 0.4), -BD / 2 - rnd.uniform(0.025, 0.06)
        cylinder(f"spill_{i}", COIN_R, COIN_T, (x, y, 0), gold, segments=8, bevel=0, rot=(0, 0, rnd.uniform(0, 360)))
    for j in range(2):
        cylinder(f"stack_{j}", COIN_R, COIN_T, (0.3 + rnd.uniform(-0.003, 0.003), -BD / 2 - 0.05, 0.004 + j * COIN_T),
                 gold, segments=8, bevel=0)


@prop
def chest_wood_open():
    rnd = random.Random(11)
    oak = material("chest_wood_open_plank", OAK, vary=0.25, scale=14)
    old = material("chest_wood_open_plank_old", OAK_OLD, vary=0.28, scale=14)
    lidw = material("chest_wood_open_lid", OAK_LID, vary=0.25, scale=14)
    iron = material("chest_wood_open_iron", IRON, rough=0.55, vary=0.2, scale=20, metal=0.6)
    gold = material("chest_wood_open_gold", GOLD, rough=0.32, vary=0.25, scale=30, crevice=0.6, metal=0.9)
    heap = material("chest_wood_open_heap", GOLD_HEAP, rough=0.5, vary=0.45, scale=60, crevice=0.6, metal=0.5)
    gems = (material("chest_wood_open_ruby", RUBY, rough=0.15, vary=0.2, scale=20, crevice=0.3),
            material("chest_wood_open_emerald", EMERALD, rough=0.15, vary=0.2, scale=20, crevice=0.3))

    # Body: the lower plank courses solid, the upper ones four walls each, with the chest's jitter.
    ph = BODY_H / BODY_PLANKS
    for i in range(BODY_PLANKS):
        mat = rnd.choice((oak, oak, old))
        w, d = BW - rnd.uniform(0, 0.006), BD - rnd.uniform(0, 0.006)
        at = (rnd.uniform(-0.002, 0.002), rnd.uniform(-0.002, 0.002), ph * (i + 0.5))
        if i < SOLID_COURSES:
            box(f"body_plank_{i}", (w, d, ph), at, mat, bevel=0.01)
            continue
        for sy in (-1, 1):
            box(f"body_plank_{i}_y{sy}", (w, WALL_T, ph), (at[0], at[1] + sy * (d - WALL_T) / 2, at[2]), mat,
                bevel=0.01)
        for sx in (-1, 1):
            box(f"body_plank_{i}_x{sx}", (WALL_T, d - 2 * WALL_T + 0.004, ph),
                (at[0] + sx * (w - WALL_T) / 2, at[1], at[2]), mat, bevel=0.01)

    # Iron corner bands and straps on the body.
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"corner_body_{sx}_{sy}_y", (CORNER_W, IRON_T, BODY_H),
                (sx * (BW / 2 - CORNER_W / 2 + 0.002), sy * (BD / 2 + IRON_T / 2), BODY_H / 2), iron, bevel=0.003)
            box(f"corner_body_{sx}_{sy}_x", (IRON_T, CORNER_W, BODY_H),
                (sx * (BW / 2 + IRON_T / 2), sy * (BD / 2 - CORNER_W / 2 + 0.002), BODY_H / 2), iron, bevel=0.003)
    for k, x in enumerate(STRAP_X):
        for sy in (-1, 1):
            box(f"strap_body_{k}_{sy}", (STRAP_W, IRON_T, BODY_H - 0.02),
                (x, sy * (BD / 2 + IRON_T / 2), BODY_H / 2 + 0.01), iron, bevel=0.003)
    for sx in (-1, 1):
        box(f"handle_plate_{sx}", (0.01, 0.08, 0.05), (sx * (BW / 2 + 0.005), 0, 0.3), iron, bevel=0.003)
        torus(f"handle_ring_{sx}", 0.045, 0.008, (sx * (BW / 2 + 0.014), 0, 0.3 - 0.04), iron,
              rot=(90, 0, 90), major=16, minor=6)
    torus("hasp_staple", 0.018, 0.005, (0, -D / 2 - IRON_T - 0.01, RIM_Z - 0.12), iron, rot=(0, 90, 0), major=12,
          minor=6)

    # The lid, swung back about the hinge line, with two hinge knuckles on the back.
    swing = (Matrix.Translation((0, HINGE[0], HINGE[1])) @ Matrix.Rotation(math.radians(-OPEN_DEG), 4, "X")
             @ Matrix.Translation((0, -HINGE[0], -HINGE[1])))
    for p in _lid(rnd, oak, old, lidw, iron):
        _set(p, swing @ _matrix(p))
    for k, x in enumerate(STRAP_X):
        cylinder(f"hinge_{k}", 0.014, 0.07, (x - 0.035, HINGE[0] + 0.006, HINGE[1]), iron, segments=8,
                 rot=(0, 90, 0), bevel=0.002)

    _coins(rnd, gold, heap, gems)

    # The open lid reaches further back than the coins spill forward: centre the whole on the origin in y.
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    ys = [(_matrix(o) @ v.co).y for o in objs for v in o.data.vertices]
    dy = -(min(ys) + max(ys)) / 2
    for o in objs:
        o.location.y += dy
