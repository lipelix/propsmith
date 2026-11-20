"""A low bramble patch: a mound of dark bramble leaves over a dark tangle, with purple-red thorny canes arching out
over the rim and down to root their tips in the ground, a dead grey cane or two, ripe and unripe blackberries and a few
pale blossoms. It stands alone, round from every side, as forest-floor or road-verge undergrowth."""
import math
import random

from mathutils import Matrix, Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall dimensions (metres), from the description.
W = 1.0  # across, x and y
H = 0.6  # height

MOUND = 0.36  # metres, radius of the leafy mound
CARD_T = 0.004  # metres, leaf card thickness
CARD_L = 0.15  # metres, bramble leaf card length (a leaf of three to five leaflets)
CARD_W = 0.12  # metres, leaf card width
CLUMP_R = 0.17  # metres, radius of a foliage clump under the leaf cards
N_CARDS = 300  # leaf cards over the clumps (about half survive the visibility test)
N_LITTER = 8  # fallen leaves on the ground around the foot
TILT = 32  # degrees, seeded tilt of a card off a clump
LIFT = 0.003  # metres, lowest point of a leaf card above the ground

N_CANES = 9  # arching canes
N_DEAD = 2  # dead grey canes
CANE_R = 0.015  # metres, cane radius at its base
SEGS = 6  # cylinders per cane
N_BERRIES = 16  # blackberry clusters
BERRY_R = 0.017  # metres
N_FLOWERS = 8  # pale five-petal blossoms
FLOWER_R = 0.02  # metres

SHADOW = (0.02, 0.032, 0.012)  # linear RGB, deep shadow green
OLIVE = (0.06, 0.085, 0.028)  # dark bramble olive
LIT = (0.15, 0.18, 0.05)  # lit yellow-green
BRONZE = (0.17, 0.075, 0.03)  # old bronzed leaves
CORE = (0.024, 0.034, 0.013)  # the dark tangle inside
CANE = (0.14, 0.035, 0.04)  # purple-red living canes
DEAD = (0.2, 0.16, 0.11)  # grey-brown dead canes
THORN = (0.25, 0.17, 0.1)  # pale thorns
RIPE = (0.03, 0.012, 0.025)  # ripe blackberries, near black-purple
UNRIPE = (0.3, 0.035, 0.025)  # unripe red berries
PETAL = (0.45, 0.36, 0.34)  # pale pink-white blossoms

SUN = Vector((0.35, -0.45, 0.82)).normalized()  # where the lit rims face
TAU = 2 * math.pi


def _mats():
    m = lambda n, c, **k: material(f"bramble_low_{n}", c, **k)  # noqa: E731
    return {
        "shadow": m("shadow", SHADOW, rough=0.9, vary=0.3, scale=25, crevice=0.6),
        "olive": m("olive", OLIVE, rough=0.85, vary=0.3, scale=25, crevice=0.6),
        "lit": m("lit", LIT, rough=0.8, vary=0.25, scale=25, crevice=0.4),
        "bronze": m("bronze", BRONZE, rough=0.85, vary=0.3, scale=25, crevice=0.5),
        "core": m("core", CORE, rough=0.95, vary=0.2, scale=10, crevice=0.7),
        "cane": m("cane", CANE, rough=0.7, vary=0.25, scale=40, crevice=0.4),
        "dead": m("dead", DEAD, rough=0.9, vary=0.3, scale=40, crevice=0.5),
        "thorn": m("thorn", THORN, rough=0.8, vary=0.2, scale=40, crevice=0.3),
        "ripe": m("ripe", RIPE, rough=0.35, vary=0.2, scale=60, crevice=0.6),
        "unripe": m("unripe", UNRIPE, rough=0.45, vary=0.25, scale=60, crevice=0.5),
        "petal": m("petal", PETAL, rough=0.75, vary=0.15, scale=40, crevice=0.25),
    }



def _point(obj, tail=0.55):
    """Reshape a leaf card box into a pointed leaf: the tip on +x, a blunt end on -x. Stays a closed mesh."""
    for v in obj.data.vertices:
        x, y = v.co.x, v.co.y
        if x > 0 and y > 0:
            v.co.x, v.co.y = x, 0.0
        elif x < 0 < y:
            v.co.x = 0.0
        elif x < 0 and y < 0:
            v.co.x, v.co.y = x * tail, 0.0
        else:
            v.co.x = 0.0
    return obj


