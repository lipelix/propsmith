"""A wrought-iron wall sconce holding a burning pitch torch, front on -y: a riveted wall plate flanked by two scrolls,
an arm out to a collar and a strap down to a cup that hold the torch leaning out from the wall, its head a bound
pitch-soaked rag wrap glowing under a short flame. The back of the plate is flat on +y, to hang on a wall; the model
stands on the foot of the torch, so a game lifts it to the height it wants."""
import math

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# About 0.3 x 0.35 x 0.6 m.
WALL_Y = 0.165  # back face of the wall plate (the wall)
PLATE_W, PLATE_T, PLATE_Z0, PLATE_Z1 = 0.11, 0.018, 0.1, 0.38  # wall plate: width, thickness, bottom, top
LEAN = 20  # degrees the torch leans out from the wall
HANDLE_R, HANDLE_L = 0.021, 0.42  # wooden haft
FOOT = (0.072, 0.008)  # y and z of the bottom of the haft axis
COLLAR_AT = 0.27  # distance up the haft of the iron collar
CUP_AT = 0.05  # distance up the haft of the lower cup
HEAD_R, HEAD_L = 0.04, 0.13  # pitch rag wrap at the top of the haft
FLAME_TOP = 0.6

IRON = (0.048, 0.046, 0.044)
IRON_WORN = (0.13, 0.115, 0.1)
WOOD = (0.17, 0.1, 0.05)
PITCH = (0.06, 0.042, 0.03)  # pitch-soaked rag
CORD = (0.2, 0.14, 0.08)
EMBER = (0.5, 0.15, 0.03)
FLAME = (0.5, 0.28, 0.035)


def _axis(d):
    """The point `d` metres up the torch axis from its foot."""
    a = math.radians(LEAN)
    return (0.0, FOOT[0] - d * math.sin(a), FOOT[1] + d * math.cos(a))


def _bar(name, p0, p1, w, t, mat):
    """A flat iron bar in the y-z plane from `p0` to `p1` (x, y, z), `w` wide (x) and `t` thick."""
    dy, dz = p1[1] - p0[1], p1[2] - p0[2]
    length = math.hypot(dy, dz)
    centre = tuple((a + b) / 2 for a, b in zip(p0, p1))
    return box(name, (w, length, t), centre, mat, rot=(math.degrees(math.atan2(dz, dy)), 0, 0), bevel=0.004)


@prop
def torch_wall_sconce():
    iron = material("torch_wall_sconce_iron", IRON, rough=0.6, vary=0.25, scale=24, metal=0.6)
    worn = material("torch_wall_sconce_worn", IRON_WORN, rough=0.45, vary=0.25, scale=24, crevice=0.3, metal=0.6)
    wood = material("torch_wall_sconce_wood", WOOD, vary=0.3, scale=30)
    pitch = material("torch_wall_sconce_pitch", PITCH, rough=0.5, vary=0.35, scale=30, crevice=0.6)
    cord = material("torch_wall_sconce_cord", CORD, vary=0.25, scale=40)
    ember = material("torch_wall_sconce_ember", EMBER, rough=0.6, vary=0.35, scale=30, crevice=0.2)
    flame = material("torch_wall_sconce_flame", FLAME, rough=0.5, vary=0.3, scale=20, crevice=0.1)

    # Wall plate with a pointed top, four rivets and two scrolls either side of the arm.
    py = WALL_Y - PLATE_T / 2
    ph = PLATE_Z1 - PLATE_Z0
    box("plate", (PLATE_W, PLATE_T, ph), (0, py, PLATE_Z0 + ph / 2), iron, bevel=0.004)
    cylinder("plate_point", PLATE_W / math.sqrt(2) * 0.72, 0.05, (0, py, PLATE_Z1 - 0.003), iron, r_top=0.004,
             segments=4, rot=(0, 0, 45), bevel=0.003)
    for sx in (-1, 1):
        for z in (PLATE_Z0 + 0.03, PLATE_Z1 - 0.03):
            cylinder(f"rivet_{sx}_{z:.2f}", 0.011, 0.012, (sx * (PLATE_W / 2 - 0.022), py - PLATE_T / 2 + 0.002, z),
                     worn, segments=8, rot=(90, 0, 0), bevel=0.003)

    collar = _axis(COLLAR_AT)
    cup = _axis(CUP_AT)
    arm_z = collar[2]
    for sx in (-1, 1):
        torus(f"scroll_{sx}", 0.032, 0.007, (sx * (PLATE_W / 2 + 0.03), py - 0.004, arm_z - 0.01), iron,
              rot=(90, 0, 0), major=14, minor=6)
        box(f"scroll_tie_{sx}", (0.02, 0.012, 0.018), (sx * (PLATE_W / 2 + 0.002), py - 0.004, arm_z - 0.01),
            iron, bevel=0.003)

    # Arm out to the collar round the haft, and a strap down to the cup holding its foot.
    _bar("arm", (0, py - PLATE_T / 2 + 0.004, arm_z), (0, collar[1] + 0.04, arm_z), 0.02, 0.016, iron)
    torus("collar", 0.034, 0.009, collar, worn, rot=(LEAN, 0, 0), major=14, minor=6)
    strap_top = (0, py - PLATE_T / 2 + 0.004, PLATE_Z0 + 0.07)
    _bar("strap", strap_top, (0, cup[1] + 0.026, cup[2] + 0.004), 0.018, 0.012, iron)
    cylinder("cup", 0.031, 0.05, _axis(CUP_AT - 0.03), iron, r_top=0.036, segments=10, rot=(LEAN, 0, 0),
             bevel=0.004)

    # Haft, pitch-soaked head bound with cord, a glowing crown and a short flame.
    cylinder("haft", HANDLE_R, HANDLE_L, _axis(0.0), wood, r_top=HANDLE_R * 1.15, segments=10, rot=(LEAN, 0, 0),
             bevel=0.004)
    head0 = HANDLE_L - 0.05
    cylinder("head", HEAD_R * 0.8, HEAD_L, _axis(head0), pitch, r_top=HEAD_R, segments=10, rot=(LEAN, 0, 0),
             bevel=0.008)
    for i, d in enumerate((0.025, 0.075)):
        torus(f"binding_{i}", HEAD_R * (0.84 + d * 1.2), 0.006, _axis(head0 + d), cord, rot=(LEAN, 0, 0), major=14,
              minor=5)
    top = head0 + HEAD_L
    blob("crown", HEAD_R * 0.95, _axis(top - 0.005), ember, squash=(1, 1, 0.45), subdiv=2, seed=3, jitter=0.18)
    tip = _axis(top)
    h = FLAME_TOP - tip[2]
    blob("flame", HEAD_R * 0.85, (0, tip[1] - 0.01, tip[2] + h / 2 - 0.004), flame,
         squash=(0.9, 0.85, h / (2 * HEAD_R * 0.85)), subdiv=2, seed=5, jitter=0.12)
    blob("flame_side", HEAD_R * 0.5, (0.018, tip[1] + 0.012, tip[2] + h * 0.3), flame, squash=(0.9, 0.85, 2.0),
         subdiv=1, seed=6, jitter=0.15)

    anchor("fire:torch", tip, size=(0.04, 0.04, 0.3))
    anchor("light:torch", (0, tip[1] - 0.02, tip[2] + 0.12))
