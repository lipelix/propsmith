"""A fallen mossy tree trunk lying on the forest floor: ridged dark bark, a weathered cut end with growth rings at the
thick end (+x), a splintered break at the thin end, broken branch stubs, and moss cushions along its top."""
import math
import random

from mathutils import Quaternion, Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall dimensions (metres), from the description.
L = 2.75  # trunk length between the cut end and the break (splinters reach further)
R_THICK, R_THIN = 0.28, 0.21  # trunk radius at the thick (+x) end and at the thin (-x) break
SPLINTER_L = 0.16  # how far the longest splinters stick out of the break
STUB_L = (0.1, 0.24)  # length range of a broken branch stub beyond the bark
MOSS_R = 0.15  # radius of a moss cushion
CARD = 0.032  # moss leaf card size
CARD_T = 0.004

BARK = (0.085, 0.062, 0.043)
BARK_DARK = (0.055, 0.042, 0.032)
BARK_GREY = (0.12, 0.1, 0.08)  # weathered, lichen-grey bark
CUT = (0.25, 0.2, 0.15)  # weathered grey-brown cut face
RING = (0.16, 0.12, 0.085)
WOOD = (0.36, 0.27, 0.16)  # fresher wood inside a break
ROT = (0.12, 0.08, 0.05)  # darker rotten wood
MOSS_DEEP = (0.035, 0.055, 0.016)
MOSS_OLIVE = (0.1, 0.13, 0.035)
MOSS_LIT = (0.21, 0.25, 0.07)

LIFT = 0.0  # the trunk underside rests on the ground
TILT = math.degrees(math.asin((R_THICK - R_THIN) / L))  # the axis rises towards the thick end: the underside is level


def _mats():
    return {
        "bark": material("log_fallen_bark", BARK, rough=1.0, vary=0.45, scale=26, crevice=0.8),
        "dark": material("log_fallen_bark_dark", BARK_DARK, rough=1.0, vary=0.4, scale=22, crevice=0.8),
        "grey": material("log_fallen_bark_grey", BARK_GREY, rough=1.0, vary=0.45, scale=30, crevice=0.75),
        "cut": material("log_fallen_cut", CUT, rough=0.95, vary=0.3, scale=11),
        "ring": material("log_fallen_ring", RING, vary=0.2, scale=12),
        "wood": material("log_fallen_wood", WOOD, rough=0.95, vary=0.3, scale=18, crevice=0.6),
        "rot": material("log_fallen_rot", ROT, rough=1.0, vary=0.35, scale=14, crevice=0.7),
        "deep": material("log_fallen_moss_deep", MOSS_DEEP, rough=0.95, vary=0.3, scale=40, crevice=0.6),
        "olive": material("log_fallen_moss_olive", MOSS_OLIVE, rough=0.95, vary=0.3, scale=40, crevice=0.5),
        "lit": material("log_fallen_moss_lit", MOSS_LIT, rough=0.9, vary=0.25, scale=40, crevice=0.35),
    }


def _axis(t):
    """Point on the trunk axis and its radius at fraction `t` from the thin end (0) to the thick end (1)."""
    a = math.radians(TILT)
    x = -L / 2 + t * L * math.cos(a)
    r = R_THIN + (R_THICK - R_THIN) * t
    return Vector((x, 0.0, LIFT + R_THIN + t * L * math.sin(a))), r


def _surface(t, phi):
    """Point and outward normal on the bark at fraction `t`, `phi` degrees round from the top towards +y."""
    c, r = _axis(t)
    p = math.radians(phi)
    n = Vector((0.0, math.sin(p), math.cos(p)))
    return c + n * r, n


def _rot_to(d):
    """Euler (degrees) turning local +z onto direction `d` (for `cylinder`)."""
    d = d.normalized()
    tilt = math.degrees(math.acos(max(-1.0, min(1.0, d.z))))
    yaw = math.degrees(math.atan2(d.x, -d.y))
    return (tilt, 0, yaw)


def _point(obj):
    """Reshape a card box into a pointed leaf (a rhombus): same vertices and faces, still closed."""
    for v in obj.data.vertices:
        x, y = v.co.x, v.co.y
        if (x > 0) == (y > 0):
            v.co.y = 0.0
        else:
            v.co.x = 0.0
    return obj


def _card(name, size, at, facing, spin, mat):
    """A thin bevel-free leaf card whose broad face looks along `facing`, turned `spin` degrees about it."""
    obj = _point(box(name, (size * 1.2, size * 0.9, CARD_T), at, mat, bevel=0))
    q = facing.normalized().to_track_quat("Z", "Y") @ Quaternion((0, 0, 1), math.radians(spin))
    obj.rotation_euler = q.to_euler("XYZ")
    return obj


