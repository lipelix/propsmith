"""A two-handed greataxe standing on its butt, as held: the haft along +z, the head at the top, its bearded crescent
edge to +x and a back spike to -x, its flats to ±y. An ash haft with an iron butt cap, a leather wrap at the foot for
the off hand and another at the middle for the main hand, iron langets up the haft under the head."""
from propsmith import grip, prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall: 1.35 m from butt to the top of the head; the head reaches 0.3 m forward of the haft.
HAFT_L, HAFT_R = 1.3, 0.019
HEAD_Z = 1.15  # centre of the eye
EYE = (0.06, 0.044, 0.11)  # the socket round the haft
CHEEK_R = 0.12  # the triangular cheek from the eye out to the edge
EDGE_R = 0.16  # the crescent edge: half its height; its centre is on the cheek's front side
EDGE_X = 0.03 + CHEEK_R * 1.5
SPIKE_L = 0.11
OFF_Z, MAIN_Z = 0.12, 0.62  # the hands along the haft
HAND = 0.085

WOOD = (0.26, 0.17, 0.09)  # linear RGB
IRON = (0.1, 0.1, 0.105)
STEEL = (0.32, 0.32, 0.33)
LEATHER = (0.12, 0.06, 0.03)
CORD = (0.2, 0.14, 0.08)


@prop
def greataxe():
    wood = material("greataxe_haft", WOOD, vary=0.22, scale=20)
    iron = material("greataxe_iron", IRON, rough=0.5, metal=0.8, vary=0.3, scale=25)
    steel = material("greataxe_steel", STEEL, rough=0.3, metal=0.9, vary=0.12, scale=24)
    leather = material("greataxe_leather", LEATHER, rough=0.75, vary=0.25, scale=40)
    cord = material("greataxe_cord", CORD, rough=0.85, vary=0.2, scale=60)

    # Haft, a little thinner towards the head, on an iron butt cap.
    cylinder("butt", HAFT_R * 1.25, 0.05, (0, 0, 0), iron, r_top=HAFT_R * 1.1, segments=10, bevel=0.004)
    cylinder("haft", HAFT_R, HAFT_L - 0.04, (0, 0, 0.04), wood, r_top=HAFT_R * 0.85, segments=10, bevel=0.003)
    cylinder("haft_top", HAFT_R * 0.9, 0.03, (0, 0, HAFT_L - 0.03), iron, r_top=HAFT_R * 0.6, segments=10,
             bevel=0.004)

    # Two leather wraps where the hands go, each bound with cord at its ends.
    for name, z, length in (("off", OFF_Z, 0.2), ("main", MAIN_Z, 0.24)):
        z0 = z - length / 2
        cylinder(f"wrap_{name}", HAFT_R * 1.12, length, (0, 0, z0), leather, segments=10, bevel=0.002)
        for i, zz in enumerate((z0, z0 + length)):
            torus(f"wrap_{name}_cord_{i}", HAFT_R * 1.14, 0.003, (0, 0, zz), cord, major=10, minor=4)

    # Langets: iron straps down the haft from the eye, front and back.
    for s in (-1, 1):
        box(f"langet_{s}", (0.008, 0.016, 0.22), (s * HAFT_R * 0.95, 0, HEAD_Z - 0.15), iron, bevel=0.002)

    # Head: the eye, a neck forward to the blade, the blade and a back spike.
    box("eye", EYE, (0, 0, HEAD_Z), iron, bevel=0.008)
    box("neck", (0.09, 0.026, 0.07), (0.06, 0, HEAD_Z), iron, bevel=0.006)
    # The blade flares from the neck: a triangular iron cheek, its point at the eye, under a steel crescent edge.
    cheek = cylinder("blade_cheek", CHEEK_R, 0.014, (0.03 + CHEEK_R, 0.007, HEAD_Z), iron, segments=3,
                     rot=(90, -90, 0), bevel=0.003)
    cheek.scale = (EDGE_R / (CHEEK_R * 0.866), 1, 1)  # a 3-sided cylinder points along its local +y
    edge = cylinder("blade_edge", EDGE_R, 0.007, (EDGE_X, 0.0035, HEAD_Z), steel, segments=28, rot=(90, 0, 0),
                    bevel=0.002)
    edge.scale = (0.4, 1, 1)
    spike = cylinder("spike", 0.022, SPIKE_L, (-EYE[0] / 2 + 0.005, 0, HEAD_Z), iron, r_top=0.002, segments=4,
                     rot=(0, -90, 0), bevel=0.002)
    spike.scale = (1, 0.7, 1)

    # The off hand at the foot, the main hand at the middle wrap, both along +z.
    grip("main", (0, 0, MAIN_Z), (0, 0, 1))
    grip("off", (0, 0, OFF_Z), (0, 0, 1))
