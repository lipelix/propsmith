"""A small timber dock crane, its jib reaching out over +x: a squared mast on a cross of sill beams with three raking
braces, a jib rising from the mast to a sheave at its tip, tied back to the mast head by a top beam, a hand winch at
the mast's foot with a rope drum, a ratchet wheel and two cranks, and the rope running up the jib and over the sheave
down to a pulley block and an iron hook."""
import math
import random

from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall size: about 2.5 m long (x), 1.5 m across the cranks (y), 3.5 m high.
MAST_X = -0.64  # the mast's axis
MAST_W, MAST_H = 0.2, 3.38  # the mast's square side and height
SILL = (1.2, 0.16, 0.16)  # each sill beam: length, width, height
BRACE_Z, BRACE_W = 1.05, 0.11  # where the braces meet the mast, their square side
JIB_FOOT_Z = 1.45  # where the jib bears on the mast
TIP = (1.0, 3.12)  # the jib tip (x, z)
JIB_W = (0.15, 0.17)  # the jib's width (y) and depth
TIE_Z = 3.2  # the top tie beam, from the mast head to the tip
SHEAVE_R = 0.12
DRUM_X, DRUM_Z, DRUM_R, DRUM_L = -0.33, 0.72, 0.1, 0.56  # the winch drum: centre (x, z), radius, length (y)
CRANK_Y = 0.66  # the crank handles reach to ±CRANK_Y
HOOK_Z = 1.15  # the bottom of the hook

TIMBER = (0.2, 0.14, 0.085)  # linear RGB
TIMBER_OLD = (0.16, 0.12, 0.08)
TIMBER_DARK = (0.12, 0.085, 0.055)
IRON = (0.05, 0.048, 0.045)
ROPE = (0.34, 0.27, 0.16)  # hemp, as pier_wood
STONE = (0.25, 0.23, 0.2)


def _beam(name, a, b, w, d, mat, bevel=0.012):
    """A squared timber from point a to point b, w wide (across, kept towards y) and d deep."""
    a, b = Vector(a), Vector(b)
    v = b - a
    obj = box(name, (d, w, v.length), (0, 0, 0), mat, bevel=bevel)
    obj.location = (a + b) / 2
    obj.rotation_euler = v.to_track_quat("Z", "Y").to_euler()
    return obj


def _rod(name, a, b, r, mat, segments=8, bevel=0):
    """A round rod (iron or rope) from point a to point b."""
    a, b = Vector(a), Vector(b)
    v = b - a
    obj = cylinder(name, r, v.length, (0, 0, 0), mat, segments=segments, bevel=bevel)
    obj.location = a
    obj.rotation_euler = v.to_track_quat("Z", "Y").to_euler()
    return obj


