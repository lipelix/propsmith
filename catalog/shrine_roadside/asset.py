"""A small roofed wayside shrine about 0.6 × 0.5 × 1.8 m: a square stone post on a low footing carries a stone niche open
to the front (-y) under a steep gabled roof of weathered boards. In the niche stand a painted icon panel against the
back wall, a lit candle and a small clay pot of wildflowers; a little bunch of flowers lies on the footing. A light
anchor sits at the candle flame."""
import math
import random

import bmesh
import bpy

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall dimensions (metres): about 0.6 × 0.5 × 1.8.
FOOT = (0.44, 0.4, 0.1)  # footing slab
POST = (0.22, 0.2)  # post cross-section
SHELF_Z = 0.98  # top of the post
SHELF = (0.44, 0.36, 0.06)  # slab the niche stands on
NICHE = (0.4, 0.32, 0.36)  # the niche box outside: x, y, height
WALL = 0.05  # niche wall thickness
LINTEL = (0.46, 0.38, 0.05)
PITCH = 45  # roof pitch, degrees
ROOF_SPAN = 0.54  # roof width over the eaves
ROOF_DEPTH = 0.5
BOARD = 0.03  # roof board thickness
NICHE_Z = SHELF_Z + SHELF[2]  # niche floor
ROOF_Z = NICHE_Z + NICHE[2] + LINTEL[2]  # top of the lintel: the roof's foot

STONE = (0.27, 0.255, 0.225)  # linear RGB: weathered grey-brown stone
STONE_OLD = (0.2, 0.19, 0.17)
WOOD = (0.15, 0.095, 0.055)  # weathered roof boards
WOOD_DARK = (0.1, 0.065, 0.04)
ICON = (0.12, 0.17, 0.3)  # muted blue painted ground
GILT = (0.42, 0.3, 0.1)  # ochre gilding
WAX = (0.5, 0.46, 0.36)
FLAME = (0.5, 0.3, 0.06)
CLAY = (0.3, 0.13, 0.06)
STEM = (0.06, 0.1, 0.03)
PETALS = ((0.46, 0.38, 0.1), (0.4, 0.12, 0.1), (0.3, 0.2, 0.42), (0.48, 0.44, 0.36))
MOSS = (0.06, 0.085, 0.03)


def _prism(name, outline, y0, y1, mat, bevel):
    """A closed prism: the (x, z) `outline` extruded from `y0` to `y1`."""
    bm = bmesh.new()
    front = [bm.verts.new((x, y0, z)) for x, z in outline]
    back = [bm.verts.new((x, y1, z)) for x, z in outline]
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
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width, mod.segments, mod.limit_method = bevel, 2, "ANGLE"
    return obj


def _flower(name, x, y, z, length, lean, yaw, colour, stem, rnd):
    """A thin stem `length` long leaning `lean` degrees toward `yaw`, with a small round flower head."""
    a, b = math.radians(lean), math.radians(yaw)
    cylinder(f"{name}_stem", 0.004, length, (x, y, z), stem, segments=5, rot=(lean, 0, yaw + 90), bevel=0)
    tip = (x + math.sin(a) * math.cos(b) * length, y + math.sin(a) * math.sin(b) * length, z + math.cos(a) * length)
    blob(f"{name}_head", rnd.uniform(0.016, 0.022), tip, colour, squash=(1, 1, 0.7), subdiv=1, seed=rnd.randrange(999))


