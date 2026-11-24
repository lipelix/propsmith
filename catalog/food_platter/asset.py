"""A wooden serving board with a handle, laid with a round crusty loaf scored across the top, a wedge of yellow cheese
with a dark rind cut from a wheel, a cured ham leg with its bone end sticking out and a carving knife lying across the
board's front edge."""
import math
import random

import bpy
from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# About 0.6 x 0.4 x 0.2 m.
BOARD_X, BOARD_Y, BOARD_T = 0.5, 0.36, 0.03
HANDLE_L, HANDLE_W = 0.075, 0.09  # the handle sticks out at +x
LOAF_R, LOAF_H = 0.095, 0.11
CHEESE_R, CHEESE_H, CHEESE_A = 0.13, 0.08, 50  # the wheel's radius, height and the wedge's angle in degrees
HAM_L, HAM_R = 0.24, 0.07

WOOD = (0.25, 0.165, 0.09)  # linear RGB
WOOD_DARK = (0.17, 0.105, 0.055)
CRUST = (0.32, 0.15, 0.05)
CRUST_DARK = (0.2, 0.085, 0.03)
CRUMB = (0.45, 0.36, 0.2)
CHEESE = (0.48, 0.34, 0.09)
RIND = (0.25, 0.13, 0.04)
HAM = (0.33, 0.1, 0.07)
HAM_CUT = (0.45, 0.2, 0.15)
FAT = (0.45, 0.38, 0.28)
BONE = (0.42, 0.37, 0.28)
STEEL = (0.2, 0.2, 0.19)


def _rod(name, r, a, b, mat, segments=8, bevel=0.002, r_top=None):
    """A round rod from point `a` to point `b`."""
    d = Vector(b) - Vector(a)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return cylinder(name, r, d.length, a, mat, r_top=r_top, segments=segments,
                    rot=tuple(math.degrees(x) for x in rot), bevel=bevel)


def _prism(name, outline, z0, h, mat, bevel=0.004):
    """A closed prism: the convex polygon `outline` [(x, y), …] extruded from z0 up by `h`."""
    n = len(outline)
    verts = [(x, y, z0) for x, y in outline] + [(x, y, z0 + h) for x, y in outline]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    mesh.materials.append(mat)
    mesh.shade_smooth()
    mesh.set_sharp_from_angle(angle=math.radians(35))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width, mod.segments, mod.limit_method = bevel, 2, "ANGLE"
    return obj


