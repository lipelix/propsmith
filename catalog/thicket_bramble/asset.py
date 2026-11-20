"""A dense, impassable bramble thicket: a hedge-like mass of dark bramble leaves over a near-black tangle, with
purple-red thorny canes arching out of it and drooping back, a few dead grey canes, clusters of ripe and unripe
blackberries and a scatter of pale blossoms. Its cross-section is the same at both ends and its lumps repeat every
1.5 m in x, so thickets set side by side along x read as one continuous hedge."""
import math
import random

from mathutils import Matrix, Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall dimensions (metres), from the description.
L = 1.5  # length along x, the repeat period of the hedge
W = 1.5  # depth across y
H = 1.6  # height

HALF_X = L / 2 - 0.01  # leaf cards stop just inside the end planes
SIDE = W / 2 - 0.2  # half-width of the leaf shell at its widest
TOP = H - 0.17  # height of the leaf shell's crown
EXP_Y, EXP_Z = 0.45, 0.4  # superellipse exponents of the cross-section: lower is boxier

CARD_T = 0.004  # metres, leaf card thickness
CARD_L = 0.2  # metres, bramble leaf card length (a leaf of three to five leaflets)
CARD_W = 0.16  # metres, leaf card width
CLUMP_R = 0.25  # metres, radius of a foliage clump under the leaf cards
FOOT_R = 0.2  # metres, radius of a low clump along the foot
N_CARDS = 300  # leaf cards over the clumps (about half survive the visibility test)
N_LITTER = 10  # fallen leaves on the ground along the foot
TILT = 32  # degrees, seeded tilt of a card off the shell
LIFT = 0.003  # metres, lowest point of a leaf card above the ground

N_CANES = 14  # arching canes
N_DEAD = 3  # dead grey canes
CANE_R = 0.017  # metres, cane radius at its base
SEGS = 6  # cylinders per cane
N_BERRIES = 24  # blackberry clusters
BERRY_R = 0.019  # metres
N_FLOWERS = 12  # pale five-petal blossoms
FLOWER_R = 0.022  # metres

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
    m = lambda n, c, **k: material(f"thicket_bramble_{n}", c, **k)  # noqa: E731
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


class Shell:
    """The leaf shell: a boxy superellipse cross-section in y-z swept along x, bulged by lumps that repeat every L."""

    def __init__(self, rnd):
        # Integer wave numbers in x keep the lumps periodic in L, so the ends of neighbouring thickets match.
        self.waves = [(rnd.choice((1, 2, 3)) * rnd.choice((-1, 1)), rnd.randint(1, 4), rnd.uniform(0, TAU),
                       rnd.uniform(0.03, 0.06)) for _ in range(6)]

        # Arc length along the cross-section, so cards spread evenly over the sides and the crown.
        ts = [i / 200 for i in range(201)]
        pts = [self._raw(t) for t in ts]
        acc = [0.0]
        for a, b in zip(pts, pts[1:]):
            acc.append(acc[-1] + (b - a).length)
        self._ts, self._acc = ts, acc

    @staticmethod
    def _raw(t):
        th = math.pi * t
        c, s = math.cos(th), max(math.sin(th), 0.0)
        return Vector((-math.copysign(abs(c) ** EXP_Y, c) * SIDE, s ** EXP_Z * TOP))

    def even(self, u):
        """The profile parameter `t` at the fraction `u` of the cross-section's length."""
        target = u * self._acc[-1]
        for i in range(1, len(self._acc)):
            if self._acc[i] >= target:
                f = (target - self._acc[i - 1]) / max(self._acc[i] - self._acc[i - 1], 1e-9)
                return self._ts[i - 1] + f * (self._ts[i] - self._ts[i - 1])
        return 1.0

    def bulge(self, x, t):
        return 1 + sum(a * math.sin(TAU * k * x / L + j * t * math.pi + ph) for k, j, ph, a in self.waves)

    def point(self, x, t, scale=1.0):
        """Point and outward normal at `x` and profile parameter `t` (0 is the -y foot, 1 the +y foot)."""
        th = math.pi * t
        c, s = math.cos(th), max(math.sin(th), 0.0)
        y = -math.copysign(abs(c) ** EXP_Y, c) * SIDE
        z = s ** EXP_Z * TOP
        b = self.bulge(x, t) * scale
        # Swell from a centre low in the mass, so the sides and the crown both bulge.
        centre = Vector((x, 0, TOP * 0.35))
        p = centre + (Vector((x, y, z)) - centre) * b
        p.z = max(p.z, 0.0)
        # Normal of the superellipse |y/SIDE|^(2/EXP_Y) + (z/TOP)^(2/EXP_Z) = 1.
        ny = math.copysign(abs(y / SIDE) ** (2 / EXP_Y - 1), y) / SIDE / EXP_Y
        nz = (max(z, 1e-4) / TOP) ** (2 / EXP_Z - 1) / TOP / EXP_Z
        n = Vector((0, ny, nz)).normalized()
        return p, n


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
    return Vector((max(-HALF_X + 0.03, min(HALF_X - 0.03, p.x)), max(-W / 2 + 0.03, min(W / 2 - 0.03, p.y)),
                   max(0.02, min(H - 0.02, p.z))))


