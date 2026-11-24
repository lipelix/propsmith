"""A hollowed-log water trough, front on -y: a long barked log hewn flat on top and dug out into a U, its ends left
solid, full nearly to the rim with still dark water, resting on two squared timber blocks with a wedge under one side,
a wooden bung in one end and a little moss and wet earth at its foot."""
import math
import random

import bmesh
import bpy
from mathutils import Vector

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall size: about 1.8 m long (x), 0.5 m deep (y), 0.5 m high to the rim.
L = 1.72  # log length
R, WALL = 0.24, 0.05  # log radius and wall thickness
END = 0.12  # the solid ends left in the log
BLOCK = (0.24, 0.5, 0.14)  # the two timber blocks under it (x, y, z)
BLOCK_X = 0.56
SINK = 0.03  # how far the log beds into the blocks
C = BLOCK[2] - SINK + R  # the log's axis height
RIM = 0.48  # the hewn flat top
WATER = RIM - 0.045  # the water surface
SEG = 20  # points along the U

BARK = (0.1, 0.07, 0.045)  # linear RGB
HEWN = (0.22, 0.15, 0.085)
END_GRAIN = (0.26, 0.19, 0.11)
BLOCK_WOOD = (0.17, 0.12, 0.075)
WATER_COL = (0.025, 0.05, 0.055)
MOSS = (0.09, 0.12, 0.035)
EARTH = (0.08, 0.06, 0.04)


