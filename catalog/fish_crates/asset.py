"""Two shallow slatted crates of fresh silver fish on a quay, front on -y: one at the back heaped with herring-sized
fish, one in front turned a little with larger fish laid head to tail; beside them a lidded wicker creel on a leather
strap with a tail sticking out from under its lid, and one fish dropped on the ground."""
import math
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# About 1.2 x 0.8 m, the creel the tallest part at about 0.45 m.
CL, CW, CH = 0.56, 0.38, 0.2  # one crate: length (x), width (y), height
POST = 0.035  # corner posts
SLAT_T = 0.014
GAP = 0.014  # between the two slats of a side
# Where the crates stand: (x, y, z of the bottom, yaw in degrees).
BACK_AT = (-0.2, 0.17, 0.0, 3)
FRONT_AT = (0.27, -0.16, 0.0, -8)
CREEL_AT = (-0.4, -0.2)  # the creel's centre (x, y)
CREEL_R, CREEL_H, CREEL_FLAT = 0.17, 0.34, 0.72  # radius (x), height, depth squash (y)

WOOD = (0.24, 0.21, 0.17)  # linear RGB: sun-greyed slats, as pier_wood
WOOD_OLD = (0.19, 0.165, 0.135)
POST_WOOD = (0.15, 0.11, 0.075)
INSIDE = (0.07, 0.06, 0.05)
SILVER = (0.33, 0.35, 0.36)
FISH_BACK = (0.13, 0.16, 0.18)  # the darker blue-grey backs
FISH_DARK = (0.2, 0.22, 0.23)  # the fish below the top layer
FIN = (0.16, 0.16, 0.15)
WICKER = (0.34, 0.22, 0.1)  # as market_stall
WICKER_OLD = (0.24, 0.16, 0.08)
LEATHER = (0.12, 0.06, 0.03)


def _frame(at):
    """The matrix that places a crate's local frame (origin at its base centre) at `at`."""
    x, y, z, yaw = at
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")


def _put(obj, m, local, rot=(0, 0, 0)):
    """Place `obj` at `local` in the frame `m`, its rotation `rot` (degrees, XYZ) turned by the frame."""
    obj.location = m @ Vector(local)
    obj.rotation_euler = (m.to_3x3() @ Euler([math.radians(v) for v in rot]).to_matrix()).to_euler()
    return obj


def _crate(prefix, at, rnd, mats):
    """A shallow crate of two slats per side on four corner posts and a plank bottom; returns its frame."""
    wood, old, post, inside = mats
    m = _frame(at)
    hx, hy = CL / 2, CW / 2
    _put(box(f"{prefix}_bottom", (CL - 0.01, CW - 0.01, 0.014), (0, 0, 0), old, bevel=0.004), m, (0, 0, 0.007))
    _put(box(f"{prefix}_inside", (CL - 2 * SLAT_T - 0.01, CW - 2 * SLAT_T - 0.01, 0.004), (0, 0, 0), inside, bevel=0),
         m, (0, 0, 0.016))
    for sx in (-1, 1):
        for sy in (-1, 1):
            _put(box(f"{prefix}_post_{sx}_{sy}", (POST, POST, CH), (0, 0, 0), post, bevel=0.005), m,
                 (sx * (hx - POST / 2), sy * (hy - POST / 2), CH / 2), (0, 0, rnd.uniform(-1.5, 1.5)))
    sh = (CH - GAP - 0.012) / 2  # slat height
    for k in range(2):
        z = 0.012 + sh * (k + 0.5) + GAP * k
        for s in (-1, 1):
            _put(box(f"{prefix}_long_{k}_{s}", (CL + 0.004, SLAT_T, sh), (0, 0, 0), (wood, old)[rnd.random() < 0.3],
                     bevel=0.004), m, (rnd.uniform(-0.004, 0.004), s * (hy + SLAT_T / 2 - 0.002), z),
                 (rnd.uniform(-0.6, 0.6), 0, 0))
            _put(box(f"{prefix}_end_{k}_{s}", (SLAT_T, CW - 2 * POST + 0.008, sh), (0, 0, 0), wood, bevel=0.004), m,
                 (s * (hx - SLAT_T / 2), 0, z), (0, rnd.uniform(-0.6, 0.6), 0))
    # Hand holes: a dark slot cut into each end's top slat.
    for s in (-1, 1):
        _put(box(f"{prefix}_grip_{s}", (SLAT_T + 0.004, 0.09, 0.022), (0, 0, 0), inside, bevel=0), m,
             (s * (hx - SLAT_T / 2), 0, 0.012 + sh * 1.5 + GAP))
    return m


