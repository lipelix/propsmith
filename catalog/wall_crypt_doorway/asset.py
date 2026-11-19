"""A 1.5 m section of crypt wall with an empty round-arched doorway about 1.1 m wide and 2.2 m high, in the dark
dressed ashlar of wall_crypt_straight: jamb blocks up to the springing line, a ring of wedge voussoirs with a slightly
proud pale keystone, coursed blocks cut to the arch above it, a recessed near black mortar core, a proud footing on the
jambs, a plain coping, worn arrises and a little damp staining."""
import math
import random

import bmesh
import bpy
from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box

MODULE = 1.5  # metres: the length wall and fence sections join at
L = MODULE
T = 0.6  # wall thickness (y)
H = 3.0  # overall height including the coping
COPING_H = 0.1
COPING_OVER = 0.02
COURSES = 9
COURSE_H = (H - COPING_H) / COURSES
FOOT_OVER = 0.025
JOINT = 0.014
INSET = 0.035  # how far the mortar core sits behind the faces
OPEN_W = 1.1  # clear width of the doorway
SPRING_COURSE = 5  # the arch springs from the top of this many courses
SPRING = SPRING_COURSE * COURSE_H  # springing line, about 1.6 m
R_IN = OPEN_W / 2  # arch intrados: the apex about 2.16 m up
R_OUT = L / 2  # arch extrados: the voussoirs reach the section ends at the springing line
VOUSSOIRS = 9
KEY_PROUD = 0.02  # how far the keystone stands proud of both faces
ARC_STEP = 4  # degrees between points of the curved edge of a block cut to the arch

# Shared stone palette of the crypt wall set (wall_crypt_straight, _corner, _doorway): keep them equal.
STONE = (0.19, 0.195, 0.205)
STONE_OLD = (0.145, 0.148, 0.155)
STONE_PALE = (0.24, 0.243, 0.25)
DAMP = (0.1, 0.11, 0.098)
MORTAR = (0.04, 0.04, 0.042)
COPING = (0.1, 0.104, 0.115)


def _mats(prefix):
    return {
        "stone": material(f"{prefix}_stone", STONE, vary=0.22, scale=7, crevice=0.7),
        "old": material(f"{prefix}_stone_old", STONE_OLD, vary=0.25, scale=8, crevice=0.7),
        "pale": material(f"{prefix}_stone_pale", STONE_PALE, vary=0.2, scale=9, crevice=0.65),
        "damp": material(f"{prefix}_damp", DAMP, rough=0.6, vary=0.3, scale=5, crevice=0.75),
        "mortar": material(f"{prefix}_mortar", MORTAR, vary=0.12, scale=20, crevice=0.9),
        "coping": material(f"{prefix}_coping", COPING, vary=0.22, scale=7, crevice=0.7),
    }


def _pick(rnd, mats, course):
    damp = (0.65, 0.3, 0.06)[min(course, 2)]
    if rnd.random() < damp:
        return mats["damp"]
    r = rnd.random()
    return mats["stone"] if r < 0.55 else mats["old"] if r < 0.85 else mats["pale"]


