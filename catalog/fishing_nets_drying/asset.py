"""Fishing nets hung to dry over a pole frame, front on -y: a long pole resting in the crotches of two crossed-pole
trestles lashed at the top, a tan net hung over it in loose folds, long at the front and shorter at the back, its foot
rope strung with cork floats, and a few more floats lying on the ground."""
import math
import random

import bmesh
import bpy
from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import cylinder, torus

# Overall size: about 2.5 m long (x), 0.8 m deep (y), 2 m high.
BAR_Z, BAR_R, BAR_L = 1.8, 0.042, 2.44  # the pole the net hangs on: height of its axis, radius, length
FRAME_X = 1.1  # the trestles stand at ±FRAME_X
LEG_Y, LEG_TOP_Y, LEG_R = 0.33, 0.035, 0.042  # a leg's foot (±y), where its top ends past the other leg, radius
NET_X = 0.98  # the net spans ±NET_X
MESH = 0.1  # the net's mesh (knot to knot)
DROP_FRONT, DROP_BACK = 1.42, 0.7  # how far the net hangs down each side
ROPE_R, FOOT_R = 0.008, 0.013  # net twine and foot rope radius (of the triangular prisms)
FLOAT_R, FLOAT_L = 0.034, 0.06

POLE = (0.17, 0.13, 0.09)  # linear RGB: weathered poles, as pier_wood's frame
POLE_OLD = (0.13, 0.105, 0.08)
NET = (0.22, 0.14, 0.07)  # tan-barked net
NET_OLD = (0.16, 0.11, 0.065)
CORK = (0.3, 0.19, 0.1)
ROPE = (0.34, 0.27, 0.16)  # hemp lashings, as pier_wood


