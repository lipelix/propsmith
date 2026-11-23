"""A small group of stoppered potion bottles and vials: a tall square bottle of green brew sealed with red wax, a
round-bellied red flask with a cork and a tied label, a squat blue bottle, a slim blue vial, two little vials of red and
green and one vial lying on its side, all with pale glass necks above the coloured brews."""
import math

from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall size: about 0.4 m wide (x), 0.3 m deep (y), the tallest bottle about 0.3 m.
W, D, H = 0.4, 0.3, 0.3

GLASS = (0.28, 0.33, 0.3)  # pale glass of the necks
RED = (0.36, 0.05, 0.04)  # linear RGB
BLUE = (0.06, 0.1, 0.33)
GREEN = (0.1, 0.28, 0.07)
CORK = (0.3, 0.2, 0.11)
WAX = (0.24, 0.05, 0.04)
TWINE = (0.32, 0.25, 0.15)
LABEL = (0.45, 0.37, 0.24)


def _neck(name, x, y, z, r, h, glass, seal, wax=False):
    """A pale glass neck standing on `z` with a cork, or a wax seal over its mouth."""
    cylinder(f"{name}_neck", r, h, (x, y, z), glass, r_top=r * 0.9, segments=10, bevel=0)
    torus(f"{name}_lip", r * 0.95, r * 0.28, (x, y, z + h), glass, major=12, minor=5)
    if wax:
        cylinder(f"{name}_seal", r * 1.25, 0.022, (x, y, z + h - 0.012), seal, r_top=r * 1.05, segments=10,
                 bevel=0.003)
    else:
        cylinder(f"{name}_cork", r * 0.85, r * 1.6, (x, y, z + h - r * 0.6), seal, r_top=r * 1.05, segments=8,
                 bevel=0.002)


@prop
def potion_bottles():
    glass = material("potion_bottles_glass", GLASS, rough=0.08, vary=0.08, scale=12, crevice=0.25)
    red = material("potion_bottles_red", RED, rough=0.1, vary=0.15, scale=14, crevice=0.3)
    blue = material("potion_bottles_blue", BLUE, rough=0.1, vary=0.15, scale=14, crevice=0.3)
    green = material("potion_bottles_green", GREEN, rough=0.1, vary=0.15, scale=14, crevice=0.3)
    cork = material("potion_bottles_cork", CORK, rough=0.9, vary=0.3, scale=60)
    wax = material("potion_bottles_wax", WAX, rough=0.45, vary=0.15, scale=30, crevice=0.3)
    twine = material("potion_bottles_twine", TWINE, rough=0.95, vary=0.25, scale=60)
    label = material("potion_bottles_label", LABEL, rough=0.95, vary=0.18, scale=30, crevice=0.4)

    # A tall square bottle of green brew at the back, sealed with red wax.
    x, y = -0.07, 0.07
    box("square_body", (0.075, 0.075, 0.19), (x, y, 0.095), green, rot=(0, 0, 12), bevel=0.012)
    cylinder("square_shoulder", 0.05, 0.03, (x, y, 0.188), glass, r_top=0.018, segments=10, bevel=0)
    _neck("square", x, y, 0.215, 0.016, 0.06, glass, wax, wax=True)

    # A round-bellied red flask in front of it with a cork and a twine-tied label.
    x, y, r = 0.06, -0.02, 0.075
    blob("round_body", r, (x, y, r * 0.93), red, subdiv=3, seed=1, jitter=0)
    _neck("round", x, y, r * 1.75, 0.02, 0.085, glass, cork)
    torus("round_twine", 0.022, 0.004, (x, y, r * 1.75 + 0.03), twine, major=10, minor=4)
    box("round_label", (0.035, 0.004, 0.045), (x + 0.012, y - 0.03, r * 1.75 + 0.005), label, rot=(-20, 0, 15),
        bevel=0.001)

    # A squat blue bottle at the right, a slim blue vial behind it.
    x, y = 0.15, 0.09
    cylinder("squat_body", 0.045, 0.09, (x, y, 0), blue, r_top=0.048, segments=14, bevel=0.006)
    cylinder("squat_shoulder", 0.048, 0.025, (x, y, 0.088), glass, r_top=0.018, segments=14, bevel=0)
    _neck("squat", x, y, 0.11, 0.015, 0.04, glass, cork)
    x, y = 0.06, 0.11
    cylinder("vial_tall_body", 0.018, 0.15, (x, y, 0), blue, r_top=0.018, segments=10, bevel=0.004)
    _neck("vial_tall", x, y, 0.148, 0.012, 0.05, glass, cork)

    # Two little vials, red and green, at the front left.
    for name, (x, y, h, mat) in {"vial_red": (-0.12, -0.06, 0.08, red),
                                 "vial_green": (-0.06, -0.09, 0.06, green)}.items():
        cylinder(f"{name}_body", 0.017, h, (x, y, 0), mat, r_top=0.017, segments=10, bevel=0.004)
        _neck(name, x, y, h - 0.002, 0.011, 0.03, glass, cork)

    # One vial lying on its side in front, its cork towards the viewer.
    start = Vector((0.09, -0.115, 0.017))
    yaw = math.radians(-15)
    axis = Vector((math.cos(yaw), math.sin(yaw), 0))
    rot = (0, 90, math.degrees(yaw))
    cylinder("vial_lying_body", 0.017, 0.07, start, green, r_top=0.017, segments=10, rot=rot, bevel=0.004)
    neck = start + axis * 0.068
    cylinder("vial_lying_neck", 0.011, 0.025, tuple(neck), glass, r_top=0.01, segments=10, rot=rot, bevel=0)
    cylinder("vial_lying_cork", 0.009, 0.018, tuple(neck + axis * 0.02), cork, r_top=0.011, segments=8, rot=rot,
             bevel=0.002)
