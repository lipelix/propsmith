"""An archery target, front on -y: a round boss of coiled straw rope, faced with painted rings (pale, red, pale, blue
and a gold centre), leaning back on a timber tripod of two front legs and a back leg, resting on a ledge rail; two
arrows are stuck in it, one near the gold and one in the outer ring."""
import math
import random

from mathutils import Matrix, Vector

import bpy
from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall size: about 1.1 m wide (x), 0.9 m deep (y), 1.5 m high to the tops of the legs.
BOSS_R, BOSS_T = 0.43, 0.2  # the straw boss: radius and thickness
BOSS_Y, BOSS_Z = 0.0, 0.93  # its centre
TILT = 15  # degrees it leans back
RINGS = (0.4, 0.31, 0.22, 0.13, 0.055)  # the painted rings' outer radii, outside in
LEG_R = 0.035
FOOT_X = 0.5  # the front legs' feet, either side
BACK_Y = 0.42  # the back leg's foot
ARROW_L, ARROW_OUT = 0.75, 0.3  # arrow length and how much of it sticks out

STRAW = (0.45, 0.35, 0.12)  # linear RGB
STRAW_DARK = (0.3, 0.22, 0.08)
PALE = (0.38, 0.33, 0.24)
RED = (0.35, 0.06, 0.04)
BLUE = (0.06, 0.1, 0.2)
GOLD = (0.45, 0.32, 0.07)
WOOD = (0.2, 0.125, 0.065)
WOOD_OLD = (0.15, 0.1, 0.06)
SHAFT = (0.3, 0.2, 0.1)
FLETCH = (0.4, 0.38, 0.33)
FLETCH_DARK = (0.13, 0.1, 0.08)
ROPE = (0.3, 0.22, 0.12)


def _rod(name, r, a, b, mat, segments=8, bevel=0.003, r_top=None):
    """A round rod from point `a` to point `b`."""
    d = Vector(b) - Vector(a)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return cylinder(name, r, d.length, a, mat, r_top=r_top, segments=segments,
                    rot=tuple(math.degrees(x) for x in rot), bevel=bevel)


def _moved(build, matrix):
    """Run `build`, then move every object it added by `matrix`."""
    before = set(bpy.data.objects)
    build()
    for obj in set(bpy.data.objects) - before:
        obj.matrix_basis = matrix @ obj.matrix_basis


