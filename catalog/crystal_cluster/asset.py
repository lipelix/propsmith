"""A cluster of tall six-sided crystals growing from a low lump of dark rock, about 1 × 1 × 1.4 m: one tall central
spire, a ring of shorter ones leaning outward at different angles, and small points breaking out of the rock round
them. The crystals are a pale glowing blue-violet, lighter at the tips; a light anchor sits in the heart of the cluster.

Each crystal is a hexagonal prism with a faceted point, rooted a little inside the rock."""
import math
import random

from mathutils import Matrix

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, cylinder

# Overall dimensions (metres): about 1.1 wide × 0.95 deep × 1.4 high.
ROCK_R, ROCK_H = 0.36, 0.3  # the rock lump: half-width and height
FLAT = 0.15  # share of the rock's height cut flat where it rests on the ground
TIP = 0.28  # length of a crystal's point as a share of its full length
LIGHT_Z = 0.75  # the light anchor, in the heart of the cluster

# (x, y, length, radius, tilt deg, yaw deg of the lean, colour): the crystals, tallest first.
CRYSTALS = (
    (0.0, 0.02, 1.16, 0.095, 4, 120, "pale"),
    (0.1, -0.1, 0.9, 0.075, 22, -60, "blue"),
    (-0.12, -0.06, 0.78, 0.07, 26, -150, "pale"),
    (-0.06, 0.13, 0.95, 0.07, 18, 110, "blue"),
    (0.14, 0.09, 0.66, 0.06, 30, 30, "violet"),
    (-0.2, 0.06, 0.5, 0.05, 40, 175, "violet"),
    (0.21, -0.02, 0.48, 0.05, 44, 5, "blue"),
    (0.02, -0.2, 0.52, 0.055, 38, -95, "violet"),
    (-0.14, -0.2, 0.34, 0.042, 50, -125, "pale"),
    (0.24, 0.2, 0.3, 0.038, 52, 45, "pale"),
    (-0.26, 0.2, 0.28, 0.036, 55, 140, "blue"),
    (0.3, -0.2, 0.24, 0.032, 58, -35, "violet"),
)

ROCK = (0.11, 0.1, 0.1)  # linear RGB, dark cave stone
ROCK_DARK = (0.065, 0.062, 0.066)
PALE = (0.46, 0.6, 0.66)  # glowing pale blue
BLUE = (0.2, 0.38, 0.56)
VIOLET = (0.32, 0.25, 0.54)


def _crystal(name, x, y, z, length, r, tilt, yaw, body, tip, rnd):
    """A hexagonal prism `length` long with a faceted point, standing on (x, y, z), leaning `tilt` degrees toward
    `yaw`."""
    rot = (tilt, 0, yaw + 90)  # tilting about local x leans the top toward -y; yaw + 90 turns that to `yaw`
    t, a = math.radians(tilt), math.radians(yaw)
    d = (math.sin(t) * math.cos(a), math.sin(t) * math.sin(a), math.cos(t))
    shaft = length * (1 - TIP)
    spin = rnd.uniform(0, 60)
    s = cylinder(f"{name}_shaft", r, shaft, (x, y, z), body, r_top=r * 0.92, segments=6, rot=rot, bevel=0.006)
    p = (x + d[0] * shaft, y + d[1] * shaft, z + d[2] * shaft)
    c = cylinder(f"{name}_point", r * 0.92, length * TIP, p, tip, r_top=r * 0.08, segments=6, rot=rot, bevel=0.004)
    for o in (s, c):
        o.data.transform(Matrix.Rotation(math.radians(spin), 4, "Z"))  # turn the facets about the crystal's axis


@prop
def crystal_cluster():
    rnd = random.Random(71)
    rock = material("crystal_cluster_rock", ROCK, rough=0.85, vary=0.3, scale=9, crevice=0.75)
    rock_dark = material("crystal_cluster_rock_dark", ROCK_DARK, rough=0.85, vary=0.3, scale=9, crevice=0.75)
    mats = {
        "pale": material("crystal_cluster_pale", PALE, rough=0.08, vary=0.25, scale=6, crevice=0.1),
        "blue": material("crystal_cluster_blue", BLUE, rough=0.08, vary=0.3, scale=6, crevice=0.1),
        "violet": material("crystal_cluster_violet", VIOLET, rough=0.08, vary=0.3, scale=6, crevice=0.1),
    }

    # The rock lump: a main boulder with its base cut flat and two smaller lumps against it.
    for i, (r, h, x, y, m, seed) in enumerate(((ROCK_R, ROCK_H, 0.0, 0.0, rock, 11),
                                               (0.2, 0.18, 0.26, 0.14, rock_dark, 12),
                                               (0.18, 0.15, -0.24, -0.16, rock_dark, 13))):
        rz = h / (2 * (1 - FLAT / 2))
        o = blob(f"rock_{i}", r, (x, y, 0), m, squash=(1.1, 1.0, rz / r), subdiv=2 if i else 3, seed=seed,
                 jitter=0.15)
        verts = o.data.vertices
        low = min(v.co.z for v in verts)
        cut = low + FLAT * (max(v.co.z for v in verts) - low)
        for v in verts:
            v.co.z = max(v.co.z, cut)
        o.location.z = -cut

    for i, (x, y, length, r, tilt, yaw, colour) in enumerate(CRYSTALS):
        # Rooted inside the rock: deeper near the middle where the rock is high.
        z = max(0.02, ROCK_H * 0.8 * (1 - (x * x + y * y) / (ROCK_R * ROCK_R * 1.4)))
        tip = mats["pale"] if colour != "violet" else mats["violet"]
        _crystal(f"crystal_{i}", x, y, z, length * rnd.uniform(0.97, 1.03), r, tilt + rnd.uniform(-3, 3),
                 yaw + rnd.uniform(-6, 6), mats[colour], tip, rnd)

    anchor("light:crystal", (0.0, 0.0, LIGHT_Z))
