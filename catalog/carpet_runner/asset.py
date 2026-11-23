"""A long red carpet runner lying on the floor, long side along y: deep madder red wool with a woven border of a gold
band between dark indigo lines, a chain of small gold and dark red lozenges along it, a sparse lattice of small dark
diamonds in the field, a gold lozenge at either end of the field, and a short knotted fringe on both short ends."""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box

# Overall size: 1.2 m wide (x), 4 m long (y) with the fringe, a centimetre and a half high.
W, L = 1.2, 3.86  # woven body
T = 0.012  # thickness of the weave
FRINGE = 0.07
P = 0.002  # pattern inlay thickness above the body
BORDER = 0.15  # width of the woven border

RED = (0.24, 0.045, 0.035)  # linear RGB, deep madder
RED_DARK = (0.13, 0.025, 0.022)
INDIGO = (0.045, 0.05, 0.1)
GOLD = (0.42, 0.28, 0.08)
FRINGE_C = (0.38, 0.32, 0.2)


@prop
def carpet_runner():
    rnd = random.Random(1204)
    red = material("carpet_runner_red", RED, rough=0.97, vary=0.25, scale=8, crevice=0.3)
    red_dark = material("carpet_runner_red_dark", RED_DARK, rough=0.97, vary=0.25, scale=12, crevice=0.3)
    indigo = material("carpet_runner_indigo", INDIGO, rough=0.97, vary=0.25, scale=14, crevice=0.3)
    gold = material("carpet_runner_gold", GOLD, rough=0.95, vary=0.25, scale=14, crevice=0.3)
    fringe = material("carpet_runner_fringe", FRINGE_C, rough=0.97, vary=0.25, scale=30, crevice=0.4)

    box("body", (W, L, T), (0, 0, T / 2), red, bevel=0.003)
    z = T + P / 2 - 0.0005

    def band(name, sx, sy, x, y, mat, rot=0, lift=0.0):
        box(name, (sx, sy, P), (x, y, z + lift), mat, rot=(0, 0, rot), bevel=0)

    # The border: an indigo edge line, a wide gold band and an inner indigo line, all the way round.
    for k, (inset, w, mat) in enumerate([(0.015, 0.02, indigo), (0.045, 0.075, gold), (0.13, 0.015, indigo)]):
        wx, ly = W - 2 * inset, L - 2 * inset
        for s in (-1, 1):
            band(f"border_{k}_x_{s}", wx, w, 0, s * (ly - w) / 2, mat)
            band(f"border_{k}_y_{s}", w, ly - 2 * w, s * (wx - w) / 2, 0, mat)

    # A chain of lozenges riding the gold band: dark red, each with a small gold heart.
    mid = 0.045 + 0.075 / 2
    n_long, n_short = 25, 7
    for k in range(n_long):
        y = -L / 2 + 0.16 + k * (L - 0.32) / (n_long - 1)
        for s in (-1, 1):
            band(f"chain_y_{k}_{s}", 0.05, 0.05, s * (W / 2 - mid), y, red_dark, rot=45, lift=0.0006)
            band(f"chain_y_heart_{k}_{s}", 0.016, 0.016, s * (W / 2 - mid), y, gold, rot=45, lift=0.0012)
    for k in range(n_short):
        x = -W / 2 + 0.2 + k * (W - 0.4) / (n_short - 1)
        for s in (-1, 1):
            band(f"chain_x_{k}_{s}", 0.05, 0.05, x, s * (L / 2 - mid), red_dark, rot=45, lift=0.0006)
            band(f"chain_x_heart_{k}_{s}", 0.016, 0.016, x, s * (L / 2 - mid), gold, rot=45, lift=0.0012)

    # The field: a sparse lattice of small dark diamonds, skipping the two end lozenges.
    fx, fy = W / 2 - BORDER - 0.1, L / 2 - BORDER - 0.12
    nx, ny = 3, 15
    ends = L / 2 - BORDER - 0.32
    for i in range(nx):
        for j in range(ny):
            x = -fx + i * 2 * fx / (nx - 1)
            y = -fy + j * 2 * fy / (ny - 1)
            if abs(x) < 0.3 and abs(abs(y) - ends) < 0.3:
                continue
            band(f"field_{i}_{j}", 0.07, 0.07, x, y, red_dark, rot=45)
            if (i + j) % 2 == 0:
                band(f"field_dot_{i}_{j}", 0.02, 0.02, x, y, gold, rot=45, lift=0.0006)

    # A gold stepped lozenge near either end of the field.
    for s in (-1, 1):
        y = s * ends
        for b, (sz, mat) in enumerate([(0.36, gold), (0.27, indigo), (0.18, red_dark), (0.08, gold)]):
            band(f"lozenge_{s}_{b}", sz, sz, 0, y, mat, rot=45, lift=b * 0.0005)

    # Knotted fringe on the short ends.
    tassels = 20
    for s in (-1, 1):
        for k in range(tassels):
            x = -W / 2 + 0.03 + k * (W - 0.06) / (tassels - 1)
            length = FRINGE * rnd.uniform(0.75, 1.0)
            box(f"fringe_{s}_{k}", (0.014, length, 0.004), (x, s * (L / 2 + length / 2 - 0.004), 0.002), fringe,
                rot=(0, 0, rnd.uniform(-8, 8)), bevel=0)
            box(f"knot_{s}_{k}", (0.022, 0.016, 0.008), (x, s * (L / 2 + 0.006), 0.004), fringe, bevel=0.002)
