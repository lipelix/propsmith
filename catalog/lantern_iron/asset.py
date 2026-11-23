"""A hand lantern of black iron standing on the ground: a square base plate on four stubby feet, four corner posts
with thin cross bands, warm translucent horn panes on every side and a stub of candle inside, a pyramid hood with a
little vent cap and a carrying ring on top."""
import math
import random

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# About 0.2 x 0.2 x 0.4 m.
W = 0.15  # body width, between the post centres plus a post
FOOT_H = 0.012
BASE_H = 0.022
BODY_H = 0.19  # height of the panes
POST = 0.014
HOOD_H = 0.075
VENT_R, VENT_H = 0.026, 0.03
RING_R, RING_T = 0.03, 0.006
CANDLE_R, CANDLE_H = 0.019, 0.075

IRON = (0.045, 0.043, 0.04)  # linear RGB
IRON_RUST = (0.1, 0.055, 0.032)
HORN = (0.42, 0.27, 0.1)  # thin scraped horn, lit warm from inside
HORN_DARK = (0.3, 0.18, 0.07)
WAX = (0.42, 0.36, 0.25)
FLAME = (0.5, 0.3, 0.05)


@prop
def lantern_iron():
    rnd = random.Random(41)
    iron = material("lantern_iron_iron", IRON, rough=0.55, vary=0.25, scale=30, metal=0.6, crevice=0.6)
    rust = material("lantern_iron_rust", IRON_RUST, rough=0.85, vary=0.3, scale=40, metal=0.2)
    horn = material("lantern_iron_horn", HORN, rough=0.35, vary=0.35, scale=40, crevice=0.2)
    horn_dark = material("lantern_iron_horn_dark", HORN_DARK, rough=0.4, vary=0.35, scale=40, crevice=0.2)
    wax = material("lantern_iron_wax", WAX, rough=0.6, vary=0.15, scale=40, crevice=0.4)
    flame = material("lantern_iron_flame", FLAME, rough=0.5, vary=0.2, scale=30, crevice=0.1)

    # Feet and base plate.
    h = W / 2 - 0.012
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        box(f"foot_{i}", (0.024, 0.024, FOOT_H), (sx * h, sy * h, FOOT_H / 2), rust, bevel=0.003)
    z0 = FOOT_H
    box("base", (W + 0.012, W + 0.012, BASE_H), (0, 0, z0 + BASE_H / 2), iron, bevel=0.005)
    z1 = z0 + BASE_H  # floor of the body
    z2 = z1 + BODY_H  # top of the panes

    # Candle stub with a drip and a small flame.
    cylinder("candle", CANDLE_R, CANDLE_H, (0, 0, z1), wax, segments=10, bevel=0.003)
    blob("drip", 0.008, (CANDLE_R - 0.002, 0, z1 + CANDLE_H - 0.02), wax, squash=(0.8, 0.8, 2.2), subdiv=1, seed=3,
         jitter=0.1)
    blob("flame", 0.011, (0, 0, z1 + CANDLE_H + 0.022), flame, squash=(0.8, 0.8, 2.0), subdiv=2, seed=4, jitter=0.08)

    # Corner posts and the frame round the top of the panes.
    p = W / 2 - POST / 2
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        box(f"post_{i}", (POST, POST, BODY_H), (sx * p, sy * p, z1 + BODY_H / 2), iron,
            rot=(0, 0, rnd.uniform(-1.5, 1.5)), bevel=0.003)
    box("top_band", (W + 0.008, W + 0.008, 0.016), (0, 0, z2 - 0.006), iron, bevel=0.004)

    # Horn panes on all four sides, each with a cross band; the front pane (-y) is a door with a hinge and a latch.
    pane_w = W - 2 * POST + 0.004
    pane_h = BODY_H - 0.02
    zc = z1 + pane_h / 2 + 0.002
    for i, yaw in enumerate((0, 90, 180, 270)):
        a = math.radians(yaw)
        nx, ny = math.sin(a), -math.cos(a)  # outward normal: -y first, then +x, +y, -x
        d = W / 2 - 0.004
        box(f"pane_{i}", (pane_w, 0.004, pane_h), (nx * d, ny * d, zc), horn if i % 2 == 0 else horn_dark,
            rot=(0, 0, yaw), bevel=0.001)
        d2 = W / 2 + 0.001
        box(f"band_{i}", (pane_w, 0.006, 0.012), (nx * d2, ny * d2, zc - 0.01), iron, rot=(0, 0, yaw), bevel=0.002)
        box(f"rib_{i}", (0.008, 0.006, pane_h), (nx * d2, ny * d2, zc), iron, rot=(0, 0, yaw), bevel=0.002)
    for k in (-1, 1):
        box(f"hinge_{k}", (0.012, 0.01, 0.022), (-p + 0.006, -W / 2 - 0.004, zc + k * 0.06), iron, bevel=0.002)
    box("latch", (0.022, 0.008, 0.012), (p - 0.012, -W / 2 - 0.005, zc + 0.02), rust, bevel=0.002)

    # Pyramid hood, vent cap and carrying ring.
    cylinder("hood", (W + 0.016) / math.sqrt(2), HOOD_H, (0, 0, z2), iron, r_top=0.03, segments=4, rot=(0, 0, 45),
             bevel=0.004)
    z3 = z2 + HOOD_H
    cylinder("vent", VENT_R, VENT_H, (0, 0, z3 - 0.004), iron, r_top=VENT_R * 0.8, segments=8, bevel=0.003)
    for i in range(4):
        a = math.radians(45 + 90 * i)
        box(f"vent_hole_{i}", (0.012, 0.004, 0.012),
            (VENT_R * 0.92 * math.cos(a), VENT_R * 0.92 * math.sin(a), z3 + 0.012), rust,
            rot=(0, 0, math.degrees(a) + 90), bevel=0)
    z4 = z3 - 0.004 + VENT_H
    cylinder("knob", 0.01, 0.008, (0, 0, z4), iron, segments=8, bevel=0.002)
    torus("ring", RING_R, RING_T, (0, 0, z4 + 0.006 + RING_R), iron, rot=(90, 0, 12), major=16, minor=6)

    anchor("light:lantern", (0, 0, z1 + CANDLE_H + 0.03))
