"""A clump of reeds and rushes for the rim of a pool: long flat blades rising from a dark wet mud base and bending
outwards, some with dry tan tips, thin round rushes between them, and a few brown bulrush heads on tall stalks."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, cylinder

# Overall dimensions (metres), from the description.
H = 1.2  # tallest bulrush stalk tip
BLADE_H = (0.55, 1.05)  # length range of a reed blade
RUSH_H = (0.5, 0.9)  # length range of a round rush
REACH = 0.28  # no blade or rush tip further than this from the centre
ROOT_R = 0.11  # radius within which the stems leave the mud
MUD_R = 0.2  # radius of the mud base
BLADE_W = 0.016  # half-width of a blade at its base
BLADE_FLAT = 0.3  # blade thickness as a share of its width
HEAD_L, HEAD_R = 0.13, 0.016  # bulrush head

REED = (0.1, 0.13, 0.035)  # linear RGB, olive
REED_DARK = (0.05, 0.075, 0.022)
REED_LIT = (0.19, 0.22, 0.06)
DRY = (0.33, 0.26, 0.1)
RUSH = (0.065, 0.09, 0.03)
HEAD = (0.13, 0.07, 0.035)
MUD = (0.045, 0.035, 0.025)
MUD_WET = (0.03, 0.026, 0.02)


def _dir(tilt, yaw):
    """Unit vector of local +z after rot=(tilt, 0, yaw) degrees (XYZ Euler)."""
    t, y = math.radians(tilt), math.radians(yaw)
    return (math.sin(t) * math.sin(y), -math.sin(t) * math.cos(y), math.cos(t))


def _path(base, length, tilt, bend, yaw, n):
    """Segment start points and tilts of a stem `length` long that leans `tilt` degrees and bends `bend` more per
    segment, scaled back so its tip stays within REACH of the centre."""
    for _ in range(12):
        pts, tilts = [base], []
        for k in range(n):
            t = min(tilt + bend * k, 80)
            d = _dir(t, yaw)
            p = pts[-1]
            pts.append((p[0] + d[0] * length / n, p[1] + d[1] * length / n, p[2] + d[2] * length / n))
            tilts.append(t)
        if max(math.hypot(p[0], p[1]) for p in pts) <= REACH:
            break
        tilt *= 0.75
        bend *= 0.75
    return pts, tilts


def _blade(name, rnd, base, length, yaw, mats, dry_tip):
    """A flat tapering reed blade in three segments, bending outwards, its tip dry on some."""
    pts, tilts = _path(base, length, rnd.uniform(4, 16), rnd.uniform(5, 13), yaw, 3)
    w = BLADE_W * rnd.uniform(0.8, 1.2)
    widths = (w, w * 0.75, w * 0.45, 0.001)
    low = rnd.choice(mats["green"])
    for k in range(3):
        mat = mats["dry"] if (k == 2 and dry_tip) else low if k < 2 else rnd.choice(mats["green"])
        seg = cylinder(f"{name}_{k}", widths[k], length / 3, pts[k], mat, r_top=widths[k + 1], segments=4,
                       rot=(tilts[k], 0, yaw), bevel=0)
        seg.scale = (1, BLADE_FLAT, 1)  # flat: the broad face looks outwards


def _rush(name, rnd, base, length, yaw, mat):
    pts, tilts = _path(base, length, rnd.uniform(1, 8), rnd.uniform(1, 4), yaw, 2)
    for k in range(2):
        cylinder(f"{name}_{k}", 0.0045 if k == 0 else 0.0035, length / 2, pts[k], mat, r_top=0.0035 if k == 0 else 0.001,
                 segments=5, rot=(tilts[k], 0, yaw), bevel=0)


def _bulrush(name, rnd, base, yaw, top, mats):
    """A tall stalk with a brown sausage-shaped head and a thin spike above it, ending at `top` metres."""
    tilt = rnd.uniform(1, 5)
    d = _dir(tilt, yaw)
    spike = 0.06
    stalk = (top - spike - HEAD_L - base[2]) / d[2]
    cylinder(f"{name}_stalk", 0.005, stalk, base, mats["rush"], r_top=0.004, segments=5, rot=(tilt, 0, yaw), bevel=0)
    p = tuple(base[i] + d[i] * stalk for i in range(3))
    cylinder(f"{name}_head", HEAD_R, HEAD_L, p, mats["head"], r_top=HEAD_R * 0.9, segments=8, rot=(tilt, 0, yaw),
             bevel=0.005)
    q = tuple(p[i] + d[i] * HEAD_L for i in range(3))
    cylinder(f"{name}_spike", 0.0035, spike, q, mats["dry"], r_top=0.0008, segments=4, rot=(tilt, 0, yaw), bevel=0)


@prop
def reeds_clump():
    rnd = random.Random(53)
    mats = {
        "green": [
            material("reeds_blade", REED, rough=0.8, vary=0.3, scale=30, crevice=0.5),
            material("reeds_blade_dark", REED_DARK, rough=0.8, vary=0.3, scale=30, crevice=0.5),
            material("reeds_blade_lit", REED_LIT, rough=0.8, vary=0.25, scale=30, crevice=0.4),
        ],
        "dry": material("reeds_dry", DRY, rough=0.9, vary=0.3, scale=30, crevice=0.4),
        "rush": material("reeds_rush", RUSH, rough=0.8, vary=0.25, scale=40, crevice=0.5),
        "head": material("reeds_head", HEAD, rough=0.95, vary=0.3, scale=60, crevice=0.6),
    }
    mud = material("reeds_mud", MUD, rough=0.95, vary=0.3, scale=20, crevice=0.6)
    wet = material("reeds_mud_wet", MUD_WET, rough=0.75, vary=0.2, scale=20, crevice=0.5)

    # The mud base: a low dark mound, wetter in patches, flat underneath.
    for i, (r, at, m) in enumerate(((MUD_R, (0, 0), mud), (0.1, (0.09, -0.07), wet), (0.08, (-0.1, 0.06), wet))):
        b = blob(f"reeds_mud_{i}", r, (at[0], at[1], 0), m, squash=(1.1, 0.95, 0.22 if i == 0 else 0.18), subdiv=2,
                 seed=11 + i, jitter=0.15)
        for v in b.data.vertices:
            v.co.z = max(v.co.z, 0.0)

    def root():
        a = rnd.uniform(0, 2 * math.pi)
        rr = ROOT_R * math.sqrt(rnd.random())
        return (rr * math.cos(a), rr * math.sin(a), 0.01), math.degrees(a)

    # Reed blades: the tallest stand in the middle, the shorter outer ones lean out more.
    for i in range(44):
        base, a = root()
        out = math.hypot(base[0], base[1]) / ROOT_R
        length = rnd.uniform(*BLADE_H) * (1 - 0.3 * out)
        yaw = a + 90 + rnd.uniform(-40, 40)  # rot yaw 0 leans towards -y: +90 turns it outwards
        _blade(f"reeds_blade_{i}", rnd, base, length, yaw, mats, dry_tip=rnd.random() < 0.3)

    for i in range(26):
        base, a = root()
        _rush(f"reeds_rush_{i}", rnd, base, rnd.uniform(*RUSH_H), a + 90 + rnd.uniform(-60, 60), mats["rush"])

    for i, top in enumerate((H - 0.005, 1.1, 1.02, 0.94, 1.14)):
        base, a = root()
        _bulrush(f"reeds_bulrush_{i}", rnd, (base[0] * 0.6, base[1] * 0.6, 0.01), a + 90, top, mats)
