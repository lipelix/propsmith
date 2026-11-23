"""A rock outcrop of dark grey stone, a tall craggy boulder with a lower one against its back and a small stone at its foot, crossed by two
seams of milky quartz studded with glinting brassy ore; a pickaxe with an iron head and an ash haft leans on it, its
haft end on the ground, and a few chips of broken stone lie round its foot.

Seam pieces and the pickaxe are placed against the finished stone by ray casts, so they sit on its surface."""
import math
import random

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall dimensions (metres): about 1.2 wide (x) × 1 deep × 1 high.
MAIN_R, MAIN_H, MAIN_STRETCH = 0.4, 1.0, 1.12  # the main crag: half-width, height, x stretch
MAIN_AT = (0.04, -0.04)
BACK_R, BACK_H = 0.3, 0.66  # the lower boulder against its back (+y), toward -x
BACK_AT = (-0.22, 0.17)
FRONT_R, FRONT_H = 0.2, 0.3  # a small stone at its front left foot
FRONT_AT = (-0.36, -0.24)
FLAT = 0.12  # share of a boulder's height cut flat where it rests on the ground
PICK_FOOT = (0.24, -0.54)  # where the haft end stands on the ground
HAFT_LEN, HAFT_R = 0.86, 0.02
PICK_SPAN = 0.56  # pickaxe head, point to chisel

STONE = (0.16, 0.155, 0.15)  # linear RGB, dark slaty grey
STONE_DARK = (0.1, 0.098, 0.095)
QUARTZ = (0.46, 0.44, 0.4)  # milky white, dulled
ORE = (0.5, 0.34, 0.09)  # brassy pyrite and gold
ORE_RED = (0.32, 0.12, 0.05)  # rusty iron-stained ore
ASH = (0.33, 0.25, 0.16)  # pale ash, against the dark stone
IRON = (0.17, 0.165, 0.16)  # worn bright by use


def _rock(name, r, h, xy, mat, seed, stretch=1.0, yaw=0.0, subdiv=3):
    """A craggy boulder `r` half-wide and `h` high: a lumpy blob with its base cut flat, standing on the ground."""
    rz = h / (2 * (1 - FLAT / 2))
    obj = blob(name, r, (xy[0], xy[1], 0), mat, squash=(stretch, 1 / stretch ** 0.5, rz / r), subdiv=subdiv,
               seed=seed, jitter=0.16)
    verts = obj.data.vertices
    low = min(v.co.z for v in verts)
    cut = low + FLAT * (max(v.co.z for v in verts) - low)
    for v in verts:
        v.co.z = max(v.co.z, cut)
    obj.rotation_euler = (0, 0, math.radians(yaw))
    obj.location.z = -cut
    bpy.context.view_layer.update()
    return obj


def _tree(objs):
    verts, polys = [], []
    for obj in objs:
        base = len(verts)
        verts += [obj.matrix_world @ v.co for v in obj.data.vertices]
        polys += [[base + i for i in p.vertices] for p in obj.data.polygons]
    return BVHTree.FromPolygons(verts, polys)


def _hit(tree, origin, direction):
    loc, normal, _, _ = tree.ray_cast(Vector(origin), Vector(direction).normalized())
    if loc is None:
        return None
    if normal.dot(Vector(direction)) > 0:
        normal = -normal
    return loc, normal


def _stud(name, size, loc, normal, sink, spin, mat, bevel):
    """A box lying on the surface at `loc`, its thin side along `normal`, sunk by `sink`."""
    obj = box(name, size, tuple(loc - normal * sink), mat, bevel=bevel)
    q = normal.to_track_quat("Z", "Y") @ Matrix.Rotation(math.radians(spin), 3, "Z").to_quaternion()
    obj.rotation_euler = q.to_euler("XYZ")
    return obj


def _seam(prefix, tree, points, direction, spin, mats, rnd):
    """Quartz lenses along a line of ray casts, turned `spin` degrees to follow it, brassy and rusty ore studs set in
    them."""
    for i, p in enumerate(points):
        got = _hit(tree, p, direction)
        if got is None:
            continue
        loc, n = got
        w = rnd.uniform(0.1, 0.14)
        _stud(f"{prefix}_quartz_{i}", (w, rnd.uniform(0.035, 0.055), 0.03), loc, n, 0.01, spin + rnd.uniform(-8, 8),
              mats["quartz"], 0.006)
        for k in range(2 if i % 2 else 1):
            off = Vector((rnd.uniform(-0.03, 0.03), 0, rnd.uniform(-0.015, 0.015)))
            got = _hit(tree, Vector(p) + off, direction)
            if got is None:
                continue
            s = rnd.uniform(0.022, 0.036)
            _stud(f"{prefix}_ore_{i}_{k}", (s, s * 0.8, s * 0.7), got[0], got[1], -0.008, rnd.uniform(0, 90),
                  mats["red"] if (i + k) % 4 == 3 else mats["ore"], 0.004)


