"""Two oak kegs lying on a timber cradle behind an inn bar: each keg of curved staves held by iron hoops, its front
head with a wooden spigot; the cradle of sills, posts and top rails with shaped chocks under each keg."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall size: about 1.45 m long, 0.65 m deep, 1 m high. The kegs lie along y, their heads and taps facing -y.
CRADLE_L = 1.42  # cradle length (x)
RAIL_Y = 0.16  # top rails and sills at y = +-RAIL_Y
RAIL_TOP = 0.45  # top of the top rails
SILL = (0.1, 0.08)  # sill section (y, z)
RAIL = (0.09, 0.09)  # top rail section (y, z)
POST = 0.08
POST_X = (-0.66, 0.0, 0.66)
KEG_X = (-0.35, 0.35)
KEG_Y = 0.02  # keg centre along y (the tap sticks out at the front)
KEG_L = 0.54  # keg length, head to head
R_BELLY, R_HEAD = 0.27, 0.235
SEG = 0.17  # length of each tapered end segment; the straight belly between
STAVES = 16
STAVE_T = 0.028
HOOP_TUBE = 0.011
CHOCK_X = 0.2  # chocks at keg centre +- this
KEG_LIFT = 0.26  # keg axis above the top rails, resting on the chocks
TAP_LEN = 0.08

WOOD = (0.2, 0.115, 0.058)  # linear RGB
WOOD_LIGHT = (0.25, 0.155, 0.08)
WOOD_OLD = (0.16, 0.11, 0.075)
WOOD_INNER = (0.11, 0.065, 0.035)
TIMBER = (0.18, 0.12, 0.07)
TIMBER_OLD = (0.14, 0.1, 0.065)
IRON = (0.045, 0.045, 0.045)
TAP = (0.24, 0.16, 0.09)


def keg_r(y):
    """Outer stave radius at distance y from the keg's middle along its axis."""
    t = abs(y)
    edge = KEG_L / 2 - SEG
    if t <= edge:
        return R_BELLY
    return R_BELLY + (R_HEAD - R_BELLY) * (t - edge) / SEG


def keg(n, cx, cz, rnd, woods, inner, heads, iron, tap):
    y0 = KEG_Y
    # A closed dark core behind the staves.
    cylinder(f"keg_{n}_core", R_HEAD - STAVE_T + 0.004, KEG_L - 0.02, (cx, y0 + KEG_L / 2 - 0.01, cz), inner,
             segments=16, rot=(90, 0, 0), bevel=0)
    tilt = math.degrees(math.atan((R_BELLY - R_HEAD) / SEG))
    pitch = 2 * math.pi * R_BELLY / STAVES
    edge = KEG_L / 2 - SEG
    spans = ((-KEG_L / 2, -edge + 0.012, tilt), (-edge - 0.012, edge + 0.012, 0.0), (edge - 0.012, KEG_L / 2, -tilt))
    for i in range(STAVES):
        b = 360 * i / STAVES + rnd.uniform(-1.2, 1.2) + 10
        w = pitch * rnd.uniform(0.9, 0.96)
        mat = woods[rnd.choice((0, 0, 1, 1, 2))]
        br = math.radians(b)
        for k, (ya, yb, t) in enumerate(spans):
            yc = (ya + yb) / 2
            rc = keg_r(yc) - STAVE_T / 2
            length = (yb - ya) / math.cos(math.radians(t))
            # Local frame: x across the stave, y along the keg, z out from the axis; tilt about x for the bulge,
            # then turn about the keg axis (y).
            box(f"keg_{n}_stave_{i}_{k}", (w, length, STAVE_T),
                (cx + rc * math.sin(br), y0 + yc, cz + rc * math.cos(br)), mat, rot=(t, b, 0), bevel=0)
    # Iron hoops at the heads and either side of the belly.
    for j, y in enumerate((-KEG_L / 2 + 0.045, -edge + 0.01, edge - 0.01, KEG_L / 2 - 0.045)):
        torus(f"keg_{n}_hoop_{j}", keg_r(y) + HOOP_TUBE * 0.5, HOOP_TUBE, (cx, y0 + y, cz), iron, rot=(90, 0, 0),
              major=20, minor=5)
    # The heads, set into the chime, the front one with a spigot and a bung.
    for s in (-1, 1):
        hy = y0 + s * (KEG_L / 2 - 0.02)
        cylinder(f"keg_{n}_head_{s}", R_HEAD - STAVE_T - 0.003, 0.025, (cx, hy - s * 0.0125, cz), heads[s > 0],
                 segments=16, rot=(90 if s > 0 else -90, 0, 0), bevel=0.004)
    front = y0 - KEG_L / 2 + 0.008
    tz = cz - R_HEAD * 0.45
    cylinder(f"keg_{n}_tap", 0.028, TAP_LEN, (cx, front + 0.02, tz), tap, r_top=0.02, segments=10,
             rot=(90, 0, 0), bevel=0.003)
    cylinder(f"keg_{n}_tap_spout", 0.013, 0.05, (cx, front - TAP_LEN + 0.03, tz + 0.002), tap, segments=8,
             rot=(180, 0, 0), bevel=0.002)
    box(f"keg_{n}_tap_key", (0.016, 0.02, 0.06), (cx, front - TAP_LEN + 0.035, tz + 0.03), tap,
        rot=(0, 0, rnd.uniform(-20, 20)), bevel=0.003)
    cylinder(f"keg_{n}_bung", 0.022, 0.012, (cx, y0 + 0.02, cz + R_BELLY - 0.004), tap, segments=10, bevel=0.003)