# A fish's body from the head (t = 0) to the root of its tail (t = 1): dorsal half-height and half-thickness, per length.
FISH_T = (0.0, 0.06, 0.18, 0.35, 0.55, 0.75, 0.9, 1.0)
FISH_H = (0.0, 0.06, 0.1, 0.11, 0.095, 0.065, 0.035, 0.025)
FISH_D = (0.0, 0.03, 0.045, 0.048, 0.04, 0.028, 0.016, 0.01)
FISH_BODY = 0.82  # the body's share of the length; the forked tail fin is the rest
RING = 8


def _fish(name, m, local, length, yaw, mats, seed, roll=0.0):
    """A fish lying on its side (back towards local +y, head towards +x before the yaw): a lofted closed body, silver
    with a darker back, and a thin forked tail fin; placed at `local` (its centre) in the frame m."""
    rnd = random.Random(seed)
    k = length * rnd.uniform(0.95, 1.05)  # a little plumper or slimmer
    bm = bmesh.new()
    x0 = length / 2
    rings = []
    for t, h, d in zip(FISH_T[1:], FISH_H[1:], FISH_D[1:]):
        x = x0 - t * FISH_BODY * length
        rings.append([bm.verts.new((x, h * k * math.cos(2 * math.pi * j / RING), d * k * math.sin(2 * math.pi * j / RING)))
                      for j in range(RING)])
    head = bm.verts.new((x0, 0, 0))
    root = bm.verts.new((x0 - FISH_BODY * length, 0, 0))

    def mat_of(j):  # the two strips round the top of the back are dark
        return 1 if j in (RING - 1, 0) else 0

    for j in range(RING):
        j2 = (j + 1) % RING
        bm.faces.new((head, rings[0][j2], rings[0][j])).material_index = mat_of(j)
        bm.faces.new((root, rings[-1][j], rings[-1][j2])).material_index = mat_of(j)
        for a, b in zip(rings, rings[1:]):
            bm.faces.new((a[j], a[j2], b[j2], b[j])).material_index = mat_of(j)
    # The tail fin: a forked plate in the body's plane, a few millimetres thick.
    xr = x0 - FISH_BODY * length + 0.006
    ft, fh = length * (1 - FISH_BODY) + 0.006, length * 0.09
    outline = [(xr, 0), (xr - ft, fh), (xr - ft * 0.7, 0), (xr - ft, -fh)]
    sides = [[bm.verts.new((x, y, z)) for x, y in outline] for z in (-0.003, 0.003)]
    lo, hi = sides
    for tri in ((0, 1, 2), (0, 2, 3)):
        bm.faces.new([lo[i] for i in reversed(tri)]).material_index = 2
        bm.faces.new([hi[i] for i in tri]).material_index = 2
    for i in range(4):
        bm.faces.new((lo[i], lo[(i + 1) % 4], hi[(i + 1) % 4], hi[i])).material_index = 2
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth()
    mesh.set_sharp_from_angle(angle=math.radians(50))
    for mat in mats:
        mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return _put(obj, m, local, (roll, 0, yaw))


