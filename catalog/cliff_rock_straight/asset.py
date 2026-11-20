"""A straight section of mossy grey cliff: a rock face 1.5 m long, about 3.5 m high and 1.5 m deep, its face on -y
leaning back as it rises, broken into ledges by layered strata and split by vertical cracks, with a grassy top and ivy
hanging over the edge. Sections set side by side on the 1.5 m grid join into one continuous cliff, and
`cliff_rock_corner` turns it round an outside corner.

The rock is one closed lattice mesh (10 cm cells on the face) whose face is pushed back by a displacement field that
repeats every 1.5 m along the face, so the joints between sections match exactly. The field and its seed are shared with
`cliff_rock_corner`: keep the two in step. Colours are picked per facet: moss and grass on the ledges and the top, dark
in the cracks and under overhangs, damp at the foot."""
import bisect
import math
import random

import bmesh
from mathutils import Matrix, Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall dimensions (metres), from the description.
MODULE = 1.5  # the grid sections join on (the wall kits' section length); also the field's period along the face
P = MODULE
HALF = MODULE / 2
H = 3.5  # height of the top
SEED = 41  # the face field, shared with cliff_rock_corner

N = 15  # lattice cells along the face (10 cm)
ND = 10  # cells across the top and the joint sides, front to back
M = 36  # cells up the face (about 10 cm)

LEAN0 = 0.15  # the face's set-back from the front of the footprint at the foot
LEAN = 0.32  # extra set-back at the top: the face leans back as it rises
JUT = 0.15  # how far a rock layer juts out or sits back
LIP = 0.05  # how far the top of each layer overhangs its foot
TILT = 0.07  # how much the layer joints wander up and down along the face
LUMP = 0.055  # broad lumps
GRIT = 0.012  # small facets
LAT = 0.03  # sideways wander of the face's columns
CRACK_W = 0.12  # half-width of a crack's groove
CROWN = 0.07  # how far the top dips below H
BROW = 0.16  # how far the top's front edge rounds down
SIDE = 0.065  # largest push of a joint side in x (the same on both, so neighbours match)
DAMP_TOP = 0.65  # damp stains reach this high

LEAF_TIP = 0.075  # ivy leaf: centre to tip
LEAF_BASE = 0.04  # centre to stalk end
LEAF_W = 0.045  # half-width
LEAF_T = 0.005  # card thickness
CUP = 0.006  # how far leaf edges curl
VINE_R = 0.009  # woody ivy stem

ROCK = (0.27, 0.262, 0.245)  # linear RGB: weathered grey rock
ROCK_DARK = (0.12, 0.12, 0.118)  # cracks and the undersides of ledges
ROCK_PALE = (0.36, 0.352, 0.33)  # lit, lichen-pale patches
DAMP = (0.12, 0.13, 0.105)  # rock darkened by damp at the foot
MOSS = (0.075, 0.1, 0.032)  # moss on ledges and patches of the face
GRASS = (0.075, 0.095, 0.03)  # turf on the top
SHADOW = (0.04, 0.06, 0.02)  # ivy: deep shadow green
OLIVE = (0.1, 0.13, 0.035)  # mid olive green
LIT = (0.21, 0.24, 0.065)  # lit yellow-green
CORE = (0.035, 0.05, 0.018)  # the dark heart of an ivy curtain
VINE = (0.13, 0.085, 0.045)  # ivy stems


def _waves(rnd, count, kmax, zfreq):
    """`count` waves along the face that repeat every P (integer wave numbers), with a random z frequency and phase."""
    out = []
    for _ in range(count):
        k = rnd.randint(1, kmax) * rnd.choice((-1, 1))
        out.append((k, rnd.uniform(-zfreq, zfreq), rnd.uniform(0, 2 * math.pi), rnd.uniform(0.5, 1.0)))
    return out


def _norm(waves, t, z):
    """The waves' sum at (t, z), scaled to about -1..1."""
    return sum(a * math.sin(2 * math.pi * k * t / P + kz * z + ph) for k, kz, ph, a in waves) / sum(w[3] for w in waves)