def _card(name, centre, normal, length, width, mat, rnd, tilt=TILT):
    """One leaf card lying roughly on the shell, tilted and spun at seeded angles, kept off the ground."""
    q = normal.to_track_quat("Z", "Y").to_matrix().to_4x4()
    m = q @ Matrix.Rotation(math.radians(rnd.uniform(-tilt, tilt)), 4, "X") \
        @ Matrix.Rotation(math.radians(rnd.uniform(-tilt, tilt) * 0.6), 4, "Y") \
        @ Matrix.Rotation(math.radians(rnd.uniform(0, 360)), 4, "Z")
    low = min((m.to_3x3() @ Vector((sx * length / 2, sy * width / 2, 0))).z for sx in (-1, 1) for sy in (-1, 1))
    c = Vector(centre)
    if c.z + low < LIFT:
        c.z = LIFT - low
    obj = _point(box(name, (length, width, CARD_T), tuple(c), mat, bevel=0))
    obj.rotation_euler = m.to_euler()
    return obj


def _shade(normal, rnd):
    light = normal.dot(SUN)
    roll = rnd.random()
    if roll < 0.06:
        return "bronze"
    if normal.z < -0.1 or light < -0.15 or roll < 0.2:
        return "shadow"
    if (light > 0.6 and roll > 0.35) or (normal.z > 0.85 and roll > 0.4):
        return "lit"
    return "olive"


def _fib(n):
    """`n` roughly even unit directions over the sphere."""
    g = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        yield Vector((r * math.cos(g * i), r * math.sin(g * i), z))


def _clump(obj, mats, rnd):
    """Give a foliage clump one material slot per facet: dark underneath and away from the sun, olive on top."""
    slots = ["core", "shadow", "olive"]
    for key in slots[1:]:
        obj.data.materials.append(mats[key])
    obj.data.set_sharp_from_angle(angle=math.radians(80))
    rot = obj.rotation_euler.to_matrix()
    for poly in obj.data.polygons:
        n = rot @ poly.normal
        light = n.dot(SUN) + rnd.uniform(-0.25, 0.25)
        if n.z < -0.3 or light < -0.2:
            slot = 0
        elif light < 0.35:
            slot = 1
        else:
            slot = 2
        poly.material_index = slot
    return obj


def _segment(name, a, b, r, r_top, mat, segments=4):
    """A cylinder from point `a` to point `b`."""
    d = b - a
    obj = cylinder(name, r, d.length, tuple(a), mat, r_top=r_top, segments=segments, bevel=0)
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return obj


def _bezier(p0, p1, p2, t):
    return p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t


def _clamp(p):
    return Vector((max(-W / 2 + 0.03, min(W / 2 - 0.03, p.x)), max(-W / 2 + 0.03, min(W / 2 - 0.03, p.y)),
                   max(0.012, min(H - 0.02, p.z))))


def _cane(prefix, k, rnd, mats, dead):
    """An arching cane: rises out of the mound, arches over its rim and dips its tip to the ground outside."""
    yaw = TAU * (k + rnd.uniform(-0.3, 0.3)) / (N_CANES + N_DEAD)
    out = Vector((math.cos(yaw), math.sin(yaw), 0))
    start = out * MOUND * 0.3 + Vector((0, 0, H * 0.3))
    reach = rnd.uniform(0.38, 0.47) if not dead else rnd.uniform(0.3, 0.4)
    end = out * reach + Vector((0, 0, 0.012))
    ctrl = out * MOUND * rnd.uniform(0.75, 1.0) + Vector((0, 0, H * rnd.uniform(0.95, 1.15)))
    pts = [_clamp(_bezier(start, ctrl, end, i / SEGS)) for i in range(SEGS + 1)]
    mat = mats["dead"] if dead else mats["cane"]
    for i in range(SEGS):
        r0 = CANE_R * (1 - 0.6 * i / SEGS)
        r1 = CANE_R * (1 - 0.6 * (i + 1) / SEGS)
        _segment(f"{prefix}_cane_{k}_{i}", pts[i], pts[i + 1], r0, r1, mat)
    # A few hooked thorns on the arch.
    for i in (2, 4):
        a = pts[i]
        d = (pts[i + 1] - a).normalized()
        side = d.cross(Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 1))).normalized()
        _segment(f"{prefix}_thorn_{k}_{i}", a, a + (side - d * 0.4).normalized() * 0.02, 0.005, 0.0005,
                 mats["thorn"], segments=3)
    tips = []
    if not dead:
        # Leaves along the outer half of the arch, facing up and out.
        for i in (3, 4, 5):
            n = (Vector((0, 0, 1)) + out * 0.5).normalized()
            _card(f"{prefix}_caneleaf_{k}_{i}", pts[i] + n * 0.025, n, CARD_L * 0.85, CARD_W * 0.85,
                  mats["lit" if rnd.random() < 0.45 else "olive"], rnd, tilt=40)
        tips = [pts[2], pts[4]]
    return tips


