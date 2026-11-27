"""A shepherd's sling hanging from the hand that holds it, loaded: the two cords' ends bound into a short leather
hand-hold at the top with a finger loop over it, the cords running down apart to a leather pouch cradling a round
stone at the bottom. The cords hang in the xz plane, the pouch long along x; the main hand closes round the hand-hold
along +z, the pouch below the little finger."""
import math

from propsmith import grip, prop
from propsmith.materials import material
from propsmith.shapes import blob, cylinder, torus

# Overall: 0.55 m from the pouch to the finger loop (cords of about 0.5 m, held doubled).
TOP = 0.545  # top of the finger loop
HOLD_L, HOLD_R = 0.07, 0.009  # the bound hand-hold the cords end in
POUCH = (0.06, 0.03, 0.035)  # half-sizes of the pouch along x, y, z
CORD_R = 0.0028
HAND = 0.085

LEATHER = (0.17, 0.09, 0.045)  # linear RGB
LEATHER_DARK = (0.11, 0.06, 0.03)
CORD = (0.3, 0.25, 0.17)
STONE = (0.3, 0.28, 0.25)


@prop
def sling():
    leather = material("sling_pouch", LEATHER, rough=0.75, vary=0.3, scale=40)
    dark = material("sling_hand_hold", LEATHER_DARK, rough=0.75, vary=0.25, scale=50)
    cord = material("sling_cord", CORD, rough=0.9, vary=0.25, scale=80)
    stone = material("sling_stone", STONE, rough=0.9, vary=0.3, scale=30, crevice=0.6)

    # Pouch: a squashed leather cup on the ground, the stone sitting in it.
    pouch = blob("pouch", 1, (0, 0, POUCH[2]), leather, squash=POUCH, subdiv=2, seed=3, jitter=0.06)
    pouch.rotation_euler = (0, 0, 0)  # long along x, as the cords hang (a blob turns at random)
    blob("stone", 0.027, (0, 0, POUCH[2] * 1.75), stone, subdiv=2, seed=5, jitter=0.08)

    # Hand-hold: the cord ends bound together in leather, with a finger loop above it.
    hold_z = TOP - 0.035 - HOLD_L
    cylinder("hold", HOLD_R, HOLD_L, (0, 0, hold_z), dark, r_top=HOLD_R * 0.85, segments=10, bevel=0.002)
    for i, z in enumerate((hold_z + 0.008, hold_z + HOLD_L - 0.008)):
        torus(f"hold_binding_{i}", HOLD_R * 1.02, 0.0025, (0, 0, z), cord, major=10, minor=4)
    torus("finger_loop", 0.016, CORD_R, (0, 0, TOP - 0.018), cord, rot=(90, 0, 0), major=12, minor=4)

    # Two cords from the hand-hold down to the pouch's ends, hanging apart in the xz plane.
    z0 = POUCH[2] * 1.2
    for s in (-1, 1):
        x0, x1 = s * HOLD_R * 0.4, s * POUCH[0] * 0.8
        run = math.hypot(x1 - x0, hold_z + 0.005 - z0)
        tilt = math.degrees(math.atan2(x0 - x1, hold_z + 0.005 - z0))
        cylinder(f"cord_{s}", CORD_R, run, (x1, 0, z0), cord, segments=6, rot=(0, tilt, 0), bevel=0)

    # The main hand round the hand-hold, along +z.
    grip("main", (0, 0, hold_z + HOLD_L / 2), (0, 0, 1))