class Field:
    """How far the face sits back from the front of the footprint at (t, z), t the distance along the face. It repeats
    every P in t, so sections join without a step."""

    def __init__(self, seed):
        rnd = random.Random(seed)
        self.bounds = [0.0]
        while self.bounds[-1] < H + 1:
            self.bounds.append(self.bounds[-1] + rnd.uniform(0.42, 0.8))  # the joints between rock layers
        self.jut = [rnd.uniform(-1, 1) for _ in self.bounds]
        self.layer = [_waves(rnd, 2, 2, 0.0) for _ in self.bounds]
        self.tilt = _waves(rnd, 2, 1, 0.0)
        self.lumps = _waves(rnd, 5, 2, 2.5)
        self.grit = _waves(rnd, 6, 6, 12.0)
        self.lat = _waves(rnd, 3, 2, 3.0)
        self.tone = _waves(rnd, 6, 3, 3.0)
        self.top = _waves(rnd, 4, 3, 2.0)
        self.side_waves = [(m, rnd.uniform(-4, 4), rnd.uniform(0, 6.3), rnd.uniform(0.5, 1)) for m in (1, 2, 3, 4)]
        self.cracks = []
        for tc in (0.32, 0.78, 1.18):  # vertical cracks, kept off the joints
            lo = rnd.uniform(0.0, 1.4)
            self.cracks.append((tc + rnd.uniform(-0.05, 0.05), lo, min(H, lo + rnd.uniform(1.3, 2.6)),
                                rnd.uniform(0.1, 0.15), rnd.uniform(0, 6.3)))

    def crack(self, t, z, cracks=None):
        t = t % P
        out = 0.0
        for tc, lo, hi, d, ph in cracks or self.cracks:
            if lo < z < hi:
                wander = 0.035 * math.sin(3 * z + ph) + 0.02 * math.sin(7.3 * z + 2 * ph)
                prof = max(0.0, 1 - abs(t - tc - wander) / CRACK_W)
                out += d * prof * min(1.0, (z - lo) / 0.6, (hi - z) / 0.6)
        return out

    def offset(self, t, z):
        zz = z + TILT * _norm(self.tilt, t, 0)
        i = max(0, bisect.bisect_right(self.bounds, zz) - 1)
        frac = max(0.0, (zz - self.bounds[i]) / (self.bounds[i + 1] - self.bounds[i]))
        layer = -JUT * (0.65 * self.jut[i] + 0.35 * _norm(self.layer[i], t, 0))
        o = LEAN0 + LEAN * (z / H) ** 1.2 + layer - LIP * frac
        o += LUMP * _norm(self.lumps, t, z) + GRIT * _norm(self.grit, t, z) + self.crack(t, z)
        return max(0.0, o)

    def side(self, v, z):
        """The push of a joint side at depth v (0 at the face, 1 at the back), zero at both edges."""
        w = self.side_waves
        total = sum(a * math.sin(math.pi * m * v) * math.cos(kz * z + ph) for m, kz, ph, a in w)
        return SIDE * total / sum(x[3] for x in w)

    def lateral(self, t, z):
        return LAT * math.sin(math.pi * (t % P) / P) * _norm(self.lat, t, z)


class Straight:
    """The straight section: lattice coordinates a = t along the face (0..P), b = depth v (0 at the face, 1 at the
    back)."""

    def __init__(self, field):
        self.f = field

    def top(self, a, b):
        dip = CROWN * math.sin(math.pi * a / P) ** 2 * (0.5 + 0.5 * _norm(self.f.top, a, 3 * b))
        return H - dip - BROW * (1 - b) ** 3

    def place(self, a, b, z):
        o = self.f.offset(a, z)
        yf = -HALF + o
        x = -HALF + a + self.f.lateral(a, z) * (1 - b) + self.f.side(b, z)
        return Vector((x, yf + b * (HALF - yf), z))

    def front(self, t):
        """Lattice coordinates of the face at t, and of a point just back from its top edge."""
        return (t, 0.0), (t, 0.07)

    def on_face(self, a, b):
        return b == 0

    def crack(self, t, z):
        return self.f.crack(t, z)

    def tone_t(self, a, b):
        return a + 0.7 * b


