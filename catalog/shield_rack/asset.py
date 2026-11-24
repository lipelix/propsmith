"""A timber shield rack, front on -y: two uprights on feet joined by a top rail with pegs and a low ledge rail, three
round wooden shields hung from the pegs and leaning back on the frame, each with an iron boss and rim and its own
painted device (a pale cross on red, a blue field with a pale ring, red and ochre quarters)."""
import math
import random

from mathutils import Matrix, Vector

import bpy
from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall size: about 1.5 m wide (x), 0.4 m deep (y), 1.2 m high to the post caps.
FOOT_L, FOOT = 0.38, 0.08  # a foot along y under each upright
POST, POST_X, POST_H = 0.08, 0.68, 1.12
FRAME_Y = 0.06  # the uprights' centre line
TOP_Z = 1.0  # top rail centre, carrying the pegs
MID_Z, MID_FRONT = 0.8, 0.0  # the rail the shields lean on: centre height and front face
LEDGE_Z = 0.34  # ledge rail centre, the shields' feet stand on it
SHIELD_R, SHIELD_T = 0.23, 0.025
SHIELD_X = (-0.49, 0.0, 0.49)
SHIELD_Z = LEDGE_Z + 0.025 + SHIELD_R * 0.99  # shield centres: their feet on the ledge
LEAN = 9  # degrees the shields lean back

WOOD = (0.2, 0.125, 0.065)  # linear RGB
WOOD_OLD = (0.15, 0.1, 0.06)
SHIELD_WOOD = (0.24, 0.155, 0.08)
IRON = (0.12, 0.115, 0.11)
IRON_DARK = (0.045, 0.045, 0.045)
RED = (0.32, 0.06, 0.04)
BLUE = (0.06, 0.1, 0.2)
PALE = (0.38, 0.33, 0.24)
OCHRE = (0.42, 0.28, 0.06)
LEATHER = (0.13, 0.07, 0.035)


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


def _half_disc(name, r, y, mat, a0, segments=12):
    """A thin painted sector from angle `a0` (degrees) through 90 degrees, on the plane y, facing -y."""
    pts = [(0, 0)] + [(r * math.cos(math.radians(a0 + 90 * i / segments)),
                       r * math.sin(math.radians(a0 + 90 * i / segments))) for i in range(segments + 1)]
    n = len(pts)
    verts = [(x, y, z) for x, z in pts] + [(x, y - 0.003, z) for x, z in pts]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _shield(k, rnd, wood, iron, dark, paints, device):
    """A round shield centred on the origin, its back on y = 0 and its face towards -y, painted with `device`."""
    r, t = SHIELD_R, SHIELD_T
    red, blue, pale, ochre = paints
    cylinder(f"shield_{k}", r, t, (0, 0, 0), wood, segments=28, rot=(90, 0, 0), bevel=0.005)
    face = -t + 0.001
    if device == "cross":
        cylinder(f"shield_{k}_field", r - 0.018, 0.003, (0, face, 0), red, segments=28, rot=(90, 0, 0), bevel=0)
        for rot in (0, 90):
            box(f"shield_{k}_cross_{rot}", (0.07, 0.003, 2 * r - 0.04), (0, face - 0.0035, 0), pale, rot=(0, rot, 0),
                bevel=0)
    elif device == "ring":
        cylinder(f"shield_{k}_field", r - 0.018, 0.003, (0, face, 0), blue, segments=28, rot=(90, 0, 0), bevel=0)
        cylinder(f"shield_{k}_ring", 0.16, 0.003, (0, face - 0.0015, 0), pale, segments=28, rot=(90, 0, 0), bevel=0)
        cylinder(f"shield_{k}_ring_in", 0.12, 0.003, (0, face - 0.003, 0), blue, segments=28, rot=(90, 0, 0),
                 bevel=0)
    else:
        for q in range(4):
            _half_disc(f"shield_{k}_quarter_{q}", r - 0.018, face + 0.0015, red if q % 2 else ochre, 90 * q)
    for i in range(3):  # scuffs through the paint
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(0.09, 0.19)
        box(f"shield_{k}_scuff_{i}", (rnd.uniform(0.04, 0.08), 0.004, 0.006),
            (d * math.cos(a), face - 0.006, d * math.sin(a)), wood, rot=(0, rnd.uniform(-60, 60), 0), bevel=0)
    cylinder(f"shield_{k}_boss_rim", 0.07, 0.008, (0, -t - 0.004, 0), iron, segments=16, rot=(90, 0, 0), bevel=0.003)
    blob(f"shield_{k}_boss", 0.055, (0, -t - 0.012, 0), iron, squash=(1, 0.6, 1), subdiv=2, seed=k, jitter=0.03)
    torus(f"shield_{k}_rim", r, 0.014, (0, -t / 2, 0), iron, rot=(90, 0, 0), major=28, minor=6)
    for i in range(8):  # rim clinches
        a = 2 * math.pi * (i + 0.5) / 8
        blob(f"shield_{k}_rivet_{i}", 0.009, ((r - 0.025) * math.cos(a), face - 0.004, (r - 0.025) * math.sin(a)),
             dark, subdiv=1, seed=i, jitter=0.05)


