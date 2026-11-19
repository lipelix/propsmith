"""A 1.5 m section of crypt wall with two burial niches (loculi) stacked in its front face: the same dark, cool dressed
ashlar as wall_crypt_straight, with a long lintel stone over each niche and a worn sill stone at its mouth. The lower
niche holds a body wrapped in a pale, stained linen shroud tied with cords; the upper one is empty but for a skull,
two long bones and grave dust.

The wall's courses are built as in wall_crypt_straight; where a niche cuts a course, each block keeps only its back
part, so the niche's back and sides show the same jointed stone."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

MODULE = 1.5  # metres: the length wall and fence sections join at
L = MODULE  # wall length along x: one module so sections join end to end
T = 0.6  # wall thickness (y)
H = 3.0  # overall height including the coping
COPING_H = 0.1
COPING_OVER = 0.02  # coping overhang on each face
COURSES = 9
COURSE_H = (H - COPING_H) / COURSES
FOOT_OVER = 0.025  # the footing course stands proud of both faces
JOINT = 0.014  # mortar joint between blocks
INSET = 0.035  # how far the mortar core sits behind the faces
SEEP_X = -0.42  # where damp seeps down the wall from a joint
SEEP_TOP = 4  # the seep darkens the blocks under it up to this course

NICHE_W = 1.28  # width of a niche opening (x)
NICHE_D = 0.43  # depth of a niche into the wall (y)
NICHES = (1, 4)  # the bottom course of each niche; each is two courses high, with a lintel course above it
NICHE_COURSES = 2
SILL_T = 0.035  # the worn sill stone at a niche's mouth
SILL_OVER = 0.02  # how far a sill stands proud of the face

BODY_L = 1.2  # length of the shrouded body (it lies along x, head at -x)
BODY_W = 0.34  # its width at the shoulders (y)

# Shared stone palette of the crypt wall set (wall_crypt_straight, _corner, _doorway, _niche): keep them equal.
STONE = (0.19, 0.195, 0.205)  # linear RGB: cool dark blue-grey ashlar
STONE_OLD = (0.145, 0.148, 0.155)
STONE_PALE = (0.24, 0.243, 0.25)
DAMP = (0.1, 0.11, 0.098)  # stone darkened by damp, a little green
MORTAR = (0.04, 0.04, 0.042)
COPING = (0.1, 0.104, 0.115)
SHROUD = (0.4, 0.36, 0.28)  # aged linen
SHROUD_STAIN = (0.28, 0.24, 0.17)  # linen stained by the grave
CORD = (0.09, 0.07, 0.048)
BONE = (0.44, 0.37, 0.23)  # yellowed bone (as bones_pile)
DUST = (0.15, 0.135, 0.11)  # grave dust
HOLLOW = (0.05, 0.04, 0.03)  # eye sockets


def _mats(prefix):
    return {
        "stone": material(f"{prefix}_stone", STONE, vary=0.22, scale=7, crevice=0.7),
        "old": material(f"{prefix}_stone_old", STONE_OLD, vary=0.25, scale=8, crevice=0.7),
        "pale": material(f"{prefix}_stone_pale", STONE_PALE, vary=0.2, scale=9, crevice=0.65),
        "damp": material(f"{prefix}_damp", DAMP, rough=0.6, vary=0.3, scale=5, crevice=0.75),
        "mortar": material(f"{prefix}_mortar", MORTAR, vary=0.12, scale=20, crevice=0.9),
        "coping": material(f"{prefix}_coping", COPING, vary=0.22, scale=7, crevice=0.7),
        "shroud": material(f"{prefix}_shroud", SHROUD, rough=0.95, vary=0.25, scale=12, crevice=0.8),
        "stain": material(f"{prefix}_shroud_stain", SHROUD_STAIN, rough=0.95, vary=0.3, scale=10, crevice=0.8),
        "cord": material(f"{prefix}_cord", CORD, rough=0.9, vary=0.2, scale=30, crevice=0.5),
        "bone": material(f"{prefix}_bone", BONE, rough=0.7, vary=0.2, scale=25, crevice=0.7),
        "dust": material(f"{prefix}_dust", DUST, rough=0.95, vary=0.3, scale=20, crevice=0.6),
        "hollow": material(f"{prefix}_hollow", HOLLOW, rough=0.9, vary=0.1, scale=20, crevice=0.3),
    }


def _pick(rnd, mats, course, seep=False):
    """Damp low down: most footing blocks, some of the next course, a rare one higher up, and the blocks of a seep."""
    damp = 0.85 if seep else (0.65, 0.3, 0.06)[min(course, 2)]
    if rnd.random() < damp:
        return mats["damp"]
    r = rnd.random()
    return mats["stone"] if r < 0.55 else mats["old"] if r < 0.85 else mats["pale"]


def _niche_of(course):
    """The niche a course is cut by (its bottom course), or None."""
    return next((n for n in NICHES if n <= course < n + NICHE_COURSES), None)


def _splits(rnd, course):
    """Block joints along x for a course. A lintel course is one long stone; the others alternate two long blocks and
    three (half, long, half), so joints stagger."""
    half = L / 2
    if course - NICHE_COURSES in NICHES:
        return [-half, half]
    if course % 2 == 0:
        return [-half, rnd.uniform(-0.08, 0.08), half]
    q = L / 4
    return [-half, -q + rnd.uniform(-0.05, 0.05), q + rnd.uniform(-0.05, 0.05), half]


def _courses(rnd, mats):
    for c in range(COURSES):
        z0 = c * COURSE_H
        h = COURSE_H - JOINT
        depth = T + (2 * FOOT_OVER if c == 0 else 0)
        cut = _niche_of(c) is not None
        xs = _splits(rnd, c)
        for i in range(len(xs) - 1):
            a, b = xs[i] + JOINT / 2, xs[i + 1] - JOINT / 2
            # Blocks at a section end reach to it, so sections join with one joint's gap.
            if i == 0:
                a = xs[0] + JOINT / 4
            if i == len(xs) - 2:
                b = xs[-1] - JOINT / 4
            bh = h * rnd.uniform(0.985, 1.0)
            dz = z0 + JOINT / 2 + bh / 2
            seep = a <= SEEP_X <= b and c < SEEP_TOP
            mat = _pick(rnd, mats, c, seep)
            rot = (rnd.uniform(-0.3, 0.3), 0, rnd.uniform(-0.4, 0.4))
            bevel = rnd.uniform(0.022, 0.032)
            if not cut:
                box(f"block_{c}_{i}", (b - a, depth * rnd.uniform(0.985, 1.0), bh), ((a + b) / 2, 0, dz), mat,
                    rot=rot, bevel=bevel)
                continue
            # A niche course: full-depth jamb parts outside the opening, only the back part inside it.
            w = NICHE_W / 2
            parts = [(a, min(b, -w), T), (max(a, -w), min(b, w), T - NICHE_D), (max(a, w), b, T)]
            for k, (pa, pb, d) in enumerate(parts):
                if pb - pa > 0.005:
                    box(f"block_{c}_{i}_{k}", (pb - pa, d, bh), ((pa + pb) / 2, T / 2 - d / 2, dz), mat,
                        rot=(0, 0, 0), bevel=min(bevel, (pb - pa) / 3))


def _core(mats):
    """The recessed mortar core behind the joints: a back slab behind the niches and front pieces around them."""
    body_h = COURSES * COURSE_H
    back0, back1 = -T / 2 + NICHE_D + INSET, T / 2 - INSET
    box("core_back", (L, back1 - back0, body_h), (0, (back0 + back1) / 2, body_h / 2), mats["mortar"], bevel=0)
    f0, f1 = -T / 2 + INSET, back0
    gap = JOINT / 2 + 0.02  # keep the core under the floor and ceiling stones of a niche
    edges = [0.0]
    for n in NICHES:
        edges += [n * COURSE_H - gap, (n + NICHE_COURSES) * COURSE_H + gap]
    edges.append(body_h)
    for k in range(0, len(edges), 2):
        z0, z1 = edges[k], edges[k + 1]
        box(f"core_front_{k}", (L, f1 - f0, z1 - z0), (0, (f0 + f1) / 2, (z0 + z1) / 2), mats["mortar"], bevel=0)
    jamb = L / 2 - NICHE_W / 2 - INSET
    for n in NICHES:
        z0, z1 = n * COURSE_H - gap, (n + NICHE_COURSES) * COURSE_H + gap
        for s in (-1, 1):
            box(f"core_jamb_{n}_{s}", (jamb, f1 - f0, z1 - z0), (s * (L / 2 - jamb / 2), (f0 + f1) / 2,
                (z0 + z1) / 2), mats["mortar"], bevel=0)


def _coping(rnd, mats):
    body_h = COURSES * COURSE_H
    zc = body_h + COPING_H / 2
    xs = [-L / 2, -0.25 + rnd.uniform(-0.05, 0.05), 0.3 + rnd.uniform(-0.05, 0.05), L / 2]
    for i in range(len(xs) - 1):
        a = xs[i] + (JOINT / 4 if i == 0 else JOINT / 2)
        b = xs[i + 1] - (JOINT / 4 if i == len(xs) - 2 else JOINT / 2)
        box(f"coping_{i}", (b - a, T + 2 * COPING_OVER, COPING_H * rnd.uniform(0.94, 1.0)), ((a + b) / 2, 0, zc),
            mats["coping"], rot=(0, 0, rnd.uniform(-0.4, 0.4)), bevel=0.022)


def _floor(n):
    """Top of the stone a niche lies on."""
    return n * COURSE_H - JOINT / 2


def _sills(rnd, mats):
    for n in NICHES:
        z = _floor(n)
        w = NICHE_W + 0.08
        box(f"sill_{n}", (w, 0.12 + SILL_OVER, SILL_T), (rnd.uniform(-0.01, 0.01), -T / 2 + (0.12 - SILL_OVER) / 2,
            z + SILL_T / 2 - 0.006), mats["old"], rot=(0, rnd.uniform(-0.3, 0.3), 0), bevel=0.012)


def _shroud(rnd, mats):
    """A body wrapped in linen lying in the lower niche, head at -x: lumps for head, chest, hips, legs and feet, tied
    with cords at the neck, waist, knees and ankles."""
    z = _floor(NICHES[0]) + SILL_T - 0.01  # rests level with the sill
    y = -T / 2 + NICHE_D / 2 + 0.01
    s = BODY_L / 1.2
    # (x, half-length, half-width, half-height, material) along the body.
    lumps = [
        (0.0, 0.57, 0.13, 0.07, "shroud"),  # the long wrapping the lumps below swell out of
        (-0.5, 0.1, 0.085, 0.085, "shroud"),  # head
        (-0.23, 0.2, BODY_W / 2, 0.1, "shroud"),  # chest and shoulders
        (0.04, 0.17, 0.14, 0.095, "stain"),  # hands folded at the hips
        (0.3, 0.2, 0.11, 0.078, "shroud"),  # shins
        (0.5, 0.09, 0.08, 0.085, "stain"),  # feet
    ]
    for i, (x, hx, hy, hz, m) in enumerate(lumps):
        o = blob(f"shroud_{i}", 1.0, (x * s, y + rnd.uniform(-0.01, 0.01), z + hz * 0.82), mats[m],
                 squash=(hx * s, hy, hz), subdiv=2, seed=60 + i, jitter=0.05)
        o.rotation_euler = (0, 0, math.radians(rnd.uniform(-3, 3)))
    o = blob("shroud_toes", 0.05, (0.56 * s, y, z + 0.12), mats["shroud"], squash=(0.8, 1.2, 1.0), subdiv=1, seed=70,
             jitter=0.08)
    o.rotation_euler = (0, 0, 0)
    # The cords: thin rings round the wrapping, squashed to its cross-section.
    for i, (x, hy, hz) in enumerate([(-0.4, 0.072, 0.07), (0.1, 0.152, 0.098), (0.3, 0.122, 0.08),
                                     (0.44, 0.088, 0.074)]):
        r = torus(f"cord_{i}", hy + 0.004, 0.011, (x * s, y, z + hz * 0.82), mats["cord"], major=16, minor=6)
        r.scale = ((hz + 0.004) / (hy + 0.004), 1.0, 1.0)  # local x is world z after the 90 degree turn about y
        r.rotation_euler = (0, math.radians(90), math.radians(rnd.uniform(-4, 4)))


def _flat(obj):
    """Undo the random turn `blob` gives, so a squashed blob keeps its long axis on x."""
    obj.rotation_euler = (0, 0, 0)
    return obj


def _remains(rnd, mats):
    """The upper niche: a skull, two long bones and a drift of grave dust."""
    z = _floor(NICHES[1]) + SILL_T - 0.01
    y = -T / 2 + NICHE_D / 2 + 0.03
    _flat(blob("dust_0", 1.0, (0.05, y, z), mats["dust"], squash=(0.45, 0.15, 0.03), subdiv=2, seed=80, jitter=0.1))
    _flat(blob("dust_1", 1.0, (-0.38, y + 0.05, z), mats["dust"], squash=(0.2, 0.1, 0.025), subdiv=1, seed=81,
               jitter=0.1))
    sx, sy = 0.32, y - 0.03
    _flat(blob("skull", 0.085, (sx, sy, z + 0.075), mats["bone"], squash=(1.1, 0.9, 0.9), subdiv=2, seed=82, jitter=0.04))
    box("skull_jaw", (0.08, 0.1, 0.04), (sx - 0.02, sy - 0.035, z + 0.02), mats["bone"], rot=(0, 0, 10), bevel=0.012)
    for k, dx in enumerate((-0.03, 0.03)):
        blob(f"skull_eye_{k}", 0.022, (sx + dx, sy - 0.072, z + 0.085), mats["hollow"], subdiv=1, seed=83 + k,
             jitter=0.05)
    for k, (x0, x1, dy) in enumerate([(-0.3, 0.12, -0.02), (-0.18, 0.2, 0.06)]):
        length = x1 - x0
        cylinder(f"bone_{k}", 0.016, length, (x0, y + dy, z + 0.022), mats["bone"], segments=8,
                 rot=(0, 90, rnd.uniform(-12, 12)), bevel=0.0)
        for e, ex in enumerate((x0, x1)):
            _flat(blob(f"bone_{k}_end_{e}", 0.032, (ex, y + dy, z + 0.026), mats["bone"], squash=(0.8, 1.1, 0.8),
                       subdiv=1, seed=90 + 2 * k + e, jitter=0.1))


@prop
def wall_crypt_niche():
    rnd = random.Random(37)
    mats = _mats("wall_crypt_niche")
    _core(mats)
    _courses(rnd, mats)
    _coping(rnd, mats)
    _sills(rnd, mats)
    _shroud(rnd, mats)
    _remains(rnd, mats)
