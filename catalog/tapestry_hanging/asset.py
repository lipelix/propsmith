"""A woven tapestry on a free-standing wooden stand, its face on -y: two square posts on long feet braced to the floor,
a turned rod with knob finials resting in their forked tops, and a faded wool hanging on cloth loops: a striped border
round a deep blue field with a stylised tree of life flanked by two birds, a band of zigzag at the foot and a fringe of
tassels along the bottom edge."""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall size: about 1 m wide (x), 0.3 m deep (y, the feet), 2 m high to the finials.
W, D, H = 1.0, 0.3, 2.0
POST = 0.05  # square posts
POST_X = 0.42  # post centres
ROD_Z = 1.9  # rod centre
ROD_R = 0.018
CLOTH_W = 0.76
CLOTH_T = 0.014
CLOTH_TOP = ROD_Z - 0.06
CLOTH_BOTTOM = 0.22
CLOTH_Y = 0.0
FACE = CLOTH_Y - CLOTH_T / 2  # the woven pattern sits on this face, toward -y

WOOD = (0.18, 0.1, 0.052)  # linear RGB
WOOD_OLD = (0.14, 0.08, 0.045)
FIELD = (0.06, 0.075, 0.13)  # faded indigo
BORDER = (0.3, 0.075, 0.05)  # madder red
OCHRE = (0.42, 0.28, 0.09)
CREAM = (0.42, 0.37, 0.26)
GREEN = (0.1, 0.16, 0.07)
BROWN = (0.2, 0.11, 0.06)


