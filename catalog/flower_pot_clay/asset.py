"""A terracotta pot with red and yellow flowers (hand-written)."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, cylinder, torus

CLAY = (0.42, 0.14, 0.06)
SOIL = (0.05, 0.03, 0.018)
LEAF = (0.045, 0.12, 0.025)
RED = (0.55, 0.05, 0.06)
YELLOW = (0.7, 0.48, 0.06)


@prop
def flower_pot_clay():
    rnd = random.Random(11)
    clay = material("pot_clay", CLAY, vary=0.2, scale=8, rough=0.9)
    cylinder("pot", 0.15, 0.3, (0, 0, 0), clay, r_top=0.2, segments=24, bevel=0.01)
    torus("rim", 0.205, 0.025, (0, 0, 0.3), clay, minor=8)
    cylinder("soil", 0.19, 0.01, (0, 0, 0.28), material("pot_soil", SOIL), segments=24, bevel=0)

    leaf = material("pot_leaf", LEAF, vary=0.35, scale=20, rough=0.7)
    for i in range(10):
        a = 2 * math.pi * i / 10 + rnd.uniform(-0.3, 0.3)
        r = rnd.uniform(0.04, 0.13)
        blob(f"leaf_{i}", rnd.uniform(0.06, 0.09), (r * math.cos(a), r * math.sin(a), rnd.uniform(0.33, 0.42)), leaf, squash=(1, 1, 0.7), seed=i, subdiv=1)
    for i in range(8):
        a = 2 * math.pi * i / 8 + rnd.uniform(-0.3, 0.3)
        r = rnd.uniform(0.0, 0.14)
        colour = (RED, YELLOW)[i % 2]
        blob(
            f"flower_{i}",
            rnd.uniform(0.03, 0.045),
            (r * math.cos(a), r * math.sin(a), rnd.uniform(0.43, 0.5)),
            material(f"pot_flower_{i % 2}", colour, vary=0.15, rough=0.6, crevice=0.3),
            squash=(1, 1, 0.6),
            seed=20 + i,
            subdiv=1,
        )
