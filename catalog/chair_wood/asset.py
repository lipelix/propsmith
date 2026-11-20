"""A rustic inn chair: a plank seat on four square legs with stretchers, the back legs rising into a ladder back of
two curved slats under a top rail."""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder

# Overall size: about 0.45 m wide, 0.45 m deep, seat top at 0.45 m, back top at 0.95 m. Front on -y.
W = 0.44  # seat width (x)
D = 0.42  # seat depth (y)
H = 0.45  # seat top height
BACK_H = 0.95  # top of the back legs
SEAT_T = 0.035
LEG = 0.045  # square leg section
BACK_LEG = 0.05
FINIAL = 0.025  # height of the cap on each back post
APRON_H = 0.06  # rails under the seat
STR_Z = (0.12, 0.2)  # side stretchers low, front and back ones a little higher
STR = 0.03
SLAT_Z = (0.62, 0.76)  # back slat centres
SLAT_H, SLAT_T = 0.07, 0.022
TOP_RAIL_H = 0.08
SEAT_BOARDS = 3

WOOD = (0.2, 0.12, 0.062)  # linear RGB
WOOD_OLD = (0.16, 0.1, 0.058)
SEAT = (0.24, 0.155, 0.085)
PEG = (0.1, 0.065, 0.035)


@prop
def chair_wood():
    rnd = random.Random(31)
    seat = material("chair_seat", SEAT, vary=0.28, scale=12)
    seat_old = material("chair_seat_old", WOOD_OLD, vary=0.3, scale=11)
    wood = material("chair_frame", WOOD, vary=0.25, scale=14)
    peg = material("chair_pegs", PEG, vary=0.2, scale=10)

    hx, hy = W / 2 - LEG / 2, D / 2 - LEG / 2
    seat_z = H - SEAT_T
    # Front legs up to the seat, back legs carrying on to the top of the back.
    for i, x in enumerate((-hx, hx)):
        box(f"leg_front_{i}", (LEG, LEG, seat_z), (x, -hy, seat_z / 2), wood, rot=(0, 0, rnd.uniform(-2, 2)),
            bevel=0.007)
        post = BACK_H - FINIAL
        box(f"leg_back_{i}", (BACK_LEG, BACK_LEG, post), (x, hy, post / 2), wood, bevel=0.008)
        # A rounded finial cap on each back post.
        cylinder(f"finial_{i}", BACK_LEG * 0.45, FINIAL, (x, hy, post - 0.002), wood, r_top=BACK_LEG * 0.25,
                 segments=10, bevel=0.004)

    # Apron rails just under the seat, all round.
    az = seat_z - APRON_H / 2
    box("apron_front", (2 * hx, 0.022, APRON_H), (0, -hy, az), wood, bevel=0.005)
    box("apron_back", (2 * hx, 0.022, APRON_H), (0, hy, az), wood, bevel=0.005)
    for i, x in enumerate((-hx, hx)):
        box(f"apron_side_{i}", (0.022, 2 * hy, APRON_H), (x, 0, az), wood, bevel=0.005)

    # Stretchers: an H of side rails low down and a front and a back rail a little higher.
    for i, x in enumerate((-hx, hx)):
        box(f"stretcher_side_{i}", (STR, 2 * hy, STR), (x, 0, STR_Z[0]), wood, bevel=0.005)
    box("stretcher_front", (2 * hx, STR, STR), (0, -hy, STR_Z[1]), wood, bevel=0.005)
    box("stretcher_back", (2 * hx, STR, STR), (0, hy, STR_Z[1] - 0.03), wood, bevel=0.005)

    # The seat: three boards along y with fine gaps, overhanging the frame a little, notched round the back posts.
    bw = (W + 0.02) / SEAT_BOARDS
    for b in range(SEAT_BOARDS):
        x = -(W + 0.02) / 2 + bw * (b + 0.5)
        depth = D + 0.02 - BACK_LEG - 0.004 if b in (0, SEAT_BOARDS - 1) else D + 0.02
        y = (-(D + 0.02) / 2 + depth / 2) if b in (0, SEAT_BOARDS - 1) else 0
        box(f"seat_{b}", (bw - 0.006, depth, SEAT_T), (x, y, H - SEAT_T / 2 + rnd.uniform(-0.002, 0.0)),
            seat if b != 1 else seat_old, rot=(0, 0, rnd.uniform(-0.8, 0.8)), bevel=0.008)
        for s in (-1, 1):
            cylinder(f"seat_peg_{b}_{s}", 0.007, 0.003, (x, s * hy * 0.9, H - 0.002), peg, segments=8, bevel=0)

    # The ladder back: two slats and a heavier top rail between the back posts, bowed back a touch.
    for k, z in enumerate(SLAT_Z):
        box(f"slat_{k}", (2 * hx - BACK_LEG + 0.01, SLAT_T, SLAT_H), (0, hy + 0.004, z), wood if k else seat_old,
            rot=(rnd.uniform(-2, 2), 0, 0), bevel=0.006)
    box("top_rail", (2 * hx + BACK_LEG + 0.02, 0.035, TOP_RAIL_H), (0, hy, BACK_H - FINIAL - TOP_RAIL_H / 2 - 0.01), seat,
        bevel=0.01)
    for i, x in enumerate((-hx, hx)):
        cylinder(f"rail_peg_{i}", 0.008, 0.004, (x, hy - 0.018, BACK_H - FINIAL - TOP_RAIL_H / 2 - 0.01), peg, segments=8,
                 rot=(90, 0, 0), bevel=0)