def _net(name, rows, mat, foot_rows):
    """One mesh of rope prisms along every edge of the node grid `rows` (a list of rows of (x, y, z)); the edges of a
    row in `foot_rows` are the thicker foot rope."""
    bm = bmesh.new()

    def prism(a, b, r):
        a, b = Vector(a), Vector(b)
        d = (b - a).normalized()
        a, b = a - d * r, b + d * r
        u = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))).normalized()
        v = d.cross(u)
        ends = []
        for p in (a, b):
            ends.append([bm.verts.new(p + r * (u * math.cos(t) + v * math.sin(t)))
                         for t in (0, 2 * math.pi / 3, 4 * math.pi / 3)])
        for k in range(3):
            bm.faces.new((ends[0][k], ends[0][(k + 1) % 3], ends[1][(k + 1) % 3], ends[1][k]))

    for j, row in enumerate(rows):
        for i, p in enumerate(row):
            if i + 1 < len(row):
                prism(p, row[i + 1], FOOT_R if j in foot_rows else ROPE_R)
            if j + 1 < len(rows):
                prism(p, rows[j + 1][i], ROPE_R)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _rod(name, a, b, r, mat, segments=8, bevel=0.008):
    """A pole from point a to point b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    obj = cylinder(name, r, d.length, (0, 0, 0), mat, r_top=r * 0.92, segments=segments, bevel=bevel)
    obj.location = a
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return obj


@prop
def fishing_nets_drying():
    rnd = random.Random(115)
    pole = material("fishing_nets_drying_pole", POLE, vary=0.3, scale=10, crevice=0.6)
    pole_old = material("fishing_nets_drying_pole_old", POLE_OLD, vary=0.3, scale=10, crevice=0.6)
    net = material("fishing_nets_drying_net", NET, vary=0.35, scale=20, crevice=0.4)
    net_old = material("fishing_nets_drying_net_old", NET_OLD, vary=0.35, scale=20, crevice=0.4)
    cork = material("fishing_nets_drying_cork", CORK, rough=1.0, vary=0.4, scale=40, crevice=0.6)
    rope = material("fishing_nets_drying_rope", ROPE, vary=0.3, scale=30, crevice=0.6)

    # The trestles: two crossed legs at each end, lashed where they cross, the pole lying in the crotch.
    top_z = BAR_Z - BAR_R  # where the legs cross: just under the pole
    t_cross = LEG_Y / (LEG_Y + LEG_TOP_Y)
    leg_top = top_z / t_cross
    for e, x in enumerate((-FRAME_X, FRAME_X)):
        for s in (-1, 1):
            foot = (x + s * 0.035 + rnd.uniform(-0.01, 0.01), s * LEG_Y, 0)
            top = (x + s * 0.035, -s * LEG_TOP_Y, leg_top)
            _rod(f"leg_{e}_{s}", foot, top, LEG_R, pole if s > 0 else pole_old)
        torus(f"lashing_{e}", LEG_R * 1.9, 0.012, (x, 0, top_z - 0.02), rope, rot=(0, 90, 0), major=12, minor=5)
        torus(f"lashing_{e}_b", LEG_R * 1.9, 0.012, (x, 0, top_z - 0.02), rope, rot=(0, 90, 0), major=12,
              minor=5).scale = (1, 1, 1.3)
    _rod("bar", (-BAR_L / 2, 0, BAR_Z), (BAR_L / 2, 0.01, BAR_Z + 0.015), BAR_R, pole, segments=10)

    # The net's knots: a shared row over the pole, then rows hanging down each side in loose folds.
    nx = round(2 * NET_X / MESH) + 1
    xs = [-NET_X + 2 * NET_X * i / (nx - 1) for i in range(nx)]
    over = [(x + rnd.uniform(-0.01, 0.01), 0, BAR_Z + BAR_R + ROPE_R) for x in xs]

    def side(sign, drop, phase, seed):
        r = random.Random(seed)
        rows = [over]
        n = round(drop / MESH)
        lengths = [drop * (1 + 0.07 * math.sin(1.1 * i + phase) - 0.05 * math.cos(0.43 * i)) for i in range(nx)]
        for j in range(1, n + 1):
            row = []
            for i, x in enumerate(xs):
                f = j / n
                z = BAR_Z - (lengths[i] - BAR_R) * f
                fold = 0.07 * math.sin(7.5 * x + phase) * f + 0.03 * math.sin(17 * x + 2 * phase) * f
                y = sign * (BAR_R + ROPE_R + 0.03 * f + fold + 0.06 * f * f) if j > 1 else sign * (BAR_R + ROPE_R)
                gather = -0.06 * math.sin(math.pi * x / NET_X) * f  # the hanging net draws in a little at the foot
                row.append((x + gather + r.uniform(-0.012, 0.012), y + r.uniform(-0.01, 0.01),
                            z + r.uniform(-0.012, 0.012)))
            rows.append(row)
        return rows

    front = side(-1, DROP_FRONT, 0.4, 7)
    back = side(1, DROP_BACK, 2.1, 8)
    _net("net_front", front, net, {len(front) - 1})
    _net("net_back", back, net_old, {len(back) - 1})

    # Cork floats strung on the foot ropes, every other knot.
    for name, rows, step in (("front", front, 2), ("back", back, 3)):
        foot = rows[-1]
        for i in range(1, len(foot) - 1, step):
            a, b = Vector(foot[i - 1]), Vector(foot[i + 1])
            d = (b - a).normalized()
            c = Vector(foot[i]) - d * FLOAT_L / 2
            obj = cylinder(f"float_{name}_{i}", FLOAT_R, FLOAT_L, (0, 0, 0), cork, r_top=FLOAT_R * 0.9, segments=8,
                           bevel=0)
            obj.location = c
            obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()

    # Spare floats lying on the ground under the net.
    for k, (x, y) in enumerate(((-0.55, -0.3), (-0.47, -0.33), (0.62, 0.24))):
        cylinder(f"spare_float_{k}", FLOAT_R, FLOAT_L, (x, y, FLOAT_R), cork, r_top=FLOAT_R * 0.9, segments=8,
                 rot=(90, 0, rnd.uniform(0, 180)), bevel=0)