@prop
def fish_crates():
    rnd = random.Random(117)
    wood = material("fish_crates_wood", WOOD, vary=0.25, scale=14)
    old = material("fish_crates_wood_old", WOOD_OLD, vary=0.3, scale=11)
    post = material("fish_crates_posts", POST_WOOD, vary=0.25, scale=12)
    inside = material("fish_crates_inside", INSIDE, vary=0.1, scale=4, crevice=0.2)
    silver = material("fish_crates_silver", SILVER, rough=0.3, vary=0.2, scale=40, crevice=0.5, metal=0.35)
    back = material("fish_crates_fish_back", FISH_BACK, rough=0.35, vary=0.25, scale=30, crevice=0.4, metal=0.2)
    dark = material("fish_crates_fish_under", FISH_DARK, rough=0.4, vary=0.3, scale=24, crevice=0.8, metal=0.2)
    fin = material("fish_crates_fin", FIN, rough=0.5, vary=0.2, scale=30)
    wicker = material("fish_crates_wicker", WICKER, vary=0.35, scale=60, rough=1.0)
    wicker_old = material("fish_crates_wicker_old", WICKER_OLD, vary=0.35, scale=50, rough=1.0)
    leather = material("fish_crates_leather", LEATHER, rough=0.7, vary=0.2, scale=12)
    mats = (wood, old, post, inside)
    fmats = (silver, back, fin)

    # The back crate: a heap of small fish crossing each other on a bed of more fish.
    m = _crate("back_crate", BACK_AT, rnd, mats)
    _put(blob("back_fill", 0.25, (0, 0, 0), dark, squash=(1.05, 0.66, 0.22), subdiv=2, seed=5, jitter=0.1), m,
         (0, 0, CH - 0.05))
    for i in range(18):
        row, col = divmod(i, 3)
        lx = -0.16 + col * 0.16 + rnd.uniform(-0.02, 0.02)
        ly = -0.125 + row * 0.05 + rnd.uniform(-0.01, 0.01)
        heap = 0.035 * max(0.0, 1 - (lx / 0.28) ** 2) * max(0.0, 1 - (ly / 0.19) ** 2)
        yaw = rnd.choice((0, 180)) + rnd.uniform(-35, 35) + (50 if i % 7 == 0 else 0)
        _fish(f"herring_{i}", m, (lx, ly, CH + 0.008 + heap + 0.012 * (i % 2)), rnd.uniform(0.17, 0.21), yaw, fmats,
              100 + i, roll=rnd.uniform(-8, 8))

    # The front crate: larger fish in neat rows, head to tail.
    m = _crate("front_crate", FRONT_AT, rnd, mats)
    _put(blob("front_fill", 0.25, (0, 0, 0), dark, squash=(1.05, 0.66, 0.2), subdiv=2, seed=6, jitter=0.08), m,
         (0, 0, CH - 0.06))
    for i in range(5):
        ly = -0.12 + i * 0.06 + rnd.uniform(-0.006, 0.006)
        yaw = (0 if i % 2 else 180) + rnd.uniform(-5, 5)
        lx = rnd.uniform(-0.03, 0.03)
        _fish(f"cod_{i}", m, (lx, ly, CH - 0.005 + 0.012 * (1 - abs(ly) / 0.15)), rnd.uniform(0.3, 0.34), yaw,
              fmats, 200 + i, roll=rnd.uniform(-12, 12) + (20 if i % 2 else -20))

    # The creel: a lidded wicker basket, flat at the back, on a leather strap.
    cx, cy = CREEL_AT
    body = cylinder("creel_body", CREEL_R * 0.9, CREEL_H - 0.03, (cx, cy, 0), wicker, r_top=CREEL_R, segments=14,
                    bevel=0.01)
    body.scale = (1, CREEL_FLAT, 1)
    for k in range(3):  # the weave's heavier rows
        z = 0.04 + k * (CREEL_H - 0.1) / 2
        rr = CREEL_R * (0.9 + 0.1 * z / (CREEL_H - 0.03))
        band = torus(f"creel_band_{k}", rr, 0.007, (cx, cy, z), wicker_old, major=18, minor=4)
        band.scale = (1, CREEL_FLAT, 1)
    lid = cylinder("creel_lid", CREEL_R + 0.012, 0.035, (cx, cy, CREEL_H - 0.035), wicker_old, r_top=CREEL_R * 0.85,
                   segments=14, bevel=0.008)
    lid.scale = (1, CREEL_FLAT, 1)
    hole = cylinder("creel_lid_hole", 0.04, 0.008, (cx + 0.03, cy, CREEL_H - 0.002), inside, segments=10, bevel=0)
    hole.scale = (1.4, 1, 1)
    torus("creel_hole_rim", 0.045, 0.008, (cx + 0.03, cy, CREEL_H), wicker, major=12, minor=5).scale = (1.4, 1, 1)
    # A tail sticking out from under the lid's edge at the front.
    tail = cylinder("creel_fish_tail", 0.035, 0.06, (cx - 0.06, cy - CREEL_R * CREEL_FLAT + 0.01, CREEL_H - 0.04), fin,
                    r_top=0.003, segments=4, rot=(0, -150, 70), bevel=0)
    tail.scale = (1, 0.2, 1)
    # The strap: up from one side, over and down to the other, buckled to loops on the body.
    torus("creel_strap", CREEL_R + 0.02, 0.012, (cx, cy, CREEL_H * 0.6), leather, rot=(90, 0, 0), major=20, minor=4)
    for s in (-1, 1):
        box(f"creel_strap_loop_{s}", (0.02, 0.05, 0.05), (cx + s * (CREEL_R * 0.97), cy, CREEL_H * 0.5), leather,
            bevel=0.004)

    # One fish dropped on the ground between the crates.
    ground = Matrix.Identity(4)
    _fish("dropped", ground, (-0.12, -0.31, 0.011), 0.22, 75, fmats, 300)
    blob("wet_patch", 0.12, (-0.12, -0.29, 0.001), inside, squash=(1.4, 0.8, 0.02), subdiv=1, seed=9, jitter=0.1)