def _berries(prefix, spots, rnd, mats):
    """Blackberry clusters: a plump drupe each, mostly ripe near-black, some still red."""
    for k, p in enumerate(spots):
        mat = mats["unripe"] if rnd.random() < 0.3 else mats["ripe"]
        r = BERRY_R * rnd.uniform(0.9, 1.25)
        b = cylinder(f"{prefix}_berry_{k}", r, r * 2.2, tuple(_clamp(p) - Vector((0, 0, r))), mat, r_top=r * 0.55,
                     segments=6, bevel=0, rot=(rnd.uniform(140, 220), rnd.uniform(-30, 30), 0))
        b.location = tuple(_clamp(p) + Vector((0, 0, r)))


def _flowers(prefix, spots, rnd, mats):
    for k, (p, n) in enumerate(spots):
        face = (n + Vector((0, 0, 0.6))).normalized()
        f = cylinder(f"{prefix}_flower_{k}", FLOWER_R, 0.005, tuple(p + n * 0.03), mats["petal"],
                     r_top=FLOWER_R * 0.8, segments=5, bevel=0)
        f.rotation_euler = face.to_track_quat("Z", "Y").to_euler()




@prop
def bramble_low():
    prefix = "bramble_low"
    rnd = random.Random(76)
    mats = _mats()

    # The tangle under the leaves: a crown clump and two rings of lumpy clumps, each facet painted by where it faces.
    lumps = [(Vector((0.02, -0.01, H - 0.1 - CLUMP_R * 1.15)), CLUMP_R * 1.15, 1.0)]
    for ring, n, rad, z, r, sz in ((0, 5, 0.14, 0.26, CLUMP_R, 1.0), (1, 8, 0.24, 0.11, CLUMP_R * 0.75, 0.75)):
        for i in range(n):
            a = TAU * (i + 0.5 * ring + rnd.uniform(-0.15, 0.15)) / n
            rr = r * rnd.uniform(0.9, 1.1)
            c = Vector((math.cos(a) * rad, math.sin(a) * rad, max(z, rr * sz * 1.16)))
            lumps.append((c, rr, sz))
    box(f"{prefix}_core", (MOUND * 1.1, MOUND * 1.1, 0.2), (0, 0, 0.11), mats["core"], rot=(0, 0, 20), bevel=0)
    for k, (c, r, sz) in enumerate(lumps):
        _clump(blob(f"{prefix}_clump_{k}", r, tuple(c), mats["core"], squash=(1, 1, sz), subdiv=1, seed=k + 40,
                    jitter=0.14), mats, rnd)

    # Leaf cards over the clumps' outer surfaces, none buried inside a neighbour.
    def outside(p, k):
        for j, (c2, r2, sz2) in enumerate(lumps):
            q = p - c2
            if j != k and (q.x / r2) ** 2 + (q.y / r2) ** 2 + (q.z / (r2 * sz2)) ** 2 < 0.85:
                return False
        return p.z > 0.02

    tops = []
    per = N_CARDS / len(lumps)
    i = 0
    for k, (c, r, sz) in enumerate(lumps):
        twist = Matrix.Rotation(rnd.uniform(0, TAU), 3, "Z")
        for d in [twist @ d for d in _fib(round(per * 1.9))]:
            p = c + Vector((d.x * r, d.y * r, d.z * r * sz)) * rnd.uniform(1.04, 1.16)
            if not outside(p, k):
                continue
            n = Vector((d.x, d.y, d.z / sz)).normalized()
            key = _shade(n, rnd)
            s = rnd.uniform(0.8, 1.15)
            _card(f"{prefix}_leaf_{i}", p, n, CARD_L * s, CARD_W * s, mats[key], rnd, tilt=45)
            if key == "lit" and n.z > 0.1:
                tops.append((p, n))
            i += 1

    # Fallen leaves lying flat around the foot.
    for i in range(N_LITTER):
        a = TAU * (i + rnd.uniform(-0.3, 0.3)) / N_LITTER
        d = rnd.uniform(0.3, 0.4)
        _point(box(f"{prefix}_litter_{i}", (CARD_L * 0.8, CARD_W * 0.8, CARD_T), (math.cos(a) * d, math.sin(a) * d,
                   CARD_T / 2), mats["bronze" if rnd.random() < 0.5 else "shadow"], rot=(0, 0, rnd.uniform(0, 360)),
                   bevel=0))

    # Arching canes, living and dead, with berries along them and on the lit top.
    spots = []
    for k in range(N_CANES + N_DEAD):
        spots += _cane(prefix, k, rnd, mats, dead=k >= N_CANES)
    picks = random.Random(9).sample(range(len(tops)), max(0, min(N_BERRIES - len(spots) // 2, len(tops))))
    berries = spots[::2] + [tops[j][0] + tops[j][1] * 0.04 for j in picks]
    _berries(prefix, berries, rnd, mats)
    rest = [tops[j] for j in range(len(tops)) if j not in picks]
    _flowers(prefix, random.Random(13).sample(rest, min(N_FLOWERS, len(rest))), rnd, mats)
