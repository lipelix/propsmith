"""A glaive standing on its butt, as held: the shaft along +z, a long single-edged blade on top with its edge to +x
and its back, with a small back hook, to -x, its flats to ±y. An ash shaft with an iron butt cap, leather wraps where
the hands go, iron langets up to a socket and a ring under the blade."""
from propsmith import grip, prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall: 2.1 m from butt to blade point (the long class of polearms, 2 m and more).
SHAFT_L, SHAFT_R = 1.6, 0.019
BLADE_L, BLADE_W, BLADE_T = 0.38, 0.095, 0.008  # the straight part of the blade
POINT_L = 0.12
OFF_Z, MAIN_Z = 0.45, 1.02  # the hands along the shaft
HAND = 0.085

WOOD = (0.26, 0.17, 0.09)  # linear RGB
IRON = (0.1, 0.1, 0.105)
STEEL = (0.32, 0.32, 0.33)
LEATHER = (0.12, 0.06, 0.03)
CORD = (0.2, 0.14, 0.08)


@prop
def glaive():
    wood = material("glaive_shaft", WOOD, vary=0.22, scale=20)
    iron = material("glaive_iron", IRON, rough=0.5, metal=0.8, vary=0.3, scale=25)
    steel = material("glaive_steel", STEEL, rough=0.3, metal=0.9, vary=0.12, scale=24)
    leather = material("glaive_leather", LEATHER, rough=0.75, vary=0.25, scale=40)
    cord = material("glaive_cord", CORD, rough=0.85, vary=0.2, scale=60)

    # Shaft on an iron butt cap, with a wrap for each hand.
    cylinder("butt", SHAFT_R * 1.2, 0.06, (0, 0, 0), iron, r_top=SHAFT_R * 1.05, segments=10, bevel=0.004)
    cylinder("shaft", SHAFT_R, SHAFT_L - 0.05, (0, 0, 0.05), wood, r_top=SHAFT_R * 0.92, segments=10, bevel=0.003)
    for name, z, length in (("off", OFF_Z, 0.2), ("main", MAIN_Z, 0.2)):
        z0 = z - length / 2
        cylinder(f"wrap_{name}", SHAFT_R * 1.1, length, (0, 0, z0), leather, segments=10, bevel=0.002)
        for i, zz in enumerate((z0, z0 + length)):
            torus(f"wrap_{name}_cord_{i}", SHAFT_R * 1.12, 0.003, (0, 0, zz), cord, major=10, minor=4)

    # Langets and a socket up to a collar under the blade.
    top = SHAFT_L
    for s in (-1, 1):
        box(f"langet_{s}", (0.007, 0.018, 0.3), (0, s * SHAFT_R * 0.95, top - 0.2), iron, bevel=0.002)
    cylinder("socket", SHAFT_R * 1.08, 0.1, (0, 0, top - 0.06), iron, r_top=SHAFT_R * 0.95, segments=10, bevel=0.003)
    box("collar", (0.05, 0.03, 0.025), (0.008, 0, top + 0.03), iron, bevel=0.005)

    # Blade: its back straight up over the shaft, its edge forward to +x, widening towards the top in two steps, then a
    # point swept back over the spine (a 3-sided cylinder points along its local +y; turned 90 deg about x it points
    # up). A short back hook halfway up.
    back = -0.012
    z0 = top + 0.04
    half = BLADE_L / 2
    for i, w in enumerate((BLADE_W * 0.78, BLADE_W)):
        box(f"blade_{i}", (w, BLADE_T, half + 0.004), (back + w / 2, 0, z0 + half * i + half / 2), steel,
            bevel=0.002)
    box("blade_back", (0.012, BLADE_T * 1.5, BLADE_L), (back + 0.006, 0, z0 + BLADE_L / 2), iron, bevel=0.002)
    r = BLADE_W / 1.732  # the triangle's circumradius for a base BLADE_W wide
    point = cylinder("point", r, BLADE_T, (back + BLADE_W / 2, BLADE_T / 2, z0 + BLADE_L + r / 2 - 0.004), steel,
                     segments=3, rot=(90, -22, 0), bevel=0.0015)
    point.scale = (1, POINT_L / (1.5 * r), 1)
    hook = cylinder("hook", 0.02, 0.07, (back + 0.004, 0, z0 + BLADE_L * 0.35), iron, r_top=0.002, segments=4,
                    rot=(0, -60, 0), bevel=0.0015)
    hook.scale = (1, 0.35, 1)

    # The main hand at the upper wrap, the off hand at the lower, both along +z.
    grip("main", (0, 0, MAIN_Z), (0, 0, 1))
    grip("off", (0, 0, OFF_Z), (0, 0, 1))