@prop
def food_platter():
    rnd = random.Random(5)
    wood = material("food_platter_board", WOOD, vary=0.25, scale=18)
    wood_dark = material("food_platter_wood_dark", WOOD_DARK, vary=0.25, scale=16)
    crust = material("food_platter_crust", CRUST, rough=0.75, vary=0.3, scale=30, crevice=0.6)
    crust_dark = material("food_platter_crust_dark", CRUST_DARK, rough=0.75, vary=0.3, scale=30)
    crumb = material("food_platter_crumb", CRUMB, rough=0.9, vary=0.2, scale=60)
    cheese = material("food_platter_cheese", CHEESE, rough=0.6, vary=0.15, scale=40, crevice=0.4)
    rind = material("food_platter_rind", RIND, rough=0.7, vary=0.25, scale=30)
    ham = material("food_platter_ham", HAM, rough=0.6, vary=0.3, scale=20, crevice=0.6)
    ham_cut = material("food_platter_ham_cut", HAM_CUT, rough=0.55, vary=0.2, scale=40)
    fat = material("food_platter_fat", FAT, rough=0.6, vary=0.15, scale=30)
    bone = material("food_platter_bone", BONE, rough=0.7, vary=0.15, scale=30)
    steel = material("food_platter_steel", STEEL, rough=0.35, vary=0.15, scale=20, metal=0.8)

    # The board: a thick slab with rounded-off corners and a handle with a hole-less grip at +x.
    t = BOARD_T
    bx, by = BOARD_X / 2, BOARD_Y / 2
    c = 0.04
    outline = [(-bx + c, -by), (bx - c, -by), (bx, -by + c), (bx, -HANDLE_W / 2), (bx + HANDLE_L, -HANDLE_W / 2 + 0.015),
               (bx + HANDLE_L + 0.012, 0), (bx + HANDLE_L, HANDLE_W / 2 - 0.015), (bx, HANDLE_W / 2), (bx, by - c),
               (bx - c, by), (-bx + c, by), (-bx, by - c), (-bx, -by + c)]
    ox = -HANDLE_L / 2
    _prism("board", [(x + ox, y) for x, y in outline], 0, t, wood, bevel=0.006)
    for i in range(3):
        y = rnd.uniform(-by + 0.05, by - 0.05)
        box(f"board_score_{i}", (rnd.uniform(0.08, 0.16), 0.003, 0.002), (rnd.uniform(-0.1, 0.1) + ox, y, t + 0.0005),
            wood_dark, rot=(0, 0, rnd.uniform(-30, 30)), bevel=0)

    # The loaf: a round crusty boule with three scores across its top, at the back left.
    lx, ly = -0.13 + ox, 0.06
    loaf = blob("loaf", LOAF_R, (lx, ly, t + LOAF_H * 0.42), crust, squash=(1.05, 1.0, LOAF_H / (2 * LOAF_R) * 1.15),
                subdiv=3, seed=2, jitter=0.03)
    loaf.rotation_euler = (0, 0, 0)
    for k in (-1, 0, 1):
        box(f"loaf_score_{k}", (0.11 - 0.03 * abs(k), 0.014, 0.01),
            (lx + 0.005, ly + k * 0.036, t + LOAF_H - 0.007 - 0.014 * abs(k)), crust_dark, rot=(k * 16, 0, 25),
            bevel=0.003)

    # The cheese: a wedge cut from a wheel, rind on the curved back and the cut faces pale.
    cx, cy = 0.09 + ox, 0.07
    seg = 6
    a0 = math.radians(-CHEESE_A / 2)
    arc = [(CHEESE_R * math.cos(a0 + math.radians(CHEESE_A) * i / seg),
            CHEESE_R * math.sin(a0 + math.radians(CHEESE_A) * i / seg)) for i in range(seg + 1)]
    wedge = _prism("cheese", [(0, 0)] + arc, 0, CHEESE_H, cheese, bevel=0.004)
    wedge.location = (cx, cy, t)
    wedge.rotation_euler = (0, 0, math.radians(120))
    rind_arc = [((CHEESE_R + 0.008) * math.cos(a0 + math.radians(CHEESE_A) * i / seg),
                 (CHEESE_R + 0.008) * math.sin(a0 + math.radians(CHEESE_A) * i / seg)) for i in range(seg + 1)]
    rind_in = [(x * (CHEESE_R - 0.004) / CHEESE_R, y * (CHEESE_R - 0.004) / CHEESE_R) for x, y in reversed(arc)]
    r_obj = _prism("cheese_rind", rind_arc + rind_in, 0.002, CHEESE_H + 0.002, rind, bevel=0.003)
    r_obj.location = (cx, cy, t)
    r_obj.rotation_euler = wedge.rotation_euler
    for i in range(4):  # a few holes on the cut faces
        a = math.radians(120 + rnd.choice((-CHEESE_A / 2, CHEESE_A / 2)))
        d = rnd.uniform(0.03, 0.1)
        n = Vector((-math.sin(a), math.cos(a), 0)) * (1 if a > math.radians(120) else -1)
        p = Vector((cx + d * math.cos(a), cy + d * math.sin(a), t + rnd.uniform(0.02, 0.06)))
        blob(f"cheese_hole_{i}", rnd.uniform(0.006, 0.01), tuple(p + n * 0.001), rind, squash=(1, 1, 1), subdiv=1,
             seed=40 + i, jitter=0.1)

    # The ham: a cured leg lying along the front, its cut face towards -x and the shank bone out at +x.
    hx, hy = 0.04 + ox, -0.065
    blob("ham", HAM_R, (hx, hy, t + HAM_R * 0.8), ham, squash=(1.7, 1.0, 0.85), subdiv=2, seed=8, jitter=0.06)
    blob("ham_shank", HAM_R * 0.55, (hx + 0.1, hy - 0.005, t + HAM_R * 0.62), ham, squash=(1.6, 0.9, 0.85), subdiv=2,
         seed=9, jitter=0.05)
    bone_end = Vector((hx + 0.2, hy - 0.008, t + HAM_R * 0.65))
    _rod("ham_bone", 0.012, (hx + 0.12, hy - 0.006, t + HAM_R * 0.62), bone_end, bone, segments=8)
    blob("ham_knuckle", 0.018, tuple(bone_end), bone, squash=(1, 1.2, 1), subdiv=1, seed=11, jitter=0.08)
    _rod("ham_twine", 0.012 * 1.15, (hx + 0.135, hy - 0.006, t + HAM_R * 0.62), (hx + 0.145, hy - 0.006,
                                                                                t + HAM_R * 0.62), wood_dark,
         segments=8, bevel=0)

    # Two slices cut from the ham, overlapping at the front left: pink meat in a rim of fat.
    for i, (x, y, tilt) in enumerate([(-0.17, -0.1, 0), (-0.12, -0.115, 7)]):
        z = t + 0.004 * i
        cylinder(f"slice_fat_{i}", 0.05, 0.007, (x + ox, y, z), fat, segments=14, rot=(tilt, 0, 0),
                 bevel=0.002).scale = (1.25, 0.9, 1)
        cylinder(f"slice_meat_{i}", 0.043, 0.0072, (x + ox + 0.004, y, z + 0.0006), ham_cut, segments=14,
                 rot=(tilt, 0, 0), bevel=0.002).scale = (1.22, 0.85, 1)

    # The knife: a carving knife lying on the board's front edge, its handle over the edge.
    kx, ky = 0.16 + ox, -by + 0.03
    yaw = -12
    blade = box("knife_blade", (0.17, 0.026, 0.003), (kx, ky, t + 0.0035), steel, rot=(0, 0, yaw), bevel=0.001)
    blade.scale = (1, 1, 1)
    hd = Vector((math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0))
    guard = Vector((kx, ky, t + 0.009)) + hd * 0.088
    box("knife_bolster", (0.012, 0.03, 0.014), tuple(guard), steel, rot=(0, 0, yaw), bevel=0.002)
    _rod("knife_handle", 0.009, guard + hd * 0.006, guard + hd * 0.11, wood_dark, segments=8)
