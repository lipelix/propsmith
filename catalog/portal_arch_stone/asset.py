"""A round stone ring gate about 2.6 × 0.8 × 2.8 m, empty inside: a full ring of fifteen wedge voussoirs with a proud
keystone at the top, set upright on a two-step base of worn slabs between two curved chock stones. Every voussoir
carries an angular glyph on both faces, filled with a faint pale violet glow; the joints are dark mortar, moss sits on
the steps. A light anchor floats in the middle of the ring."""
import math
import random

import bmesh
import bpy

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, box

# Overall dimensions (metres): about 2.6 × 0.8 × 2.8.
STEP_LOW = (2.6, 0.8, 0.14)  # lower step: x, y, height
STEP_HIGH = (2.1, 0.62, 0.14)  # upper step
BASE_H = STEP_LOW[2] + STEP_HIGH[2]
R_OUT = 1.28  # outer radius of the ring
R_IN = 0.96  # inner radius: the empty opening
DEPTH = 0.44  # ring thickness (y)
EMBED = 0.1  # how far the bottom of the ring sits down into the upper step
CZ = BASE_H - EMBED + R_OUT  # centre of the ring
CHOCK_X = 1.0  # outer end of the curved chock stones that seat the ring
CHOCK_DEPTH = 0.52
BLOCKS = 15  # voussoirs; odd, so one is the keystone at the top
JOINT = 0.9  # degrees of mortar between voussoirs
KEY_PROUD = 0.05  # how far the keystone stands out of the ring (radially and on both faces)
INSET = 0.03  # how far the mortar core sits behind the faces
ARC_STEP = 6  # degrees between points of a curved edge
GLYPH = 0.2  # rune glyph height (radial)
STROKE = 0.026
LIGHT_Z = CZ  # the light anchor, in the middle of the ring

STONE = (0.23, 0.225, 0.22)  # linear RGB: grey dressed stone
STONE_OLD = (0.17, 0.168, 0.165)
STONE_PALE = (0.29, 0.282, 0.27)
MORTAR = (0.045, 0.043, 0.042)
GLOW = (0.46, 0.46, 0.74)  # pale violet rune glow
MOSS = (0.06, 0.085, 0.03)

# Rune glyphs as strokes in a unit cell (u -0.5..0.5 across, v 0..1 outward): (u0, v0, u1, v1).
RUNES = (
    ((0, 0, 0, 1), (0, 0.55, 0.4, 0.9)),
    ((-0.25, 0, -0.25, 1), (-0.25, 1, 0.3, 0.6), (0.3, 0.6, -0.25, 0.25)),
    ((0, 0, 0, 1), (-0.35, 0.75, 0.35, 0.45)),
    ((0, 0, 0, 1), (0, 0.5, -0.35, 1), (0, 0.5, 0.35, 1)),
    ((-0.3, 0, 0.3, 1), (0.3, 0, -0.3, 1)),
    ((0, 0, 0, 1), (0, 1, 0.35, 0.65), (0, 0.6, 0.35, 0.3)),
    ((-0.3, 1, 0.3, 0.5), (0.3, 0.5, -0.3, 0)),
    ((-0.3, 0, -0.3, 1), (0.3, 0, 0.3, 1), (-0.3, 0.7, 0.3, 0.35)),
)


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
        mod.angle_limit = math.radians(40)
    return obj


def _sector(r_in, r_out, a0, a1):
    """The (x, z) outline of the ring between angles a0 and a1 (degrees) and radii r_in and r_out."""
    n = max(1, round((a1 - a0) / ARC_STEP))
    angles = [math.radians(a0 + (a1 - a0) * k / n) for k in range(n + 1)]
    outer = [(r_out * math.cos(a), CZ + r_out * math.sin(a)) for a in angles]
    inner = [(r_in * math.cos(a), CZ + r_in * math.sin(a)) for a in reversed(angles)]
    return outer + inner


def _glyph(name, am, rune, y, mat):
    """One rune on a voussoir face at y, centred on the block's middle angle `am` (radians), reading outward."""
    radial = (math.cos(am), math.sin(am))
    tangent = (-math.sin(am), math.cos(am))
    v0 = R_IN + (R_OUT - R_IN - GLYPH) / 2
    for k, (u0, w0, u1, w1) in enumerate(rune):
        pts = []
        for u, w in ((u0, w0), (u1, w1)):
            r, t = v0 + w * GLYPH, u * GLYPH * 0.6
            pts.append((radial[0] * r + tangent[0] * t, CZ + radial[1] * r + tangent[1] * t))
        (x0, z0), (x1, z1) = pts
        length = math.hypot(x1 - x0, z1 - z0) + STROKE * 0.6
        ang = math.degrees(math.atan2(z1 - z0, x1 - x0))
        box(f"{name}_{k}", (length, 0.016, STROKE), ((x0 + x1) / 2, y, (z0 + z1) / 2),
            mat, rot=(0, -ang, 0), bevel=0)


