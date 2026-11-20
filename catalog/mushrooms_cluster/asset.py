"""A cluster of woodland toadstools on a low mound of dark soil and leaf litter: a few tall brown-capped ones with
domed caps, and smaller pale ones with flatter caps, their stems leaning a little apart, gills darker under the caps."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall dimensions (metres), from the description.
MOUND_R = 0.13  # radius of the soil mound the toadstools grow from
MOUND_H = 0.035  # its height
CARD_T = 0.003  # thickness of a fallen leaf card

BROWN = (0.2, 0.1, 0.045)  # linear RGB
BROWN_DARK = (0.12, 0.062, 0.03)
TAN = (0.42, 0.34, 0.22)  # pale caps
PALE = (0.5, 0.44, 0.33)
STEM = (0.46, 0.41, 0.31)
STEM_DARK = (0.3, 0.25, 0.17)
GILL = (0.24, 0.19, 0.13)
SOIL = (0.055, 0.042, 0.03)
LITTER = (0.2, 0.12, 0.05)
LITTER_DARK = (0.12, 0.075, 0.035)
MOSS = (0.1, 0.13, 0.035)

# (x, y, stem height, cap radius, kind, tilt deg, yaw deg): kind "b" brown dome, "p" pale flat.
TOADSTOOLS = (
    (0.01, 0.03, 0.17, 0.062, "b", 6, 200),
    (-0.06, -0.01, 0.13, 0.05, "b", 14, 100),
    (0.06, -0.035, 0.11, 0.045, "b", 16, 300),
    (0.075, 0.06, 0.08, 0.035, "b", 22, 230),
    (-0.03, 0.08, 0.09, 0.04, "p", 18, 160),
    (-0.09, 0.055, 0.06, 0.032, "p", 26, 130),
    (0.0, -0.08, 0.07, 0.036, "p", 22, 10),
    (-0.075, -0.07, 0.045, 0.026, "p", 30, 60),
    (0.1, -0.005, 0.05, 0.028, "p", 30, 280),
    (0.035, -0.095, 0.035, 0.02, "b", 25, 340),
)


def _dir(tilt, yaw):
    """Unit vector of local +z after rot=(tilt, 0, yaw) degrees (XYZ Euler)."""
    t, y = math.radians(tilt), math.radians(yaw)
    return (math.sin(t) * math.sin(y), -math.sin(t) * math.cos(y), math.cos(t))


def _point(obj):
    """Reshape a card box into a pointed leaf (a rhombus): same vertices and faces, still closed."""
    for v in obj.data.vertices:
        if (v.co.x > 0) == (v.co.y > 0):
            v.co.y = 0.0
        else:
            v.co.x = 0.0
    return obj


def _toadstool(name, x, y, h, rc, kind, tilt, yaw, mats, rnd):
    rot = (tilt, 0, yaw)
    rs = rc * (0.28 if kind == "b" else 0.24)
    base = (x, y, 0.004)
    stem = mats["stem"] if rnd.random() < 0.7 else mats["stem_dark"]
    cylinder(f"{name}_stem", rs, h, base, stem, r_top=rs * 0.75, segments=10, rot=rot, bevel=0)
    blob(f"{name}_foot", rs * 1.35, (x, y, rs * 0.6), stem, squash=(1, 1, 0.7), subdiv=1, seed=rnd.randrange(999),
         jitter=0.1)
    d = _dir(tilt, yaw)
    top = (x + d[0] * h, y + d[1] * h, 0.004 + d[2] * h)
    cylinder(f"{name}_gills", rc * 0.9, 0.01, (top[0] - d[0] * 0.006, top[1] - d[1] * 0.006, top[2] - d[2] * 0.006),
             mats["gill"], segments=14, rot=rot, bevel=0)
    # The cap: a squashed icosphere whose underside is flattened just above the gills, then tilted with the stem.
    if kind == "b":
        squash, mat = (1, 1, rnd.uniform(0.75, 0.9)), mats["brown"] if rnd.random() < 0.65 else mats["brown_dark"]
    else:
        squash, mat = (1, 1, rnd.uniform(0.42, 0.52)), mats["pale"] if rnd.random() < 0.6 else mats["tan"]
    cap = blob(f"{name}_cap", rc, top, mat, squash=squash, subdiv=2, seed=rnd.randrange(999), jitter=0.05)
    floor = -rc * 0.12
    for v in cap.data.vertices:
        v.co.z = max(v.co.z, floor) - floor + 0.004
    cap.rotation_euler = [math.radians(a) for a in rot]


@prop
def mushrooms_cluster():
    rnd = random.Random(41)
    mats = {
        "brown": material("mushrooms_cap_brown", BROWN, rough=0.6, vary=0.3, scale=30, crevice=0.5),
        "brown_dark": material("mushrooms_cap_brown_dark", BROWN_DARK, rough=0.6, vary=0.3, scale=30, crevice=0.5),
        "tan": material("mushrooms_cap_tan", TAN, rough=0.7, vary=0.25, scale=30, crevice=0.45),
        "pale": material("mushrooms_cap_pale", PALE, rough=0.7, vary=0.2, scale=30, crevice=0.45),
        "stem": material("mushrooms_stem", STEM, rough=0.8, vary=0.2, scale=40, crevice=0.5),
        "stem_dark": material("mushrooms_stem_dark", STEM_DARK, rough=0.8, vary=0.2, scale=40, crevice=0.5),
        "gill": material("mushrooms_gill", GILL, rough=0.9, vary=0.2, scale=60, crevice=0.6),
    }
    soil = material("mushrooms_soil", SOIL, rough=1.0, vary=0.3, scale=30, crevice=0.6)
    litter = material("mushrooms_litter", LITTER, rough=0.95, vary=0.3, scale=30, crevice=0.5)
    litter_dark = material("mushrooms_litter_dark", LITTER_DARK, rough=0.95, vary=0.3, scale=30, crevice=0.5)
    moss = material("mushrooms_moss", MOSS, rough=0.95, vary=0.3, scale=40, crevice=0.5)

    # A low mound of dark soil with a little moss, and fallen leaves round it.
    mound = blob("mushrooms_mound", MOUND_R, (0, 0, 0.0), soil, squash=(1.05, 0.95, MOUND_H / MOUND_R), subdiv=2,
                 seed=5, jitter=0.12)
    for v in mound.data.vertices:
        v.co.z = max(v.co.z, 0.0)  # a flat underside on the ground
    for i in range(3):
        a = math.radians(120 * i + 40)
        blob(f"mushrooms_moss_{i}", 0.045, (0.09 * math.cos(a), 0.09 * math.sin(a), 0.012), moss,
             squash=(1.2, 1, 0.35), subdiv=1, seed=20 + i, jitter=0.2)
    for i in range(9):
        a = math.radians(40 * i + rnd.uniform(-12, 12))
        rr = rnd.uniform(0.1, 0.15)
        ln = rnd.uniform(0.045, 0.065)
        _point(box(f"mushrooms_leaf_{i}", (ln, ln * 0.55, CARD_T), (rr * math.cos(a), rr * math.sin(a), 0.006),
                   litter if i % 3 else litter_dark, rot=(rnd.uniform(-8, 8), rnd.uniform(-8, 8), rnd.uniform(0, 360)),
                   bevel=0))

    for i, t in enumerate(TOADSTOOLS):
        _toadstool(f"mushroom_{i}", *t, mats, rnd)
