"""A broken free-standing stone arch about 3 × 1 × 3.5 m: two piers of coursed weathered sandstone blocks over a 1.5 m
opening. The left pier stands to its full height and rises on above the springing as a ragged wall stump; from it the
round arch reaches a little past its crown and ends in a sagging last voussoir, the rest of the arch gone. The right
pier is broken off below the springing with a block slumped askew on its top. Fallen blocks and a voussoir lie in the
grass round it, ivy climbs the front of the left pier and spills over the arch, moss sits on the broken tops."""
import math
import random

import bmesh
import bpy

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall dimensions (metres): about 2.9 × 1.2 × 3.25 (fallen pieces included).
OPEN_W = 1.5  # clear width of the opening
PIER_W = 0.7  # pier width (x)
DEPTH = 0.8  # pier and arch depth (y)
SPRING = 2.0  # springing line of the arch
COURSE_H = 0.25  # nominal course height
R_IN = OPEN_W / 2  # arch intrados
R_OUT = R_IN + 0.4  # arch extrados
VOUSSOIRS = 11  # in the whole arch
KEPT = 7  # voussoirs still standing, from the left springing
RIGHT_COURSES = 6  # courses left of the right pier
STUMP_W = 0.3  # the wall stump over the left pier, outside the arch
STUMP_COURSES = 5
JOINT = 0.012
INSET = 0.03  # mortar core inset behind the faces
ARC_STEP = 5  # degrees between points of a curved edge
PIER_X = OPEN_W / 2 + PIER_W / 2  # pier centres at ±PIER_X

STONE = (0.27, 0.255, 0.225)  # linear RGB: weathered grey-brown sandstone
STONE_OLD = (0.2, 0.19, 0.17)
STONE_PALE = (0.33, 0.315, 0.28)
MORTAR = (0.06, 0.056, 0.05)
MOSS = (0.06, 0.085, 0.03)
IVY = ((0.04, 0.06, 0.02), (0.1, 0.13, 0.035), (0.21, 0.24, 0.065))  # shadow, olive, lit
VINE = (0.13, 0.085, 0.045)
GRASS = (0.075, 0.075, 0.038)