def _link(name, bm, mats, bevel=0.0):
    """Make a mesh object of `bm` with the materials `mats` (face material_index picks one) and an optional bevel."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth()
    mesh.set_sharp_from_angle(angle=math.radians(35))
    for m in mats:
        mesh.materials.append(m)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width, mod.segments, mod.limit_method = bevel, 2, "ANGLE"
    return obj


def _arc(r, top):
    """Points (y, z) on a circle of radius `r` round the axis, from the right side at height `top` under the bottom to
    the left side at the same height."""
    phi = math.asin((top - C) / r)
    span = math.pi + 2 * phi
    return [(r * math.cos(phi - span * k / SEG), C + r * math.sin(phi - span * k / SEG)) for k in range(SEG + 1)]


def _prism(name, profile, x0, x1, mats, side_mat=0, cap_mat=1, bevel=0.0):
    """A closed prism of the convex `profile` [(y, z), ...] from x0 to x1."""
    bm = bmesh.new()
    a = [bm.verts.new((x0, y, z)) for y, z in profile]
    b = [bm.verts.new((x1, y, z)) for y, z in profile]
    n = len(profile)
    for k in range(n):
        f = bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
        f.material_index = side_mat
    for ring in (a, b):
        bm.faces.new(ring).material_index = cap_mat
    return _link(name, bm, mats, bevel)


def _trough(name, x0, x1, mats):
    """The dug-out middle of the log: a closed U-shaped shell, bark outside (material 0), hewn wood inside (1)."""
    outer = _arc(R, RIM)
    inner = _arc(R - WALL, RIM)
    bm = bmesh.new()
    rows = [[[bm.verts.new((x, y, z)) for y, z in pts] for pts in (outer, inner)] for x in (x0, x1)]
    (oa, ia), (ob, ib) = rows
    for k in range(SEG):
        bm.faces.new((oa[k], oa[k + 1], ob[k + 1], ob[k])).material_index = 0
        bm.faces.new((ia[k], ib[k], ib[k + 1], ia[k + 1])).material_index = 1
        bm.faces.new((oa[k], ia[k], ia[k + 1], oa[k + 1])).material_index = 1
        bm.faces.new((ob[k], ob[k + 1], ib[k + 1], ib[k])).material_index = 1
    for k in (0, SEG):  # the two hewn rims
        bm.faces.new((oa[k], ob[k], ib[k], ia[k])).material_index = 1
    return _link(name, bm, mats, bevel=0.012)


@prop
def water_trough():
    rnd = random.Random(18)
    bark = material("water_trough_bark", BARK, rough=1.0, vary=0.45, scale=24, crevice=0.8)
    hewn = material("water_trough_hewn", HEWN, vary=0.3, scale=12)
    grain = material("water_trough_end_grain", END_GRAIN, vary=0.3, scale=30, crevice=0.7)
    block = material("water_trough_block", BLOCK_WOOD, vary=0.3, scale=9)
    water = material("water_trough_water", WATER_COL, rough=0.05, vary=0.1, scale=4, crevice=0)
    moss = material("water_trough_moss", MOSS, rough=1.0, vary=0.4, scale=30)
    earth = material("water_trough_earth", EARTH, rough=1.0, vary=0.3, scale=12)

    # The blocks, a wedge under one, and wet earth where the water slops over.
    for i, x in enumerate((-BLOCK_X, BLOCK_X)):
        box(f"block_{i}", BLOCK, (x, rnd.uniform(-0.01, 0.01), BLOCK[2] / 2), block,
            rot=(0, 0, rnd.uniform(-4, 4)), bevel=0.015)
    box("wedge", (0.12, 0.06, 0.035), (BLOCK_X + 0.02, -R * 0.75, BLOCK[2] + 0.0), block, rot=(0, -12, 8),
        bevel=0.004)
    cylinder("wet_earth", 0.25, 0.008, (-0.15, -0.02, 0), earth, segments=14, bevel=0).scale = (2.6, 1.0, 1)
    for i in range(3):
        blob(f"moss_{i}", 0.05, (-BLOCK_X + rnd.uniform(-0.08, 0.08), -BLOCK[1] / 2 + 0.02, 0.03 + 0.03 * i), moss,
             squash=(1.4, 0.5, 0.7), subdiv=1, seed=30 + i)

    # The log: solid ends, the dug-out middle, and the water in it.
    x0, x1 = -L / 2, L / 2
    _prism("end_left", _arc(R, RIM), x0, x0 + END, [bark, grain], bevel=0.012)
    _prism("end_right", _arc(R, RIM), x1 - END, x1, [bark, grain], bevel=0.012)
    _trough("trough", x0 + END - 0.01, x1 - END + 0.01, [bark, hewn])
    _prism("water", _arc(R - WALL + 0.004, WATER), x0 + END - 0.005, x1 - END + 0.005, [water, water])

    # The ends show growth rings and a crack; a bung plugs a drain hole in the right end.
    for side, x in ((-1, x0), (1, x1)):
        for i, r in enumerate((0.13, 0.07)):
            cylinder(f"ring_{side}_{i}", r, 0.002 * (i + 1), (x, 0, C - 0.01), bark, segments=16,
                     rot=(0, 90 * side, 0), bevel=0)
        box(f"crack_{side}", (0.006, 0.01, R * 0.8), (x + side * 0.002, 0.02, C - R * 0.45), bark,
            rot=(rnd.uniform(-10, 10), 0, 0), bevel=0)
    cylinder("bung", 0.03, 0.06, (x1 - 0.02, -0.06, C - R * 0.55), hewn, r_top=0.024, segments=10, rot=(0, 90, 0),
             bevel=0.004)

    # Bark detail: knots and a strip of bark gone, and a crack along the rim.
    for i, (x, a) in enumerate(((-0.5, -40), (0.2, -70), (0.6, -25))):
        t = math.radians(a)
        blob(f"knot_{i}", 0.035, (x, -R * math.cos(t) * 0.97, C + R * math.sin(t)), bark, squash=(1, 0.5, 1),
             subdiv=1, seed=50 + i)
    box("rim_crack", (0.4, 0.008, 0.01), (-0.2, -0.17, RIM), bark, rot=(0, 0, 2),
        bevel=0)

    anchor("water:basin", (0, 0, WATER), size=(L / 2 - END, (R - WALL) * 0.7, WATER - (C - R + WALL)))