@prop
def shrine_roadside():
    rnd = random.Random(316)
    stone = material("shrine_roadside_stone", STONE, vary=0.3, scale=8, crevice=0.65)
    old = material("shrine_roadside_stone_old", STONE_OLD, vary=0.3, scale=9, crevice=0.7)
    wood = material("shrine_roadside_wood", WOOD, vary=0.3, scale=14, crevice=0.55)
    wood_dark = material("shrine_roadside_wood_dark", WOOD_DARK, vary=0.3, scale=14, crevice=0.55)
    icon = material("shrine_roadside_icon", ICON, vary=0.2, scale=20, crevice=0.3)
    gilt = material("shrine_roadside_gilt", GILT, rough=0.45, vary=0.2, scale=20, crevice=0.4, metal=0.5)
    wax = material("shrine_roadside_wax", WAX, rough=0.5, vary=0.1, scale=20, crevice=0.3)
    flame = material("shrine_roadside_flame", FLAME, rough=0.4, vary=0.1, scale=20, crevice=0.0)
    clay = material("shrine_roadside_clay", CLAY, vary=0.25, scale=14, crevice=0.5)
    stem = material("shrine_roadside_stem", STEM, rough=0.9, vary=0.2, scale=30, crevice=0.3)
    petals = [material(f"shrine_roadside_petal_{k}", c, rough=0.8, vary=0.2, scale=30, crevice=0.3)
              for k, c in enumerate(PETALS)]
    moss = material("shrine_roadside_moss", MOSS, rough=0.95, vary=0.35, scale=16, crevice=0.6)

    # Footing, post and the shelf slab.
    box("footing", FOOT, (0, 0, FOOT[2] / 2), old, rot=(0, 0, 2), bevel=0.02)
    box("post", (POST[0], POST[1], SHELF_Z - FOOT[2] + 0.01), (0, 0, (SHELF_Z + FOOT[2]) / 2), stone, bevel=0.015)
    box("shelf", SHELF, (0, -0.01, SHELF_Z + SHELF[2] / 2), old, bevel=0.015)

    # The niche: back wall, two side walls, open to the front; a lintel slab on top.
    nx, ny, nh = NICHE
    zc = NICHE_Z + nh / 2
    box("niche_back", (nx, WALL, nh), (0, ny / 2 - WALL / 2, zc), stone, bevel=0.012)
    for s in (-1, 1):
        box(f"niche_side_{s}", (WALL, ny - WALL + 0.005, nh), (s * (nx / 2 - WALL / 2), -WALL / 2, zc), stone,
            rot=(0, 0, rnd.uniform(-1, 1)), bevel=0.012)
    box("lintel", LINTEL, (0, -0.01, ROOF_Z - LINTEL[2] / 2), old, bevel=0.015)

    # The gabled roof: a gable block, two sloping board panels, a ridge board.
    half = ROOF_SPAN / 2 - 0.04
    rise = half * math.tan(math.radians(PITCH))
    _prism("gable", [(-half + 0.02, ROOF_Z), (half - 0.02, ROOF_Z), (0, ROOF_Z + rise - 0.02)],
           -LINTEL[1] / 2 + 0.01, LINTEL[1] / 2 - 0.01, wood_dark, 0.006)
    c, s_ = math.cos(math.radians(PITCH)), math.sin(math.radians(PITCH))
    length = ROOF_SPAN / 2 / c + 0.02
    ridge = (0, ROOF_Z + rise)
    for s in (-1, 1):
        # The panel runs down from the ridge along (s*c, -s_), lifted by half its thickness along its normal.
        mx = ridge[0] + s * c * length / 2 + s * s_ * BOARD / 2
        mz = ridge[1] - s_ * length / 2 + c * BOARD / 2
        box(f"roof_{s}", (length, ROOF_DEPTH, BOARD), (mx, 0, mz), wood, rot=(0, s * PITCH, 0), bevel=0.008)
        # Board joints: thin dark strips across each panel.
        for k in range(1, 4):
            y = -ROOF_DEPTH / 2 + k * ROOF_DEPTH / 4 + rnd.uniform(-0.01, 0.01)
            box(f"roof_{s}_joint_{k}", (length - 0.01, 0.008, 0.006), (mx + s * s_ * BOARD / 2, y, mz + c * BOARD / 2),
                wood_dark, rot=(0, s * PITCH, 0), bevel=0)
    box("ridge", (0.05, ROOF_DEPTH + 0.02, 0.04), (0, 0, ridge[1] + BOARD * 0.9), wood_dark, rot=(0, 45, 0),
        bevel=0.006)

    # In the niche: an icon panel on the back wall, a candle, a pot of wildflowers.
    back_y = ny / 2 - WALL
    box("icon_frame", (0.2, 0.02, 0.24), (0, back_y - 0.01, NICHE_Z + 0.17), gilt, bevel=0.004)
    box("icon_panel", (0.16, 0.012, 0.2), (0, back_y - 0.018, NICHE_Z + 0.17), icon, bevel=0.002)
    cylinder("icon_halo", 0.035, 0.006, (0, back_y - 0.024, NICHE_Z + 0.21), gilt, segments=12, rot=(90, 0, 0),
             bevel=0)
    box("icon_figure", (0.05, 0.006, 0.1), (0, back_y - 0.024, NICHE_Z + 0.14), gilt, bevel=0.002)
    cx, cy = 0.1, -0.03
    cylinder("candle_dish", 0.035, 0.012, (cx, cy, NICHE_Z), clay, segments=12, bevel=0.003)
    cylinder("candle", 0.018, 0.08, (cx, cy, NICHE_Z + 0.012), wax, segments=10, bevel=0.003)
    cylinder("candle_flame", 0.008, 0.03, (cx, cy, NICHE_Z + 0.094), flame, r_top=0.001, segments=8, bevel=0)
    px, py = -0.1, -0.03
    cylinder("pot", 0.035, 0.07, (px, py, NICHE_Z), clay, r_top=0.045, segments=12, bevel=0.004)
    for k in range(6):
        yaw = k * 60 + rnd.uniform(-15, 15)
        _flower(f"flower_{k}", px, py, NICHE_Z + 0.05, rnd.uniform(0.09, 0.14), rnd.uniform(8, 22), yaw,
                petals[k % 3], stem, rnd)

    # A small bunch of flowers laid on the footing in front of the post.
    for k in range(4):
        x = rnd.uniform(-0.06, 0.06)
        _flower(f"laid_{k}", x, -0.14, FOOT[2] + 0.006, rnd.uniform(0.12, 0.16), 88, 180 + rnd.uniform(-20, 20),
                petals[(k + 1) % 4], stem, rnd)

    # Moss at the foot of the post and on the footing's edge.
    for k, (x, y) in enumerate(((0.1, -0.1), (-0.12, 0.09), (0.15, 0.12))):
        blob(f"moss_{k}", rnd.uniform(0.04, 0.06), (x, y, FOOT[2]), moss, squash=(1.3, 1.0, 0.45), subdiv=1,
             seed=90 + k)

    anchor("light:candle", (cx, cy, NICHE_Z + 0.11))