@prop
def archery_target():
    rnd = random.Random(17)
    straw = material("archery_target_straw", STRAW, rough=0.95, vary=0.35, scale=50, crevice=0.8)
    straw_dark = material("archery_target_straw_dark", STRAW_DARK, rough=0.95, vary=0.3, scale=50)
    paints = [material(f"archery_target_paint_{n}", c, rough=0.85, vary=0.3, scale=15)
              for n, c in (("pale", PALE), ("red", RED), ("pale_inner", PALE), ("blue", BLUE), ("gold", GOLD))]
    wood = material("archery_target_wood", WOOD, vary=0.28, scale=10)
    old = material("archery_target_wood_old", WOOD_OLD, vary=0.3, scale=9)
    shaft = material("archery_target_shaft", SHAFT, rough=0.6, vary=0.15, scale=20)
    fletch = material("archery_target_fletch", FLETCH, rough=0.9, vary=0.2, scale=30)
    fletch_dark = material("archery_target_fletch_dark", FLETCH_DARK, rough=0.9, vary=0.2, scale=30)
    rope = material("archery_target_rope", ROPE, rough=0.9, vary=0.25, scale=50)

    # The boss, built upright around its centre with the face on -y, then leaned back.
    r, t = BOSS_R, BOSS_T
    arrows = [(0.07, 0.05, 6, -8), (-0.28, -0.16, -10, 4)]  # (x, z, yaw, pitch) on the face

    def boss():
        cylinder("boss", r, t, (0, t / 2, 0), straw, segments=32, rot=(90, 0, 0), bevel=0.03)
        # The coils of straw rope round its rim.
        for i, y in enumerate((-t / 2 + 0.035, -0.02, 0.035, t / 2 - 0.035)):
            torus(f"boss_coil_{i}", r - 0.012, 0.03, (0, y, 0), straw_dark if i % 2 else straw, rot=(90, 0, 0),
                  major=32, minor=6)
        # The stitching of the coils across the face, under the paint.
        for i in range(12):
            a = 2 * math.pi * i / 12 + rnd.uniform(-0.1, 0.1)
            box(f"boss_stitch_{i}", (0.02, 0.008, 0.05), (0.415 * math.cos(a), -t / 2 - 0.006, 0.415 * math.sin(a)),
                straw_dark, rot=(0, -math.degrees(a), 0), bevel=0.002)
        # The painted rings, each a thin disc a little proud of the one behind.
        for i, (ring, paint) in enumerate(zip(RINGS, paints)):
            cylinder(f"ring_{i}", ring, 0.004, (0, -t / 2 + 0.002 - 0.0015 * i, 0), paint, segments=32,
                     rot=(90, 0, 0), bevel=0)
        # A few straw ends sticking out of the rim.
        for i in range(10):
            a = 2 * math.pi * i / 10 + rnd.uniform(-0.2, 0.2)
            y = rnd.uniform(-t / 2 + 0.03, t / 2 - 0.03)
            p = (r * math.cos(a), y, r * math.sin(a))
            q = ((r + rnd.uniform(0.03, 0.06)) * math.cos(a + 0.08), y + rnd.uniform(-0.03, 0.03),
                 (r + rnd.uniform(0.03, 0.06)) * math.sin(a + 0.08))
            _rod(f"boss_straw_{i}", 0.008, p, q, straw, segments=4, bevel=0, r_top=0.002)
        # The ledge rail it rests on, its ends on the front legs.
        box("ledge", (2 * r + 0.18, t + 0.06, 0.05), (0, 0.0, -r - 0.025), old, bevel=0.01)
        box("ledge_lip", (2 * r - 0.1, 0.025, 0.06), (0, -t / 2 - 0.045, -r + 0.005), wood, bevel=0.008)
        # Two arrows: shaft, a head buried in the straw, three fletches at the nock.
        for k, (x, z, yaw, pitch) in enumerate(arrows):
            d = Vector((math.sin(math.radians(yaw)), -1, math.sin(math.radians(pitch)))).normalized()
            hit = Vector((x, -t / 2 - 0.006, z))
            tail = hit + d * ARROW_OUT
            _rod(f"arrow_{k}", 0.0075, hit - d * (ARROW_L - ARROW_OUT), tail, shaft, segments=6, bevel=0)
            _rod(f"arrow_nock_{k}", 0.009, tail, tail + d * 0.012, fletch_dark, segments=6, bevel=0)
            side = d.cross(Vector((0, 0, 1))).normalized()
            up = side.cross(d).normalized()
            for j in range(3):
                a = 2 * math.pi * j / 3 + math.radians(30)
                n = side * math.cos(a) + up * math.sin(a)
                c = tail - d * 0.07 + n * 0.018
                fl = box(f"arrow_fletch_{k}_{j}", (0.003, 0.13, 0.032), (0, 0, 0), fletch if j else fletch_dark,
                         bevel=0)
                # Orient: local y along the shaft, local z outwards from it.
                m = Matrix(((-d).cross(n), -d, n)).transposed().to_4x4()
                fl.matrix_basis = Matrix.Translation(c) @ m

    tilt = Matrix.Translation((0, BOSS_Y, BOSS_Z)) @ Matrix.Rotation(math.radians(-TILT), 4, "X")
    _moved(boss, tilt)

    # The tripod: two front legs behind the boss's sides, a back leg propping it, lashed at the top.
    for side in (-1, 1):
        top = tilt @ Vector((side * 0.27, t / 2 + LEG_R + 0.005, r + 0.1))
        foot = Vector((side * FOOT_X, top.y - (top.z * math.tan(math.radians(TILT))), 0.013))
        leg = top - foot
        top = foot + leg * ((leg.length + 0.04) / leg.length)
        _rod(f"leg_{side}", LEG_R, foot, top, wood, segments=8, bevel=0.006)
        # The ledge rail's peg through the leg.
        mid = tilt @ Vector((side * (r + 0.05), 0, -r - 0.025))
        _rod(f"ledge_peg_{side}", 0.014, mid + Vector((0, -0.12, 0)), mid + Vector((0, 0.17, 0)), old, segments=6)
    top = tilt @ Vector((0, t / 2 + LEG_R + 0.02, r + 0.06))
    _rod("leg_back", LEG_R, (0, BACK_Y, 0.013), top + Vector((0, 0, 0.04)), old, segments=8, bevel=0.006)
    # A crossbar between the front legs at the top, lashed with rope.
    a = tilt @ Vector((-0.3, t / 2 + LEG_R * 2 + 0.01, r + 0.03))
    b = tilt @ Vector((0.3, t / 2 + LEG_R * 2 + 0.01, r + 0.03))
    _rod("top_bar", 0.028, a, b, old, segments=8)
    torus("lashing", 0.045, 0.012, tuple(tilt @ Vector((0, t / 2 + LEG_R + 0.03, r + 0.05))), rope,
          rot=(90 - TILT + 30, 0, 0), major=12, minor=6)
