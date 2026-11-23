"""A fresh grave: a long low mound of dark, newly turned earth, lumpy with clods, a few clods and stones fallen on the
ground round it, and a wooden spade with an iron blade and a D-grip stuck into its foot end, leaning a little."""
import math
import random

import bmesh
from mathutils import Matrix

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall dimensions (metres): the mound about 2 m long (x), 1 m wide, 0.4 m high; the spade stands above it.
A, B = 0.95, 0.46  # mound half length and half width at the ground
HM = 0.36  # mound crest height
POWER = 2.6  # footprint shape: 2 is an ellipse, higher is squarer
RINGS, SEGS = 10, 40  # mound mesh resolution
SPADE_AT = (0.5, -0.06)  # where the blade enters the mound
SPADE_TILT = (-6, 14)  # degrees about x (top toward -y) and y (top toward +x)
SPADE_LEN = 0.93  # blade tip to grip top
BLADE = (0.19, 0.01, 0.3)
SHAFT_R = 0.022

EARTH = (0.075, 0.055, 0.036)  # linear RGB: damp, freshly dug
EARTH_DRY = (0.115, 0.09, 0.062)  # drier crumbs on the crest
STONE = (0.25, 0.235, 0.21)
WOOD = (0.26, 0.18, 0.105)  # pale ash handle
IRON = (0.1, 0.097, 0.092)  # worn bright by digging


def _profile(t):
    """Height fraction at radius fraction `t` (0 centre, 1 edge): a full rounded crest falling steeply at the sides."""
    return max(0.0, 1 - t ** 2.2) ** 0.75


def _mound(earth, rnd):
    """The mound as one closed mesh: rings round a crest, the outermost on the ground, closed by a flat bottom."""
    waves = [(rnd.uniform(-9, 9), rnd.uniform(-9, 9), rnd.uniform(0, 6.3), rnd.uniform(0.008, 0.018)) for _ in range(6)]
    bm = bmesh.new()
    top = bm.verts.new((0, 0, HM + sum(h * math.sin(ph) for _, _, ph, h in waves)))
    rings = []
    for k in range(1, RINGS + 1):
        t = k / RINGS
        ring = []
        for s in range(SEGS):
            th = 2 * math.pi * s / SEGS
            c, sn = math.cos(th), math.sin(th)
            # Superellipse footprint.
            r = (abs(c) ** POWER + abs(sn) ** POWER) ** (-1 / POWER)
            x, y = A * t * r * c, B * t * r * sn
            if k == RINGS:
                z = 0.0
            else:
                z = HM * _profile(t) * (1 - 0.12 * (x / A) ** 2)
                z += sum(h * math.sin(fx * x + fy * y + ph) for fx, fy, ph, h in waves) * (1 - t)
                z += rnd.uniform(-0.005, 0.005)
                x += rnd.uniform(-0.015, 0.015)
                y += rnd.uniform(-0.015, 0.015)
            ring.append(bm.verts.new((x, y, z)))
        rings.append(ring)
    for s in range(SEGS):
        bm.faces.new((top, rings[0][s], rings[0][(s + 1) % SEGS]))
    for k in range(RINGS - 1):
        a, b = rings[k], rings[k + 1]
        for s in range(SEGS):
            bm.faces.new((a[s], b[s], b[(s + 1) % SEGS], a[(s + 1) % SEGS]))
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) == 4], quad_method="SHORT_EDGE")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    obj = box("grave_mound_earth", (1, 1, 1), (0, 0, 0), earth, bevel=0)
    mesh = obj.data
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth()
    return obj


def _height(x, y):
    """The mound's height above (x, y) before its noise, for placing things on it."""
    p = (abs(x / A) ** POWER + abs(y / B) ** POWER) ** (1 / POWER)
    return HM * _profile(min(p, 1.0)) * (1 - 0.12 * (x / A) ** 2)


