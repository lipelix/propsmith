"""A stone grave cross on a stepped base: two dressed steps and a socket block, a square-cut Latin cross with flared
ends and a small ring at the crossing, a worn inscription panel on the socket's face (-y), moss on the steps and the
arms, the stones settled a little out of true."""
import math
import random

from mathutils import Matrix

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, torus

# Overall dimensions (metres): about 0.7 wide (x), 0.4 deep, 1.4 m high.
STEPS = [(0.68, 0.38, 0.13), (0.5, 0.3, 0.12)]  # (x, y, height) of each step, bottom up
SOCKET = (0.3, 0.2, 0.2)
SHAFT = (0.13, 0.11)  # square shaft, x and y
TOP = 1.39
ARM_W, ARM_H = 0.5, 0.12  # cross arm span and height
ARM_Z = 1.12  # arm centre
FLARE = 0.03  # each end widens by this much
LEAN = 1.5  # degrees, the cross settled toward +x

STONE = (0.25, 0.245, 0.23)  # linear RGB: cool grey limestone
STONE_OLD = (0.2, 0.195, 0.18)
CARVE = (0.08, 0.077, 0.07)
MOSS = (0.06, 0.085, 0.03)


@prop
def gravestone_cross():
    rnd = random.Random(33)
    stone = material("gravestone_cross_stone", STONE, vary=0.28, scale=7, crevice=0.6)
    old = material("gravestone_cross_stone_old", STONE_OLD, vary=0.3, scale=9, crevice=0.6)
    carve = material("gravestone_cross_carve", CARVE, vary=0.2, scale=20)
    moss = material("gravestone_cross_moss", MOSS, rough=0.95, vary=0.35, scale=16, crevice=0.6)

    # The steps, each a little turned on the one below.
    z = 0.0
    for i, (sx, sy, sh) in enumerate(STEPS):
        box(f"step_{i}", (sx, sy, sh), (rnd.uniform(-0.005, 0.005), 0, z + sh / 2), old if i == 0 else stone,
            rot=(0, 0, rnd.uniform(-1.5, 1.5)), bevel=0.02)
        z += sh
    base_top = z
    box("socket", SOCKET, (0, 0, base_top + SOCKET[2] / 2), stone, rot=(0, 0, 0.8), bevel=0.018)
    face = -SOCKET[1] / 2
    # Inscription panel on the socket: a sunk-looking frame and three worn lines.
    sz = base_top + SOCKET[2] / 2
    for k, (w, h, dz) in enumerate(((0.22, 0.008, 0.06), (0.22, 0.008, -0.06))):
        box(f"panel_{k}", (w, 0.006, h), (0, face - 0.002, sz + dz), carve, bevel=0)
    for s in (-1, 1):
        box(f"panel_side_{s}", (0.008, 0.006, 0.128), (s * 0.11, face - 0.002, sz), carve, bevel=0)
    for row, (dz, half) in enumerate(((0.03, 0.07), (0.0, 0.05), (-0.03, 0.08))):
        x = -half
        while x < half:
            if rnd.random() > 0.25:
                box(f"letter_{row}_{x:.3f}", (0.007, 0.006, 0.018 * rnd.uniform(0.7, 1)),
                    (x, face - 0.002, sz + dz), carve, rot=(0, rnd.choice((0, 0, 20, -20)), 0), bevel=0)
            x += rnd.uniform(0.018, 0.026)

    # The cross, built upright then settled a little.
    parts = []
    sx, sy = SHAFT
    shaft_z0 = base_top + SOCKET[2] - 0.02
    parts.append(box("shaft", (sx, sy, TOP - FLARE - shaft_z0 - 0.02), (0, 0, (shaft_z0 + TOP - 0.05) / 2), stone,
                     bevel=0.014))
    parts.append(box("head", (sx + FLARE, sy + 0.01, 0.07), (0, 0, TOP - 0.035), stone, bevel=0.012))
    parts.append(box("arm", (ARM_W - 0.1, sy, ARM_H), (0, 0, ARM_Z), stone, bevel=0.014))
    for s in (-1, 1):
        parts.append(box(f"arm_end_{s}", (0.07, sy + 0.01, ARM_H + FLARE), (s * (ARM_W / 2 - 0.035), 0, ARM_Z), stone,
                         bevel=0.012))
    parts.append(box("foot", (sx + FLARE, sy + 0.01, 0.06), (0, 0, shaft_z0 + 0.03), stone, bevel=0.012))
    # A ring round the crossing, standing proud of both faces.
    ring = torus("ring", 0.135, 0.022, (0, 0, ARM_Z), stone, rot=(90, 0, 0), major=28, minor=6)
    ring.scale = (1, 1, 1.9)  # a flat band, deep in y
    parts.append(ring)
    # A small carved cross on the boss at the crossing.
    parts.append(box("boss", (0.07, sy + 0.016, 0.07), (0, 0, ARM_Z), old, rot=(0, 45, 0), bevel=0.01))
    # Moss on the arms' top and the head.
    for k, x in enumerate((-0.17, 0.12)):
        parts.append(blob(f"moss_arm_{k}", 0.045, (x, rnd.uniform(-0.01, 0.01), ARM_Z + ARM_H / 2 + 0.005), moss,
                          squash=(1.3, 1.1, 0.3), subdiv=1, seed=10 + k))
    parts.append(blob("moss_head", 0.045, (0, 0, TOP - 0.01), moss, squash=(1.1, 1.0, 0.25), subdiv=1, seed=13))
    pivot = Matrix.Translation((0, 0, shaft_z0))
    tilt = pivot @ Matrix.Rotation(math.radians(LEAN), 4, "Y") @ pivot.inverted()
    for obj in parts:
        obj.matrix_basis = tilt @ obj.matrix_basis

    # Moss in the angles of the steps.
    for k, (x, y, zz, r) in enumerate(((-0.27, -0.12, STEPS[0][2], 0.06), (0.26, 0.1, STEPS[0][2], 0.06),
                                       (-0.22, 0.17, STEPS[0][2], 0.04), (0.18, -0.1, base_top, 0.05),
                                       (-0.13, 0.07, base_top, 0.04))):
        blob(f"moss_step_{k}", r, (x, y, zz + r * 0.1), moss, squash=(1.3, 1.0, 0.35), subdiv=1, seed=20 + k)