def _ring(key, U, W):
    """The boundary of a U x W lattice face, as keys in order."""
    return ([key(u, 0) for u in range(U + 1)] + [key(U, w) for w in range(1, W + 1)]
            + [key(u, W) for u in range(U - 1, -1, -1)] + [key(0, w) for w in range(W - 1, 0, -1)])


def _rock(shape, mats):
    """The rock as one closed mesh: the face, the joint sides and the top as quads, the flat back and floor as
    n-gons."""
    bm = bmesh.new()
    verts, info = {}, []

    def vert(key):
        if key not in verts:
            i, j, k = key
            a, b = i * P / N, j / ND
            z = k / M * shape.top(a, b)
            verts[key] = bm.verts.new(shape.place(a, b, z))
            info.append((shape.tone_t(a, b), shape.on_face(a, b)))
        return verts[key]

    quads = []
    for i in range(N):
        for k in range(M):
            quads.append([(i, 0, k), (i + 1, 0, k), (i + 1, 0, k + 1), (i, 0, k + 1)])  # the face (-y)
        for j in range(ND):
            quads.append([(i, j, M), (i + 1, j, M), (i + 1, j + 1, M), (i, j + 1, M)])  # the top
    for j in range(ND):
        for k in range(M):
            quads.append([(0, j, k), (0, j, k + 1), (0, j + 1, k + 1), (0, j + 1, k)])  # joint (-x)
            quads.append([(N, j, k), (N, j + 1, k), (N, j + 1, k + 1), (N, j, k + 1)])  # joint (+x)
    ngons = [
        _ring(lambda i, k: (i, ND, k), N, M),  # back (+y)
        _ring(lambda i, j: (i, j, 0), N, ND),  # floor
    ]
    return _finish(bm, quads, ngons, vert, info, mats)


def _finish(bm, quads, ngons, vert, info, mats):
    for q in quads:
        bm.faces.new([vert(k) for k in q])
    for ring in ngons:
        bm.faces.new([vert(k) for k in ring])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) == 4], quad_method="SHORT_EDGE")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    obj = box("cliff_rock", (1, 1, 1), (0, 0, 0), mats["rock"], bevel=0)
    mesh = obj.data
    bm.to_mesh(mesh)
    bm.free()
    for name in ("dark", "pale", "damp", "moss", "grass"):
        mesh.materials.append(mats[name])
    mesh.shade_flat()
    return mesh, info


def _paint(mesh, info, shape):
    """Pick a material per facet: grass on the top, moss on ledges and in patches high on the face, dark in cracks and
    under overhangs, damp at the foot, pale and dark patches from the repeating tone field."""
    for poly in mesh.polygons:
        x, y, z = poly.center
        nz = poly.normal.z
        vs = [info[v] for v in poly.vertices]
        t = sum(v[0] for v in vs) / len(vs)
        face = any(v[1] for v in vs)
        tone = _norm(shape.f.tone, t, z)
        if nz > 0.55:
            slot = 5 if z > H - 0.25 else 4  # grass / moss
        elif (face and shape.crack(t, z) > 0.055) or nz < -0.3:
            slot = 1
        elif z < DAMP_TOP * (0.25 + 0.75 * (0.5 + 0.5 * _norm(shape.f.lumps, t, 0))):
            slot = 3
        elif face and (tone + 0.9 * z / H > 1.05 or (nz > 0.25 and tone > -0.2)):
            slot = 4
        elif tone > 0.6 and face:
            slot = 2
        elif tone < -0.65 and face:
            slot = 1
        else:
            slot = 0
        poly.material_index = slot