@prop
def keg_rack():
    rnd = random.Random(51)
    woods = [
        material("keg_rack_staves", WOOD, vary=0.25, scale=14),
        material("keg_rack_staves_light", WOOD_LIGHT, vary=0.25, scale=12),
        material("keg_rack_staves_old", WOOD_OLD, vary=0.3, scale=11),
    ]
    inner = material("keg_rack_inner", WOOD_INNER, vary=0.2, scale=8)
    heads = (material("keg_rack_head", WOOD_OLD, vary=0.3, scale=13),
             material("keg_rack_head_light", WOOD_LIGHT, vary=0.3, scale=13))
    timber = material("keg_rack_timber", TIMBER, vary=0.28, scale=10)
    timber_old = material("keg_rack_timber_old", TIMBER_OLD, vary=0.3, scale=9)
    iron = material("keg_rack_hoops", IRON, rough=0.5, metal=0.8, vary=0.3, scale=20)
    tap = material("keg_rack_tap", TAP, vary=0.2, scale=12)

    # The cradle: two sills on the ground, three posts on each, two top rails, and cross ties at the ends.
    sy, sz = SILL
    ry, rz = RAIL
    for i, s in enumerate((-1, 1)):
        y = s * RAIL_Y
        box(f"sill_{i}", (CRADLE_L, sy, sz), (0, y, sz / 2), timber_old, rot=(0, 0, rnd.uniform(-0.4, 0.4)),
            bevel=0.012)
        box(f"rail_{i}", (CRADLE_L, ry, rz), (0, y, RAIL_TOP - rz / 2), timber, rot=(0, 0, rnd.uniform(-0.4, 0.4)),
            bevel=0.012)
        for j, x in enumerate(POST_X):
            ph = RAIL_TOP - rz - sz
            box(f"post_{i}_{j}", (POST, POST, ph + 0.004), (x + rnd.uniform(-0.01, 0.01), y, sz + ph / 2), timber,
                rot=(0, 0, rnd.uniform(-2, 2)), bevel=0.01)
    for j, x in enumerate((POST_X[0], POST_X[2])):
        box(f"tie_{j}", (0.06, 2 * RAIL_Y + ry + 0.06, 0.07), (x, 0, RAIL_TOP - 0.11), timber_old, bevel=0.008)

    # Each keg on four chocks cut to its curve (two on each top rail), then the keg.
    for n, cx in enumerate(KEG_X):
        cz = RAIL_TOP + KEG_LIFT
        for i, s in enumerate((-1, 1)):
            for j, d in enumerate((-1, 1)):
                box(f"chock_{n}_{i}_{j}", (0.12, ry - 0.01, 0.1), (cx + d * CHOCK_X, s * RAIL_Y, RAIL_TOP + 0.04),
                    timber_old, rot=(0, -d * 30, 0), bevel=0.008)
        keg(n, cx, cz, rnd, woods, inner, heads, iron, tap)
