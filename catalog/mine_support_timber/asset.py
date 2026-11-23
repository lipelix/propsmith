"""A mine tunnel set: two round pine props with their bark on, splayed a little wider at the foot, standing on flat sill
blocks and carrying a squared cap beam; pairs of hardwood wedges are driven in between each prop head and the cap, a
few split lagging boards lie across the cap and iron dogs pin the joints. The opening faces -y."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall dimensions (metres): about 2.2 wide (x) × 0.4 deep × 2.4 high.
SILL = (0.34, 0.3, 0.06)  # foot block under each prop
FOOT_X, HEAD_X = 0.86, 0.79  # prop centres at the foot and at the head
PROP_R = 0.11  # prop radius at the foot
CAP = (2.16, 0.26, 0.22)  # cap beam: length (x), depth (y), height (z)
CAP_Z = 2.1  # underside of the cap
WEDGE_T = 0.035  # wedge thickness at its butt
LAGGING = 5  # split boards across the top of the cap
LAG = (0.2, 0.4, 0.045)  # one board: width (x), length (y), thickness

WOOD = (0.21, 0.14, 0.08)  # linear RGB, hewn pine
WOOD_OLD = (0.17, 0.13, 0.095)  # greyed lagging
BARK = (0.1, 0.075, 0.05)
WEDGE = (0.26, 0.17, 0.09)  # fresh-cut hardwood, paler
IRON = (0.05, 0.045, 0.042)
ROPE = (0.33, 0.26, 0.16)


def _rot(d):
    """Euler XYZ (degrees) turning local +z onto unit direction d."""
    a = math.degrees(math.acos(max(-1.0, min(1.0, d[2]))))
    c = math.degrees(math.atan2(d[0], -d[1]))
    return (a, 0, c)


def _wedge(name, length, width, at, mat, rot, butt):
    """A wedge `length` along x, `width` along y, `butt` thick at +x tapering to a sliver at -x, centred on `at`."""
    obj = box(name, (length, width, butt), at, mat, rot=rot, bevel=0.003)
    for v in obj.data.vertices:
        if v.co.x < 0:
            v.co.z *= 0.15
    return obj


@prop
def mine_support_timber():
    rnd = random.Random(41)
    wood = material("mine_support_wood", WOOD, vary=0.3, scale=10)
    old = material("mine_support_wood_old", WOOD_OLD, vary=0.32, scale=10)
    bark = material("mine_support_bark", BARK, rough=0.95, vary=0.35, scale=16, crevice=0.7)
    pale = material("mine_support_wedge", WEDGE, vary=0.25, scale=14)
    iron = material("mine_support_iron", IRON, rough=0.55, vary=0.3, scale=16, metal=0.7)
    rope = material("mine_support_rope", ROPE, rough=1.0, vary=0.2, scale=40)

    sx, sy, sz = SILL
    cx, cy, cz = CAP
    for s in (-1, 1):
        box(f"sill_{s}", (sx, sy, sz), (s * FOOT_X, rnd.uniform(-0.01, 0.01), sz / 2), old,
            rot=(0, 0, rnd.uniform(-3, 3)), bevel=0.01)
        # The prop: a barked pine log leaning in, its head just under the cap.
        foot = (s * FOOT_X, 0.0, sz - 0.005)
        head = (s * HEAD_X, 0.0, CAP_Z - 0.04)
        d = tuple(b - a for a, b in zip(foot, head))
        length = math.sqrt(sum(c * c for c in d))
        rot = _rot(tuple(c / length for c in d))
        cylinder(f"prop_{s}", PROP_R, length, foot, bark, r_top=PROP_R * 0.88, segments=12, rot=rot, bevel=0.006)
        # Bark knocked off in patches shows the pale wood; a knot or two.
        for k in range(2):
            t = 0.3 + 0.35 * k + rnd.uniform(-0.05, 0.05)
            p = tuple(a + b * t for a, b in zip(foot, d))
            ang = math.radians(rnd.uniform(-60, 60) - 90)
            r = PROP_R * (1 - 0.12 * t)
            blob(f"scar_{s}_{k}", 0.06, (p[0] + r * 0.8 * math.cos(ang), p[1] + r * 0.8 * math.sin(ang), p[2]), wood,
                 squash=(0.7, 0.7, 2.2), subdiv=1, seed=500 + 10 * s + k, jitter=0.15)
        # A flat head on the prop, cut square, the wedges driven in over it from front and back.
        box(f"head_{s}", (0.2, 0.2, 0.04), (s * HEAD_X, 0, CAP_Z - 0.04), wood, bevel=0.006)
        for f in (-1, 1):
            _wedge(f"wedge_{s}_{f}", 0.2, 0.08, (s * HEAD_X + rnd.uniform(-0.02, 0.02), f * 0.115, CAP_Z),
                   pale, (0, 0, -f * 90 + rnd.uniform(-6, 6)), WEDGE_T)
        # An iron dog (a staple) pinning the cap to the prop on the front face.
        y = -cy / 2 - 0.006
        box(f"dog_{s}", (0.022, 0.012, 0.24), (s * (HEAD_X - 0.05), y, CAP_Z + 0.01), iron, rot=(0, -s * 4, 0),
            bevel=0.003)
        for e in (-1, 1):
            box(f"dog_tooth_{s}_{e}", (0.022, 0.03, 0.022), (s * (HEAD_X - 0.05) - s * e * 0.008, y + 0.012,
                CAP_Z + 0.01 + e * 0.11), iron, bevel=0)

    # The cap beam, squared with an adze: a little out of true, the ends darker.
    box("cap", (cx, cy, cz), (0, 0, CAP_Z + cz / 2), wood, rot=(rnd.uniform(-1, 1), 0.6, 0), bevel=0.018)
    for s in (-1, 1):
        box(f"cap_end_{s}", (0.01, cy - 0.02, cz - 0.02), (s * (cx / 2 + 0.002), 0, CAP_Z + cz / 2), old, bevel=0)

    # Split lagging boards laid across the cap (they would carry the roof rock).
    top = CAP_Z + cz + 0.008
    lx, ly, lz = LAG
    for k in range(LAGGING):
        x = -cx / 2 + 0.16 + k * (cx - 0.32) / (LAGGING - 1) + rnd.uniform(-0.03, 0.03)
        box(f"lagging_{k}", (lx * rnd.uniform(0.85, 1.05), ly * rnd.uniform(0.94, 1.0), lz),
            (x, rnd.uniform(-0.01, 0.01), top + lz / 2), old if k % 2 else wood,
            rot=(rnd.uniform(-2, 2), rnd.uniform(-2, 2), rnd.uniform(-5, 5)), bevel=0.008)

    # A spike driven into the left prop with a coil of rope hung on it.
    hx = -(FOOT_X + (HEAD_X - FOOT_X) * 0.72)
    cylinder("spike", 0.01, 0.12, (hx, -PROP_R + 0.02, 1.55), iron, segments=6, rot=(90, 0, 0), bevel=0)
    for k in range(3):
        torus(f"rope_{k}", 0.1 - k * 0.006, 0.012, (hx + rnd.uniform(-0.01, 0.01), -PROP_R - 0.04 - k * 0.012, 1.46),
              rope, rot=(90 + rnd.uniform(-6, 6), rnd.uniform(-8, 8), 0), major=16, minor=6)