@prop
def ore_vein_rock():
    rnd = random.Random(53)
    mats = {
        "stone": material("ore_vein_rock_stone", STONE, rough=0.85, vary=0.3, scale=8, crevice=0.75),
        "dark": material("ore_vein_rock_stone_dark", STONE_DARK, rough=0.85, vary=0.3, scale=8, crevice=0.75),
        "quartz": material("ore_vein_rock_quartz", QUARTZ, rough=0.4, vary=0.2, scale=30, crevice=0.4),
        "ore": material("ore_vein_rock_ore", ORE, rough=0.25, vary=0.3, scale=40, metal=0.85),
        "red": material("ore_vein_rock_ore_rust", ORE_RED, rough=0.6, vary=0.3, scale=30, metal=0.3),
    }
    ash = material("ore_vein_rock_haft", ASH, vary=0.22, scale=18)
    iron = material("ore_vein_rock_pick", IRON, rough=0.45, vary=0.3, scale=20, metal=0.75)

    rocks = [
        _rock("rock_main", MAIN_R, MAIN_H, MAIN_AT, mats["stone"], seed=61, stretch=MAIN_STRETCH, yaw=-8),
        _rock("rock_back", BACK_R, BACK_H, BACK_AT, mats["dark"], seed=62, stretch=1.1, yaw=30, subdiv=2),
        _rock("rock_front", FRONT_R, FRONT_H, FRONT_AT, mats["stone"], seed=63, stretch=1.2, yaw=-20, subdiv=2),
    ]
    tree = _tree(rocks)

    # Two seams: one climbing across the front (-y), one dipping across the +x shoulder.
    front = [(x, -2.0, 0.3 + 0.36 * (x + 0.45) + 0.04 * math.sin(7 * x)) for x in
             [-0.4 + 0.075 * i for i in range(12)]]
    _seam("seam_front", tree, front, (0, 1, 0), 20, mats, rnd)
    side = [(2.0, y, 0.68 - 0.3 * (y + 0.35) + 0.03 * math.sin(9 * y)) for y in [-0.34 + 0.075 * i for i in range(8)]]
    _seam("seam_side", tree, side, (-1, 0, 0), -17, mats, rnd)
    # Ore glinting in the top of the crag too.
    top = [(0.0 + 0.07 * i, -0.2 + 0.04 * i, 3.0) for i in range(5)]
    _seam("seam_top", tree, top, (0, 0, -1), 30, mats, rnd)

    # Broken chips at the foot, some with ore in them.
    for k in range(7):
        a = math.radians(-150 + 22 * k + rnd.uniform(-8, 8))
        x, y = 0.5 * math.cos(a) * MAIN_STRETCH, 0.47 * math.sin(a) - 0.04
        r = rnd.uniform(0.03, 0.05)
        blob(f"chip_{k}", r, (x, y, r * 0.75), mats["ore"] if k in (2, 5) else mats["stone"], squash=(1.2, 1, 0.55),
             subdiv=1, seed=600 + k, jitter=0.3)

    # The pickaxe: its haft end on the ground in front, laid back toward the crag until the head or haft touches it.
    fx, fy = PICK_FOOT
    base = Vector((fx, fy, 0.0))
    toward = Vector((-0.15, 1, 0)).normalized()  # into the front face, across the review view
    side = toward.cross(Vector((0, 0, 1))).normalized()  # the head runs along this, across the lean
    half = PICK_SPAN / 2
    d = Vector((0, 0, 1))
    for step in range(60):
        lean = math.radians(2 + step)
        d = (toward * math.sin(lean) + Vector((0, 0, math.cos(lean)))).normalized()
        top = base + d * HAFT_LEN
        probes = [(base + d * (HAFT_LEN * t / 10), HAFT_R + 0.01) for t in range(3, 11)]
        probes += [(top + side * (half * t / 4), 0.03) for t in range(-4, 5)]
        if any(tree.find_nearest(p)[3] < gap for p, gap in probes):
            break
    frame = Matrix((side, d.cross(side), d)).transposed().to_4x4()
    frame.translation = base
    parts = []
    # Built along local +z from the haft end (at the origin) up to the head; the head runs along local x.
    parts.append(cylinder("haft", HAFT_R * 0.9, HAFT_LEN, (0, 0, 0), ash, r_top=HAFT_R, segments=10, bevel=0.004))
    parts.append(box("pick_eye", (0.07, 0.05, 0.07), (0, 0, HAFT_LEN - 0.04), iron, bevel=0.006))
    for e, tip in ((-1, 0.006), (1, 0.018)):
        # Each arm tapers from the eye to a point (or a narrow chisel) and droops a little toward the haft end.
        arm = box(f"pick_arm_{e}", (half, 0.034, 0.042), (e * half / 2, 0, HAFT_LEN - 0.05), iron, rot=(0, e * 9, 0),
                  bevel=0.004)
        for v in arm.data.vertices:
            if v.co.x * e > 0:
                v.co.z *= tip / 0.042
                v.co.y *= 0.55
        parts.append(arm)
    parts.append(box("haft_wedge", (0.01, 0.03, 0.012), (0, 0, HAFT_LEN - 0.002), iron, bevel=0))
    for obj in parts:
        obj.matrix_basis = frame @ obj.matrix_basis
    bpy.context.view_layer.update()
    # Lift the pickaxe so its lowest point rests on the ground.
    low = min((obj.matrix_world @ v.co).z for obj in parts for v in obj.data.vertices)
    for obj in parts:
        obj.location.z -= low