def _prism(name, outline, y0, y1, mat, bevel):
    """A closed prism: the (x, z) `outline` extruded from `y0` to `y1`, its origin at the outline's centroid."""
    cx = sum(x for x, _ in outline) / len(outline)
    cz = sum(z for _, z in outline) / len(outline)
    bm = bmesh.new()
    front = [bm.verts.new((x - cx, y0, z - cz)) for x, z in outline]
    back = [bm.verts.new((x - cx, y1, z - cz)) for x, z in outline]
    n = len(outline)
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], back[i], back[j], front[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth()
    mesh.set_sharp_from_angle(angle=math.radians(35))
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (cx, 0, cz)
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width, mod.segments, mod.limit_method = bevel, 2, "ANGLE"
        mod.angle_limit = math.radians(40)
    return obj


def _sector(a0, a1, r_in=R_IN, r_out=R_OUT):
    """The (x, z) outline of the arch ring between angles a0 and a1 (degrees)."""
    n = max(1, round(abs(a1 - a0) / ARC_STEP))
    angles = [math.radians(a0 + (a1 - a0) * k / n) for k in range(n + 1)]
    outer = [(r_out * math.cos(a), SPRING + r_out * math.sin(a)) for a in angles]
    inner = [(r_in * math.cos(a), SPRING + r_in * math.sin(a)) for a in reversed(angles)]
    return outer + inner


def _ground(obj):
    """Lower or lift `obj` so its lowest vertex rests on z = 0."""
    low = min((obj.matrix_basis @ v.co).z for v in obj.data.vertices)
    obj.location.z -= low


def _segment(name, p, q, r, mat):
    """A thin cylinder from p to q."""
    d = [q[i] - p[i] for i in range(3)]
    length = math.sqrt(sum(c * c for c in d))
    tilt = math.degrees(math.acos(max(-1.0, min(1.0, d[2] / length))))
    yaw = math.degrees(math.atan2(d[1], d[0]))
    cylinder(name, r, length, p, mat, segments=5, rot=(tilt, 0, yaw + 90), bevel=0)


def _course_blocks(rnd, x0, x1, z0, z1, splits, mats, name):
    """One course of blocks between x0 and x1, split at the given fractions, with joints and a little jitter."""
    edges = [x0] + [x0 + (x1 - x0) * f for f in splits] + [x1]
    for k in range(len(edges) - 1):
        a, b = edges[k], edges[k + 1]
        box(f"{name}_{k}", (b - a - JOINT, DEPTH + rnd.uniform(-0.02, 0.015), z1 - z0 - JOINT),
            ((a + b) / 2 + rnd.uniform(-0.005, 0.005), rnd.uniform(-0.01, 0.01), (z0 + z1) / 2), rnd.choice(mats),
            rot=(0, 0, rnd.uniform(-1.2, 1.2)), bevel=0.02)


@prop
def ruin_arch_stone():
    rnd = random.Random(416)
    stone = material("ruin_arch_stone_stone", STONE, vary=0.3, scale=7, crevice=0.65)
    old = material("ruin_arch_stone_old", STONE_OLD, vary=0.3, scale=8, crevice=0.7)
    pale = material("ruin_arch_stone_pale", STONE_PALE, vary=0.25, scale=9, crevice=0.6)
    mats = (stone, stone, old, pale)
    mortar = material("ruin_arch_stone_mortar", MORTAR, vary=0.12, scale=20, crevice=0.9)
    moss = material("ruin_arch_stone_moss", MOSS, rough=0.95, vary=0.35, scale=16, crevice=0.6)
    ivy = [material(f"ruin_arch_stone_ivy_{k}", c, rough=0.8, vary=0.3, scale=30, crevice=0.4)
           for k, c in enumerate(IVY)]
    vine = material("ruin_arch_stone_vine", VINE, rough=0.9, vary=0.25, scale=40, crevice=0.4)
    grass = material("ruin_arch_stone_grass", GRASS, rough=0.95, vary=0.35, scale=10)

    # The piers: a mortar core and coursed blocks round it, joints staggered course to course.
    for side, courses in ((-1, round(SPRING / COURSE_H)), (1, RIGHT_COURSES)):
        x0, x1 = side * PIER_X - PIER_W / 2, side * PIER_X + PIER_W / 2
        top = courses * COURSE_H
        box(f"pier_core_{side}", (PIER_W - 2 * INSET, DEPTH - 2 * INSET, top - 0.02), (side * PIER_X, 0, top / 2),
            mortar, bevel=0)
        for c in range(courses):
            split = (0.45,) if c % 2 else (0.6,)
            _course_blocks(rnd, x0, x1, c * COURSE_H, (c + 1) * COURSE_H, split, mats, f"pier_{side}_{c}")
    # The right pier's broken top: one block slumped askew, a chip beside it.
    rt = RIGHT_COURSES * COURSE_H
    box("slumped", (0.42, DEPTH * 0.9, COURSE_H - JOINT), (PIER_X + 0.08, -0.04, rt + COURSE_H / 2 - 0.03), old,
        rot=(4, -11, 6), bevel=0.02)
    box("chip", (0.18, 0.3, 0.12), (PIER_X - 0.2, 0.18, rt + 0.05), stone, rot=(6, 8, 20), bevel=0.015)

    # The wall stump over the left pier, outside the arch: narrowing courses, a ragged top.
    sx1 = -R_OUT - 0.02
    sx0 = -PIER_X - PIER_W / 2
    core_w = (sx1 - sx0) * (1 - 0.12 * (STUMP_COURSES - 3)) - 2 * INSET  # as wide as the narrowest course
    box("stump_core", (core_w, DEPTH - 2 * INSET, STUMP_COURSES * COURSE_H - 0.12),
        (sx0 + INSET + core_w / 2, 0, SPRING + (STUMP_COURSES * COURSE_H - 0.12) / 2), mortar, bevel=0)
    for c in range(STUMP_COURSES):
        z0 = SPRING + c * COURSE_H
        w = (sx1 - sx0) * (1 - 0.12 * max(0, c - 2))
        _course_blocks(rnd, sx0, sx0 + w, z0, z0 + COURSE_H, (), mats, f"stump_{c}")

    # The arch: voussoirs from the left springing past the crown; the last one sags out of line.
    step = 180 / VOUSSOIRS
    for k in range(KEPT):
        a0, a1 = 180 - k * step - JOINT * 20, 180 - (k + 1) * step + JOINT * 20
        sag = k == KEPT - 1
        o = _prism(f"voussoir_{k}", _sector(a0, a1, R_IN + rnd.uniform(-0.01, 0.01), R_OUT + rnd.uniform(-0.02, 0.01)),
                   -DEPTH / 2 + rnd.uniform(0, 0.02), DEPTH / 2 - rnd.uniform(0, 0.02),
                   pale if k == 3 else rnd.choice(mats), 0.02)
        if sag:
            o.location.z -= 0.05
            o.location.x -= 0.01
            o.rotation_euler.y = math.radians(7)
    _prism("arch_core", _sector(180, 180 - (KEPT - 1) * step, R_IN + INSET, R_OUT - INSET), -DEPTH / 2 + INSET,
           DEPTH / 2 - INSET, mortar, 0)

    # Fallen pieces in the grass: a voussoir and loose blocks, mostly by the broken right side.
    fallen = []
    o = _prism("fallen_voussoir", _sector(90 - step / 2, 90 + step / 2), -0.2, 0.2, old, 0.02)
    o.location = (0.35, -0.2, 0)
    o.rotation_euler = (math.radians(90), math.radians(15), math.radians(-30))
    fallen.append(o)
    for k, (x, y, sx, sy, sz, rot) in enumerate(((1.15, -0.36, 0.42, 0.34, 0.24, (8, -14, 25)),
                                                 (-0.15, 0.36, 0.36, 0.3, 0.22, (-6, 4, -12)),
                                                 (0.9, 0.38, 0.32, 0.28, 0.2, (20, 10, 40)),
                                                 (0.5, -0.38, 0.22, 0.2, 0.14, (30, -20, 10)))):
        fallen.append(box(f"fallen_{k}", (sx, sy, sz), (x, y, 0), rnd.choice(mats), rot=rot, bevel=0.02))
    for o in fallen:
        _ground(o)
    for k in range(6):  # rubble
        r = rnd.uniform(0.04, 0.08)
        blob(f"rubble_{k}", r, (rnd.uniform(-0.6, 1.25), rnd.uniform(-0.42, 0.42), r * 0.6 * 1.2), rnd.choice(mats),
             squash=(1.2, 1.0, 0.6), subdiv=1, seed=100 + k, jitter=0.2)

    # Grass at the foot of the piers.
    for k, (x, y, r) in enumerate(((-1.3, -0.42, 0.14), (-0.8, -0.42, 0.12), (-1.1, 0.42, 0.14), (0.85, -0.42, 0.12),
                                   (1.3, 0.4, 0.13), (1.32, -0.3, 0.11))):
        blob(f"grass_{k}", r, (x, y, r * 0.4 * 1.15), grass, squash=(1.2, 0.7, 0.4), subdiv=2, seed=120 + k,
             jitter=0.12)

    # Moss on the broken tops.
    for k, (x, y, z) in enumerate(((-1.3, 0.1, SPRING + STUMP_COURSES * COURSE_H - 0.02), (0.9, 0.15, rt),
                                   (0.95, -0.2, rt), (-0.6, 0.0, SPRING + R_OUT))):
        blob(f"moss_{k}", rnd.uniform(0.07, 0.1), (x, y, z - 0.03), moss, squash=(1.5, 1.2, 0.45), subdiv=1,
             seed=130 + k)

    # Ivy: a vine climbing the front of the left pier, along the top of the arch, with leaves round it.
    front = -DEPTH / 2 - 0.012
    path = [(-1.25, front, 0.05), (-1.15, front, 0.6), (-1.3, front, 1.2), (-1.05, front, 1.75), (-1.2, front, 2.3),
            (-1.0, front, 2.75)]
    for k in range(len(path) - 1):
        _segment(f"vine_{k}", path[k], path[k + 1], 0.012, vine)
    leaves = 0

    def leaf(at, rot):
        nonlocal leaves
        box(f"leaf_{leaves}", (0.09, 0.006, 0.07), at, rnd.choice(ivy), rot=rot, bevel=0)
        leaves += 1

    for k in range(len(path) - 1):
        p, q = path[k], path[k + 1]
        n = 7 if k < 3 else 9
        for j in range(n):
            t = (j + rnd.random()) / n
            x = p[0] + (q[0] - p[0]) * t + rnd.uniform(-0.16, 0.16)
            z = p[2] + (q[2] - p[2]) * t + rnd.uniform(-0.05, 0.05)
            leaf((max(-1.43, x), front - rnd.uniform(0.0, 0.02), z), (rnd.uniform(-25, 10), rnd.uniform(0, 360), 0))
    # Over the arch: leaves on the extrados and hanging down its front face.
    for j in range(32):
        a = math.radians(rnd.uniform(95, 178))
        if j % 2:
            r = R_OUT + 0.01
            leaf((r * math.cos(a), rnd.uniform(-0.38, 0.0), SPRING + r * math.sin(a)),
                 (90 + rnd.uniform(-15, 15), 90 - math.degrees(a), 0))
        else:
            r = R_OUT - rnd.uniform(0.02, 0.18)
            leaf((r * math.cos(a), front - 0.01, SPRING + r * math.sin(a)), (rnd.uniform(-25, 10), rnd.uniform(0, 360), 0))
    arc = [((R_OUT + 0.012) * math.cos(math.radians(a)), -0.2, SPRING + (R_OUT + 0.012) * math.sin(math.radians(a)))
           for a in (178, 160, 140, 120, 100)]
    for k in range(len(arc) - 1):
        _segment(f"vine_arch_{k}", arc[k], arc[k + 1], 0.01, vine)
