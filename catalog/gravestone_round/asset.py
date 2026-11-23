"""A weathered round-topped headstone leaning back and to one side in a low tuft of sod: a thick slab with a
semicircular top and chamfered shoulders, a shallow incised border, a cross roundel and a few rows of worn lettering on
its face (-y), and patches of moss on its top and foot."""
import math
import random

from mathutils import Matrix

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall dimensions (metres): about 0.6 wide (x), 0.2 deep, 1 m high.
W = 0.52  # slab width
T = 0.13  # slab thickness
H = 0.95  # slab height to the crown, before the lean
SHOULDER = H - W / 2  # where the round top starts
LEAN_BACK = 6  # degrees, top toward +y
LEAN_SIDE = 4  # degrees, top toward +x
FACE = -T / 2  # the inscribed face

STONE = (0.27, 0.255, 0.225)  # linear RGB: weathered grey-brown sandstone
CARVE = (0.085, 0.08, 0.07)  # shadowed letter cuts
MOSS = (0.06, 0.085, 0.03)
SOD = (0.075, 0.075, 0.038)  # turf and dead grass at the foot


def _strokes(name, rnd, x0, x1, z, h, mat, out):
    """A row of short worn letter strokes across the face, some missing."""
    x = x0
    while x < x1:
        w = rnd.uniform(0.008, 0.012)
        sh = h * rnd.uniform(0.75, 1.0)
        if rnd.random() > 0.2:
            out.append(box(f"{name}_{len(out)}", (w, 0.006, sh), (x, FACE - 0.001, z + rnd.uniform(-0.004, 0.004)), mat,
                           rot=(0, rnd.choice((0, 0, 18, -18)), 0), bevel=0))
        if rnd.random() < 0.35:  # a cross stroke
            out.append(box(f"{name}_{len(out)}", (0.03, 0.006, w), (x + 0.012, FACE - 0.001, z + rnd.uniform(-1, 1) * sh / 3),
                           mat, bevel=0))
        x += rnd.uniform(0.028, 0.042) + (0.03 if rnd.random() < 0.15 else 0)


@prop
def gravestone_round():
    rnd = random.Random(21)
    stone = material("gravestone_round_stone", STONE, vary=0.3, scale=7, crevice=0.6)
    carve = material("gravestone_round_carve", CARVE, vary=0.2, scale=20)
    moss = material("gravestone_round_moss", MOSS, rough=0.95, vary=0.35, scale=16, crevice=0.6)
    sod = material("gravestone_round_sod", SOD, rough=0.95, vary=0.35, scale=10)
    parts = []

    # The slab: a box to the shoulders and a half disc on top, a little thinner chamfered rim round the crown.
    parts.append(box("slab", (W, T, SHOULDER), (0, 0, SHOULDER / 2), stone, bevel=0.018))
    parts.append(cylinder("crown", W / 2, T, (0, T / 2, SHOULDER), stone, segments=28, rot=(90, 0, 0), bevel=0.018))

    # Incised border: a thin dark line inset round the face, an arch over the straight sides.
    inset = 0.045
    for s in (-1, 1):
        parts.append(box(f"border_{s}", (0.008, 0.006, SHOULDER - 0.12), (s * (W / 2 - inset), FACE - 0.001,
                         0.12 + (SHOULDER - 0.12) / 2), carve, bevel=0))
    ra, n = W / 2 - inset, 14
    for k in range(n):
        a0, a1 = math.pi * k / n, math.pi * (k + 1) / n
        am = (a0 + a1) / 2
        parts.append(box(f"border_arch_{k}", (ra * (a1 - a0) + 0.002, 0.006, 0.008),
                         (ra * math.cos(am), FACE - 0.001, SHOULDER + ra * math.sin(am)), carve,
                         rot=(0, -math.degrees(am) + 90, 0), bevel=0))
    parts.append(box("border_base", (W - 2 * inset, 0.006, 0.008), (0, FACE - 0.001, 0.12), carve, bevel=0))
    # A cross in a roundel under the crown.
    cz = SHOULDER + 0.07
    parts.append(torus("roundel", 0.075, 0.006, (0, FACE - 0.002, cz), carve, rot=(90, 0, 0), major=20, minor=4))
    parts.append(box("cross_v", (0.014, 0.008, 0.12), (0, FACE - 0.002, cz), carve, bevel=0))
    parts.append(box("cross_h", (0.09, 0.008, 0.014), (0, FACE - 0.002, cz + 0.02), carve, bevel=0))
    # Worn lettering: a name line, a shorter date line, two faint lines lower down.
    for row, (z, h, half) in enumerate(((SHOULDER - 0.08, 0.05, 0.17), (SHOULDER - 0.17, 0.04, 0.11),
                                        (SHOULDER - 0.27, 0.032, 0.15), (SHOULDER - 0.33, 0.032, 0.12))):
        _strokes(f"letter_{row}", rnd, -half, half, z, h, carve, parts)

    # Moss on the crown and creeping up the foot.
    for k in range(4):
        a = math.radians(25 + 40 * k + rnd.uniform(-10, 10))
        # Mostly inside the stone, so only a thin cushion shows over the rim and on both faces.
        rm = rnd.uniform(0.045, 0.06)
        r = W / 2 - rm + 0.018
        parts.append(blob(f"moss_top_{k}", rm, (-r * math.cos(a), rnd.uniform(-0.005, 0.005), SHOULDER + r * math.sin(a)),
                          moss, squash=(1, 1.3, 1), subdiv=2, seed=30 + k, jitter=0.08))
    for k, x in enumerate((-0.2, -0.06, 0.17)):
        parts.append(blob(f"moss_foot_{k}", rnd.uniform(0.05, 0.07), (x, FACE - 0.005, 0.07 + rnd.uniform(0, 0.04)), moss,
                          squash=(1.3, 0.35, 0.9), subdiv=1, seed=40 + k))

    # Lean the stone about its back foot edge, then put its lowest point on the ground.
    tilt = Matrix.Rotation(math.radians(LEAN_SIDE), 4, "Y") @ Matrix.Rotation(math.radians(-LEAN_BACK), 4, "X")
    for obj in parts:
        obj.matrix_basis = tilt @ obj.matrix_basis
    pts = [obj.matrix_basis @ v.co for obj in parts for v in obj.data.vertices]
    cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
    cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    lift = Matrix.Translation((-cx, -cy, -min(p.z for p in pts)))
    for obj in parts:
        obj.matrix_basis = lift @ obj.matrix_basis

    # A low tuft of sod and dead grass round the foot, flat on the ground.
    for k, (x, y, r) in enumerate(((-0.17, -0.01, 0.15), (0.13, 0.02, 0.16), (0.0, 0.04, 0.13), (0.03, -0.05, 0.12))):
        h = 0.45
        blob(f"sod_{k}", r, (x, y, r * h * 1.1), sod, squash=(1.2, 0.7, h), subdiv=2, seed=50 + k, jitter=0.1)