def _mats():
    return {
        "rock": material("cliff_rock_rock", ROCK, rough=0.92, vary=0.25, scale=5, crevice=0.8),
        "dark": material("cliff_rock_dark", ROCK_DARK, rough=0.92, vary=0.25, scale=7, crevice=0.8),
        "pale": material("cliff_rock_pale", ROCK_PALE, rough=0.9, vary=0.22, scale=8, crevice=0.75),
        "damp": material("cliff_rock_damp", DAMP, rough=0.65, vary=0.3, scale=5, crevice=0.8),
        "moss": material("cliff_rock_moss", MOSS, rough=0.95, vary=0.35, scale=9, crevice=0.6),
        "grass": material("cliff_rock_grass", GRASS, rough=0.95, vary=0.3, scale=12, crevice=0.5),
        "shadow": material("cliff_rock_ivy_shadow", SHADOW, rough=0.85, vary=0.3, scale=30, crevice=0.6),
        "olive": material("cliff_rock_ivy_olive", OLIVE, rough=0.75, vary=0.3, scale=30, crevice=0.5),
        "lit": material("cliff_rock_ivy_lit", LIT, rough=0.7, vary=0.25, scale=30, crevice=0.35),
        "core": material("cliff_rock_ivy_core", CORE, rough=0.95, vary=0.25, scale=20, crevice=0.6),
        "vine": material("cliff_rock_ivy_vine", VINE, rough=0.9, vary=0.25, scale=40, crevice=0.4),
    }


def _jitter(rnd, v, amount):
    return (v + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * amount).normalized()


def _leaf(name, at, normal, tip, mat, rnd):
    """One pointed ivy leaf card: a thin kite with its tip along `tip` and its face along `normal`."""
    size = rnd.uniform(0.75, 1.2)
    obj = box(name, (1, 1, LEAF_T), (0, 0, 0), mat, bevel=0)
    tip = (tip - normal * tip.dot(normal)).normalized()
    side = normal.cross(tip)
    m = Matrix((tip, side, normal)).transposed()
    corners = {(1, 1): (LEAF_TIP, 0), (-1, 1): (0, LEAF_W), (-1, -1): (-LEAF_BASE, 0), (1, -1): (0, -LEAF_W)}
    for v in obj.data.vertices:
        lx, ly = corners[(1 if v.co.x > 0 else -1, 1 if v.co.y > 0 else -1)]
        lx, ly = lx * size, ly * size
        v.co = m @ Vector((lx, ly, v.co.z + CUP * (abs(ly) / LEAF_W) ** 2)) + at
    return obj


def _stick(name, a, b, mat, r=VINE_R):
    """A thin four-sided stem segment from a to b."""
    d = b - a
    ln = d.length
    d.normalize()
    tilt = math.degrees(math.acos(max(-1.0, min(1.0, d.z))))
    yaw = math.degrees(math.atan2(d.x, -d.y))
    cylinder(name, r, ln, tuple(a), mat, r_top=r * 0.8, segments=4, rot=(tilt, 0, yaw), bevel=0)


def _surface(shape, t, z, out=0.0):
    """A point on the face at (t, z) pushed `out` along its outward normal, and that normal."""
    e = 0.02

    def at(tt, zz):
        (a, b), _ = shape.front(tt)
        return shape.place(a, b, zz)

    n = (at(t + e, z) - at(t - e, z)).cross(at(t, z + e) - at(t, z - e)).normalized()
    n = (n + Vector((0, 0, 0.15))).normalized()  # the field is rough: lean the normal a little up and out
    return at(t, z) + n * out, n


