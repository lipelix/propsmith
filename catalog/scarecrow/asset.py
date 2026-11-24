"""A ragged scarecrow, front on -y: a pole stuck in a little earth mound with a crossbar for the arms, a patched old
coat buttoned over a straw body with straw out of the cuffs and the hem, a rope belt, a stuffed sack head with a
stitched face, and a battered wide-brimmed hat with a dented crown."""
import math
import random

from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall size: about 1.6 m across the arms (x), 0.4 m deep (y), 2.1 m to the top of the hat.
POLE_R, POLE_H = 0.045, 1.78
ARM_Z, ARM_L = 1.45, 1.52  # crossbar height and length
SLEEVE_R = 0.075
COAT_Z0, COAT_Z1 = 0.82, 1.52  # hem and shoulders of the coat
HEAD_R, HEAD_Z = 0.15, 1.72
BRIM_R, CROWN_R, CROWN_H = 0.22, 0.12, 0.2
MOUND_R = 0.2

WOOD = (0.17, 0.11, 0.06)  # linear RGB
WOOD_OLD = (0.14, 0.1, 0.065)
COAT = (0.12, 0.14, 0.09)
COAT_PATCH = (0.3, 0.14, 0.07)
COAT_PATCH2 = (0.2, 0.17, 0.12)
SACK = (0.36, 0.27, 0.15)
STITCH = (0.06, 0.045, 0.035)
STRAW = (0.45, 0.35, 0.12)
ROPE = (0.3, 0.22, 0.12)
HAT = (0.16, 0.12, 0.08)
EARTH = (0.11, 0.075, 0.045)


def _rod(name, r, a, b, mat, segments=8, bevel=0.003, r_top=None):
    """A round rod from point `a` to point `b`."""
    d = Vector(b) - Vector(a)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return cylinder(name, r, d.length, a, mat, r_top=r_top, segments=segments,
                    rot=tuple(math.degrees(x) for x in rot), bevel=bevel)


