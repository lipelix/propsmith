"""A cemetery railing section: a low dressed-stone plinth wall running the full 1.5 m along x so sections join end to
end, a square stone pier with a pyramid cap at each end, and between them rusted wrought-iron railings: two flat rails
and a row of round bars with spear tips, one bar bent out of line, finials on the top rail and rust streaks."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

MODULE = 1.5  # metres: the length wall and fence sections join at
# Overall dimensions: the fence runs along x through the origin, one module long and about 1.3 m high.
L = MODULE - 0.01  # plinth length, the full module less a hair so neighbours meet without overlapping
PLINTH = (0.24, 0.26)  # plinth wall depth and height
COPE = (0.28, 0.05)  # coping on the plinth: depth and height
PIER = 0.26  # square pier width
PIER_H = 1.2  # pier shaft top, before its cap
CAP_H = 0.1  # the pyramid cap
PIER_X = L / 2 - (PIER + 0.03) / 2  # piers at the ends, their bands flush with the plinth ends
BAR_R = 0.011  # round railing bar
BAR_PITCH = 0.115
BAR_TOP = 1.13  # bar tops, under their spear tips
TIP_H = 0.09
RAIL_Z = (0.4, 1.02)  # flat rails, low and high
RAIL = (0.012, 0.035)  # flat rail thickness and height

STONE = (0.25, 0.24, 0.22)  # linear RGB: grey dressed stone
STONE_OLD = (0.2, 0.193, 0.175)
IRON = (0.045, 0.044, 0.042)
RUST = (0.1, 0.055, 0.033)
RUST_LIGHT = (0.16, 0.08, 0.042)


def _spear(name, x, y, z, mat, lean=(0, 0, 0)):
    """A four-sided spear tip with a little collar, its foot at z."""
    cylinder(f"{name}_collar", BAR_R + 0.006, 0.014, (x, y, z), mat, segments=8, rot=lean, bevel=0.002)
    cylinder(f"{name}_tip", 0.024, TIP_H, (x, y, z + 0.012), mat, r_top=0.0, segments=4, rot=lean, bevel=0)


@prop
def fence_iron_cemetery():
    rnd = random.Random(29)
    stone = material("fence_iron_cemetery_stone", STONE, vary=0.28, scale=7, crevice=0.6)
    old = material("fence_iron_cemetery_stone_old", STONE_OLD, vary=0.3, scale=9, crevice=0.6)
    iron = material("fence_iron_cemetery_iron", IRON, rough=0.6, vary=0.3, scale=18, metal=0.55)
    rust = material("fence_iron_cemetery_rust", RUST, rough=0.85, vary=0.35, scale=24, metal=0.25)
    rust_light = material("fence_iron_cemetery_rust_light", RUST_LIGHT, rough=0.9, vary=0.35, scale=30, metal=0.15)

    # The plinth wall in three blocks and its coping, full length so neighbours meet.
    pd, ph = PLINTH
    n_blocks = 3
    bl = L / n_blocks
    for i in range(n_blocks):
        x = -L / 2 + bl * (i + 0.5)
        box(f"plinth_{i}", (bl - 0.006, pd * rnd.uniform(0.97, 1.0), ph), (x, 0, ph / 2), old if i == 1 else stone,
            rot=(0, 0, rnd.uniform(-0.4, 0.4)), bevel=0.016)
    cd, ch = COPE
    box("coping", (L, cd, ch), (0, 0, ph + ch / 2), stone, bevel=0.015)
    base = ph + ch

    # Two square piers with a plain band and a pyramid cap.
    for s in (-1, 1):
        x = s * PIER_X
        mat = old if s > 0 else stone
        box(f"pier_{s}", (PIER, PIER, PIER_H - base), (x, 0, base + (PIER_H - base) / 2), mat,
            rot=(0, 0, rnd.uniform(-1, 1)), bevel=0.018)
        box(f"pier_band_{s}", (PIER + 0.03, PIER + 0.03, 0.06), (x, 0, PIER_H - 0.03), stone, bevel=0.012)
        cylinder(f"pier_cap_{s}", (PIER + 0.03) / math.sqrt(2), CAP_H, (x, 0, PIER_H), stone, r_top=0.02,
                 segments=4, rot=(0, 0, 45), bevel=0.01)
        box(f"pier_plinth_{s}", (PIER + 0.03, PIER + 0.03, 0.1), (x, 0, base + 0.05), old, bevel=0.012)

    # The railing between the piers: flat rails into the piers, bars with spear tips through them.
    inner = PIER_X - PIER / 2
    rt, rh = RAIL
    for k, z in enumerate(RAIL_Z):
        box(f"rail_{k}", (2 * inner + 0.04, rt, rh), (0, 0, z), iron if k else rust, bevel=0.003)
    n = int(2 * inner / BAR_PITCH)
    pitch = 2 * inner / n
    bent = 2  # this bar was knocked out of line
    for i in range(n - 1):
        x = -inner + pitch * (i + 1)
        lean = (rnd.uniform(-1.2, 1.2), rnd.uniform(-1, 1), 0)
        if i == bent:
            lean = (-7, 3, 0)
        mat = rust if rnd.random() < 0.35 else iron
        h = BAR_TOP - base
        cylinder(f"bar_{i}", BAR_R, h, (x, 0, base), mat, segments=8, rot=lean, bevel=0)
        # The tip follows the bar's lean.
        ax, ay = math.radians(lean[0]), math.radians(lean[1])
        tx = x + h * math.sin(ay) * math.cos(ax)
        ty = -h * math.sin(ax)
        tz = base + h * math.cos(ax) * math.cos(ay)
        _spear(f"spear_{i}", tx, ty, tz - 0.004, rust_light if mat is rust else iron, lean)
        # Lead-set foot in the coping.
        cylinder(f"bar_foot_{i}", BAR_R + 0.008, 0.012, (x, 0, base - 0.004), iron, segments=8, bevel=0)
    # Rings between the bars under the top rail.
    for i in range(n - 2):
        x = -inner + pitch * (i + 1.5)
        torus(f"ring_{i}", 0.028, 0.006, (x, 0, RAIL_Z[1] - 0.05), rust if i % 3 == 0 else iron, rot=(90, 0, 0),
              major=12, minor=4)
    # Rust streaks bleeding down the coping under the rail.
    for k in range(4):
        x = rnd.uniform(-inner + 0.1, inner - 0.1)
        box(f"stain_{k}", (rnd.uniform(0.018, 0.03), 0.004, rnd.uniform(0.08, 0.14)),
            (x, -pd / 2 - 0.001, ph - 0.06), rust_light, bevel=0)
