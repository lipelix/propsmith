"""A straight 1.5 m section of narrow-gauge mine track: two flat-bottomed iron rails spiked to five rough-hewn wooden
sleepers laid on a thin bed of gravel; sleepers sit every 0.3 m so the spacing carries on across the joint and sections
join end to end along x."""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

MODULE = 1.5  # metres: the length wall, fence and track sections join at
# Overall dimensions: the track runs along x through the origin, one module long.
L = MODULE - 0.004  # rail length, a hair short so neighbours meet without overlapping
GAUGE = 0.6  # metres between the rail centre lines (narrow mine gauge; `mine_cart` wheels match it)
SLEEPERS = 5
PITCH = MODULE / SLEEPERS  # 0.3 m, so the spacing continues over the joint
SLEEPER = (0.13, 0.86, 0.075)  # x, y, z of one sleeper
# Rail profile (flat-bottomed): foot, web and head, stacked on the sleepers.
FOOT = (0.056, 0.01)  # width, height
WEB = (0.012, 0.04)
HEAD = (0.03, 0.022)

WOOD = (0.17, 0.11, 0.065)  # linear RGB, dark tarred oak
WOOD_OLD = (0.2, 0.15, 0.1)  # one grey, older sleeper
IRON = (0.07, 0.06, 0.052)  # rail sides, rusty dark
IRON_TOP = (0.2, 0.19, 0.18)  # rail head, worn bright by wheels
RUST = (0.2, 0.085, 0.035)
GRAVEL = (0.15, 0.135, 0.115)


@prop
def rail_track_straight():
    rnd = random.Random(23)
    wood = material("rail_track_sleeper", WOOD, vary=0.3, scale=12)
    old = material("rail_track_sleeper_old", WOOD_OLD, vary=0.3, scale=12)
    iron = material("rail_track_iron", IRON, rough=0.6, vary=0.35, scale=18, metal=0.6)
    head = material("rail_track_head", IRON_TOP, rough=0.35, vary=0.2, scale=25, metal=0.85)
    rust = material("rail_track_rust", RUST, rough=0.9, vary=0.35, scale=20)
    gravel = material("rail_track_gravel", GRAVEL, rough=0.95, vary=0.35, scale=14, crevice=0.7)

    sx, sy, sz = SLEEPER
    for i in range(SLEEPERS):
        x = -MODULE / 2 + PITCH * (i + 0.5) + rnd.uniform(-0.012, 0.012)
        mat = old if i == 3 else wood
        box(f"sleeper_{i}", (sx * rnd.uniform(0.92, 1.05), sy * rnd.uniform(0.96, 1.0), sz), (x, rnd.uniform(-0.02, 0.02),
            sz / 2), mat, rot=(0, 0, rnd.uniform(-2.5, 2.5)), bevel=0.012)
        for s in (-1, 1):
            y = s * GAUGE / 2
            # A tie plate under the rail foot and a spike head either side of it.
            box(f"plate_{i}_{s}", (0.1, 0.12, 0.008), (x, y, sz + 0.004), rust, bevel=0)
            for e in (-1, 1):
                box(f"spike_head_{i}_{s}_{e}", (0.022, 0.03, 0.008), (x + e * 0.025, y + e * 0.036, sz + 0.016),
                    iron, rot=(0, 0, rnd.uniform(-8, 8)), bevel=0)

    # The rails: foot, web and a worn head, each the full length.
    z = sz + 0.008
    for s in (-1, 1):
        y = s * GAUGE / 2
        box(f"rail_foot_{s}", (L, FOOT[0], FOOT[1]), (0, y, z + FOOT[1] / 2), iron, bevel=0.003)
        box(f"rail_web_{s}", (L, WEB[0], WEB[1] + 0.004), (0, y, z + FOOT[1] + WEB[1] / 2), iron, bevel=0)
        box(f"rail_head_{s}", (L, HEAD[0], HEAD[1]), (0, y, z + FOOT[1] + WEB[1] + HEAD[1] / 2), head, bevel=0.005)
        # Fishplates at the -x end, where this section is bolted to the next.
        for f in (-1, 1):
            py = y + f * (WEB[0] / 2 + 0.006)
            box(f"fishplate_{s}_{f}", (0.16, 0.01, 0.036), (-L / 2 + 0.08, py, z + FOOT[1] + WEB[1] / 2), iron,
                bevel=0.002)
            for b in (-1, 1):
                cylinder(f"bolt_{s}_{f}_{b}", 0.008, 0.012, (-L / 2 + 0.08 + b * 0.05, py + f * 0.004,
                         z + FOOT[1] + WEB[1] / 2), iron, segments=6, rot=(-f * 90, 0, 0), bevel=0)

    # A thin bed of gravel between the sleepers, kept low so the track still lies flat on any floor.
    for k in range(16):
        x = rnd.uniform(-L / 2 + 0.06, L / 2 - 0.06)
        y = rnd.uniform(-0.4, 0.4)
        r = rnd.uniform(0.025, 0.045)
        blob(f"gravel_{k}", r, (x, y, r * 0.35), gravel, squash=(1.2, 1, 0.45), subdiv=1, seed=300 + k, jitter=0.25)
