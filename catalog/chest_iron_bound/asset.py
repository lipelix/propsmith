"""A heavy dark chest wrapped in iron, closed: a body of dark plank courses on an iron-shod plinth, a low domed lid,
iron bands round the body and lid, straps over the dome, studs and corner plates, side ring handles, and a round lock
plate on the front (-y) with a raised sigil (a ring round a five-pointed star) round the keyhole, under a hasp."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall dimensions (metres): about 1 x 0.7 x 0.7 m.
W, D, H = 0.98, 0.66, 0.68  # lid width (x), lid depth (y), total height (z)
BW, BD = W - 0.02, D - 0.02  # body, inset under the lid band
PLINTH_H = 0.06  # iron-shod base skirt
BODY_H = 0.44  # top of the body
BODY_PLANKS = 4
BAND_H = 0.08  # straight lid band below the dome
RIM_Z = BODY_H + BAND_H  # where the dome starts
SAG = H - RIM_Z  # dome rise
R = (D * D / 4 + SAG * SAG) / (2 * SAG)  # dome radius from chord D and rise SAG
CZ = H - R  # dome axis height
TH_MAX = math.asin(D / 2 / R)  # half angle of the dome
LID_PLANKS = 6
LID_T = 0.12  # radial depth of a dome plank

IRON_T = 0.008  # band and strap thickness
CORNER_W = 0.07
STRAP_W = 0.06
STRAP_X = (-0.3, 0.3)
HOOP_Z = (0.18, 0.36)  # horizontal bands round the body
STUD_R = 0.012
PLATE_R = 0.11  # sigil lock plate
PLATE_Z = 0.3
SIGIL_R = 0.082

WOOD = (0.1, 0.062, 0.036)  # linear RGB: dark stained oak
WOOD_OLD = (0.08, 0.052, 0.032)
IRON = (0.042, 0.041, 0.04)
IRON_WORN = (0.13, 0.12, 0.105)
RUST = (0.09, 0.055, 0.035)
HOLE = (0.04, 0.04, 0.042)


@prop
def chest_iron_bound():
    rnd = random.Random(642)
    wood = material("chest_iron_bound_plank", WOOD, vary=0.28, scale=14)
    wood_old = material("chest_iron_bound_plank_old", WOOD_OLD, vary=0.3, scale=14)
    iron = material("chest_iron_bound_iron", IRON, rough=0.55, vary=0.22, scale=20, metal=0.6)
    worn = material("chest_iron_bound_iron_worn", IRON_WORN, rough=0.4, vary=0.2, scale=18, metal=0.7)
    rust = material("chest_iron_bound_rust", RUST, rough=0.8, vary=0.3, scale=24, metal=0.3)
    hole = material("chest_iron_bound_hole", HOLE, vary=0.05, scale=10)

    def plate(name, size, at, rot=(0, 0, 0)):
        """A thin iron plate: a one-segment bevel is enough to catch the light."""
        obj = box(name, size, at, iron, rot=rot, bevel=0.003)
        obj.modifiers["bevel"].segments = 1
        return obj

    def stud(name, at, rot=(90, 0, 0)):
        """A domed rivet head; the default `rot` faces it to -y."""
        cylinder(name, STUD_R, 0.01, at, rnd.choice((worn, iron)), r_top=STUD_R * 0.5, rot=rot, segments=8,
                 bevel=0)

    # Plinth: an iron-shod skirt the body stands on.
    box("plinth", (BW + 0.02, BD + 0.02, PLINTH_H), (0, 0, PLINTH_H / 2), iron, bevel=0.008)
    # Body: horizontal plank courses above the plinth.
    ph = (BODY_H - PLINTH_H) / BODY_PLANKS
    for i in range(BODY_PLANKS):
        box(f"body_plank_{i}", (BW - rnd.uniform(0, 0.006), BD - rnd.uniform(0, 0.006), ph),
            (rnd.uniform(-0.002, 0.002), rnd.uniform(-0.002, 0.002), PLINTH_H + ph * (i + 0.5)),
            rnd.choice((wood, wood, wood_old)), bevel=0.01)

    # Lid: a straight band, then a low dome of planks running along x, closed at the ends by two end caps.
    box("lid_band", (W, D, BAND_H), (0, 0, BODY_H + BAND_H / 2), wood, bevel=0.012)
    step = 2 * TH_MAX / LID_PLANKS
    pw = 2 * R * math.tan(step / 2)
    angles = [-TH_MAX + step * (i + 0.5) for i in range(LID_PLANKS)]
    for i, th in enumerate(angles):
        r = R - LID_T / 2 - rnd.uniform(0, 0.003)
        box(f"lid_plank_{i}", (W - 0.03 - rnd.uniform(0, 0.006), pw, LID_T), (0, r * math.sin(th), CZ + r * math.cos(th)),
            rnd.choice((wood, wood, wood_old)), rot=(-math.degrees(th) + rnd.uniform(-0.4, 0.4), 0, 0), bevel=0.01)
    # Iron lid edges: a band along the dome's end on each side, as a row of short plates following the curve.
    for sx in (-1, 1):
        for i, th in enumerate(angles):
            r = R + IRON_T / 2 - 0.002
            plate(f"lid_edge_{sx}_{i}", (0.05, pw + 0.004, IRON_T), (sx * (W / 2 - 0.035), r * math.sin(th),
                CZ + r * math.cos(th)), rot=(-math.degrees(th), 0, 0))

    # Corner bands: an L of two legs on every vertical corner of the body and the lid band, with studs.
    for sx in (-1, 1):
        for sy in (-1, 1):
            for part, (w, d, z0, z1) in (("body", (BW, BD, PLINTH_H, BODY_H)), ("band", (W, D, BODY_H, RIM_Z))):
                h, zc = z1 - z0, (z0 + z1) / 2
                plate(f"corner_{part}_{sx}_{sy}_y", (CORNER_W, IRON_T, h),
                    (sx * (w / 2 - CORNER_W / 2 + 0.002), sy * (d / 2 + IRON_T / 2), zc))
                plate(f"corner_{part}_{sx}_{sy}_x", (IRON_T, CORNER_W, h),
                    (sx * (w / 2 + IRON_T / 2), sy * (d / 2 - CORNER_W / 2 + 0.002), zc))

    # Horizontal hoops round the body: four plates per hoop, one per face.
    for k, z in enumerate(HOOP_Z):
        for sy in (-1, 1):
            plate(f"hoop_{k}_y{sy}", (BW + 2 * IRON_T, IRON_T, 0.05), (0, sy * (BD / 2 + IRON_T / 2), z))
        for sx in (-1, 1):
            plate(f"hoop_{k}_x{sx}", (IRON_T, BD + 2 * IRON_T, 0.05), (sx * (BW / 2 + IRON_T / 2), 0, z))

    # Two straps up the front, over the dome and down the back, studded on the front.
    fy = -(BD / 2 + IRON_T)
    for k, x in enumerate(STRAP_X):
        for sy in (-1, 1):
            plate(f"strap_body_{k}_{sy}", (STRAP_W, IRON_T, BODY_H - PLINTH_H),
                (x, sy * (BD / 2 + 1.5 * IRON_T), (BODY_H + PLINTH_H) / 2))
            plate(f"strap_band_{k}_{sy}", (STRAP_W, IRON_T, BAND_H),
                (x, sy * (D / 2 + IRON_T / 2), BODY_H + BAND_H / 2))
        for i, th in enumerate(angles):
            r = R + IRON_T / 2 - 0.001
            plate(f"strap_lid_{k}_{i}", (STRAP_W, pw + 0.004, IRON_T), (x, r * math.sin(th), CZ + r * math.cos(th)),
                  rot=(-math.degrees(th), 0, 0))
            if i in (1, 3, 4):
                r2 = R + IRON_T
                stud(f"stud_lid_{k}_{i}", (x, r2 * math.sin(th), CZ + r2 * math.cos(th)), (-math.degrees(th), 0, 0))
        for j, z in enumerate((0.11, 0.27, 0.41)):
            stud(f"stud_front_{k}_{j}", (x, fy - IRON_T, z))
        stud(f"stud_band_{k}", (x, -(D / 2 + IRON_T), BODY_H + BAND_H / 2))

    # Side ring handles on the x ends.
    for sx in (-1, 1):
        plate(f"handle_plate_{sx}", (0.012, 0.1, 0.06), (sx * (BW / 2 + IRON_T + 0.006), 0, 0.33))
        torus(f"handle_ring_{sx}", 0.05, 0.009, (sx * (BW / 2 + IRON_T + 0.018), 0, 0.33 - 0.045), worn,
              rot=(90, 0, 90), major=16, minor=6)

    # Front: a round lock plate with a raised sigil round the keyhole, and a hasp from the lid band over it.
    py = fy - IRON_T  # front face of the hoops and straps
    cylinder("lock_plate", PLATE_R, 0.014, (0, py + 0.004, PLATE_Z), rust, rot=(90, 0, 0), segments=24, bevel=0.004)
    face = py - 0.01
    ring = torus("sigil_ring", SIGIL_R, 0.006, (0, face, PLATE_Z), worn, rot=(90, 0, 0), major=28, minor=6)
    ring.scale = (1, 1, 0.6)
    pts = [(SIGIL_R * math.cos(math.pi / 2 + 2 * math.pi * i / 5), SIGIL_R * math.sin(math.pi / 2 + 2 * math.pi * i / 5))
           for i in range(5)]
    for i in range(5):
        (ax, az), (bx, bz) = pts[i], pts[(i + 2) % 5]
        length = math.hypot(bx - ax, bz - az)
        ang = math.degrees(math.atan2(bz - az, bx - ax))
        box(f"sigil_star_{i}", (length, 0.006, 0.01), ((ax + bx) / 2, face, PLATE_Z + (az + bz) / 2), worn,
            rot=(0, -ang, 0), bevel=0.001)
    cylinder("keyhole_boss", 0.026, 0.008, (0, face + 0.002, PLATE_Z), iron, rot=(90, 0, 0), segments=12,
             bevel=0.002)
    cylinder("keyhole", 0.009, 0.004, (0, face - 0.0045, PLATE_Z + 0.006), hole, rot=(90, 0, 0), segments=8, bevel=0)
    box("keyhole_slot", (0.007, 0.004, 0.02), (0, face - 0.0045, PLATE_Z - 0.008), hole, bevel=0)
    hy = -(D / 2 + IRON_T)
    plate("hasp", (0.07, IRON_T, 0.12), (0, hy - 0.004, RIM_Z - 0.07))
    stud("hasp_stud", (0, hy - 0.008, RIM_Z - 0.03))
    torus("hasp_loop", 0.022, 0.006, (0, hy - 0.012, RIM_Z - 0.13), worn, rot=(0, 90, 0), major=12, minor=6)