@prop
def tapestry_hanging():
    rnd = random.Random(75)
    wood = material("tapestry_hanging_wood", WOOD, vary=0.22, scale=14)
    old = material("tapestry_hanging_wood_old", WOOD_OLD, vary=0.28, scale=11)
    field = material("tapestry_hanging_field", FIELD, rough=0.95, vary=0.25, scale=24, crevice=0.4)
    border = material("tapestry_hanging_border", BORDER, rough=0.95, vary=0.25, scale=24, crevice=0.4)
    ochre = material("tapestry_hanging_ochre", OCHRE, rough=0.95, vary=0.25, scale=24, crevice=0.4)
    cream = material("tapestry_hanging_cream", CREAM, rough=0.95, vary=0.2, scale=24, crevice=0.4)
    green = material("tapestry_hanging_green", GREEN, rough=0.95, vary=0.25, scale=24, crevice=0.4)
    brown = material("tapestry_hanging_brown", BROWN, rough=0.95, vary=0.25, scale=24, crevice=0.4)

    # The stand: feet, posts with braces, forked tops; a low stretcher ties the posts together at the back.
    for i, s in enumerate((-1, 1)):
        x = s * POST_X
        box(f"foot_{i}", (0.07, D - 0.01, 0.06), (x, 0, 0.03), old, bevel=0.012)
        for e in (-1, 1):
            box(f"foot_{i}_pad_{e}", (0.075, 0.05, 0.015), (x, e * (D / 2 - 0.035), 0.0075), wood, bevel=0.005)
        box(f"post_{i}", (POST, POST, ROD_Z - 0.06), (x, 0, (ROD_Z - 0.06) / 2 + 0.03), wood if i else old,
            rot=(0, rnd.uniform(-0.3, 0.3), 0), bevel=0.01)
        for e in (-1, 1):
            # Diagonal braces from the foot to the post.
            box(f"brace_{i}_{e}", (0.032, 0.2, 0.032), (x, e * 0.075, 0.13), old, rot=(e * -45, 0, 0), bevel=0.006)
            # The fork the rod rests in.
            box(f"fork_{i}_{e}", (POST, 0.016, 0.07), (x, e * 0.026, ROD_Z + 0.005), wood, bevel=0.005)
    box("stretcher", (2 * POST_X, 0.04, 0.05), (0, 0.06, 0.12), wood, bevel=0.008)

    # The rod with turned finials beyond the posts.
    cylinder("rod", ROD_R, 2 * POST_X + 0.08, (-POST_X - 0.04, 0, ROD_Z), wood, rot=(0, 90, 0), segments=10,
             bevel=0.003)
    for i, s in enumerate((-1, 1)):
        x = s * (POST_X + 0.04)
        cylinder(f"finial_neck_{i}", 0.022, 0.02, (x, 0, ROD_Z), old, rot=(0, s * 90, 0), segments=10, bevel=0.003)
        blob(f"finial_{i}", 0.03, (x + s * 0.035, 0, ROD_Z), old, squash=(1.1, 1, 1), subdiv=1, seed=40 + i,
             jitter=0.04)

    # Cloth: loops over the rod, then the hanging, then its pattern on the -y face.
    loops = 7
    for k in range(loops):
        x = -CLOTH_W / 2 + 0.05 + k * (CLOTH_W - 0.1) / (loops - 1)
        box(f"loop_{k}", (0.06, 2 * ROD_R + 0.016, 0.07), (x, CLOTH_Y, ROD_Z - 0.012), border, bevel=0.01)
    body_h = CLOTH_TOP - CLOTH_BOTTOM
    box("hanging", (CLOTH_W, CLOTH_T, body_h), (0, CLOTH_Y, CLOTH_BOTTOM + body_h / 2), field, bevel=0.004)
    # A gentle ripple: two shallow vertical folds standing proud of the back.
    for k, x in enumerate((-0.2, 0.18)):
        box(f"fold_{k}", (0.07, 0.01, body_h - 0.04), (x, CLOTH_Y + CLOTH_T / 2 + 0.003, CLOTH_BOTTOM + body_h / 2),
            field, bevel=0.004)

    y = FACE - 0.0015
    t = 0.003

    def patch(name, w, h, x, z, mat, rot=0):
        box(name, (w, t, h), (x, y, z), mat, rot=(0, rot, 0), bevel=0)

    # Border: red bands with an inner ochre line.
    bw = 0.07
    mid = CLOTH_BOTTOM + body_h / 2
    patch("border_top", CLOTH_W, bw, 0, CLOTH_TOP - bw / 2, border)
    patch("border_bottom", CLOTH_W, bw, 0, CLOTH_BOTTOM + bw / 2, border)
    for s in (-1, 1):
        patch(f"border_side_{s}", bw, body_h, s * (CLOTH_W - bw) / 2, mid, border)
        patch(f"line_side_{s}", 0.014, body_h - 2 * bw - 0.02, s * (CLOTH_W / 2 - bw - 0.015), mid, ochre)
    for k, z in enumerate((CLOTH_TOP - bw - 0.015, CLOTH_BOTTOM + bw + 0.015)):
        patch(f"line_{k}", CLOTH_W - 2 * bw - 0.02, 0.014, 0, z, ochre)
    # Small cream lozenges along the red border.
    for k in range(6):
        x = -CLOTH_W / 2 + 0.11 + k * (CLOTH_W - 0.22) / 5
        for z in (CLOTH_TOP - bw / 2, CLOTH_BOTTOM + bw / 2):
            box(f"lozenge_{k}_{z:.2f}", (0.03, t + 0.001, 0.03), (x, y - 0.0005, z), cream, rot=(0, 45, 0), bevel=0)
    for s in (-1, 1):
        for k in range(8):
            z = CLOTH_BOTTOM + bw + 0.1 + k * (body_h - 2 * bw - 0.2) / 7
            box(f"lozenge_side_{s}_{k}", (0.03, t + 0.001, 0.03), (s * (CLOTH_W - bw) / 2, y - 0.0005, z), cream,
                rot=(0, 45, 0), bevel=0)

    # Zigzag band above the bottom border.
    zz = CLOTH_BOTTOM + bw + 0.09
    for k in range(10):
        x = -0.27 + k * 0.06
        patch(f"zigzag_{k}", 0.075, 0.016, x, zz, ochre, rot=45 if k % 2 else -45)

    # The tree of life: a trunk, branching limbs with leaf lozenges and a ground mound.
    base = zz + 0.07
    top = CLOTH_TOP - bw - 0.12
    patch("trunk", 0.04, top - base, 0, (top + base) / 2, brown)
    patch("ground", 0.32, 0.04, 0, base + 0.02, green)
    for k in range(4):
        z = base + 0.3 + k * 0.26
        span = 0.24 - k * 0.04
        for s in (-1, 1):
            patch(f"limb_{k}_{s}", span, 0.022, s * span / 2 * 0.9, z + span * 0.22, brown, rot=-s * 28)
            box(f"leaf_{k}_{s}", (0.07, t + 0.001, 0.07), (s * span * 0.95, y - 0.0005, z + span * 0.45), green,
                rot=(0, 45, 0), bevel=0)
    box("crown", (0.12, t + 0.001, 0.12), (0, y - 0.0005, top), green, rot=(0, 45, 0), bevel=0)
    blob("fruit", 0.025, (0, y - 0.002, top), border, squash=(1, 0.15, 1), subdiv=1, seed=2, jitter=0.03)
    # Two facing birds: a body, a head and a tail each.
    for s in (-1, 1):
        bx, bz = s * 0.2, base + 0.12
        box(f"bird_{s}_body", (0.12, t + 0.001, 0.06), (bx, y - 0.0005, bz), cream, rot=(0, s * 12, 0), bevel=0)
        box(f"bird_{s}_head", (0.04, t + 0.001, 0.04), (bx - s * 0.07, y - 0.0005, bz + 0.04), cream, bevel=0)
        box(f"bird_{s}_tail", (0.06, t + 0.001, 0.03), (bx + s * 0.075, y - 0.0005, bz + 0.03), ochre,
            rot=(0, s * 35, 0), bevel=0)
        box(f"bird_{s}_beak", (0.02, t + 0.002, 0.01), (bx - s * 0.1, y - 0.001, bz + 0.035), ochre, bevel=0)

    # Fringe: short tassels under the bottom edge.
    tassels = 16
    for k in range(tassels):
        x = -CLOTH_W / 2 + 0.025 + k * (CLOTH_W - 0.05) / (tassels - 1)
        length = rnd.uniform(0.06, 0.09)
        box(f"tassel_{k}", (0.016, 0.01, length), (x, CLOTH_Y, CLOTH_BOTTOM - length / 2 + 0.004),
            border if k % 2 else ochre, rot=(0, rnd.uniform(-5, 5), 0), bevel=0.002)
