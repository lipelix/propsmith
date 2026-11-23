"""A giant cave toadstool about 2.2 m high with two smaller ones at its foot, growing from a low mound of dark cave
soil, about 1.5 × 1.5 × 2.2 m. The big one has a thick pale stem that bends a little as it rises, a ragged skirt ring
under the cap, a broad domed dusky violet cap with pale warty spots and dark gills beneath; the small ones lean away
from it.

A cap is a squashed blob with its underside pressed flat, a gill disc under it and spots set on its upper surface."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, cylinder

# Overall dimensions (metres): about 1.5 wide × 1.5 deep × 2.2 high.
MOUND_R, MOUND_H = 0.5, 0.07  # the soil mound
SEGS = 4  # stem segments

# (x, y, stem height, stem radius, cap radius, cap height, lean deg, lean yaw deg, spots, ring)
TOADSTOOLS = (
    (0.0, 0.05, 1.8, 0.16, 0.66, 0.38, 6, 150, 11, True),
    (0.38, -0.3, 0.62, 0.07, 0.25, 0.15, 18, -40, 5, False),
    (-0.3, -0.36, 0.42, 0.055, 0.19, 0.12, 24, -130, 4, False),
)

CAP = (0.22, 0.09, 0.14)  # linear RGB, dusky violet
CAP_DARK = (0.13, 0.05, 0.1)
SPOT = (0.46, 0.42, 0.34)  # pale warts
STEM = (0.46, 0.4, 0.3)
STEM_DARK = (0.3, 0.25, 0.18)
GILL = (0.16, 0.11, 0.1)
SOIL = (0.06, 0.05, 0.04)


def _toadstool(name, x, y, h, rs, rc, hc, lean, yaw, spots, ring, mats, rnd):
    a = math.radians(yaw)
    step = (h - MOUND_H * 0.5) / SEGS
    z, cx, cy = MOUND_H * 0.5, x, y  # rooted in the mound, so a lean never dips under the ground
    for i in range(SEGS):
        f0, f1 = i / SEGS, (i + 1) / SEGS
        r0 = rs * (1.35 - 0.45 * f0 + 0.25 * f0 * f0)  # a swollen foot, narrowing, flaring a little under the cap
        r1 = rs * (1.35 - 0.45 * f1 + 0.25 * f1 * f1)
        tilt = lean * (0.3 + 0.7 * f1)  # bends more as it rises
        cylinder(f"{name}_stem{i}", r0, step * 1.06, (cx, cy, z), mats["stem_dark"] if i == 0 else mats["stem"],
                 r_top=r1, segments=14, rot=(tilt, 0, yaw + 90), bevel=0)
        t = math.radians(tilt)
        cx += math.sin(t) * math.cos(a) * step
        cy += math.sin(t) * math.sin(a) * step
        z += math.cos(t) * step
        if ring and i == SEGS - 2:
            # A ragged skirt ring hanging from the stem.
            skirt = cylinder(f"{name}_ring", r1 * 1.75, 0.14, (cx, cy, z - 0.13), mats["stem"], r_top=r1 * 1.02,
                             segments=16, rot=(tilt, 0, yaw + 90), bevel=0)
            for v in skirt.data.vertices:
                if v.co.z < 0.01:
                    v.co.z += rnd.uniform(0, 0.04)
    # The cap: its underside pressed nearly flat, sitting on the stem top.
    base = z - hc * 0.15
    cap = blob(f"{name}_cap", 1.0, (cx, cy, base), mats["cap"], squash=(rc, rc, hc), subdiv=3,
               seed=rnd.randrange(1000), jitter=0.04)
    for v in cap.data.vertices:
        if v.co.z < 0:
            v.co.z *= 0.18  # the underside nearly flat, a slight bulge
    # The gills: a dark disc under the cap rim.
    cylinder(f"{name}_gills", rc * 0.93, hc * 0.12, (cx, cy, base - hc * 0.2), mats["gill"], r_top=rc * 0.3,
             segments=20, bevel=0)
    # Pale warts on the upper surface.
    for k in range(spots):
        u = rnd.uniform(0.15, 0.85)
        b = 2 * math.pi * k / spots + rnd.uniform(-0.3, 0.3)
        sx, sy = cx + rc * u * math.cos(b), cy + rc * u * math.sin(b)
        sz = base + hc * math.sqrt(max(0.0, 1 - u * u)) * 0.98
        sr = rc * rnd.uniform(0.07, 0.11)
        blob(f"{name}_spot{k}", sr, (sx, sy, sz), mats["spot"], squash=(1, 1, 0.45), subdiv=1,
             seed=rnd.randrange(1000), jitter=0.15)


@prop
def mushroom_giant():
    rnd = random.Random(17)
    mats = {
        "cap": material("mushroom_giant_cap", CAP, rough=0.45, vary=0.35, scale=4, crevice=0.6),
        "spot": material("mushroom_giant_spot", SPOT, rough=0.7, vary=0.2, scale=20, crevice=0.4),
        "stem": material("mushroom_giant_stem", STEM, rough=0.6, vary=0.25, scale=6, crevice=0.6),
        "stem_dark": material("mushroom_giant_stem_dark", STEM_DARK, rough=0.7, vary=0.3, scale=6, crevice=0.6),
        "gill": material("mushroom_giant_gills", GILL, rough=0.9, vary=0.2, scale=30, crevice=0.7),
    }
    soil = material("mushroom_giant_soil", SOIL, rough=0.95, vary=0.35, scale=8, crevice=0.7)

    # The soil mound, flat underneath.
    m = blob("mound", MOUND_R, (0, -0.04, 0), soil, squash=(1.1, 1.0, MOUND_H * 2 / MOUND_R), subdiv=3, seed=5,
             jitter=0.2)
    for v in m.data.vertices:
        v.co.z = max(v.co.z, 0.0)

    for i, t in enumerate(TOADSTOOLS):
        _toadstool(f"toadstool{i}", *t, mats, rnd)
