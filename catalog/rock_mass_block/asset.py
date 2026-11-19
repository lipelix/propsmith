"""A block of solid rough rock filling a 1.5 x 1.5 m footprint about 3 m high: the bedrock a crypt is cut into, for
filling the space between corridors. It is seamless when repeated side by side on a 1.5 m grid.

The block is one closed lattice mesh (a box divided into about 10 cm cells) whose vertices are pushed by a displacement
field that repeats every 1.5 m in x and y. Where two blocks touch, their shared faces start at the same points and move
by the same amounts, so the faces you see run on across the joint without a step, a gap or a repeat line. The field
mixes rough lumps with tilted strata, so the faces read as split, ledged rock; the top is a broken, uneven crown that
also repeats with the grid. Colours are picked per facet from the same repeating field, damp and dark near the floor."""
import math
import random

import bmesh

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box

MODULE = 1.5  # metres: the grid the block repeats on (the wall kits' section length)
P = MODULE  # period of the displacement field in x and y
H = 3.0  # height of the highest point of the crown
CROWN = 0.32  # how far the broken crown dips below H
N = 15  # cells across x and y (10 cm)
M = 30  # cells up z (10 cm)
SIDE_AMP = 0.1  # largest push of a side face in x or y
STRATA = 0.36  # metres, mean thickness of a rock layer
DAMP_TOP = 0.7  # damp stains reach this high

ROCK = (0.22, 0.215, 0.208)  # linear RGB: cool grey bedrock, a shade warmer than the crypt ashlar
ROCK_DARK = (0.14, 0.14, 0.142)
ROCK_PALE = (0.3, 0.292, 0.278)
DAMP = (0.115, 0.125, 0.108)  # rock darkened by damp, a little green


def _waves(rnd, count, kmax, zfreq, amp):
    """`count` plane waves that repeat every P in x and y: integer wave numbers, random z frequency and phase."""
    waves = []
    for _ in range(count):
        kx, ky = rnd.randint(-kmax, kmax), rnd.randint(-kmax, kmax)
        if kx == 0 and ky == 0:
            kx = 1
        waves.append((kx, ky, rnd.uniform(-zfreq, zfreq), rnd.uniform(0, 2 * math.pi), amp * rnd.uniform(0.5, 1.0)))
    return waves


def _sum(waves, x, y, z):
    return sum(a * math.sin(2 * math.pi * (kx * x + ky * y) / P + kz * z + ph) for kx, ky, kz, ph, a in waves)


class Field:
    """The displacement field: periodic in x and y with period P, so tiles match exactly."""

    def __init__(self, seed):
        rnd = random.Random(seed)
        self.lumps = [_waves(rnd, 5, 2, 5.0, 1.0), _waves(rnd, 5, 2, 5.0, 1.0)]  # broad lumps (x, y)
        self.grit = [_waves(rnd, 7, 6, 24.0, 1.0), _waves(rnd, 7, 6, 24.0, 1.0)]  # small facets (x, y)
        self.jut = [rnd.uniform(-1, 1) for _ in range(2 * 16)]  # how far each whole layer juts (x, y)
        self.dip = _waves(rnd, 2, 1, 0.0, 1.0)  # tilt of the strata
        self.ledge = [_waves(rnd, 3, 2, 0.0, 1.0), _waves(rnd, 3, 2, 0.0, 1.0)]  # how far each layer juts
        self.crown = _waves(rnd, 7, 4, 0.0, 1.0)  # the broken top
        self.tone = _waves(rnd, 6, 3, 4.0, 1.0)  # colour patches

    def _norm(self, waves, x, y, z):
        return _sum(waves, x, y, z) / sum(w[4] for w in waves)

    def side(self, x, y, z):
        """Push (dx, dy) of a point: lumps, grit and the ledges of tilted strata."""
        layer = (z + 0.12 * self._norm(self.dip, x, y, 0)) / STRATA
        frac = layer - math.floor(layer)  # 0 at the bottom of a layer, 1 at its top: each layer leans out
        out = []
        for i in range(2):
            lump = self._norm(self.lumps[i], x, y, z)
            grit = self._norm(self.grit[i], x, y, z)
            n = math.floor(layer) % 16
            jut = 0.5 * self.jut[2 * n + i] + 0.5 * self._norm(self.ledge[i], x, y, n)
            ledge = jut * (0.6 + 0.4 * frac)  # each layer juts as one, its top edge a little further out
            out.append(SIDE_AMP * (0.3 * lump + 0.2 * grit + 0.5 * ledge))
        return out

    def crown_dip(self, x, y):
        """How far the crown sits below H at (x, y), 0 to CROWN."""
        return CROWN * (0.5 + 0.5 * self._norm(self.crown, x, y, 0))

    def tone_at(self, x, y, z):
        return self._norm(self.tone, x, y, z)


