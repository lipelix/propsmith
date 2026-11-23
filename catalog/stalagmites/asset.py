"""A group of four wet limestone stalagmites of different heights rising from a shared low flowstone base, about
1.2 × 1.2 × 1.6 m: a tall one about 1.6 m high, one about 1.1 m, one about 0.75 m and a stubby one about 0.4 m.

Each stalagmite is a stack of slightly offset tapering drums with lumpy drip rings at the joins and a rounded tip, so
it reads as grown, not turned; the cream-grey stone is darker and glossy where it is wet low down."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, cylinder

# Overall dimensions (metres): about 1.2 wide × 1.2 deep × 1.6 high.
BASE_R, BASE_H = 0.5, 0.08  # the flowstone base: half-width and height
DRUMS = 6  # drums per stalagmite

# (x, y, height, base radius, lean deg, lean yaw deg): the four stalagmites, tallest first.
SPIRES = (
    (0.06, 0.12, 1.6, 0.27, 3, 60),
    (-0.26, -0.12, 1.1, 0.21, 6, 200),
    (0.32, -0.08, 0.75, 0.17, 8, -10),
    (-0.04, -0.36, 0.42, 0.15, 10, -100),
)

LIME = (0.48, 0.44, 0.35)  # linear RGB, cream limestone
LIME_WET = (0.3, 0.27, 0.21)  # darker where wet
FLOW = (0.32, 0.28, 0.21)  # the flowstone base
PUDDLE = (0.06, 0.065, 0.06)


def _spire(name, x, y, h, r, lean, yaw, dry, wet, rnd):
    """Tapering drums stacked up to `h`, each a little off the one under it, a drip ring at each join."""
    a = math.radians(yaw)
    step = (h - BASE_H * 0.4 - r * 0.2) / DRUMS
    z, cx, cy = BASE_H * 0.4, x, y  # rooted in the flowstone, so a lean never dips under the ground
    for i in range(DRUMS):
        f0, f1 = 1 - i / DRUMS, 1 - (i + 1) / DRUMS
        r0, r1 = r * (0.14 + 0.86 * f0 ** 0.75), r * (0.14 + 0.86 * f1 ** 0.75)
        mat = wet if i < 2 else dry
        tilt = lean + rnd.uniform(-3, 3)
        cylinder(f"{name}_drum{i}", r0, step * 1.04, (cx, cy, z), mat, r_top=r1, segments=12,
                 rot=(tilt, 0, yaw + 90), bevel=0)
        t = math.radians(tilt)
        cx += math.sin(t) * math.cos(a) * step
        cy += math.sin(t) * math.sin(a) * step
        z += math.cos(t) * step
        if 0 < i + 1 < DRUMS:
            blob(f"{name}_ring{i}", r1 * rnd.uniform(1.03, 1.12), (cx, cy, z), wet if i < 2 else dry,
                 squash=(1, rnd.uniform(0.85, 1.0), 0.5), subdiv=2, seed=rnd.randrange(1000), jitter=0.14)
    # The rounded tip.
    tip = r * 0.2
    blob(f"{name}_tip", tip, (cx, cy, h - tip * 1.5), dry, squash=(1, 1, 1.5), subdiv=2, seed=rnd.randrange(1000),
         jitter=0.08)


@prop
def stalagmites():
    rnd = random.Random(29)
    dry = material("stalagmites_limestone", LIME, rough=0.35, vary=0.3, scale=7, crevice=0.6)
    wet = material("stalagmites_limestone_wet", LIME_WET, rough=0.15, vary=0.3, scale=7, crevice=0.6)
    flow = material("stalagmites_flowstone", FLOW, rough=0.2, vary=0.35, scale=5, crevice=0.7)
    puddle = material("stalagmites_puddle", PUDDLE, rough=0.03, vary=0.1, scale=4, crevice=0.2)

    # The flowstone base: overlapping low lobes, flat underneath, cut to the ground.
    lobes = ((0.0, 0.05, BASE_R, 1.0), (-0.22, -0.12, 0.3, 0.9), (0.3, -0.08, 0.24, 0.8), (-0.04, -0.32, 0.22, 0.8))
    for i, (x, y, r, k) in enumerate(lobes):
        o = blob(f"flow_{i}", r, (x, y, 0), flow, squash=(1.05, 0.95, BASE_H * k * 2 / r), subdiv=2, seed=40 + i,
                 jitter=0.1)
        for v in o.data.vertices:
            v.co.z = max(v.co.z, 0.0)
    # A shallow puddle on the front of the base where the drips land.
    cylinder("puddle", 0.12, 0.004, (0.24, -0.32, BASE_H * 0.5), puddle, r_top=0.115, segments=16, bevel=0)

    for i, (x, y, h, r, lean, yaw) in enumerate(SPIRES):
        _spire(f"spire{i}", x, y, h, r, lean, yaw, dry, wet, rnd)