def _prism(name, outline, y0, y1, mat, bevel):
    """A closed prism: the counter-clockwise (x, z) `outline` extruded from `y0` to `y1`."""
    bm = bmesh.new()
    front = [bm.verts.new((x, y0, z)) for x, z in outline]
    back = [bm.verts.new((x, y1, z)) for x, z in outline]
    n = len(outline)
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], back[i], back[j], front[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth()
    mesh.set_sharp_from_angle(angle=math.radians(35))
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width, mod.segments, mod.limit_method = bevel, 2, "ANGLE"
        mod.angle_limit = math.radians(40)
    return obj


def _cut(x0, x1, z0, z1, r):
    """The rectangle x0..x1, z0..z1 less the disc of radius `r` about the springing centre: a list of counter-clockwise
    (x, z) outlines, none when the disc covers it, two when the disc splits it. A lower edge follows the arc where the
    disc reaches into the rectangle."""

    def bottom_z(x):
        z = SPRING + math.sqrt(r * r - x * x) if abs(x) < r else z0
        return min(max(z0, z), z1)

    xs = {x0, x1}
    for k in range(0, 181, ARC_STEP):
        xs.add(r * math.cos(math.radians(k)))
    for z in (z0, z1):  # where the arc crosses the rectangle's top and bottom
        if SPRING <= z < SPRING + r:
            w = math.sqrt(r * r - (z - SPRING) ** 2)
            xs.update((w, -w))
    pts = [(x, bottom_z(x)) for x in sorted(x for x in xs if x0 <= x <= x1)]
    below = [z < z1 - 1e-4 for _, z in pts]
    outlines = []
    i = 0
    while i < len(pts):
        if not below[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(pts) and below[j + 1]:
            j += 1
        run = pts[max(i - 1, 0):min(j + 2, len(pts))]  # with the points where the arc meets the top edge
        outline = list(run)
        if outline[-1][1] < z1 - 1e-4:
            outline.append((outline[-1][0], z1))
        if outline[0][1] < z1 - 1e-4:
            outline.append((outline[0][0], z1))
        if len(outline) >= 3:
            outlines.append(outline)
        i = j + 1
    return outlines


def _mirror(outline, s):
    """`outline` on the +x side, or mirrored onto -x (reversed to stay counter-clockwise)."""
    return outline if s > 0 else [(-x, z) for x, z in reversed(outline)]


def _polar(r, a):
    return (r * math.cos(a), SPRING + r * math.sin(a))


@prop
def wall_crypt_doorway():
    rnd = random.Random(41)
    mats = _mats("wall_crypt_doorway")
    body_h = COURSES * COURSE_H
    jamb = (L - OPEN_W) / 2
    core = T - 2 * INSET
    xj = (OPEN_W / 2 + L / 2) / 2  # jamb centre

    # Mortar core: behind the jambs, and above the springing line cut to the arch (a little inside the voussoirs).
    for s in (-1, 1):
        box(f"core_jamb_{s}", (jamb - 2 * INSET, core, SPRING), (s * xj, 0, SPRING / 2), mats["mortar"], bevel=0)
        for k, outline in enumerate(_cut(0, L / 2, SPRING, body_h, R_IN + INSET)):
            _prism(f"core_arch_{s}_{k}", _mirror(outline, s), -core / 2, core / 2, mats["mortar"], 0)

    # Jambs: one block per course on each side, up to the springing line.
    for c in range(SPRING_COURSE):
        z0 = c * COURSE_H + JOINT / 2
        h = COURSE_H - JOINT
        depth = T + (2 * FOOT_OVER if c == 0 else 0)
        for s in (-1, 1):
            a, b = OPEN_W / 2, L / 2 - JOINT / 4
            bh = h * rnd.uniform(0.985, 1.0)
            box(f"jamb_{c}_{s}", (b - a, depth * rnd.uniform(0.985, 1.0), bh),
                (s * (a + b) / 2, rnd.uniform(-0.004, 0.004), z0 + bh / 2), _pick(rnd, mats, c),
                rot=(0, 0, rnd.uniform(-0.4, 0.4)), bevel=rnd.uniform(0.022, 0.032))

    # Arch ring: wedge voussoirs, the keystone pale and a little proud.
    step = math.pi / VOUSSOIRS
    half_j = JOINT / 2 / R_OUT
    for i in range(VOUSSOIRS):
        a0, a1 = i * step + half_j, (i + 1) * step - half_j
        if i == 0:
            a0 = 0
        if i == VOUSSOIRS - 1:
            a1 = math.pi
        key = i == VOUSSOIRS // 2
        outline = [_polar(R_IN, a0), _polar(R_OUT, a0), _polar(R_OUT, a1), _polar(R_IN, a1)]
        if i == 0:  # stand on the jamb's bed joint
            outline[0] = (R_IN, SPRING + JOINT / 2)
            outline[1] = (R_OUT - JOINT / 4, SPRING + JOINT / 2)
        if i == VOUSSOIRS - 1:
            outline[2] = (-R_OUT + JOINT / 4, SPRING + JOINT / 2)
            outline[3] = (-R_IN, SPRING + JOINT / 2)
        d = T / 2 + (KEY_PROUD if key else rnd.uniform(-0.004, 0.002))
        _prism(f"voussoir_{i}", outline, -d, d, mats["pale"] if key else _pick(rnd, mats, 3), 0.024)

    # Courses above the springing line, cut to the arch's extrados; two blocks per course meeting off the centre.
    for c in range(SPRING_COURSE, COURSES):
        z0 = c * COURSE_H + JOINT / 2
        z1 = (c + 1) * COURSE_H - JOINT / 2
        split = rnd.uniform(-0.12, 0.12) if (c - SPRING_COURSE) % 2 else rnd.uniform(0.25, 0.4) * rnd.choice((-1, 1))
        for k, (xa, xb) in enumerate(((-L / 2 + JOINT / 4, split - JOINT / 2), (split + JOINT / 2, L / 2 - JOINT / 4))):
            parts = _cut(xa, xb, z0, z1, R_OUT + JOINT / 2)
            d = T / 2 + rnd.uniform(-0.004, 0.002)
            mat = _pick(rnd, mats, c)
            for p, outline in enumerate(parts):
                _prism(f"block_{c}_{k}_{p}", outline, -d, d, mat, 0.026)

    # Coping.
    zc = body_h + COPING_H / 2
    xs = [-L / 2, -0.3 + rnd.uniform(-0.05, 0.05), 0.25 + rnd.uniform(-0.05, 0.05), L / 2]
    for i in range(len(xs) - 1):
        a = xs[i] + (JOINT / 4 if i == 0 else JOINT / 2)
        b = xs[i + 1] - (JOINT / 4 if i == len(xs) - 2 else JOINT / 2)
        box(f"coping_{i}", (b - a, T + 2 * COPING_OVER, COPING_H * rnd.uniform(0.94, 1.0)), ((a + b) / 2, 0, zc),
            mats["coping"], rot=(0, 0, rnd.uniform(-0.4, 0.4)), bevel=0.022)
