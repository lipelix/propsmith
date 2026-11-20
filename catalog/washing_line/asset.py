"""A washing line: two leaning round posts with short cross arms, a sagging rope between them and laundry pegged on
it (a sheet, a shirt, a pair of hose, an apron and two rags), the cloths hanging along x."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall dimensions (metres): about 3 long, 0.3 deep and 2 high.
L = 3.0
POST_X = 1.4  # posts at +-POST_X
POST_R = 0.055
POST_H = 1.9
ARM_W = 0.28  # cross arm length along y
ARM_Z = 1.8  # rope height at the posts
SAG = 0.16  # how far the rope dips at mid-span
ROPE_R = 0.008
ROPE_SEGS = 12
CLOTH_T = 0.012

WOOD = (0.2, 0.14, 0.09)
WOOD_OLD = (0.16, 0.12, 0.085)
ROPE = (0.32, 0.27, 0.19)
PEG = (0.24, 0.18, 0.11)
STONE = (0.3, 0.27, 0.23)

# Laundry: kind, centre x, width, drop, colour.
LAUNDRY = (
    ("sheet", -0.88, 0.8, 0.95, (0.42, 0.39, 0.32)),  # unbleached linen
    ("shirt", -0.12, 0.5, 0.62, (0.2, 0.26, 0.33)),  # faded blue
    ("hose", 0.42, 0.26, 0.62, (0.28, 0.17, 0.09)),  # brown wool
    ("apron", 0.84, 0.42, 0.55, (0.36, 0.3, 0.2)),  # oatmeal
    ("rag", 1.17, 0.2, 0.26, (0.33, 0.13, 0.08)),  # madder red
)


def rope_z(x):
    """The rope's height at x: a parabola from ARM_Z at the posts down by SAG at the middle."""
    return ARM_Z - SAG * (1 - (x / POST_X) ** 2)


@prop
def washing_line():
    rnd = random.Random(23)
    wood = material("washing_line_wood", WOOD, vary=0.3, scale=14)
    wood_old = material("washing_line_wood_old", WOOD_OLD, vary=0.3, scale=14)
    rope = material("washing_line_rope", ROPE, vary=0.25, scale=40)
    peg = material("washing_line_peg", PEG, vary=0.2, scale=30)
    stone = material("washing_line_stone", STONE, vary=0.25, scale=9, crevice=0.6)

    # Two round posts, each with a cross arm, a knee brace and a few stones packed round its foot.
    for s in (-1, 1):
        x = s * POST_X
        cylinder(f"post_{s}", POST_R, POST_H, (x, 0, 0), wood_old if s > 0 else wood, r_top=POST_R * 0.85,
                 segments=9, rot=(rnd.uniform(-1, 1), s * 1.0, rnd.uniform(0, 360)), bevel=0.01)
        box(f"arm_{s}", (0.07, ARM_W, 0.06), (x + s * 0.04, 0, ARM_Z + 0.04), wood, rot=(rnd.uniform(-3, 3), 0, 0),
            bevel=0.01)
        for k in range(3):
            a = rnd.uniform(0, 2 * math.pi) + k * 2.1
            blob(f"foot_{s}_{k}", 0.07, (x + 0.1 * math.cos(a), 0.09 * math.sin(a), 0.036), stone,
                 squash=(1.1, 0.9, 0.5), subdiv=1, seed=100 + k + 10 * (s + 1))
        # Rope tied round the arm end: a short knot.
        cylinder(f"knot_{s}", 0.02, 0.05, (x + s * 0.02, 0, ARM_Z - 0.012), rope, segments=8, rot=(0, 90, 0),
                 bevel=0.004)

    # The rope: straight pieces along the sag curve.
    x0 = -POST_X + 0.02
    x1 = POST_X - 0.02
    for i in range(ROPE_SEGS):
        a = x0 + (x1 - x0) * i / ROPE_SEGS
        b = x0 + (x1 - x0) * (i + 1) / ROPE_SEGS
        za, zb = rope_z(a), rope_z(b)
        length = math.hypot(b - a, zb - za) + 0.004
        pitch = math.degrees(math.atan2(b - a, zb - za))
        cylinder(f"rope_{i}", ROPE_R, length, (a, 0, za), rope, segments=6, rot=(0, pitch, 0), bevel=0)

    # The laundry, pegged over the rope.
    for k, (kind, cx, w, drop, colour) in enumerate(LAUNDRY):
        cloth = material(f"washing_line_{kind}", colour, vary=0.2, scale=12, crevice=0.4)
        top = rope_z(cx) + 0.01
        slope = math.degrees(math.atan2(rope_z(cx + 0.1) - rope_z(cx - 0.1), 0.2))
        sway = rnd.uniform(-2, 2)
        y = rnd.uniform(-0.01, 0.01)
        if kind == "shirt":
            # Body hung by its hem, sleeves hanging beside it.
            box(f"{kind}_body", (w * 0.62, CLOTH_T, drop), (cx, y, top - drop / 2), cloth, rot=(sway, -slope, 0),
                bevel=0.004)
            for s in (-1, 1):
                box(f"{kind}_sleeve_{s}", (w * 0.2, CLOTH_T, drop * 0.55),
                    (cx + s * w * 0.4, y, top - 0.08 - drop * 0.27), cloth, rot=(sway, -slope - s * 6, 0), bevel=0.004)
            box(f"{kind}_collar", (w * 0.3, CLOTH_T + 0.006, 0.05), (cx, y, top - drop + 0.03), cloth,
                rot=(sway, -slope, 0), bevel=0.004)
            pegs = (cx - w * 0.25, cx + w * 0.25)
        elif kind == "hose":
            for s in (-1, 1):
                box(f"{kind}_leg_{s}", (w * 0.4, CLOTH_T * 1.6, drop), (cx + s * w * 0.27, y, top - drop / 2), cloth,
                    rot=(sway, -slope - s * 3, 0), bevel=0.005)
                box(f"{kind}_foot_{s}", (w * 0.48, CLOTH_T * 1.6, 0.08),
                    (cx + s * w * 0.27 + s * 0.03, y, top - drop + 0.04), cloth, rot=(sway, -slope, 0), bevel=0.005)
            pegs = (cx - w * 0.27, cx + w * 0.27)
        else:
            # Folded over the rope: a front fall and a shorter back fall, the hem a little uneven.
            box(f"{kind}_front", (w, CLOTH_T, drop), (cx, y - CLOTH_T, top - drop / 2), cloth,
                rot=(sway, -slope, 0), bevel=0.004)
            box(f"{kind}_back", (w * 0.98, CLOTH_T, drop * 0.55), (cx, y + CLOTH_T, top - drop * 0.275), cloth,
                rot=(-sway, -slope, 0), bevel=0.004)
            pegs = (cx - w * 0.38, cx + w * 0.38) if w > 0.3 else (cx,)
        for j, px in enumerate(pegs):
            box(f"peg_{k}_{j}", (0.018, 0.035, 0.08), (px, 0, rope_z(px) - 0.015), peg,
                rot=(0, rnd.uniform(-6, 6), 0), bevel=0.004)