@prop
def crane_dock_wood():
    rnd = random.Random(116)
    timber = material("crane_dock_wood_timber", TIMBER, vary=0.25, scale=10)
    old = material("crane_dock_wood_timber_old", TIMBER_OLD, vary=0.3, scale=9)
    dark = material("crane_dock_wood_timber_dark", TIMBER_DARK, vary=0.3, scale=12)
    iron = material("crane_dock_wood_iron", IRON, rough=0.55, vary=0.2, scale=12, metal=0.7)
    rope = material("crane_dock_wood_rope", ROPE, vary=0.3, scale=30, crevice=0.6)
    stone = material("crane_dock_wood_stone", STONE, vary=0.25, scale=8, crevice=0.7)

    # The base: two sill beams crossing under the mast, three braces up to it, stones weighting the back.
    sl, sw, sh = SILL
    box("sill_x", (sl, sw, sh), (MAST_X, 0, sh / 2), old, rot=(0, 0, rnd.uniform(-1, 1)))
    box("sill_y", (sw, sl, sh), (MAST_X, 0, sh * 1.5), old, rot=(0, 0, rnd.uniform(-1, 1)))
    box("mast", (MAST_W, MAST_W, MAST_H - 2 * sh), (MAST_X, 0, 2 * sh + (MAST_H - 2 * sh) / 2), timber)
    box("mast_cap", (MAST_W + 0.04, MAST_W + 0.04, 0.05), (MAST_X, 0, MAST_H - 0.025), dark, bevel=0.01)
    for k, (dx, dy, z0) in enumerate(((-1, 0, sh), (0, -1, 2 * sh), (0, 1, 2 * sh))):  # the winch braces +x
        foot = (MAST_X + dx * (sl / 2 - 0.1), dy * (sl / 2 - 0.1), z0 + BRACE_W * 0.35)
        top = (MAST_X + dx * (MAST_W / 2 + 0.02), dy * (MAST_W / 2 + 0.02), BRACE_Z + rnd.uniform(-0.03, 0.03))
        _beam(f"brace_{k}", foot, top, BRACE_W, BRACE_W, timber if k % 2 else old)
    for i, (x, y) in enumerate(((MAST_X - 0.5, 0.0), (MAST_X - 0.43, 0.14), (MAST_X - 0.46, -0.13))):
        blob(f"ballast_{i}", 0.1, (x, y, sh + 0.07 + 0.02 * i), stone, squash=(1, 0.9, 0.7), subdiv=1, seed=20 + i)

    # The jib from its heel on the mast up to the tip, the top tie back to the mast head, an iron strap at each joint.
    tx, tz = TIP
    heel = (MAST_X + MAST_W / 2 + 0.03, 0, JIB_FOOT_Z)
    _beam("jib", heel, (tx, 0, tz), JIB_W[0], JIB_W[1], timber)
    _beam("tie", (MAST_X - MAST_W / 2 - 0.05, 0, TIE_Z), (tx + 0.06, 0, TIE_Z + 0.01), 0.13, 0.13, dark)
    box("jib_cleat", (0.08, 0.22, 0.14), (MAST_X + MAST_W / 2 + 0.04, 0, JIB_FOOT_Z - 0.13), dark)
    for k, (x, z) in enumerate(((MAST_X, JIB_FOOT_Z), (MAST_X, TIE_Z))):
        box(f"strap_{k}", (MAST_W + 0.025, MAST_W + 0.025, 0.05), (x, 0, z), iron, bevel=0.006)
    # The tip: two cheek plates either side of the sheave.
    for s in (-1, 1):
        box(f"cheek_{s}", (0.3, 0.025, 0.32), (tx, s * (JIB_W[0] / 2 + 0.0125), tz + 0.02), dark, bevel=0.008)
    cylinder("sheave", SHEAVE_R, 0.06, (tx + 0.04, -0.03, tz - 0.02), old, segments=16, rot=(-90, 0, 0), bevel=0.008)
    cylinder("sheave_pin", 0.02, JIB_W[0] + 0.1, (tx + 0.04, -JIB_W[0] / 2 - 0.05, tz - 0.02), iron, segments=8,
             rot=(-90, 0, 0), bevel=0)

    # The winch: two cheek posts beside the mast carrying the drum, a ratchet wheel and a pawl, two cranks.
    for s in (-1, 1):
        y = s * (DRUM_L / 2 + 0.04)
        box(f"winch_post_{s}", (0.12, 0.07, DRUM_Z + 0.12 - 2 * sh), (DRUM_X, y, 2 * sh + (DRUM_Z + 0.12 - 2 * sh) / 2),
            dark)
        _beam(f"winch_stay_{s}", (DRUM_X, y, DRUM_Z + 0.1), (MAST_X + MAST_W / 2, y * 0.55, DRUM_Z + 0.32), 0.06, 0.06,
              dark)
    cylinder("drum", DRUM_R, DRUM_L, (DRUM_X, -DRUM_L / 2, DRUM_Z), old, segments=14, rot=(-90, 0, 0), bevel=0.01)
    for k in range(5):  # the rope wound on the drum
        torus(f"drum_rope_{k}", DRUM_R + 0.012, 0.014, (DRUM_X, -0.16 + k * 0.028, DRUM_Z), rope, rot=(90, 0, 0),
              major=16, minor=5)
    cylinder("axle", 0.022, 2 * CRANK_Y - 0.12, (DRUM_X, -CRANK_Y + 0.06, DRUM_Z), iron, segments=8, rot=(-90, 0, 0),
             bevel=0)
    ratchet = cylinder("ratchet", DRUM_R + 0.05, 0.03, (DRUM_X, DRUM_L / 2 - 0.035, DRUM_Z), iron, segments=12,
                       rot=(-90, 0, 0), bevel=0.004)
    ratchet.rotation_euler.y = math.radians(15)
    _beam("pawl", (DRUM_X + 0.02, DRUM_L / 2 - 0.02, DRUM_Z + 0.27), (DRUM_X + 0.06, DRUM_L / 2 - 0.02,
                                                                       DRUM_Z + DRUM_R + 0.06), 0.02, 0.025, iron,
          bevel=0.004)
    for s in (-1, 1):
        y = s * (CRANK_Y - 0.06)
        a = math.radians(40 if s < 0 else 220)
        end = (DRUM_X + 0.26 * math.cos(a), y, DRUM_Z + 0.26 * math.sin(a))
        _beam(f"crank_arm_{s}", (DRUM_X, y, DRUM_Z), end, 0.03, 0.045, iron, bevel=0.005)
        cylinder(f"crank_grip_{s}", 0.022, 0.13, (end[0], y, end[2]), timber,
                 segments=8, rot=(-90 * s, 0, 0), bevel=0.004)

    # The rope: off the drum's top, up along the jib's underside, over the sheave and down to the block and hook.
    start = (DRUM_X + 0.03, -0.02, DRUM_Z + DRUM_R + 0.015)
    under = Vector((tx, 0, tz)) - Vector(heel)
    n = Vector((-under.z, 0, under.x)).normalized()  # the jib's upward normal in the xz plane
    lead = (tx - 0.12 - n.x * 0.12, -0.02, tz - 0.06 - n.z * 0.12 - 0.03)
    _rod("rope_lead", start, lead, 0.013, rope)
    _rod("rope_lead_top", lead, (tx + 0.04 - SHEAVE_R * 0.7, -0.02, tz - 0.02 + SHEAVE_R * 0.7), 0.013, rope)
    fall_x = tx + 0.04 + SHEAVE_R + 0.005
    block_z = HOOK_Z + 0.4
    _rod("rope_fall", (fall_x, -0.0, tz - 0.02), (fall_x, 0, block_z + 0.12), 0.013, rope)
    box("block", (0.1, 0.08, 0.2), (fall_x, 0, block_z + 0.02), dark, bevel=0.012)
    cylinder("block_sheave", 0.06, 0.09, (fall_x, -0.045, block_z + 0.02), old, segments=12, rot=(-90, 0, 0),
             bevel=0.004)
    # The hook: an eye, a shank and a curved bill of short iron rods.
    torus("hook_eye", 0.035, 0.011, (fall_x, 0, block_z - 0.11), iron, rot=(90, 0, 0), major=12, minor=6)
    _rod("hook_shank", (fall_x, 0, block_z - 0.14), (fall_x, 0, HOOK_Z + 0.06), 0.014, iron)
    cx, cz = fall_x + 0.06, HOOK_Z + 0.06
    pts = [(cx + 0.06 * math.cos(t), 0, cz + 0.06 * math.sin(t)) for t in (math.pi * (1 + k / 4) for k in range(5))]
    pts.append((cx + 0.05, 0, cz + 0.045))
    for k in range(len(pts) - 1):
        _rod(f"hook_bill_{k}", pts[k], pts[k + 1], 0.014, iron)