def _ivy(shape, curtains, lip, seed, mats):
    """Ivy over the top edge: a band of leaves along the lip and curtains hanging down the face, each over a dark core
    and a few woody stems."""
    rnd = random.Random(seed)
    k = 0

    def colour(up):
        r = rnd.random()
        if up > 0.5:
            return "lit" if r < 0.55 else "olive"
        return "olive" if r < 0.55 else ("shadow" if r < 0.8 else "lit")

    for c, (tc, width, length) in enumerate(curtains):
        (a, b), _ = shape.front(tc)
        ztop = shape.top(a, b) - 0.03
        # The dark core behind the leaves.
        mid, n = _surface(shape, tc, ztop - length * 0.4, 0.03)
        core = blob(f"cliff_rock_ivy_core_{c}", 0.1, tuple(mid), mats["core"],
                    squash=(width * 3.2, 0.35, length * 4.0), subdiv=1, seed=seed + c, jitter=0.15)
        core.rotation_euler = (0, 0, math.atan2(n.y, n.x) + math.pi / 2)
        # Woody stems down the curtain.
        for s in range(2):
            t0 = tc + (s - 0.5) * width * 0.4
            steps = 4
            p, _ = _surface(shape, t0, ztop, 0.03)
            for q in range(steps):
                zq = ztop - length * 0.9 * (q + 1) / steps
                t0 += rnd.uniform(-0.05, 0.05)
                pq, _ = _surface(shape, t0, zq, 0.035)
                _stick(f"cliff_rock_ivy_stem_{c}_{s}_{q}", p, pq, mats["vine"])
                p = pq
        # Leaves, thick at the top and thinning to a tip.
        count = round(70 * width * length + 18)
        for i in range(count):
            u = ((i + rnd.random()) / count) ** 1.25
            w = width * (1 - u) ** 0.7 + 0.06
            t = tc + rnd.uniform(-0.5, 0.5) * w
            z = ztop - length * u + rnd.uniform(-0.03, 0.03)
            at, n = _surface(shape, t, z, 0.04 + rnd.uniform(0, 0.05) + 0.05 * (1 - u))
            ln = _jitter(rnd, n + Vector((0, 0, 0.6)), 0.5)
            tip = _jitter(rnd, Vector((0, 0, -1)) + n * 0.3, 0.45)
            _leaf(f"cliff_rock_ivy_leaf_{k}", at, ln, tip, mats[colour(ln.z)], rnd)
            k += 1

    # The band along the lip: leaves over the edge and on the turf just behind it.
    t0, t1, per_m = lip
    count = round((t1 - t0) * per_m)
    for i in range(count):
        t = t0 + (t1 - t0) * (i + rnd.random()) / count
        (a, b), (a2, b2) = shape.front(t)
        if rnd.random() < 0.55:
            z = shape.top(a, b) - rnd.uniform(0.0, 0.18)
            at, n = _surface(shape, t, z, 0.03 + rnd.uniform(0, 0.04))
            ln = _jitter(rnd, n + Vector((0, 0, 0.9)), 0.45)
            tip = _jitter(rnd, Vector((0, 0, -1)) + n, 0.5)
        else:
            f = rnd.uniform(0.2, 1.0)
            a3, b3 = a + (a2 - a) * f, b + (b2 - b) * f
            at = shape.place(a3, b3, shape.top(a3, b3)) + Vector((0, 0, 0.025))
            _, n = _surface(shape, t, shape.top(a, b) - 0.05)
            ln = _jitter(rnd, Vector((0, 0, 1)) + n * 0.4, 0.4)
            tip = _jitter(rnd, n, 0.6)
        _leaf(f"cliff_rock_ivy_leaf_{k}", at, ln, tip, mats[colour(ln.z)], rnd)
        k += 1


def _tufts(shape, ts, seed, mats):
    """Low grass tufts on the turf just behind the edge, breaking up the top's outline."""
    rnd = random.Random(seed)
    for i, t in enumerate(ts):
        _, (a, b) = shape.front(t)
        p = shape.place(a, b, shape.top(a, b))
        r = rnd.uniform(0.08, 0.12)
        blob(f"cliff_rock_tuft_{i}", r, (p.x, p.y, p.z + r * 0.2), mats["grass" if i % 2 else "moss"],
             squash=(1.6, 1.3, 0.55), subdiv=1, seed=seed + i, jitter=0.2)


@prop
def cliff_rock_straight():
    field = Field(SEED)
    mats = _mats()
    shape = Straight(field)
    mesh, info = _rock(shape, mats)
    _paint(mesh, info, shape)
    _ivy(shape, [(0.3, 0.42, 1.25), (0.82, 0.3, 0.6), (1.2, 0.36, 0.95)], (0.08, 1.42, 26), 7, mats)
    _tufts(shape, (0.15, 0.55, 1.0, 1.38), 13, mats)