@prop
def portal_arch_stone():
    rnd = random.Random(216)
    stones = [
        material("portal_arch_stone_stone", STONE, vary=0.25, scale=7, crevice=0.65),
        material("portal_arch_stone_old", STONE_OLD, vary=0.28, scale=8, crevice=0.7),
        material("portal_arch_stone_pale", STONE_PALE, vary=0.2, scale=9, crevice=0.6),
    ]
    mortar = material("portal_arch_stone_mortar", MORTAR, vary=0.12, scale=20, crevice=0.9)
    glow = material("portal_arch_stone_glow", GLOW, rough=0.3, vary=0.15, scale=12, crevice=0.05)
    moss = material("portal_arch_stone_moss", MOSS, rough=0.95, vary=0.35, scale=16, crevice=0.6)

    # The stepped base: each step a row of worn slabs with a little jitter.
    z = 0.0
    for s, (sx, sy, sh) in enumerate((STEP_LOW, STEP_HIGH)):
        n = 3 if s == 0 else 2
        w = sx / n
        for k in range(n):
            box(f"step_{s}_{k}", (w - 0.012, sy + rnd.uniform(-0.02, 0.0), sh + rnd.uniform(-0.01, 0.0)),
                (-sx / 2 + w * (k + 0.5), rnd.uniform(-0.01, 0.01), z + sh / 2), rnd.choice(stones),
                rot=(0, 0, rnd.uniform(-1, 1)), bevel=0.02)
        z += sh

    # The ring: a dark mortar core with a gap-jointed voussoir over it; the keystone (block 0) at the top.
    step = 360 / BLOCKS
    for i in range(BLOCKS):
        am = 90 + i * step
        a0, a1 = am - step / 2, am + step / 2
        _prism(f"core_{i}", _sector(R_IN + INSET, R_OUT - INSET, a0, a1), -DEPTH / 2 + INSET, DEPTH / 2 - INSET,
               mortar, 0)
        key = i == 0
        r_out = R_OUT + (KEY_PROUD if key else rnd.uniform(-0.015, 0.01))
        half = DEPTH / 2 + (KEY_PROUD if key else rnd.uniform(-0.01, 0.005))
        mat = stones[2] if key else rnd.choice(stones)
        _prism(f"voussoir_{i}", _sector(R_IN + (-0.02 if key else rnd.uniform(-0.01, 0.01)), r_out,
                                        a0 + JOINT / 2, a1 - JOINT / 2), -half, half, mat, 0.02)
        rune = RUNES[rnd.randrange(len(RUNES))]
        if i not in (7, 8):  # the two blocks sunk in the base carry no glyph
            for side in (-1, 1):
                _glyph(f"rune_{i}_{side}", math.radians(am), rune, side * (half + 0.004 - 0.008), glow)

    # Two curved chock stones on the upper step, hugging the lower flanks of the ring.
    xa = math.sqrt(R_OUT ** 2 - (CZ - BASE_H) ** 2)
    arc = []
    for k in range(8):
        x = CHOCK_X - (CHOCK_X - xa) * k / 7
        arc.append((x, CZ - math.sqrt((R_OUT - 0.01) ** 2 - x * x)))
    for side in (-1, 1):
        outline = [(xa - 0.02, BASE_H - 0.02), (CHOCK_X + 0.04, BASE_H - 0.02), (CHOCK_X + 0.04, arc[0][1])] + arc
        _prism(f"chock_{side}", [(side * x, z) for x, z in outline], -CHOCK_DEPTH / 2, CHOCK_DEPTH / 2,
               stones[1], 0.02)

    # Moss on the steps and at the foot of the ring.
    for k, (x, y, zz, r) in enumerate(((-1.05, -0.33, STEP_LOW[2], 0.08), (0.8, -0.3, BASE_H, 0.07),
                                       (-0.55, 0.28, BASE_H, 0.09), (1.15, 0.3, STEP_LOW[2], 0.07),
                                       (0.35, -0.2, BASE_H, 0.06))):
        blob(f"moss_{k}", r, (x, y, zz), moss, squash=(1.5, 1.0, 0.35), subdiv=1, seed=80 + k)

    anchor("light:portal", (0, 0, LIGHT_Z))