@prop
def shield_rack():
    rnd = random.Random(41)
    wood = material("shield_rack_wood", WOOD, vary=0.28, scale=10)
    old = material("shield_rack_wood_old", WOOD_OLD, vary=0.3, scale=9)
    shield_wood = material("shield_rack_shield_wood", SHIELD_WOOD, vary=0.3, scale=14)
    iron = material("shield_rack_iron", IRON, rough=0.45, metal=0.85, vary=0.3, scale=25, crevice=0.8)
    dark = material("shield_rack_iron_dark", IRON_DARK, rough=0.6, metal=0.6, vary=0.2, scale=20)
    paints = [material(f"shield_rack_paint_{n}", c, rough=0.8, vary=0.35, scale=16)
              for n, c in (("red", RED), ("blue", BLUE), ("pale", PALE), ("ochre", OCHRE))]
    leather = material("shield_rack_leather", LEATHER, rough=0.7, vary=0.25, scale=30)

    # The frame: footed uprights with short braces, a top rail with pegs, a ledge rail low down.
    for side in (-1, 1):
        x = side * POST_X
        box(f"foot_{side}", (FOOT, FOOT_L, FOOT), (x, 0, FOOT / 2), old, rot=(0, 0, rnd.uniform(-2, 2)),
            bevel=0.012)
        box(f"post_{side}", (POST, POST, POST_H - FOOT + 0.005), (x, FRAME_Y, FOOT + (POST_H - FOOT) / 2 - 0.0025),
            wood, bevel=0.01)
        box(f"cap_{side}", (POST + 0.025, POST + 0.025, 0.04), (x, FRAME_Y, POST_H + 0.02), old, bevel=0.01)
        for dy in (-1, 1):
            _rod(f"brace_{side}_{dy}", 0.018, (x, FRAME_Y + dy * 0.14, FOOT - 0.005),
                 (x, FRAME_Y + dy * 0.03, FOOT + 0.22), old, segments=6)
    box("top_rail", (2 * POST_X + 0.12, 0.06, 0.08), (0, FRAME_Y - POST / 2 - 0.03, TOP_Z), wood, bevel=0.012)
    box("mid_rail", (2 * POST_X + 0.1, FRAME_Y - MID_FRONT, 0.06), (0, (FRAME_Y + MID_FRONT) / 2 - 0.002, MID_Z),
        old, bevel=0.01)
    box("ledge_rail", (2 * POST_X + 0.12, 0.13, 0.05), (0, -0.045, LEDGE_Z), old, bevel=0.01)
    box("ledge_lip", (2 * POST_X + 0.08, 0.025, 0.03), (0, -0.1, LEDGE_Z + 0.035), wood, bevel=0.006)

    # The shields: each hung by a leather strap from a peg on the top rail, its foot on the ledge rail.
    rail_front = FRAME_Y - POST / 2 - 0.06
    for k, (x, device) in enumerate(zip(SHIELD_X, ("cross", "ring", "quarters"))):
        _rod(f"peg_{k}", 0.014, (x, rail_front + 0.02, TOP_Z + 0.015), (x, rail_front - 0.05, TOP_Z + 0.03), old,
             segments=6)
        lean = math.radians(LEAN + rnd.uniform(-2, 2))
        # The shield's back leans on the middle rail, its foot stands on the ledge.
        cz = SHIELD_Z
        cy = MID_FRONT - (MID_Z - cz) * math.tan(lean) - 0.002
        m = (Matrix.Translation((x, cy, cz)) @ Matrix.Rotation(-lean, 4, "X") @
             Matrix.Rotation(math.radians(rnd.uniform(-8, 8)), 4, "Y"))
        _moved(lambda: _shield(k, rnd, shield_wood, iron, dark, paints, device), m)
        top = m @ Vector((0, 0.005, SHIELD_R - 0.03))
        _rod(f"strap_{k}", 0.01, top, (x, rail_front - 0.035, TOP_Z + 0.03), leather, segments=6)
