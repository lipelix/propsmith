"""An ore cart: a flared tub of thick planks bound with iron corner straps and a rim band, on two timber frame beams
and two iron axles with four flanged wheels set to the gauge of `rail_track_straight`, half full of dark rock and
glinting ore. Coupling links hang at both ends; the long axis runs along x, as on the track."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall dimensions (metres): about 1.3 long (x) × 0.9 wide × 1 high.
GAUGE = 0.6  # wheel centre lines, as `rail_track_straight`'s rail centre lines
WHEEL_R = 0.15  # tread radius
FLANGE_R = 0.18  # flange radius: the lowest point, standing on the ground
WHEEL_W = 0.06
AXLE_X = 0.33  # axles at +-x
TUB_Z0, TUB_Z1 = 0.42, 0.98  # tub floor underside and rim top
TUB_X0, TUB_X1 = 0.46, 0.55  # tub half length at the floor and at the rim
TUB_Y0, TUB_Y1 = 0.3, 0.42  # tub half width at the floor and at the rim
BOARD_T = 0.045  # plank thickness
BOARDS = 4  # planks up each wall
FILL_Z = 0.72  # top of the ore bed: about half full

WOOD = (0.19, 0.12, 0.07)  # linear RGB, oiled oak
WOOD_OLD = (0.16, 0.12, 0.085)
IRON = (0.055, 0.05, 0.047)
IRON_WORN = (0.17, 0.16, 0.15)  # wheel treads, bright from the rails
RUST = (0.2, 0.09, 0.04)
ROCK = (0.12, 0.115, 0.11)
ROCK_DARK = (0.075, 0.07, 0.068)
ORE = (0.5, 0.33, 0.1)  # brassy pyrite and gold glints


def _lerp(a, b, t):
    return a + (b - a) * t


def _wall_rot(dz, dy):
    return math.degrees(math.atan2(dy, dz))


@prop
def mine_cart():
    rnd = random.Random(31)
    wood = material("mine_cart_wood", WOOD, vary=0.28, scale=12)
    old = material("mine_cart_wood_old", WOOD_OLD, vary=0.3, scale=11)
    iron = material("mine_cart_iron", IRON, rough=0.55, vary=0.3, scale=16, metal=0.7)
    worn = material("mine_cart_tread", IRON_WORN, rough=0.35, vary=0.2, scale=25, metal=0.85)
    rust = material("mine_cart_rust", RUST, rough=0.9, vary=0.35, scale=18)
    rock = material("mine_cart_rock", ROCK, rough=0.9, vary=0.3, scale=10, crevice=0.75)
    dark = material("mine_cart_rock_dark", ROCK_DARK, rough=0.9, vary=0.3, scale=10, crevice=0.75)
    ore = material("mine_cart_ore", ORE, rough=0.3, vary=0.3, scale=30, metal=0.8)

    h = TUB_Z1 - TUB_Z0
    tilt_y = _wall_rot(h, TUB_Y1 - TUB_Y0)  # long walls lean out by this about x
    tilt_x = _wall_rot(h, TUB_X1 - TUB_X0)  # end walls about y
    slant_y = math.hypot(h, TUB_Y1 - TUB_Y0)
    slant_x = math.hypot(h, TUB_X1 - TUB_X0)

    # Floor planks, across the tub.
    for i in range(5):
        w = 2 * TUB_X0 / 5
        box(f"floor_{i}", (w - 0.006, 2 * TUB_Y0, BOARD_T), (-TUB_X0 + w * (i + 0.5), 0, TUB_Z0 + BOARD_T / 2),
            old if i % 2 else wood, bevel=0)

    # Long walls (-y and +y): planks the full length, leaning out.
    bh = slant_y / BOARDS
    for s in (-1, 1):
        for k in range(BOARDS):
            t = (k + 0.5) / BOARDS
            z = _lerp(TUB_Z0, TUB_Z1, t)
            y = s * (_lerp(TUB_Y0, TUB_Y1, t) + BOARD_T / 2)
            length = 2 * _lerp(TUB_X0, TUB_X1, t) + 2 * BOARD_T
            box(f"side_{s}_{k}", (length, BOARD_T, bh - 0.008), (0, y, z), old if (k + s) % 3 == 0 else wood,
                rot=(-s * tilt_y + rnd.uniform(-0.5, 0.5), 0, 0), bevel=0.007)
    # End walls (-x and +x): planks between the long walls.
    bh = slant_x / BOARDS
    for e in (-1, 1):
        for k in range(BOARDS):
            t = (k + 0.5) / BOARDS
            z = _lerp(TUB_Z0, TUB_Z1, t)
            x = e * (_lerp(TUB_X0, TUB_X1, t) + BOARD_T / 2)
            width = 2 * _lerp(TUB_Y0, TUB_Y1, t)
            box(f"end_{e}_{k}", (BOARD_T, width, bh - 0.008), (x, 0, z), wood if k % 2 else old,
                rot=(0, e * tilt_x, 0), bevel=0.007)

    # Iron: a band round the rim, straps up each corner and across the middle of each long wall.
    zr = TUB_Z1 - 0.03
    xr, yr = TUB_X1 + BOARD_T + 0.006, TUB_Y1 + BOARD_T + 0.006
    for s in (-1, 1):
        box(f"rim_y_{s}", (2 * xr + 0.02, 0.014, 0.06), (0, s * (yr + 0.002), zr), iron,
            rot=(-s * tilt_y, 0, 0), bevel=0.003)
        box(f"rim_x_{s}", (0.014, 2 * yr + 0.02, 0.06), (s * (xr + 0.002), 0, zr), iron,
            rot=(0, s * tilt_x, 0), bevel=0.003)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p0 = (sx * (TUB_X0 + BOARD_T), sy * (TUB_Y0 + BOARD_T), TUB_Z0)
            p1 = (sx * (TUB_X1 + BOARD_T), sy * (TUB_Y1 + BOARD_T), TUB_Z1)
            mid = tuple((a + b) / 2 for a, b in zip(p0, p1))
            length = math.dist(p0, p1)
            box(f"corner_{sx}_{sy}", (0.07, 0.07, length), mid, iron, rot=(-sy * tilt_y, sx * tilt_x, 0),
                bevel=0.004)
        for sy in (-1, 1):
            x = sx * 0.2
            box(f"strap_{sx}_{sy}", (0.06, 0.012, slant_y), (x, sy * ((TUB_Y0 + TUB_Y1) / 2 + BOARD_T + 0.006),
                (TUB_Z0 + TUB_Z1) / 2), iron, rot=(-sy * tilt_y, 0, 0), bevel=0.003)
            for k in range(3):
                t = (k + 0.5) / 3
                cylinder(f"rivet_{sx}_{sy}_{k}", 0.009, 0.012, (x, sy * (_lerp(TUB_Y0, TUB_Y1, t) + BOARD_T + 0.01),
                         _lerp(TUB_Z0, TUB_Z1, t)), iron, segments=6, rot=(-sy * (90 - tilt_y), 0, 0), bevel=0)
    # A rust streak or two under the band.
    box("rust_a", (0.05, 0.004, 0.22), (-0.35, -(_lerp(TUB_Y0, TUB_Y1, 0.75) + BOARD_T + 0.003), _lerp(TUB_Z0, TUB_Z1, 0.75)),
        rust, rot=(tilt_y, 0, 0), bevel=0)

    # Undercarriage: two frame beams along x, axle boxes and axles.
    axle_z = FLANGE_R
    for s in (-1, 1):
        box(f"frame_{s}", (2 * TUB_X0 + 0.1, 0.1, 0.12), (0, s * 0.17, TUB_Z0 - 0.06), wood, bevel=0.01)
        for e in (-1, 1):
            box(f"bearing_{s}_{e}", (0.12, 0.1, 0.09), (e * AXLE_X, s * 0.17, axle_z + 0.04), iron, bevel=0.006)
    for e in (-1, 1):
        cylinder(f"axle_{e}", 0.028, GAUGE + 0.1, (e * AXLE_X, -(GAUGE + 0.1) / 2, axle_z), iron, segments=10,
                 rot=(-90, 0, 0), bevel=0)

    # Four flanged wheels: a worn tread, a flange on the inside (toward the cart's centre line) and a hub.
    for e in (-1, 1):
        for s in (-1, 1):
            x, y = e * AXLE_X, s * GAUGE / 2
            cylinder(f"tread_{e}_{s}", WHEEL_R, WHEEL_W, (x, y - WHEEL_W / 2, axle_z), worn, segments=16,
                     rot=(-90, 0, 0), bevel=0.006)
            cylinder(f"flange_{e}_{s}", FLANGE_R, 0.014, (x, y - s * (WHEEL_W / 2 + 0.012), axle_z), iron,
                     r_top=WHEEL_R, segments=16, rot=(s * 90, 0, 0), bevel=0)
            cylinder(f"web_{e}_{s}", WHEEL_R - 0.02, WHEEL_W + 0.012, (x, y - (WHEEL_W + 0.012) / 2, axle_z), iron,
                     segments=16, rot=(-90, 0, 0), bevel=0)
            cylinder(f"hub_{e}_{s}", 0.05, 0.05, (x, y + s * WHEEL_W / 2, axle_z), iron, segments=10,
                     rot=(-s * 90, 0, 0), bevel=0.006)

    # Couplings: an iron eye at each end with a hanging link.
    for e in (-1, 1):
        x = e * (TUB_X0 + 0.05)
        box(f"drawbar_{e}", (0.12, 0.06, 0.05), (x, 0, TUB_Z0 - 0.06), iron, bevel=0.005)
        torus(f"link_{e}", 0.04, 0.01, (x + e * 0.06, 0, TUB_Z0 - 0.12), iron, rot=(90, 0, 0), major=12, minor=6)

    # The load: a bed of broken rock levelled at about half the tub's depth, lumps heaped on it, ore glinting in it.
    fx = _lerp(TUB_X0, TUB_X1, (FILL_Z - TUB_Z0) / h)
    fy = _lerp(TUB_Y0, TUB_Y1, (FILL_Z - TUB_Z0) / h)
    box("ore_bed", (2 * fx - 0.01, 2 * fy - 0.01, FILL_Z - TUB_Z0 - BOARD_T), (0, 0, (FILL_Z + TUB_Z0 + BOARD_T) / 2),
        dark, bevel=0)
    for k in range(15):
        a = rnd.uniform(0, 2 * math.pi)
        d = math.sqrt(rnd.uniform(0, 1))
        x, y = 0.9 * fx * d * math.cos(a), 0.88 * fy * d * math.sin(a)
        r = rnd.uniform(0.06, 0.11)
        z = FILL_Z + 0.09 * (1 - d * d) - r * 0.3
        blob(f"lump_{k}", r, (x, y, z), dark if k % 3 == 0 else rock, squash=(1.2, 1, 0.75), subdiv=1, seed=400 + k,
             jitter=0.3)
    for k in range(12):
        a = rnd.uniform(0, 2 * math.pi)
        d = math.sqrt(rnd.uniform(0, 0.85))
        x, y = 0.8 * fx * d * math.cos(a), 0.75 * fy * d * math.sin(a)
        r = rnd.uniform(0.03, 0.05)
        blob(f"ore_{k}", r, (x, y, FILL_Z + 0.09 * (1 - d * d) + r * 0.2), ore, squash=(1.1, 1, 0.8), subdiv=1,
             seed=440 + k, jitter=0.3)
