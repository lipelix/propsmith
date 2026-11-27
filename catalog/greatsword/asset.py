"""A two-handed greatsword standing on its pommel, as held: the grip along +z, the blade up, its edges to ±x and its
flats to ±y. A long leather-wrapped grip for two hands, a broad crossguard with down-turned quillons, a short ricasso
with parrying lugs and a long double-edged blade of diamond section. The main hand closes under the guard, the off hand
below it by the pommel."""
from propsmith import grip, prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall: 1.45 m from pommel to point, the guard 0.36 m wide.
POMMEL_H, POMMEL_R = 0.055, 0.032
GRIP_L, GRIP_R = 0.3, 0.016  # room for two hands
GUARD_W, GUARD_T, GUARD_H = 0.36, 0.034, 0.03
RICASSO_L = 0.1
BLADE_L, BLADE_W, BLADE_T = 0.92, 0.05, 0.009  # past the ricasso, to the start of the point
POINT_L = 0.07
HAND = 0.085  # the hand the grips are spaced for

GRIP_Z0 = POMMEL_H - 0.006
GUARD_Z = GRIP_Z0 + GRIP_L  # bottom of the guard
BLADE_Z = GUARD_Z + GUARD_H

STEEL = (0.32, 0.32, 0.33)  # linear RGB
STEEL_DARK = (0.1, 0.1, 0.105)
LEATHER = (0.12, 0.06, 0.03)
CORD = (0.2, 0.14, 0.08)


@prop
def greatsword():
    steel = material("greatsword_steel", STEEL, rough=0.3, metal=0.9, vary=0.12, scale=24)
    dark = material("greatsword_fittings", STEEL_DARK, rough=0.45, metal=0.85, vary=0.25, scale=30)
    leather = material("greatsword_leather", LEATHER, rough=0.75, vary=0.25, scale=40)
    cord = material("greatsword_cord", CORD, rough=0.85, vary=0.2, scale=60)

    # Pommel: a faceted wheel on a short neck, the tang's end peened over its top.
    cylinder("pommel", POMMEL_R, POMMEL_H - 0.012, (0, 0, 0), dark, r_top=POMMEL_R * 0.8, segments=10, bevel=0.006)
    cylinder("pommel_neck", GRIP_R * 0.9, 0.016, (0, 0, POMMEL_H - 0.014), dark, segments=10, bevel=0.002)

    # Grip: a long leather-wrapped core, a cord binding at each end and a riser ring between the hands.
    cylinder("grip", GRIP_R, GRIP_L, (0, 0, GRIP_Z0), leather, r_top=GRIP_R * 0.94, segments=12, bevel=0.003)
    for i, z in enumerate((GRIP_Z0 + 0.012, GRIP_Z0 + GRIP_L * 0.48, GUARD_Z - 0.012)):
        torus(f"grip_binding_{i}", GRIP_R * 0.98, 0.0035, (0, 0, z), cord, major=12, minor=5)

    # Crossguard: a bar with quillons turned down towards the hands, and a langet each side over the blade.
    box("guard", (GUARD_W * 0.62, GUARD_T, GUARD_H), (0, 0, GUARD_Z + GUARD_H / 2), dark, bevel=0.006)
    for s in (-1, 1):
        x = s * (GUARD_W * 0.31 + 0.045)
        box(f"quillon_{s}", (0.1, GUARD_T * 0.8, GUARD_H * 0.8), (x, 0, GUARD_Z + GUARD_H / 2 - 0.012), dark,
            rot=(0, s * 14, 0), bevel=0.006)
        cylinder(f"quillon_end_{s}", 0.016, 0.03, (s * (GUARD_W / 2 - 0.016), 0, GUARD_Z - 0.03), dark,
                 segments=8, bevel=0.005)
        box(f"langet_{s}", (0.03, 0.006, 0.05), (0, s * (GUARD_T / 2 + 0.002), BLADE_Z + 0.02), dark, bevel=0.002)

    # Ricasso: the blunt foot of the blade, with parrying lugs at its top.
    box("ricasso", (BLADE_W * 0.9, BLADE_T * 1.2, RICASSO_L), (0, 0, BLADE_Z + RICASSO_L / 2), steel, bevel=0.002)
    for s in (-1, 1):
        box(f"lug_{s}", (0.04, BLADE_T, 0.02), (s * (BLADE_W * 0.45 + 0.012), 0, BLADE_Z + RICASSO_L - 0.01),
            steel, rot=(0, s * -30, 0), bevel=0.003)

    # Blade: a long diamond section, its edges to ±x, tapering to a four-sided point.
    z0 = BLADE_Z + RICASSO_L - 0.004
    flat = BLADE_T / BLADE_W
    blade = cylinder("blade", BLADE_W / 2, BLADE_L, (0, 0, z0), steel, r_top=BLADE_W * 0.4, segments=4, bevel=0.0015)
    blade.scale = (1, flat * 1.6, 1)
    point = cylinder("point", BLADE_W * 0.4, POINT_L, (0, 0, z0 + BLADE_L - 0.001), steel, r_top=0.001, segments=4,
                     bevel=0.001)
    point.scale = (1, flat * 2, 1)

    # The main hand under the guard, the off hand a hand's breadth and more below it, both along +z.
    grip("main", (0, 0, GUARD_Z - 0.06), (0, 0, 1))
    grip("off", (0, 0, GUARD_Z - 0.06 - HAND * 1.6), (0, 0, 1))
