"""A halberd standing on its butt, as held: the shaft along +z, the head at the top with its axe blade to +x, a
hooked back fluke to -x and a long thrusting spike up, its flats to ±y. An ash shaft with an iron butt spike, leather
wraps where the hands go and iron langets nailed up to a socket under the head."""
from propsmith import grip, prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall: 2.25 m from butt to spike point (the long class of polearms, 2 m and more).
SHAFT_L, SHAFT_R = 1.95, 0.02
HEAD_Z = 1.88  # middle of the axe blade
BLADE_R = 0.1  # the triangular cheek from the socket out to the edge
EDGE_H = 0.24  # height of the straight edge
SPIKE_L = 0.36
FLUKE_L = 0.13
OFF_Z, MAIN_Z = 0.62, 1.22  # the hands along the shaft
HAND = 0.085

WOOD = (0.26, 0.17, 0.09)  # linear RGB
IRON = (0.1, 0.1, 0.105)
STEEL = (0.32, 0.32, 0.33)
LEATHER = (0.12, 0.06, 0.03)
CORD = (0.2, 0.14, 0.08)


@prop
def halberd():
    wood = material("halberd_shaft", WOOD, vary=0.22, scale=20)
    iron = material("halberd_iron", IRON, rough=0.5, metal=0.8, vary=0.3, scale=25)
    steel = material("halberd_steel", STEEL, rough=0.3, metal=0.9, vary=0.12, scale=24)
    leather = material("halberd_leather", LEATHER, rough=0.75, vary=0.25, scale=40)
    cord = material("halberd_cord", CORD, rough=0.85, vary=0.2, scale=60)

    # Shaft on a short butt spike.
    cylinder("butt", SHAFT_R * 0.5, 0.05, (0, 0, 0), iron, r_top=SHAFT_R * 1.15, segments=8, bevel=0.002)
    cylinder("ferrule", SHAFT_R * 1.15, 0.05, (0, 0, 0.045), iron, segments=10, bevel=0.003)
    cylinder("shaft", SHAFT_R, SHAFT_L - 0.09, (0, 0, 0.09), wood, r_top=SHAFT_R * 0.9, segments=10, bevel=0.003)
    for name, z, length in (("off", OFF_Z, 0.2), ("main", MAIN_Z, 0.2)):
        z0 = z - length / 2
        cylinder(f"wrap_{name}", SHAFT_R * 1.1, length, (0, 0, z0), leather, segments=10, bevel=0.002)
        for i, zz in enumerate((z0, z0 + length)):
            torus(f"wrap_{name}_cord_{i}", SHAFT_R * 1.12, 0.003, (0, 0, zz), cord, major=10, minor=4)

    # Langets down the shaft from the socket, a socket ring and the socket itself.
    top = SHAFT_L
    for s in (-1, 1):
        box(f"langet_{s}", (0.007, 0.018, 0.4), (0, s * SHAFT_R * 0.95, top - 0.24), iron, bevel=0.002)
    torus("socket_ring", SHAFT_R * 1.05, 0.005, (0, 0, top - 0.44), iron, major=10, minor=4)
    cylinder("socket", SHAFT_R * 1.05, 0.12, (0, 0, top - 0.06), iron, r_top=SHAFT_R * 0.8, segments=10, bevel=0.003)

    # Axe blade: a triangular cheek from the socket (a 3-sided cylinder points along its local +y) to a straight
    # steel edge.
    cheek = cylinder("blade", BLADE_R, 0.008, (SHAFT_R * 0.6 + BLADE_R, 0.004, HEAD_Z), iron, segments=3,
                     rot=(90, -90, 0), bevel=0.002)
    cheek.scale = (EDGE_H / 2 / (BLADE_R * 0.866), 1, 1)
    front = SHAFT_R * 0.6 + BLADE_R * 1.5
    box("edge", (0.022, 0.006, EDGE_H), (front, 0, HEAD_Z), steel, bevel=0.002)
    for s in (-1, 1):
        cylinder(f"edge_horn_{s}", 0.011, 0.035, (front, 0, HEAD_Z + s * EDGE_H / 2), steel, r_top=0.001,
                 segments=4, rot=(0 if s > 0 else 180, 0, 0), bevel=0.001).scale = (1, 0.3, 1)

    # A hooked back fluke, drooping a little.
    fluke = cylinder("fluke", 0.026, FLUKE_L, (-SHAFT_R * 0.6, 0, HEAD_Z + 0.03), iron, r_top=0.002, segments=4,
                     rot=(0, -100, 0), bevel=0.002)
    fluke.scale = (1, 0.28, 1)

    # The thrusting spike, a long four-sided point.
    spike = cylinder("spike", 0.022, SPIKE_L, (0, 0, top - 0.005), steel, r_top=0.001, segments=4, bevel=0.0015)
    spike.scale = (1, 0.5, 1)

    # The main hand under the head, the off hand lower, both along +z.
    grip("main", (0, 0, MAIN_Z), (0, 0, 1))
    grip("off", (0, 0, OFF_Z), (0, 0, 1))
