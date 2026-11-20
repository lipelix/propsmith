"""A village notice board: two square timber posts carrying a framed plank board under a small pitched shingle roof,
with parchment notices pinned to its front (-y) face, some curling and one torn."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder

# Overall dimensions (metres): about 1.5 wide, 0.4 deep and 2.2 high.
W = 1.5  # roof length along x
D = 0.4  # roof depth along y
H = 2.2  # roof ridge
POST = 0.12  # post section
POST_X = 0.6  # posts at +-POST_X
POST_TOP = 2.02
BOARD_W = 2 * POST_X - POST  # the board fills the gap between the posts
BOARD_Z0, BOARD_Z1 = 0.85, 1.8  # board bottom and top
BOARD_T = 0.04
FRAME = 0.06  # frame width
ROOF_PITCH = 28  # degrees
ROOF_T = 0.035
FOOT_H = 0.08  # stone pads under the posts

WOOD = (0.19, 0.12, 0.065)
WOOD_OLD = (0.15, 0.1, 0.06)
BOARD = (0.22, 0.15, 0.085)  # paler, sun-bleached planks
SHINGLE = (0.13, 0.09, 0.06)
STONE = (0.3, 0.27, 0.23)
PAPER = (0.45, 0.4, 0.29)  # parchment
PAPER_OLD = (0.38, 0.31, 0.19)  # yellowed
PAPER_RED = (0.3, 0.12, 0.07)  # a faded red bill
INK = (0.06, 0.05, 0.045)
IRON = (0.045, 0.045, 0.045)

# Notices: centre (x, z) on the board, size (w, h), tilt in degrees, paper kind.
NOTICES = (
    ((-0.33, 1.5), (0.26, 0.34), -4, "paper"),
    ((-0.02, 1.56), (0.22, 0.28), 3, "old"),
    ((0.3, 1.47), (0.3, 0.38), -2, "paper"),
    ((-0.36, 1.1), (0.2, 0.26), 6, "red"),
    ((-0.05, 1.12), (0.28, 0.22), -3, "old"),
    ((0.26, 1.08), (0.18, 0.24), 8, "paper"),
)


@prop
def notice_board():
    rnd = random.Random(19)
    wood = material("notice_board_wood", WOOD, vary=0.3, scale=16)
    wood_old = material("notice_board_wood_old", WOOD_OLD, vary=0.3, scale=14)
    board = material("notice_board_board", BOARD, vary=0.3, scale=12)
    shingle = material("notice_board_shingle", SHINGLE, vary=0.35, scale=10, crevice=0.7)
    stone = material("notice_board_stone", STONE, vary=0.25, scale=9, crevice=0.6)
    papers = {
        "paper": material("notice_board_paper", PAPER, vary=0.15, scale=20, crevice=0.3),
        "old": material("notice_board_paper_old", PAPER_OLD, vary=0.2, scale=20, crevice=0.3),
        "red": material("notice_board_paper_red", PAPER_RED, vary=0.2, scale=20, crevice=0.3),
    }
    ink = material("notice_board_ink", INK, vary=0.1, scale=30)
    iron = material("notice_board_iron", IRON, rough=0.55, vary=0.2, scale=20, metal=0.6)

    # Posts on low stone pads.
    for s in (-1, 1):
        x = s * POST_X
        box(f"pad_{s}", (0.2, 0.2, FOOT_H), (x, 0, FOOT_H / 2), stone, rot=(0, 0, rnd.uniform(-6, 6)), bevel=0.015)
        h = POST_TOP - FOOT_H + 0.01
        box(f"post_{s}", (POST, POST, h), (x, 0, FOOT_H - 0.01 + h / 2), wood if s < 0 else wood_old,
            rot=(0, rnd.uniform(-0.6, 0.6), rnd.uniform(-2, 2)), bevel=0.018)

    # The board: vertical planks between the posts, a little proud of their centre line towards -y.
    by = -0.02
    n = 6
    pw = BOARD_W / n
    bh = BOARD_Z1 - BOARD_Z0
    for i in range(n):
        x = -BOARD_W / 2 + pw * (i + 0.5)
        box(f"plank_{i}", (pw - 0.006, BOARD_T, bh * rnd.uniform(0.985, 1.0)), (x, by, BOARD_Z0 + bh / 2), board,
            rot=(0, rnd.uniform(-0.4, 0.4), 0), bevel=0.008)
    # A frame round it, a little proud of the planks, and a back batten.
    ft = BOARD_T + 0.02
    for name, size, at in (
        ("frame_top", (BOARD_W + 0.02, ft, FRAME), (0, by, BOARD_Z1)),
        ("frame_bottom", (BOARD_W + 0.02, ft, FRAME), (0, by, BOARD_Z0)),
        ("ledge", (BOARD_W, 0.08, 0.025), (0, by - 0.03, BOARD_Z0 - FRAME / 2 - 0.005)),
    ):
        box(name, size, at, wood, bevel=0.01)
    box("batten", (BOARD_W, 0.03, 0.08), (0, by + BOARD_T / 2 + 0.015, (BOARD_Z0 + BOARD_Z1) / 2), wood_old,
        bevel=0.008)

    # Pinned notices on the -y face: thin sheets, a pin at the top, ink lines; one corner of each curls forward.
    face = by - ft / 2 - 0.002
    for k, ((x, z), (w, h), tilt, kind) in enumerate(NOTICES):
        tilt += rnd.uniform(-1, 1)
        t = 0.004
        y = face - t / 2 - 0.001 * k
        box(f"notice_{k}", (w, t, h), (x, y, z), papers[kind], rot=(0, tilt, 0), bevel=0.0015)
        a = math.radians(tilt)
        # A curled lower corner: a small sheet bent off the board.
        cx, cz = _turn(x, z, w / 2 - 0.03, -h / 2 + 0.03, a)
        if k % 2 == 0:
            box(f"curl_{k}", (0.06, t, 0.06), (cx, y - 0.012, cz), papers[kind], rot=(-25, tilt, 0), bevel=0.0015)
        # Ink: a heading and a few lines.
        lines = 1 + int(h / 0.07)
        for j in range(lines):
            lw = (w * 0.7 if j == 0 else w * rnd.uniform(0.45, 0.72))
            lz = h / 2 - 0.06 - j * (h - 0.11) / max(lines - 1, 1)
            if j == lines - 1 and k % 2:
                continue
            lx = -w / 2 + 0.03 + lw / 2 if j else 0
            px, pz = _turn(x, z, lx, lz, a)
            box(f"ink_{k}_{j}", (lw, 0.002, 0.016 if j == 0 else 0.009), (px, y - t / 2 - 0.0005, pz), ink,
                rot=(0, tilt, 0), bevel=0)
        # The pin through the top.
        px, pz = _turn(x, z, 0, h / 2 - 0.025, a)
        cylinder(f"pin_{k}", 0.009, 0.014, (px, y - t / 2, pz), iron, segments=8, rot=(90, 0, 0), bevel=0.002)

    # The roof: a ridge beam on the posts and two shingled slopes falling to front and back.
    box("ridge_beam", (W - 0.06, 0.1, 0.1), (0, 0, POST_TOP + 0.05), wood_old, bevel=0.012)
    a = math.radians(ROOF_PITCH)
    half = D / 2 / math.cos(a)
    rise = D / 2 * math.tan(a)
    for s in (-1, 1):
        cy = s * D / 4
        cz = H - 0.012 - rise / 2 - ROOF_T / 2 / math.cos(a)
        box(f"roof_{s}", (W, half, ROOF_T), (0, cy, cz), shingle, rot=(-s * ROOF_PITCH, 0, 0), bevel=0.01)
        # Shingle courses: thin strips laid down the slope.
        for c in range(3):
            d = (c + 0.5) / 3 - 0.5  # along the slope, -0.5 ridge side to +0.5 eave
            sy = cy + s * d * half * math.cos(a)
            sz = cz - d * half * math.sin(a) + (ROOF_T / 2 + 0.006) * math.cos(a)
            box(f"course_{s}_{c}", (W - 0.02, half / 3 - 0.01, 0.012), (0, sy, sz), shingle,
                rot=(-s * (ROOF_PITCH + 3), 0, rnd.uniform(-0.5, 0.5)), bevel=0.004)
    box("ridge_cap", (W - 0.01, 0.07, 0.04), (0, 0, H - 0.025), wood, bevel=0.01)
    # Two knee braces from each post to the beam.
    for s in (-1, 1):
        x0, z0 = s * POST_X, POST_TOP - 0.25
        x1, z1 = s * (POST_X + 0.12), POST_TOP + 0.01
        box(f"brace_{s}", (math.hypot(x1 - x0, z1 - z0) + 0.04, 0.06, 0.05),
            ((x0 + x1) / 2, 0, (z0 + z1) / 2), wood, rot=(0, -s * math.degrees(math.atan2(z1 - z0, abs(x1 - x0))), 0),
            bevel=0.008)


def _turn(x, z, dx, dz, a):
    """The point (dx, dz) off (x, z) on a sheet tilted by `a` radians about y."""
    return x + dx * math.cos(a) + dz * math.sin(a), z - dx * math.sin(a) + dz * math.cos(a)