def _lattice(bm, field):
    """A closed box lattice (N x N x M cells, surface points only) displaced by `field`."""
    verts = {}

    def vert(i, j, k):
        key = (i, j, k)
        if key not in verts:
            x, y, z0 = -P / 2 + i * P / N, -P / 2 + j * P / N, k / M  # z0: 0 at the floor, 1 at the top
            top = H - field.crown_dip(x, y)
            z = z0 * top
            dx, dy = field.side(x, y, z)
            # Keep the floor flat on z = 0 and the crown's edge lip from folding over: fade the push near the floor.
            fade = min(1.0, z / 0.15)
            verts[key] = bm.verts.new((x + dx * fade, y + dy * fade, z))
        return verts[key]

    faces = []
    for a in range(N):
        for b in range(M):
            faces.append([vert(a, 0, b), vert(a + 1, 0, b), vert(a + 1, 0, b + 1), vert(a, 0, b + 1)])  # -y
            faces.append([vert(a, N, b), vert(a, N, b + 1), vert(a + 1, N, b + 1), vert(a + 1, N, b)])  # +y
            faces.append([vert(0, a, b), vert(0, a, b + 1), vert(0, a + 1, b + 1), vert(0, a + 1, b)])  # -x
            faces.append([vert(N, a, b), vert(N, a + 1, b), vert(N, a + 1, b + 1), vert(N, a, b + 1)])  # +x
        for b in range(N):
            faces.append([vert(a, b, M), vert(a + 1, b, M), vert(a + 1, b + 1, M), vert(a, b + 1, M)])  # top
            faces.append([vert(a, b, 0), vert(a, b + 1, 0), vert(a + 1, b + 1, 0), vert(a + 1, b, 0)])  # floor
    for f in faces:
        bm.faces.new(f)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="SHORT_EDGE")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def _paint(mesh, field):
    """Pick a material slot per facet from the repeating tone field: damp low down, dark and pale patches above."""
    for poly in mesh.polygons:
        x, y, z = poly.center
        t = field.tone_at(x, y, z)
        if z < DAMP_TOP * (0.25 + 0.75 * (0.5 + 0.5 * t)) and poly.normal.z < 0.7:
            slot = 3
        elif t > 0.45:
            slot = 2
        elif t < -0.3 or poly.normal.z < -0.2:
            slot = 1  # dark patches and the undersides of ledges
        else:
            slot = 0
        poly.material_index = slot


@prop
def rock_mass_block():
    field = Field(41)
    mats = [
        material("rock_mass_block_rock", ROCK, rough=0.92, vary=0.25, scale=6, crevice=0.8),
        material("rock_mass_block_dark", ROCK_DARK, rough=0.92, vary=0.25, scale=7, crevice=0.8),
        material("rock_mass_block_pale", ROCK_PALE, rough=0.9, vary=0.22, scale=8, crevice=0.75),
        material("rock_mass_block_damp", DAMP, rough=0.6, vary=0.3, scale=5, crevice=0.8),
    ]
    obj = box("rock", (P, P, H), (0, 0, H / 2), mats[0], bevel=0)
    obj.location = (0, 0, 0)
    bm = bmesh.new()
    _lattice(bm, field)
    mesh = obj.data
    bm.to_mesh(mesh)
    bm.free()
    for m in mats[1:]:
        mesh.materials.append(m)
    mesh.shade_flat()
    _paint(mesh, field)