@prop
def grave_mound():
    rnd = random.Random(17)
    earth = material("grave_mound_earth", EARTH, rough=0.95, vary=0.35, scale=9, crevice=0.65)
    dry = material("grave_mound_earth_dry", EARTH_DRY, rough=0.95, vary=0.35, scale=12, crevice=0.6)
    stone = material("grave_mound_stone", STONE, vary=0.3, scale=10)
    wood = material("grave_mound_spade_wood", WOOD, vary=0.25, scale=14)
    iron = material("grave_mound_spade_iron", IRON, rough=0.5, vary=0.3, scale=20, metal=0.6)

    _mound(earth, rnd)

    # Clods on the mound and fallen round its foot, a few stones turned up with them.
    for k in range(9):
        x, y = rnd.uniform(-0.8, 0.8), rnd.uniform(-0.32, 0.32)
        r = rnd.uniform(0.04, 0.07)
        blob(f"clod_top_{k}", r, (x, y, _height(x, y) - r * 0.2), dry if k % 3 == 0 else earth,
             squash=(1.2, 1, 0.7), subdiv=1, seed=100 + k, jitter=0.25)
    for k in range(9):
        th = rnd.uniform(0, 2 * math.pi)
        x, y = (A + 0.03) * math.cos(th), (B + 0.03) * math.sin(th)
        r = rnd.uniform(0.035, 0.06)
        blob(f"clod_{k}", r, (x, y, r * 0.75 * 1.25), earth, squash=(1.2, 1, 0.75), subdiv=1, seed=120 + k,
             jitter=0.25)
    for k in range(4):
        th = rnd.uniform(0, 2 * math.pi)
        x, y = (A - 0.05) * math.cos(th), (B - 0.02) * math.sin(th)
        r = rnd.uniform(0.04, 0.06)
        blob(f"stone_{k}", r, (x, y, r * 0.6 * 1.12 + _height(x, y) * 0.5), stone, squash=(1.3, 1, 0.6), subdiv=1,
             seed=140 + k)

    # The spade, built upright from its blade tip at the origin, then tilted and pushed into the mound.
    parts = []
    bw, bt, bh = BLADE
    parts.append(box("blade", (bw, bt, bh), (0, 0, bh / 2), iron, bevel=0.003))
    parts.append(box("blade_tread", (bw + 0.004, 0.026, 0.01), (0, 0, bh), iron, bevel=0.003))
    parts.append(cylinder("socket", 0.026, 0.12, (0, 0, bh - 0.01), iron, r_top=SHAFT_R + 0.004, segments=10,
                          bevel=0.003))
    grip_r = 0.065
    shaft_top = SPADE_LEN - 2 * grip_r
    parts.append(cylinder("shaft", SHAFT_R, shaft_top - bh, (0, 0, bh), wood, r_top=SHAFT_R * 0.9, segments=10,
                          bevel=0.004))
    # D-grip: a split ring of ash wood round a crossbar.
    grip = torus("grip", grip_r, 0.016, (0, 0, shaft_top + grip_r - 0.01), wood, rot=(90, 0, 0), major=16, minor=6)
    grip.scale = (0.85, 1, 1)
    parts.append(grip)
    parts.append(cylinder("grip_bar", 0.016, 2 * grip_r * 0.85 - 0.01, (-grip_r * 0.85 + 0.005, 0,
                          shaft_top + 2 * grip_r - 0.03), wood, segments=8, rot=(0, 90, 0), bevel=0.003))
    for k, z in enumerate((bh + 0.06, bh + 0.1)):
        parts.append(torus(f"socket_rivet_{k}", SHAFT_R + 0.005, 0.003, (0, 0, z), iron, major=10, minor=4))
    sx, sy = SPADE_AT
    depth = 0.12  # how far the blade is in the earth
    place = (Matrix.Translation((sx, sy, _height(sx, sy) - depth))
             @ Matrix.Rotation(math.radians(SPADE_TILT[1]), 4, "Y")
             @ Matrix.Rotation(math.radians(SPADE_TILT[0]), 4, "X")
             @ Matrix.Rotation(math.radians(-20), 4, "Z"))
    for obj in parts:
        obj.matrix_basis = place @ obj.matrix_basis
    # Earth heaped up round where the blade went in.
    for k in range(3):
        a = math.radians(120 * k + 30)
        x, y = sx + 0.07 * math.cos(a), sy + 0.05 * math.sin(a)
        blob(f"heap_{k}", 0.05, (x, y, _height(x, y)), earth, squash=(1.3, 1, 0.6), subdiv=1, seed=160 + k,
             jitter=0.25)
