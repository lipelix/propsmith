"""A flat woven rug lying on the floor, long side along x: faded madder red wool with an indigo and ochre striped
border, a field of small cream and indigo diamonds round a large stepped medallion at the centre, and knotted fringe
on both short ends."""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box

# Overall size: 2 m long (x) with fringe, 1.5 m wide (y), a few millimetres thick.
L, Wd = 1.84, 1.46  # woven body
T = 0.012  # thickness of the weave
FRINGE = 0.07
P = 0.002  # pattern inlay thickness above the body

RED = (0.26, 0.06, 0.045)  # linear RGB, faded madder
RED_DARK = (0.17, 0.04, 0.035)
INDIGO = (0.05, 0.06, 0.12)
OCHRE = (0.4, 0.26, 0.08)
CREAM = (0.4, 0.35, 0.24)
FRINGE_C = (0.38, 0.33, 0.23)


@prop
def rug_woven():
    rnd = random.Random(2015)
    red = material("rug_woven_red", RED, rough=0.97, vary=0.25, scale=10, crevice=0.3)
    red_dark = material("rug_woven_red_dark", RED_DARK, rough=0.97, vary=0.25, scale=10, crevice=0.3)
    indigo = material("rug_woven_indigo", INDIGO, rough=0.97, vary=0.25, scale=14, crevice=0.3)
    ochre = material("rug_woven_ochre", OCHRE, rough=0.97, vary=0.25, scale=14, crevice=0.3)
    cream = material("rug_woven_cream", CREAM, rough=0.97, vary=0.2, scale=14, crevice=0.3)
    fringe = material("rug_woven_fringe", FRINGE_C, rough=0.97, vary=0.25, scale=30, crevice=0.4)

    # The body.
    box("body", (L, Wd, T), (0, 0, T / 2), red, bevel=0.003)
    z = T + P / 2 - 0.0005

    def band(name, sx, sy, x, y, mat, rot=0, lift=0.0):
        box(name, (sx, sy, P), (x, y, z + lift), mat, rot=(0, 0, rot), bevel=0)

    # Border: an outer indigo band, an ochre stripe and an inner indigo line.
    for k, (inset, w, mat) in enumerate([(0.0, 0.09, indigo), (0.11, 0.03, ochre), (0.16, 0.015, indigo)]):
        lx, wy = L - 2 * inset, Wd - 2 * inset
        for s in (-1, 1):
            band(f"border_{k}_x_{s}", lx, w, 0, s * (wy - w) / 2, mat)
            band(f"border_{k}_y_{s}", w, wy - 2 * w, s * (lx - w) / 2, 0, mat)
    # Red diamonds riding the outer indigo band.
    for k in range(13):
        x = -L / 2 + 0.12 + k * (L - 0.24) / 12
        for s in (-1, 1):
            band(f"border_diamond_{k}_{s}", 0.045, 0.045, x, s * (Wd / 2 - 0.045), red_dark, rot=45, lift=0.0006)
    for k in range(9):
        y = -Wd / 2 + 0.14 + k * (Wd - 0.28) / 8
        for s in (-1, 1):
            band(f"border_diamond_y_{k}_{s}", 0.045, 0.045, s * (L / 2 - 0.045), y, red_dark, rot=45, lift=0.0006)

    # The field: a lattice of small diamonds, skipping the medallion.
    fx, fy = L / 2 - 0.26, Wd / 2 - 0.26
    nx, ny = 9, 6
    for i in range(nx):
        for j in range(ny):
            x = -fx + i * 2 * fx / (nx - 1)
            y = -fy + j * 2 * fy / (ny - 1)
            if abs(x) / 0.62 + abs(y) / 0.46 < 1.0:
                continue
            mat = cream if (i + j) % 2 else indigo
            band(f"field_{i}_{j}", 0.06, 0.06, x, y, mat, rot=45)

    # The medallion: stacked stepped diamonds, light on dark, with a red heart and a cross of ochre.
    for k, (sx, sy, mat) in enumerate([(0.95, 0.68, indigo), (0.78, 0.55, ochre), (0.62, 0.43, red_dark),
                                       (0.42, 0.29, cream), (0.24, 0.17, indigo)]):
        # A stepped lozenge: a cross of three bars, each narrower than the last.
        for b in range(3):
            f = 1 - b * 0.33
            band(f"medallion_{k}_{b}_x", sx * f, sy * (0.34 + 0.33 * b), 0, 0, mat, lift=k * 0.0004)
    band("heart", 0.08, 0.08, 0, 0, red, rot=45, lift=0.0024)
    for s in (-1, 1):
        band(f"arm_x_{s}", 0.14, 0.02, s * 0.56, 0, ochre)
        band(f"arm_y_{s}", 0.02, 0.1, 0, s * 0.41, ochre)

    # Knotted fringe on the short ends: tassels with a knot where they leave the weave.
    tassels = 24
    for s in (-1, 1):
        for k in range(tassels):
            y = -Wd / 2 + 0.03 + k * (Wd - 0.06) / (tassels - 1)
            length = FRINGE * rnd.uniform(0.75, 1.0)
            box(f"fringe_{s}_{k}", (length, 0.014, 0.004), (s * (L / 2 + length / 2 - 0.004), y, 0.002), fringe,
                rot=(0, 0, rnd.uniform(-8, 8)), bevel=0)
            box(f"knot_{s}_{k}", (0.016, 0.022, 0.008), (s * (L / 2 + 0.006), y, 0.004), fringe, bevel=0.002)
