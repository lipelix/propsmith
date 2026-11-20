"""A cult banner, about 1 x 0.4 m and 2.5 m high: a tattered dark wine-red cloth hanging from an iron crossbar on a
tall iron pole with a spiked finial, its lower edge torn into ragged tails of uneven length, a pale sigil painted on
its front (-y): a ring round a five-pointed star with an eye-like dot at the centre. The pole stands in a heavy
cross-shaped iron foot."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

W, D, H = 1.0, 0.4, 2.5  # overall width (crossbar, x), depth (foot, y), height
POLE_R = 0.022
POLE_Y = 0.05  # the pole stands a little behind the cloth
BAR_Z = 2.27  # crossbar height
BAR_R = 0.016
FINIAL = 0.14  # spike above the pole top
FOOT_T = 0.05  # foot bar thickness
CLOTH_W = 0.84
CLOTH_T = 0.012
CLOTH_Y = POLE_Y - POLE_R - CLOTH_T / 2 - 0.01
PANEL_BOTTOM = 0.95  # where the whole cloth ends and the torn tails begin
SIGIL_Z = 1.62  # centre of the sigil
SIGIL_R = 0.28

IRON = (0.048, 0.046, 0.044)  # linear RGB
IRON_WORN = (0.13, 0.115, 0.1)
CLOTH = (0.085, 0.028, 0.032)  # dark wine red, faded
CLOTH_OLD = (0.065, 0.032, 0.034)
PAINT = (0.34, 0.29, 0.21)  # pale bone paint


@prop
def banner_cult():
    rnd = random.Random(632)
    iron = material("banner_cult_iron", IRON, rough=0.55, vary=0.25, scale=12, metal=0.6)
    worn = material("banner_cult_iron_worn", IRON_WORN, rough=0.45, vary=0.2, scale=14, metal=0.7)
    cloth = material("banner_cult_cloth", CLOTH, rough=0.95, vary=0.3, scale=6, crevice=0.6)
    cloth_old = material("banner_cult_cloth_old", CLOTH_OLD, rough=0.95, vary=0.35, scale=8, crevice=0.6)
    paint = material("banner_cult_paint", PAINT, rough=0.9, vary=0.35, scale=10, crevice=0.4)

    # Foot: two crossed flat bars, a boss and a socket.
    box("foot_x", (0.4, 0.07, FOOT_T), (0, POLE_Y - 0.05, FOOT_T / 2), iron, bevel=0.01)
    box("foot_y", (0.07, D - 0.02, FOOT_T), (0, 0, FOOT_T / 2), iron, bevel=0.01)
    for i, (x, y) in enumerate([(-0.19, POLE_Y - 0.05), (0.19, POLE_Y - 0.05), (0, -D / 2 + 0.02), (0, D / 2 - 0.02)]):
        cylinder(f"foot_pad_{i}", 0.035, FOOT_T + 0.008, (x, y, 0), worn, segments=10, bevel=0.006)
    cylinder("boss", 0.07, 0.06, (0, POLE_Y - 0.0, FOOT_T - 0.01), iron, r_top=0.05, segments=14, bevel=0.008)
    cylinder("socket", 0.035, 0.2, (0, POLE_Y, FOOT_T + 0.04), iron, r_top=0.03, segments=12, bevel=0.006)
    # Pole, finial and crossbar.
    top = H - FINIAL
    cylinder("pole", POLE_R, top - FOOT_T, (0, POLE_Y, FOOT_T), iron, segments=12, bevel=0.004)
    cylinder("collar", 0.03, 0.03, (0, POLE_Y, top - 0.03), worn, segments=12, bevel=0.005)
    cylinder("finial", 0.026, FINIAL, (0, POLE_Y, top), worn, r_top=0.002, segments=8, bevel=0)
    cylinder("crossbar", BAR_R, W - 0.06, (-(W - 0.06) / 2, CLOTH_Y, BAR_Z), iron, rot=(0, 90, 0), segments=10,
             bevel=0.003)
    for side in (-1, 1):
        blob(f"bar_knob_{side}", 0.03, (side * (W / 2 - 0.03), CLOTH_Y, BAR_Z), worn, subdiv=1, seed=side + 5,
             jitter=0.05)
    box("bar_brace", (0.05, POLE_Y - CLOTH_Y + 0.02, 0.05), (0, (POLE_Y + CLOTH_Y) / 2, BAR_Z), iron, bevel=0.006)
    # Cloth: a sleeve round the bar and the panel hanging under it.
    box("sleeve", (CLOTH_W, CLOTH_T + 2 * BAR_R + 0.008, 0.07), (0, CLOTH_Y, BAR_Z - 0.005), cloth, bevel=0.012)
    panel_top = BAR_Z - 0.03
    box("panel", (CLOTH_W, CLOTH_T, panel_top - PANEL_BOTTOM), (0, CLOTH_Y, (panel_top + PANEL_BOTTOM) / 2), cloth,
        rot=(0, 0, 0), bevel=0.003)
    # Ragged tails of uneven length, a few twisted or lifted a little.
    tails = 7
    tw = CLOTH_W / tails
    for i in range(tails):
        length = rnd.uniform(0.18, 0.62)
        x = -CLOTH_W / 2 + tw * (i + 0.5) + rnd.uniform(-0.01, 0.01)
        w = tw * rnd.uniform(0.82, 1.02)
        rot_y = rnd.uniform(-5, 5)
        box(f"tail_{i}", (w, CLOTH_T * 0.9, length), (x, CLOTH_Y + rnd.uniform(-0.004, 0.004), PANEL_BOTTOM - length / 2
            + 0.02), rnd.choice([cloth, cloth_old]), rot=(rnd.uniform(-3, 3), rot_y, 0), bevel=0.002)
        # A tapered torn tip.
        tip = rnd.uniform(0.06, 0.12)
        box(f"tail_{i}_tip", (w * 0.5, CLOTH_T * 0.8, tip),
            (x + rnd.uniform(-0.02, 0.02) - math.sin(math.radians(rot_y)) * length,
             CLOTH_Y, PANEL_BOTTOM - length - tip / 2 + 0.03), cloth_old, rot=(0, rot_y + rnd.uniform(-8, 8), 0),
            bevel=0.002)
    # The sigil, painted on the front of the cloth.
    face = CLOTH_Y - CLOTH_T / 2 - 0.0015
    ring = torus("sigil_ring", SIGIL_R, 0.018, (0, face, SIGIL_Z), paint, rot=(90, 0, 0), major=40, minor=4)
    ring.scale = (1, 1, 0.12)
    pts = [(SIGIL_R * math.cos(math.pi / 2 + 2 * math.pi * i / 5), SIGIL_R * math.sin(math.pi / 2 + 2 * math.pi * i / 5))
           for i in range(5)]
    for i in range(5):
        (ax, az), (bx, bz) = pts[i], pts[(i + 2) % 5]
        length = math.hypot(bx - ax, bz - az)
        ang = math.degrees(math.atan2(bz - az, bx - ax))
        box(f"sigil_star_{i}", (length, 0.004, 0.028), ((ax + bx) / 2, face, SIGIL_Z + (az + bz) / 2), paint,
            rot=(0, -ang, 0), bevel=0)
    cylinder("sigil_eye", 0.05, 0.004, (0, face + 0.002, SIGIL_Z), paint, rot=(90, 0, 0), segments=14, bevel=0)
    # Drips of paint under the sigil and a band at the top.
    for i, (x, length) in enumerate([(-0.12, 0.12), (0.05, 0.2), (0.17, 0.08)]):
        box(f"sigil_drip_{i}", (0.016, 0.004, length), (x, face, SIGIL_Z - SIGIL_R - length / 2 + 0.01), paint, bevel=0)
    box("band", (CLOTH_W - 0.06, 0.004, 0.03), (0, face, panel_top - 0.1), paint, bevel=0)