@prop
def scarecrow():
    rnd = random.Random(14)
    wood = material("scarecrow_wood", WOOD, vary=0.28, scale=10)
    old = material("scarecrow_wood_old", WOOD_OLD, vary=0.3, scale=9)
    coat = material("scarecrow_coat", COAT, rough=0.95, vary=0.3, scale=30, crevice=0.7)
    patch = material("scarecrow_patch", COAT_PATCH, rough=0.95, vary=0.3, scale=30)
    patch2 = material("scarecrow_patch_grey", COAT_PATCH2, rough=0.95, vary=0.3, scale=30)
    sack = material("scarecrow_sack", SACK, rough=0.95, vary=0.3, scale=40, crevice=0.7)
    stitch = material("scarecrow_stitch", STITCH, rough=0.9, vary=0.1, scale=20)
    straw = material("scarecrow_straw", STRAW, rough=0.9, vary=0.35, scale=60)
    rope = material("scarecrow_rope", ROPE, rough=0.9, vary=0.25, scale=50)
    hat = material("scarecrow_hat", HAT, rough=0.95, vary=0.3, scale=20, crevice=0.7)
    earth = material("scarecrow_earth", EARTH, rough=1.0, vary=0.3, scale=12)

    # The pole in a small heap of earth, and the crossbar lashed to it.
    cylinder("mound", MOUND_R, 0.09, (0, 0, 0), earth, r_top=MOUND_R * 0.45, segments=12, bevel=0.02)
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.6
        blob(f"clod_{i}", 0.04, (0.2 * math.cos(a), 0.18 * math.sin(a), 0.025), earth, squash=(1, 1, 0.6),
             subdiv=1, seed=20 + i)
    cylinder("pole", POLE_R, POLE_H, (0, 0, 0.005), wood, r_top=POLE_R * 0.85, segments=10, rot=(1.5, -1, 0),
             bevel=0.004)
    _rod("crossbar", 0.032, (-ARM_L / 2, 0.0, ARM_Z + 0.02), (ARM_L / 2, 0.0, ARM_Z - 0.02), old, segments=8)
    for i, rx in enumerate((45, -45)):
        torus(f"lashing_{i}", 0.05, 0.01, (0, 0, ARM_Z), rope, rot=(rx, 0, 0), major=14, minor=6)

    # The coat: a slightly flared body, buttoned, with sleeves along the crossbar and patches sewn on.
    cylinder("coat", 0.19, COAT_Z1 - COAT_Z0, (0, 0, COAT_Z0), coat, r_top=0.15, segments=14, bevel=0.01).scale = (
        1.15, 0.72, 1)
    cylinder("collar", 0.135, 0.05, (0, 0, COAT_Z1 - 0.01), coat, r_top=0.09, segments=14, bevel=0.008).scale = (
        1.15, 0.8, 1)
    box("coat_seam", (0.01, 0.01, COAT_Z1 - COAT_Z0 - 0.04), (0.012, -0.142, (COAT_Z0 + COAT_Z1) / 2 - 0.02), stitch,
        rot=(-3, 0, 0), bevel=0)
    for i in range(4):
        z = COAT_Z1 - 0.12 - i * 0.14
        cylinder(f"button_{i}", 0.014, 0.012, (-0.02, -0.138 - i * 0.006, z), stitch, segments=8, rot=(90, 0, 0),
                 bevel=0.002)
    box("patch_0", (0.11, 0.02, 0.1), (0.1, -0.13, 1.08), patch, rot=(rnd.uniform(-6, 6), -8, rnd.uniform(-8, 8)),
        bevel=0.004)
    box("patch_1", (0.09, 0.02, 0.09), (-0.11, -0.115, 1.32), patch2, rot=(-6, 10, rnd.uniform(-8, 8)), bevel=0.004)
    torus("belt", 0.185, 0.016, (0, 0, 1.0), rope, major=20, minor=6).scale = (1.13, 0.75, 1)
    _rod("belt_end", 0.012, (0.05, -0.14, 1.0), (0.07, -0.15, 0.88), rope, segments=6)
    for side in (-1, 1):
        x0, x1 = side * 0.12, side * (ARM_L / 2 - 0.1)
        _rod(f"sleeve_{side}", SLEEVE_R, (x0, 0, ARM_Z - 0.03), (x1, 0, ARM_Z - 0.015 * side), coat, segments=10,
             bevel=0.01, r_top=SLEEVE_R * 0.8)
        box(f"sleeve_patch_{side}", (0.12, 0.03, 0.08), (side * 0.38, -SLEEVE_R + 0.005, ARM_Z - 0.02),
            patch2 if side < 0 else patch, rot=(0, side * 4, 0), bevel=0.004)
        for i in range(7):  # straw out of the cuff
            a = 2 * math.pi * i / 7 + rnd.uniform(-0.3, 0.3)
            y, z = 0.035 * math.cos(a), 0.035 * math.sin(a)
            zc = ARM_Z - 0.015 * side - 0.01
            tip = (side * (ARM_L / 2 + rnd.uniform(0.0, 0.04)), y * 2.0, zc + z * 1.6 - rnd.uniform(0.02, 0.06))
            _rod(f"cuff_straw_{side}_{i}", 0.015, (x1 - side * 0.03, y, zc + z), tip, straw, segments=5, bevel=0,
                 r_top=0.002)
    # Ragged hem: straw hanging out below the coat.
    for i in range(14):
        a = 2 * math.pi * i / 14 + rnd.uniform(-0.15, 0.15)
        x, y = 0.15 * math.cos(a), 0.1 * math.sin(a)
        _rod(f"hem_straw_{i}", 0.018, (x, y, COAT_Z0 + 0.06),
             (x * 1.35, y * 1.35, COAT_Z0 - rnd.uniform(0.12, 0.22)), straw, segments=5, bevel=0, r_top=0.003)

    # The head: a stuffed sack tied at the neck, a stitched face, straw tufts out from under the hat.
    torus("neck_rope", 0.07, 0.014, (0, 0, HEAD_Z - 0.135), rope, major=16, minor=6)
    blob("head", HEAD_R, (0, 0, HEAD_Z), sack, squash=(1, 0.92, 1.05), subdiv=2, seed=11, jitter=0.05)
    for i, x in enumerate((-0.05, 0.05)):
        box(f"eye_{i}_a", (0.05, 0.012, 0.01), (x, -0.135, HEAD_Z + 0.03), stitch, rot=(0, 45, 0), bevel=0)
        box(f"eye_{i}_b", (0.05, 0.012, 0.01), (x, -0.135, HEAD_Z + 0.03), stitch, rot=(0, -45, 0), bevel=0)
    for i in range(5):  # a stitched grin
        x = -0.06 + i * 0.03
        z = HEAD_Z - 0.06 + 0.012 * abs(i - 2)
        box(f"mouth_{i}", (0.028, 0.012, 0.008), (x, -0.133 + 0.004 * abs(i - 2), z), stitch, rot=(0, 0, 0), bevel=0)
        box(f"mouth_tick_{i}", (0.006, 0.012, 0.026), (x, -0.134 + 0.004 * abs(i - 2), z), stitch, bevel=0)
    for i in range(9):
        a = 2 * math.pi * i / 9 + rnd.uniform(-0.2, 0.2)
        if math.sin(a) < -0.6:
            continue  # keep the face clear
        x, y = 0.12 * math.cos(a), 0.12 * math.sin(a)
        _rod(f"hair_{i}", 0.014, (x, y, HEAD_Z + 0.06), (x * 1.7, y * 1.7, HEAD_Z - rnd.uniform(0.0, 0.07)), straw,
             segments=5, bevel=0, r_top=0.002)

    # The hat: a drooping wide brim and a dented crown with a band.
    hz = HEAD_Z + 0.1
    cylinder("hat_brim", BRIM_R, 0.02, (0, 0, hz), hat, r_top=BRIM_R - 0.02, segments=20, rot=(-7, 5, 0),
             bevel=0.006)
    cylinder("hat_crown", CROWN_R, CROWN_H, (0.0, 0.0, hz + 0.01), hat, r_top=CROWN_R * 0.82, segments=14,
             rot=(-5, 7, 0), bevel=0.01)
    torus("hat_band", CROWN_R - 0.002, 0.012, (0.0, 0.0, hz + 0.045), rope, rot=(-5, 7, 0), major=16, minor=6)
    blob("hat_dent", 0.06, (0.02, -0.01, hz + CROWN_H + 0.005), hat, squash=(1.3, 0.8, 0.35), subdiv=1, seed=6,
         jitter=0.05)
    box("hat_tear", (0.06, 0.03, 0.02), (BRIM_R - 0.05, -0.08, hz + 0.02), stitch, rot=(-7, 5, 20), bevel=0)