def _cane(prefix, k, shell, rnd, mats, dead):
    """An arching cane: rises out of the tangle, arches past the leaves and droops back onto the shell."""
    x0 = rnd.uniform(-HALF_X + 0.15, HALF_X - 0.15)
    t0 = rnd.uniform(0.12, 0.88)
    start, _ = shell.point(x0, t0, 0.6)
    x2 = max(-HALF_X + 0.06, min(HALF_X - 0.06, x0 + rnd.uniform(-0.45, 0.45)))
    t2 = min(0.97, max(0.03, t0 + rnd.choice((-1, 1)) * rnd.uniform(0.15, 0.3)))
    end, n_end = shell.point(x2, t2, 1.02)
    mid_p, mid_n = shell.point((x0 + x2) / 2, (t0 + t2) / 2, 1.0)
    ctrl = _clamp(mid_p + mid_n * rnd.uniform(0.3, 0.5) + Vector((0, 0, rnd.uniform(0.05, 0.18))))
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
        _segment(f"{prefix}_thorn_{k}_{i}", a, a + (side - d * 0.4).normalized() * 0.022, 0.005, 0.0005,
                 mats["thorn"], segments=3)
    tips = []
    if not dead:
        # Leaves on short stalks along the outer half of the arch.
        for i in (3, 5, 6):
            d = (pts[min(i, SEGS)] - pts[i - 1]).normalized()
            up = (Vector((0, 0, 1)) - d * d.z).normalized()
            out = (up + n_end * 0.6).normalized()
            _card(f"{prefix}_caneleaf_{k}_{i}", pts[i] + out * 0.03, out, CARD_L * 0.85, CARD_W * 0.85,
                  mats["lit" if rnd.random() < 0.45 else "olive"], rnd, tilt=40)
        tips = [pts[SEGS - 1], pts[SEGS - 2], pts[3]]
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
def thicket_bramble():
    prefix = "thicket_bramble"
    rnd = random.Random(67)
    mats = _mats()
    shell = Shell(rnd)

    # The tangle under the leaves: lumpy clumps that run the full length (so neighbours join with no light gap), each
    # facet painted shadow, olive or lit by where it faces, so the mass reads as foliage between the cards.
    lumps = []
    for x in (-0.47, -0.16, 0.16, 0.47):
        r = CLUMP_R * (0.93 if abs(x) > 0.3 else 1.05)
        for u in (0.08, 0.3, 0.5, 0.7, 0.92):
            c, _ = shell.point(x * rnd.uniform(0.95, 1.0), shell.even(u), 0.74)
            c.z = max(c.z, r * 1.25)
            lumps.append((c, r * rnd.uniform(0.95, 1.05), 1.1))
    # Low clumps along the foot, so the base sits on undergrowth with no gap.
    for side in (-1, 1):
        for x in (-0.55, -0.27, 0.0, 0.27, 0.55):
            r = FOOT_R * rnd.uniform(0.9, 1.1)
            lumps.append((Vector((x + rnd.uniform(-0.04, 0.04), side * (SIDE - r * 0.6), r * 0.95 * 1.16)), r, 0.95))
    # A dark block inside the lumps so no light shows through the hedge between them.
    box(f"{prefix}_core", (L - 0.36, SIDE * 1.2, TOP * 0.5), (0, 0, TOP * 0.25 + 0.02), mats["core"], bevel=0)
    for k, (c, r, sz) in enumerate(lumps):
        _clump(blob(f"{prefix}_clump_{k}", r, tuple(c), mats["core"], squash=(1, 1, sz), subdiv=1, seed=k,
                    jitter=0.14), mats, rnd)

    # Leaf cards over the clumps' outer surfaces, none buried inside a neighbour or past the end planes.
    def outside(p, k):
        for j, (c2, r2, sz2) in enumerate(lumps):
            q = p - c2
            if j != k and (q.x / r2) ** 2 + (q.y / r2) ** 2 + (q.z / (r2 * sz2)) ** 2 < 0.85:
                return False
        return abs(p.x) < HALF_X - 0.03 and p.z > 0.02

    tops = []
    per = N_CARDS / len(lumps)
    i = 0
    for k, (c, r, sz) in enumerate(lumps):
        twist = Matrix.Rotation(rnd.uniform(0, TAU), 3, "Z")
        dirs = [twist @ d for d in _fib(round(per * 1.9))]
        for d in dirs:
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

    # Fallen leaves lying flat along the foot on both sides.
    for i in range(N_LITTER):
        side = 1 if i % 2 else -1
        at = (rnd.uniform(-HALF_X + 0.1, HALF_X - 0.1), side * (SIDE + rnd.uniform(-0.04, 0.02)), CARD_T / 2)
        _point(box(f"{prefix}_litter_{i}", (CARD_L * 0.8, CARD_W * 0.8, CARD_T), at,
                   mats["bronze" if rnd.random() < 0.5 else "shadow"], rot=(0, 0, rnd.uniform(0, 360)), bevel=0))

    # Arching canes, living and dead, with berries near their tips.
    spots = []
    for k in range(N_CANES + N_DEAD):
        spots += _cane(prefix, k, shell, rnd, mats, dead=k >= N_CANES)
    picks = random.Random(9).sample(range(len(tops)), min(N_BERRIES - len(spots) // 2, len(tops)))
    berries = spots[::2] + [tops[j][0] + tops[j][1] * 0.04 for j in picks]
    _berries(prefix, berries, rnd, mats)
    rest = [tops[j] for j in range(len(tops)) if j not in picks]
    _flowers(prefix, random.Random(13).sample(rest, min(N_FLOWERS, len(rest))), rnd, mats)
