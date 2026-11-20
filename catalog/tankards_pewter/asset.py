"""Three pewter tankards and a pewter jug on a small rimmed wooden tray: one tankard lidded, two full of ale, the jug
bellied with a pinched spout and a loop handle."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall size: a tray about 0.48 × 0.32 m; the jug, the tallest part, about 0.27 m high on it.
TRAY_X, TRAY_Y = 0.48, 0.32
TRAY_T = 0.018  # tray bottom board
RIM_H, RIM_T = 0.035, 0.016  # rim boards round the edge
FOOT_H = 0.008  # two battens under the tray
TANK_R, TANK_H = 0.042, 0.125  # a tankard
HANDLE_R, HANDLE_T = 0.032, 0.008
# The jug body: (height, radius) rings from the foot to the lip.
JUG = ((0.0, 0.058), (0.025, 0.07), (0.1, 0.082), (0.17, 0.062), (0.215, 0.044), (0.25, 0.05))
JUG_AT = (0.12, 0.04)
TANKARDS = ((-0.15, 0.07, 0), (-0.06, -0.075, 1), (0.03, 0.065, 2))  # x, y, kind (0 lidded, 1 and 2 full)

WOOD = (0.2, 0.125, 0.065)  # linear RGB
WOOD_OLD = (0.16, 0.1, 0.058)
PEWTER = (0.34, 0.34, 0.35)
PEWTER_DULL = (0.27, 0.27, 0.28)
ALE = (0.12, 0.06, 0.02)
FOAM = (0.42, 0.38, 0.3)


def tankard(name, x, y, z, kind, rnd, pewter, dull, ale, foam):
    turn = rnd.uniform(-25, 25)
    body = pewter if kind != 2 else dull
    cylinder(name, TANK_R, TANK_H, (x, y, z), body, r_top=TANK_R * 0.9, segments=16, bevel=0.003)
    torus(f"{name}_foot", TANK_R - 0.002, 0.005, (x, y, z + 0.005), body, major=16, minor=6)
    torus(f"{name}_band", TANK_R * 0.95, 0.0035, (x, y, z + TANK_H * 0.5), body, major=16, minor=6)
    torus(f"{name}_rim", TANK_R * 0.9 - 0.003, 0.0045, (x, y, z + TANK_H), body, major=16, minor=6)
    # The loop handle on +x, turned a little per tankard.
    a = math.radians(turn)
    hx, hy = x + (TANK_R + 0.006) * math.cos(a), y + (TANK_R + 0.006) * math.sin(a)
    torus(f"{name}_handle", HANDLE_R, HANDLE_T, (hx, hy, z + TANK_H * 0.52), body, rot=(90, 0, turn),
          major=12, minor=6)
    if kind == 0:
        # A domed hinged lid with a thumb piece over the handle.
        cylinder(f"{name}_lid", TANK_R * 0.93, 0.012, (x, y, z + TANK_H - 0.002), body, r_top=TANK_R * 0.55,
                 segments=16, bevel=0.003)
        tx, ty = x + (TANK_R + 0.004) * math.cos(a), y + (TANK_R + 0.004) * math.sin(a)
        box(f"{name}_thumb", (0.018, 0.012, 0.022), (tx, ty, z + TANK_H + 0.01), body, rot=(0, -25, turn),
            bevel=0.003)
    else:
        cylinder(f"{name}_ale", TANK_R * 0.9 - 0.005, 0.004, (x, y, z + TANK_H - 0.008), ale, segments=16, bevel=0)
        cylinder(f"{name}_foam", TANK_R * 0.9 - 0.006, 0.005, (x, y, z + TANK_H - 0.005), foam, segments=16,
                 bevel=0)


@prop
def tankards_pewter():
    rnd = random.Random(41)
    wood = material("tankards_tray", WOOD, vary=0.25, scale=16)
    old = material("tankards_tray_old", WOOD_OLD, vary=0.3, scale=13)
    pewter = material("tankards_pewter", PEWTER, rough=0.45, vary=0.12, scale=30, metal=0.45)
    dull = material("tankards_pewter_dull", PEWTER_DULL, rough=0.6, vary=0.18, scale=26, metal=0.35)
    ale = material("tankards_ale", ALE, rough=0.2, vary=0.05, scale=10)
    foam = material("tankards_foam", FOAM, rough=0.9, vary=0.2, scale=40)

    # The tray: two battens, a bottom board, and four rim boards.
    for i, x in enumerate((-TRAY_X * 0.32, TRAY_X * 0.32)):
        box(f"tray_batten_{i}", (0.04, TRAY_Y - 0.03, FOOT_H), (x, 0, FOOT_H / 2), old, bevel=0.002)
    z0 = FOOT_H
    box("tray_board", (TRAY_X - 0.01, TRAY_Y - 0.01, TRAY_T), (0, 0, z0 + TRAY_T / 2), wood, bevel=0.004)
    for i, s in enumerate((-1, 1)):
        box(f"tray_rim_long_{i}", (TRAY_X, RIM_T, RIM_H), (0, s * (TRAY_Y - RIM_T) / 2, z0 + RIM_H / 2),
            wood if i else old, rot=(0, 0, rnd.uniform(-0.5, 0.5)), bevel=0.004)
        box(f"tray_rim_end_{i}", (RIM_T, TRAY_Y - 2 * RIM_T, RIM_H + 0.012), (s * (TRAY_X - RIM_T) / 2, 0,
            z0 + (RIM_H + 0.012) / 2), wood, bevel=0.004)

    floor = z0 + TRAY_T
    for i, (x, y, kind) in enumerate(TANKARDS):
        tankard(f"tankard_{i}", x, y, floor, kind, rnd, pewter, dull, ale, foam)

    # The jug: a bellied body of stacked frustums, a pinched spout to -x, a loop handle to +x.
    jx, jy = JUG_AT
    for k in range(len(JUG) - 1):
        (z_a, r_a), (z_b, r_b) = JUG[k], JUG[k + 1]
        cylinder(f"jug_{k}", r_a, z_b - z_a + 0.002, (jx, jy, floor + z_a), pewter, r_top=r_b, segments=20,
                 bevel=0)
    top = floor + JUG[-1][0]
    torus("jug_lip", JUG[-1][1] - 0.002, 0.005, (jx, jy, top), pewter, major=20, minor=6)
    torus("jug_foot", JUG[0][1], 0.006, (jx, jy, floor + 0.006), pewter, major=20, minor=6)
    # A pinched lip spout: a short flattened cone leaning out from the rim.
    cylinder("jug_spout", 0.026, 0.04, (jx - JUG[-1][1] + 0.012, jy, top - 0.022), pewter, r_top=0.008,
             segments=10, rot=(0, -75, 0), bevel=0.002)
    torus("jug_handle", 0.06, 0.009, (jx + 0.065, jy, floor + 0.15), pewter, rot=(90, 0, 0), major=14, minor=6)
    cylinder("jug_ale", JUG[-1][1] - 0.008, 0.004, (jx, jy, top - 0.012), ale, segments=16, bevel=0)
