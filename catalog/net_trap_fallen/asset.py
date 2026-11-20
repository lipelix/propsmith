"""A fallen net trap, about 2 × 2 m: a heavy square rope net with a thicker border rope, dropped from above and lying in
a heap, its middle bunched up over a mass of folded net, its edges sagging out flat to a lashed stone weight at each
corner, with the coiled drop line lying on the heap."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, cylinder, torus

E = 1.76  # side of the spread net, corner node to corner node
N = 12  # rope nodes per side
ROPE_R = 0.017  # mesh rope radius
EDGE_R = 0.024  # border rope radius
HEAP = (0.12, 0.06)  # where the heap stands (x, y)
HEAP_H = 0.34  # its height over the ground
HEAP_R = 0.42  # its radius (the bell's width)
GATHER = 0.45  # how much the net is drawn in towards the heap (0: flat, 1: all into a point)
WEIGHT_R = 0.075  # corner weight radius

ROPE = (0.34, 0.27, 0.16)  # linear RGB: hemp, as pier_wood and shelf_wood
ROPE_OLD = (0.24, 0.19, 0.115)  # older, dirtier rope
ROPE_DARK = (0.12, 0.095, 0.06)  # the folded net under the heap, in its own shade
STONE = (0.19, 0.195, 0.205)  # weights: crypt stone
STONE_OLD = (0.145, 0.148, 0.155)


def _segment(name, a, b, r, mat):
    """A rope from point a to point b (x, y, z), a little longer than the gap so neighbours meet at the knots."""
    dx, dy, dz = (b[i] - a[i] for i in range(3))
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    ux, uy, uz = dx / length, dy / length, dz / length
    start = (a[0] - ux * r * 0.6, a[1] - uy * r * 0.6, a[2] - uz * r * 0.6)
    pitch = math.degrees(math.acos(max(-1.0, min(1.0, uz))))
    yaw = math.degrees(math.atan2(dy, dx))
    cylinder(name, r, length + r * 1.2, start, mat, segments=6, rot=(0, pitch, yaw), bevel=0)


@prop
def net_trap_fallen():
    rnd = random.Random(68)
    rope = material("net_trap_fallen_rope", ROPE, vary=0.3, scale=30, crevice=0.6)
    old = material("net_trap_fallen_rope_old", ROPE_OLD, vary=0.3, scale=30, crevice=0.6)
    dark = material("net_trap_fallen_rope_dark", ROPE_DARK, vary=0.35, scale=22, crevice=0.8)
    stone = material("net_trap_fallen_stone", STONE, vary=0.22, scale=9, crevice=0.7)
    stone_old = material("net_trap_fallen_stone_old", STONE_OLD, vary=0.25, scale=9, crevice=0.7)

    # Rope nodes: a square grid drawn in towards the heap, lifted into a lumpy bell over it, edges sagging flat.
    nodes = []
    hx, hy = HEAP
    for j in range(N):
        row = []
        for i in range(N):
            x0 = -E / 2 + E * i / (N - 1)
            y0 = -E / 2 + E * j / (N - 1)
            edge = i in (0, N - 1) or j in (0, N - 1)
            corner = i in (0, N - 1) and j in (0, N - 1)
            d0 = math.hypot(x0 - hx, y0 - hy)
            pull = GATHER * math.exp(-((d0 / 0.75) ** 2)) * (0 if corner else 1)
            x = x0 + (hx - x0) * pull + (0 if corner else rnd.uniform(-0.025, 0.025))
            y = y0 + (hy - y0) * pull + (0 if corner else rnd.uniform(-0.025, 0.025))
            d = math.hypot(x - hx, y - hy)
            z = HEAP_H * math.exp(-((d / HEAP_R) ** 2))
            z += 0.05 * math.sin(4.1 * x + 1.3) * math.sin(3.3 * y + 0.4) * math.exp(-((d / 0.7) ** 2))
            z += rnd.uniform(0, 0.03) * math.exp(-((d / 0.5) ** 2))
            r = EDGE_R if edge else ROPE_R
            row.append((x, y, max(0.0, z) + r))
        nodes.append(row)

    # The folded net under the heap: a dark lumpy mass the top layer drapes over.
    blob("heap_mass", 0.4, (hx, hy, 0.155), dark, squash=(1.0, 0.92, 0.34), subdiv=2, seed=11, jitter=0.15)
    blob("heap_fold", 0.22, (hx - 0.32, hy + 0.12, 0.095), dark, squash=(1.0, 0.7, 0.36), subdiv=1, seed=12, jitter=0.2)

    # The mesh: ropes between neighbouring nodes; the border rope is thicker.
    for j in range(N):
        for i in range(N):
            for di, dj in ((1, 0), (0, 1)):
                i2, j2 = i + di, j + dj
                if i2 >= N or j2 >= N:
                    continue
                edge = (dj == 0 and j in (0, N - 1)) or (di == 0 and i in (0, N - 1))
                mat = rope if rnd.random() > 0.3 else old
                _segment(f"rope_{i}_{j}_{di}{dj}", nodes[j][i], nodes[j2][i2], EDGE_R if edge else ROPE_R, mat)

    # A lashed stone weight at each corner, just outside the corner knot.
    for k, (i, j) in enumerate(((0, 0), (N - 1, 0), (0, N - 1), (N - 1, N - 1))):
        x, y, _ = nodes[j][i]
        sx, sy = math.copysign(1, x), math.copysign(1, y)
        wx, wy = x + sx * 0.035, y + sy * 0.035
        squash = (1.0, 0.95, 0.8)
        wz = WEIGHT_R * squash[2] * 1.08  # its centre: the jitter keeps the bottom on the ground
        blob(f"weight_{k}", WEIGHT_R, (wx, wy, wz), rnd.choice([stone, stone_old]), squash=squash, subdiv=2,
             seed=40 + k, jitter=0.08)
        torus(f"weight_lash_{k}", WEIGHT_R * 0.98, 0.012, (wx, wy, wz), rope, major=14, minor=5)
        lash = torus(f"weight_lash_v_{k}", WEIGHT_R * 0.88, 0.01, (wx, wy, wz), old, rot=(90, 0, 45 + 90 * k),
                     major=14, minor=5)
        lash.scale = (1, squash[2], 1)  # flattened (local y is up once stood on edge) to hug the squat stone

    # The coiled drop line lying on the heap and trailing off it.
    top = HEAP_H + 0.02
    for c in range(2):
        torus(f"coil_{c}", 0.13 - c * 0.025, 0.016, (hx - 0.05 + c * 0.012, hy - 0.03, top + c * 0.026), rope,
              rot=(rnd.uniform(-6, 6), rnd.uniform(-6, 6), 0), major=18, minor=5)
    tail = [(hx + 0.07, hy - 0.11, top - 0.01), (hx + 0.3, hy - 0.3, 0.17), (hx + 0.52, hy - 0.42, 0.05),
            (hx + 0.66, hy - 0.62, 0.02)]
    for k in range(len(tail) - 1):
        _segment(f"drop_line_{k}", tail[k], tail[k + 1], 0.016, rope)