def _cushion(name, t, phi, rc, mats, rnd, cards):
    """A moss cushion hugging the bark at (`t`, `phi`): a squashed deep-green core and lit cards round it."""
    hit, n = _surface(t, phi)
    core = blob(f"{name}_core", rc, hit + n * (rc * 0.12), mats["olive"], squash=(1.3, 1.0, 0.45), subdiv=1,
                seed=rnd.randrange(1000), jitter=0.2)
    core.rotation_euler = n.to_track_quat("Z", "X").to_euler("XYZ")
    _, r = _axis(t)
    for i in range(cards):
        a = math.radians(137.5 * i + rnd.uniform(-15, 15))
        rho = rc * math.sqrt((i + 0.5) / cards) * rnd.uniform(0.8, 1.1)
        dt = rho * math.cos(a) * 1.3 / L
        dphi = math.degrees(rho * math.sin(a) / r)
        loc, nn = _surface(min(max(t + dt, 0.02), 0.98), phi + dphi)
        edge = rho / rc
        lift = rc * 0.55 * (1 - 0.8 * edge * edge)
        out = Vector((math.cos(a), math.sin(a) * nn.z, -math.sin(a) * nn.y)) * (0.15 + 0.4 * edge)
        if edge < 0.6:
            mat = mats["lit"] if rnd.random() < 0.7 else mats["olive"]
        else:
            mat = rnd.choice([mats["lit"], mats["olive"], mats["deep"]])
        _card(f"{name}_card_{i}", CARD * rnd.uniform(0.8, 1.25), loc + nn * lift, nn + out, rnd.uniform(0, 360), mat)


def _stub(name, t, phi, lean, length, r0, mats, rnd):
    """A broken branch stub leaving the bark at (`t`, `phi`), leaning `lean` degrees towards the thin end, with a
    jagged pale break at its tip."""
    base, n = _surface(t, phi)
    lr = math.radians(lean)
    d = (n * math.cos(lr) + Vector((-math.sin(lr), 0, 0))).normalized()
    start = base - n * 0.06
    total = length + 0.06
    rot = _rot_to(d)
    cylinder(name, r0, total, start, mats["bark"], r_top=r0 * 0.78, segments=8, rot=rot, bevel=0.006)
    blob(f"{name}_collar", r0 * 1.35, base + n * 0.005, mats["dark"], squash=(1, 1, 0.55), subdiv=1,
         seed=rnd.randrange(1000), jitter=0.12).rotation_euler = n.to_track_quat("Z", "X").to_euler("XYZ")
    tip = start + d * total
    rt = r0 * 0.78
    # the break: a pale stump face and two or three splinters
    cylinder(f"{name}_break", rt * 0.85, 0.012, tip - d * 0.008, mats["wood"], segments=8, rot=rot, bevel=0)
    for k in range(rnd.choice((2, 3))):
        a = math.radians(120 * k + rnd.uniform(-30, 30))
        side = Vector((0, 0, 1)).cross(d)
        if side.length < 0.1:
            side = Vector((1, 0, 0))
        side.normalize()
        up = d.cross(side)
        off = (side * math.cos(a) + up * math.sin(a)) * rt * 0.45
        sd = (d + off.normalized() * 0.15).normalized()
        cylinder(f"{name}_splinter_{k}", rt * 0.42, rnd.uniform(0.04, 0.08), tip + off - d * 0.01,
                 mats["wood"] if k else mats["grey"], r_top=0.002, segments=4, rot=_rot_to(sd), bevel=0)


def _ridges(rnd, mats):
    """Long ragged bark ridges running along the trunk, none on the underside."""
    a = math.radians(TILT)
    n = 18
    for i in range(n * 2):
        phi = 360 * (i % n) / n + rnd.uniform(-7, 7) + (360 / n / 2 if i >= n else 0)
        if abs((phi + 180) % 360 - 180) > 125:
            continue  # the underside touches the ground
        t0 = rnd.uniform(0.02, 0.5)
        t1 = min(t0 + rnd.uniform(0.15, 0.45), 0.97)
        tm = (t0 + t1) / 2
        p, nrm = _surface(tm, phi)
        p += nrm * 0.004
        length = (t1 - t0) * L
        mat = mats["dark"] if i % 3 == 0 else mats["grey"] if i % 5 == 1 else mats["bark"]
        obj = box(f"log_ridge_{i}", (length, rnd.uniform(0.03, 0.05), rnd.uniform(0.016, 0.026)), p, mat, bevel=0)
        q = Quaternion((0, 1, 0), -a) @ Quaternion((1, 0, 0), math.radians(phi))
        q = q @ Quaternion((0, 0, 1), math.radians(rnd.uniform(-1.5, 1.5)))
        obj.rotation_euler = q.to_euler("XYZ")


