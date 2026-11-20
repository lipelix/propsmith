"""A shallow puddle of dark standing water, about 1 m across and a few centimetres high, lying on the floor: an
irregular glossy pool of three merged lobes, cool near-black with a faint green, inside a wider rim of wet darkened
silt that laps over its edges, with a few stones and grit poking out at the margin."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob

X, Y = 1.0, 0.8  # overall footprint
WATER_T = 0.011  # half the thickness of the water lens: its top is about twice this
RIM_T = 0.0095  # half the thickness of the silt rim lens, a little under the water in the middle

# The pool's lobes: (centre x, y, radius x, y). The rim lobes are these grown by RIM_GROW.
LOBES = [
    (0.0, 0.0, 0.3, 0.24),
    (0.16, 0.06, 0.18, 0.15),
    (-0.18, -0.05, 0.17, 0.14),
    (0.05, -0.13, 0.15, 0.11),
]
RIM_GROW = 0.07

WATER = (0.04, 0.05, 0.05)  # linear RGB: dark, faintly green standing water
SILT = (0.085, 0.078, 0.066)  # wet darkened silt
SILT_DRY = (0.125, 0.118, 0.105)  # the drier outer margin
STONE = (0.19, 0.195, 0.205)  # crypt stone chips
STONE_OLD = (0.145, 0.148, 0.155)


def _lens(name, rx, ry, t, at, mat, seed, jitter, subdiv=3):
    """A flat lumpy lens of half-thickness `t` lying on the ground centred over `at` (x, y)."""
    r = max(rx, ry)
    lift = t * (1 + jitter)
    return blob(name, r, (at[0], at[1], lift), mat, squash=(rx / r, ry / r, t / r), subdiv=subdiv, seed=seed,
                jitter=jitter)


@prop
def puddle_water():
    rnd = random.Random(912)
    water = material("puddle_water_water", WATER, rough=0.04, vary=0.12, scale=3, crevice=0.0)
    silt = material("puddle_water_silt", SILT, rough=0.35, vary=0.3, scale=12, crevice=0.6)
    dry = material("puddle_water_silt_dry", SILT_DRY, rough=0.9, vary=0.3, scale=16, crevice=0.6)
    stone = material("puddle_water_stone", STONE, rough=0.4, vary=0.22, scale=14, crevice=0.6)
    old = material("puddle_water_stone_old", STONE_OLD, rough=0.4, vary=0.25, scale=14, crevice=0.6)

    for i, (x, y, rx, ry) in enumerate(LOBES):
        _lens(f"water_{i}", rx, ry, WATER_T, (x, y), water, 10 + i, 0.04)
        _lens(f"rim_{i}", rx + RIM_GROW, ry + RIM_GROW * 0.9, RIM_T, (x * 1.05, y * 1.05), silt, 20 + i, 0.08)
        _lens(f"margin_{i}", rx + RIM_GROW * 1.4, ry + RIM_GROW * 1.3, RIM_T * 0.6, (x * 1.08, y * 1.08), dry,
              30 + i, 0.1, subdiv=2)

    # Stones and grit at the margin, half sunk in the silt.
    for i in range(14):
        a = 2 * math.pi * i / 14 + rnd.uniform(-0.2, 0.2)
        ex, ey = 0.4, 0.31
        d = rnd.uniform(0.86, 1.04)
        x, y = ex * d * math.cos(a), ey * d * math.sin(a)
        r = rnd.uniform(0.012, 0.03) if i % 3 else rnd.uniform(0.03, 0.045)
        blob(f"stone_{i}", r, (x, y, r * 0.45), rnd.choice([stone, old, dry]), squash=(1.2, 1, 0.55), subdiv=1,
             seed=rnd.randint(0, 9999), jitter=0.25)
