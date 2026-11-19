"""A blacksmith's iron anvil about 0.75 m long on a sawn wooden log block with an iron band."""
import math

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# The log block (metres).
R_LOG, H_LOG = 0.235, 0.5
CUT = 0.02  # pale sawn face on top
BAND_Z, BAND_R = 0.4, 0.012  # iron band height and tube radius

# The anvil, its long axis along x: horn toward -x, square heel toward +x.
L_ANVIL = 0.75
X_HORN_TIP, X_HEEL = -L_ANVIL / 2, L_ANVIL / 2
X_BODY = X_HEEL - 0.5  # where the horn meets the body
FOOT_H, WAIST_H, BODY_H = 0.06, 0.1, 0.09
BODY_W = 0.13
FACE_T = 0.012
HORN_L, HORN_R = X_BODY - X_HORN_TIP, 0.056

BARK = (0.14, 0.092, 0.058)
CUT_WOOD = (0.4, 0.3, 0.18)
RING = (0.26, 0.18, 0.1)
IRON = (0.06, 0.06, 0.064)
STEEL = (0.13, 0.13, 0.135)
SOOT = (0.04, 0.038, 0.036)


@prop
def anvil_iron():
    bark = material("anvil_iron_bark", BARK, vary=0.4, scale=26, rough=1.0)
    cut = material("anvil_iron_cut", CUT_WOOD, vary=0.2, scale=9)
    ring = material("anvil_iron_ring", RING, vary=0.15, scale=9)
    iron = material("anvil_iron_body", IRON, rough=0.55, metal=0.8, vary=0.25, scale=18)
    steel = material("anvil_iron_face", STEEL, rough=0.3, metal=0.9, vary=0.15, scale=12)
    soot = material("anvil_iron_soot", SOOT, rough=0.7, metal=0.5, vary=0.1, scale=20)

    # The log block: bark sides, a pale sawn top with rings, one iron band with rivets.
    cylinder("log", R_LOG, H_LOG - CUT, (0, 0, 0), bark, r_top=R_LOG - 0.01, segments=20, bevel=0.01)
    cylinder("log_cut", R_LOG - 0.018, CUT, (0, 0, H_LOG - CUT - 0.002), cut, segments=20, bevel=0.008)
    for i, rr in enumerate((0.19, 0.13, 0.07)):
        torus(f"log_ring_{i}", rr, 0.004, (0.005 * i, -0.004 * i, H_LOG - 0.003), ring, major=24, minor=4)
    rb = R_LOG - 0.012 * BAND_Z / H_LOG  # log radius at the band
    torus("band", rb, BAND_R, (0, 0, BAND_Z), iron, major=28, minor=6)
    for i in range(6):
        a = math.radians(i * 60 + 15)
        box(f"rivet_{i}", (0.016, 0.016, 0.016), (rb * math.cos(a) * 1.04, rb * math.sin(a) * 1.04, BAND_Z), soot,
            rot=(0, 0, math.degrees(a)), bevel=0.004)

    # The anvil body, standing on the block.
    z0 = H_LOG
    cx = (X_BODY + X_HEEL) / 2  # centre of the body block
    # A wide base with four splayed feet, narrowing into the waist.
    fx = cx - 0.02
    box("anvil_base", (0.3, 0.17, FOOT_H), (fx, 0, z0 + FOOT_H / 2), iron, bevel=0.012)
    for i, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        box(f"anvil_foot_{i}", (0.07, 0.07, 0.035), (fx + sx * 0.14, sy * 0.085, z0 + 0.0175), iron,
            rot=(0, 0, 45 * sx * sy), bevel=0.01)
    box("anvil_waist_lo", (0.24, 0.12, WAIST_H * 0.5), (fx, 0, z0 + FOOT_H + WAIST_H * 0.2), iron, bevel=0.012)
    box("anvil_waist_hi", (0.2, 0.095, WAIST_H * 0.6), (fx, 0, z0 + FOOT_H + WAIST_H * 0.6), iron, bevel=0.012)
    zb = z0 + FOOT_H + WAIST_H - 0.01
    box("anvil_body", (X_HEEL - X_BODY, BODY_W, BODY_H), (cx, 0, zb + BODY_H / 2), iron, bevel=0.014)
    # The step between horn and face (the table), a touch lower than the face.
    box("anvil_table", (0.07, BODY_W * 0.9, BODY_H * 0.5), (X_BODY - 0.03, 0, zb + BODY_H * 0.55), iron, bevel=0.01)
    # The hardened face on top, with the hardy and pritchel holes near the heel.
    zf = zb + BODY_H
    box("anvil_face", (X_HEEL - X_BODY - 0.012, BODY_W - 0.008, FACE_T), (cx + 0.004, 0, zf + FACE_T / 2 - 0.002),
        steel, bevel=0.005)
    box("hardy_hole", (0.026, 0.026, 0.004), (X_HEEL - 0.08, 0.015, zf + FACE_T - 0.0005), soot, bevel=0.002)
    cylinder("pritchel_hole", 0.008, 0.004, (X_HEEL - 0.13, 0.015, zf + FACE_T - 0.0025), soot, segments=8, bevel=0)
    # The tapered horn: a cone pointing -x, its top roughly level with the table.
    hz = zb + BODY_H * 0.55 + 0.004
    cylinder("anvil_horn", HORN_R, HORN_L - 0.06, (X_BODY - 0.06, 0, hz), iron, r_top=0.01, segments=12,
             rot=(0, -90, 0), bevel=0.004)