def _cut_end(mats, rnd):
    """The thick end: a weathered sawn face with growth rings and a dark heart, facing +x."""
    c, r = _axis(1.0)
    a = math.radians(TILT)
    d = Vector((math.cos(a), 0, math.sin(a)))
    rot = _rot_to(d)
    cylinder("log_cut_face", r - 0.018, 0.03, c - d * 0.022, mats["cut"], segments=20, rot=rot, bevel=0.008)
    for i, rr in enumerate((0.2, 0.155, 0.11, 0.07)):
        torus(f"log_ring_{i}", rr * r / 0.28, 0.0045, c + d * 0.008 + Vector((0, 0.004 * i, -0.003 * i)), mats["ring"],
              rot=rot, major=20, minor=4)
    cylinder("log_heart", 0.032, 0.006, c + d * 0.004 + Vector((0, 0.015, -0.01)), mats["rot"], segments=10, rot=rot,
             bevel=0)
    for k in range(3):
        ang = rnd.uniform(0, 360)
        ln = rnd.uniform(0.09, 0.15)
        obj = box(f"log_check_{k}", (0.012, ln, 0.009), c + d * 0.006, mats["rot"], bevel=0)
        q = Quaternion((0, 1, 0), -a) @ Quaternion((1, 0, 0), math.radians(ang))
        obj.rotation_euler = q.to_euler("XYZ")
        obj.location += (q @ Vector((0, 1, 0))) * (0.05 + ln / 2)


def _break_end(mats, rnd):
    """The thin end: a jagged break of splinters and rotten wood pointing -x."""
    c, r = _axis(0.0)
    a = math.radians(TILT)
    d = Vector((-math.cos(a), 0, -math.sin(a)))
    blob("log_break_core", r * 0.88, c + d * 0.01, mats["rot"], squash=(0.35, 1, 1), subdiv=2, seed=7, jitter=0.08)
    for k in range(9):
        ang = math.radians(40 * k + rnd.uniform(-12, 12))
        rr = r * rnd.uniform(0.35, 0.8)
        off = Vector((0, rr * math.sin(ang), rr * math.cos(ang)))
        if c.z + off.z < 0.06:
            off.z = 0.06 - c.z + rnd.uniform(0, 0.03)
        ln = SPLINTER_L * rnd.uniform(0.45, 1.0)
        sd = (d + off.normalized() * rnd.uniform(0.05, 0.25)).normalized()
        cylinder(f"log_splinter_{k}", rnd.uniform(0.035, 0.06), ln, c + off - d * 0.02,
                 mats["wood"] if k % 3 else mats["grey"], r_top=0.003, segments=5, rot=_rot_to(sd), bevel=0)


@prop
def log_fallen():
    rnd = random.Random(23)
    mats = _mats()
    # The trunk lies along x, tapering from the thick cut end (+x) to the thin break (-x), its underside on the ground.
    cylinder("log_trunk", R_THIN, L, (-L / 2, 0, R_THIN + LIFT), mats["bark"], r_top=R_THICK, segments=20,
             rot=(0, 90 - TILT, 0), bevel=0.012)
    _ridges(rnd, mats)
    # Knots and a few patches where the bark has fallen away, showing grey weathered wood.
    for i, (t, phi) in enumerate(((0.22, -70), (0.5, -85), (0.62, 75), (0.36, 95))):
        p, n = _surface(t, phi)
        blob(f"log_knot_{i}", 0.05, p, mats["dark"], squash=(1.4, 1, 1), subdiv=1, seed=30 + i, jitter=0.15)
    for i, (t, phi, ln) in enumerate(((0.42, -75, 0.42), (0.75, -95, 0.3))):
        p, n = _surface(t, phi)
        obj = box(f"log_bare_{i}", (ln, 0.13, 0.03), p + n * 0.006, mats["grey"], bevel=0.01)
        q = Quaternion((0, 1, 0), -math.radians(TILT)) @ Quaternion((1, 0, 0), math.radians(phi))
        obj.rotation_euler = q.to_euler("XYZ")
    _cut_end(mats, rnd)
    _break_end(mats, rnd)

    # Broken branch stubs: two up-and-sideways on the far side, one on the near side, one short upright snag.
    for i, (t, phi, lean, ln, r0) in enumerate((
        (0.3, -50, 25, 0.3, 0.075),
        (0.55, 50, 30, 0.28, 0.07),
        (0.7, -15, 15, 0.12, 0.06),
        (0.16, 25, 20, 0.15, 0.05),
        (0.86, 60, 35, 0.14, 0.055),
    )):
        _stub(f"log_stub_{i}", t, phi, lean, ln, r0, mats, rnd)

    # Moss cushions along the top and creeping down the shoulders.
    for i, (t, phi, s) in enumerate((
        (0.12, 10, 1.0), (0.24, -25, 0.9), (0.4, 15, 1.1), (0.48, -40, 0.75), (0.6, 5, 1.0),
        (0.78, -20, 0.95), (0.92, 20, 0.8), (0.34, 45, 0.7), (0.66, 40, 0.75), (0.88, -48, 0.6),
    )):
        _cushion(f"log_moss_{i}", t, phi, MOSS_R * s, mats, rnd, 18)
