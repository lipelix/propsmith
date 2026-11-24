"""A tall weathered standing stone about 3 m high: a square tapering shaft of grey stone with a low pyramid cap, set on
a rough slab plinth in a ring of turf. Each face carries a column of angular rune glyphs cut into the stone and filled
with a faint pale blue-green glow, the column on the front (-y) longest; moss creeps up
its foot. A light anchor sits just in front of the front runes."""
import math
import random

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall dimensions (metres): about 0.8 × 0.8 × 3.
PLINTH = (0.74, 0.7, 0.2)  # the rough base slab: x, y, height
BASE_HALF = 0.25  # half-side of the shaft at its foot
TOP_HALF = 0.18  # half-side of the shaft under the cap
SHAFT_H = 2.45
CAP_H = 0.3  # the pyramid cap
Z0 = PLINTH[2]  # foot of the shaft
GLYPH = 0.15  # height of one rune glyph
STROKE = 0.02  # width of a rune stroke
PROUD = 0.004  # how far the glowing fill stands out of the face
LIGHT_Z = 1.55  # the light anchor, in front of the middle of the front runes

STONE = (0.25, 0.245, 0.235)  # linear RGB: weathered grey stone
STONE_DARK = (0.17, 0.168, 0.165)
GLOW = (0.36, 0.7, 0.66)  # pale blue-green rune glow
MOSS = (0.06, 0.085, 0.03)
SOD = (0.075, 0.075, 0.038)

# (start z above the shaft foot, glyph count) of the rune column on each face: -y, +x, +y, -x.
COLUMNS = {(0, -1): (0.45, 9), (1, 0): (0.7, 7), (0, 1): (0.6, 6), (-1, 0): (0.8, 5)}

# Rune glyphs as strokes in a unit cell (x -0.5..0.5, z 0..1): (x0, z0, x1, z1).
RUNES = (
    ((0, 0, 0, 1), (0, 0.55, 0.4, 0.9)),
    ((-0.25, 0, -0.25, 1), (-0.25, 1, 0.3, 0.6), (0.3, 0.6, -0.25, 0.25)),
    ((0, 0, 0, 1), (-0.35, 0.75, 0.35, 0.45)),
    ((-0.3, 0, -0.3, 1), (0.3, 0, 0.3, 1), (-0.3, 0.7, 0.3, 0.35)),
    ((0, 0, 0, 1), (0, 0.5, -0.35, 1), (0, 0.5, 0.35, 1)),
    ((-0.3, 0, 0.3, 1), (0.3, 0, -0.3, 1)),
    ((0, 0, 0, 1), (0, 1, 0.35, 0.65), (0, 0.6, 0.35, 0.3)),
    ((-0.3, 1, 0.3, 0.5), (0.3, 0.5, -0.3, 0)),
    ((0, 0, 0, 1), (-0.35, 0.2, 0.35, 0.55)),
)


def _half(z):
    """Half-side of the shaft at height z."""
    t = (z - Z0) / SHAFT_H
    return BASE_HALF + (TOP_HALF - BASE_HALF) * t


def _glyph(name, face, centre_u, z_base, rune, mat, out):
    """The strokes of one rune on `face` ((dx, dy) of its outward normal), centred at u along the face."""
    dx, dy = face
    slope = math.degrees(math.atan((BASE_HALF - TOP_HALF) / SHAFT_H))
    for k, (x0, z0, x1, z1) in enumerate(rune):
        ux0, ux1 = centre_u + x0 * GLYPH * 0.6, centre_u + x1 * GLYPH * 0.6
        zz0, zz1 = z_base + z0 * GLYPH, z_base + z1 * GLYPH
        um, zm = (ux0 + ux1) / 2, (zz0 + zz1) / 2
        length = math.hypot(ux1 - ux0, zz1 - zz0) + STROKE * 0.6
        ang = math.degrees(math.atan2(zz1 - zz0, ux1 - ux0))
        n = _half(zm) + PROUD - 0.008  # half sunk into the face
        if dy:  # face along x: u runs along x (mirrored on +y so glyphs read from outside)
            u = um if dy < 0 else -um
            a = -ang if dy < 0 else ang
            out.append(box(f"{name}_{k}", (length, 0.016, STROKE), (u, dy * n, zm), mat,
                           rot=(dy * slope, a, 0), bevel=0))
        else:  # face along y
            u = um if dx > 0 else -um
            a = ang if dx > 0 else -ang
            out.append(box(f"{name}_{k}", (0.016, length, STROKE), (dx * n, u, zm), mat,
                           rot=(a, -dx * slope, 0), bevel=0))


@prop
def obelisk_rune():
    rnd = random.Random(116)
    stone = material("obelisk_rune_stone", STONE, vary=0.3, scale=6, crevice=0.65)
    dark = material("obelisk_rune_stone_dark", STONE_DARK, vary=0.3, scale=7, crevice=0.7)
    glow = material("obelisk_rune_glow", GLOW, rough=0.3, vary=0.15, scale=12, crevice=0.05)
    moss = material("obelisk_rune_moss", MOSS, rough=0.95, vary=0.35, scale=16, crevice=0.6)
    sod = material("obelisk_rune_sod", SOD, rough=0.95, vary=0.35, scale=10)
    parts = []  # the rune strokes

    # The plinth: a rough slab, its top a little uneven, set slightly askew.
    box("plinth", PLINTH, (0, 0, PLINTH[2] / 2), dark, rot=(0, 0, 3), bevel=0.03)
    # The shaft: a square frustum (four-sided cylinder turned 45 deg so its faces lie on the axes), then the cap.
    r0, r1 = BASE_HALF * math.sqrt(2), TOP_HALF * math.sqrt(2)
    cylinder("shaft", r0, SHAFT_H, (0, 0, Z0 - 0.02), stone, r_top=r1, segments=4, rot=(0, 0, 45), bevel=0.02)
    cylinder("cap", r1 * 1.02, CAP_H, (0, 0, Z0 - 0.02 + SHAFT_H), stone, r_top=0.02, segments=4, rot=(0, 0, 45),
             bevel=0.015)

    # Rune columns on each face.
    for (dx, dy), (start, count) in COLUMNS.items():
        z = Z0 + start
        for g in range(count):
            rune = RUNES[rnd.randrange(len(RUNES))]
            _glyph(f"rune_{dx}_{dy}_{g}", (dx, dy), rnd.uniform(-0.015, 0.015), z, rune, glow, parts)
            z += GLYPH * 1.45

    # Moss creeping up the foot of the shaft and on the plinth.
    for k in range(6):
        side = rnd.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
        u = rnd.uniform(-0.18, 0.18)
        x = side[0] * BASE_HALF + (u if side[1] else 0)
        y = side[1] * BASE_HALF + (u if side[0] else 0)
        blob(f"moss_{k}", rnd.uniform(0.06, 0.09), (x, y, Z0 + rnd.uniform(0.02, 0.12)), moss,
             squash=(1.2 if side[1] else 0.4, 1.2 if side[0] else 0.4, 1.0), subdiv=1, seed=60 + k)
    # A ring of turf round the plinth.
    for k in range(7):
        a = math.radians(k * 360 / 7 + rnd.uniform(-15, 15))
        r = rnd.uniform(0.1, 0.13)
        d = 0.27
        blob(f"sod_{k}", r, (d * math.cos(a), d * math.sin(a), r * 0.5 * 1.12), sod, squash=(1.1, 1.0, 0.5),
             subdiv=2,
             seed=70 + k, jitter=0.1)

    anchor("light:rune", (0, -BASE_HALF - 0.12, LIGHT_Z))
