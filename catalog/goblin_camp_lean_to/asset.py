"""A crude goblin lean-to, about 2 x 2 m and 1.5 m high, open to the front (-y): two forked branch posts hold a
crooked ridge pole, five rough branch rafters lean steeply from it back to the ground, and ragged hides of tan, dark
brown and grey are thrown over them in overlapping rows, more hanging down the open sides and over the front as a flap
and two spread on the ground behind, weighed down with stones. Underneath, a bed of trodden straw with a matted grey fur on it and gnawed bones beside it; a stick by the
entrance carries a small horned skull, and a crude stone-tipped spear leans on a post.

Branches are bent cylinders (two lengths and a knot at the bend), bound where they cross with rope rings. Hides are
thin lumpy lenses laid in the plane of the rafters, so their outlines are ragged like real skins. The roof is steep
(SLOPE) because the review camera's 30 deg view runs along a roof of 25 to 50 deg and shows it edge-on."""
import math
import random

from mathutils import Matrix, Quaternion, Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall dimensions (metres), from the description: about 2 x 2 x 1.5 m.
X, Y, H = 2.0, 2.0, 1.5
FRONT_Y = -0.62  # the ridge pole and the posts
SLOPE = 60  # degrees: the roof leans back steeply from the ridge to the ground
SKIRT_Y = 0.5  # centre of the hides spread on the ground behind the roof
POST_X = 0.8
RIDGE_Z = 1.3  # centre of the ridge pole
RIDGE_R = 0.045
RIDGE_HALF = 0.96  # half its length
RAFTER_X = (-0.8, -0.42, -0.02, 0.4, 0.79)
RAFTER_R = 0.032
OVERHANG = 0.07  # how far the rafters run past the ridge
HIDE_T = 0.012  # half the thickness of a hide
BED = (0.0, -0.33, 0.6, 0.3)  # straw bed: centre x, y and radii x, y
BED_H = 0.09

BARK = (0.13, 0.09, 0.055)  # linear RGB: rough grey-brown bark
BARK_DARK = (0.08, 0.058, 0.038)
WOOD_PALE = (0.3, 0.22, 0.14)  # stripped ends
HIDE = (0.25, 0.165, 0.09)  # tanned hide
HIDE_DARK = (0.12, 0.075, 0.042)
HIDE_GREY = (0.17, 0.155, 0.13)
FUR = (0.13, 0.12, 0.105)  # matted grey fur
STRAW = (0.42, 0.32, 0.14)
STRAW_OLD = (0.26, 0.19, 0.085)
STRAW_DAMP = (0.16, 0.12, 0.06)
ROPE = (0.22, 0.17, 0.1)
BONE = (0.42, 0.38, 0.29)
STONE = (0.22, 0.215, 0.2)
FLINT = (0.09, 0.09, 0.095)


def _mats():
    return {
        "bark": material("goblin_camp_lean_to_bark", BARK, rough=0.95, vary=0.3, scale=18, crevice=0.6),
        "bark_dark": material("goblin_camp_lean_to_bark_dark", BARK_DARK, rough=0.95, vary=0.3, scale=18),
        "pale": material("goblin_camp_lean_to_wood_pale", WOOD_PALE, rough=0.85, vary=0.2, scale=20),
        "hide": material("goblin_camp_lean_to_hide", HIDE, rough=0.8, vary=0.3, scale=7, crevice=0.5),
        "hide_dark": material("goblin_camp_lean_to_hide_dark", HIDE_DARK, rough=0.85, vary=0.3, scale=7, crevice=0.5),
        "hide_grey": material("goblin_camp_lean_to_hide_grey", HIDE_GREY, rough=0.9, vary=0.3, scale=9, crevice=0.5),
        "fur": material("goblin_camp_lean_to_fur", FUR, rough=0.98, vary=0.35, scale=30, crevice=0.6),
        "straw": material("goblin_camp_lean_to_straw", STRAW, rough=0.9, vary=0.25, scale=40, crevice=0.4),
        "straw_old": material("goblin_camp_lean_to_straw_old", STRAW_OLD, rough=0.95, vary=0.3, scale=40),
        "straw_damp": material("goblin_camp_lean_to_straw_damp", STRAW_DAMP, rough=0.95, vary=0.3, scale=30),
        "rope": material("goblin_camp_lean_to_rope", ROPE, rough=0.95, vary=0.25, scale=40),
        "bone": material("goblin_camp_lean_to_bone", BONE, rough=0.7, vary=0.2, scale=20, crevice=0.6),
        "stone": material("goblin_camp_lean_to_stone", STONE, rough=0.9, vary=0.28, scale=12, crevice=0.7),
        "flint": material("goblin_camp_lean_to_flint", FLINT, rough=0.4, vary=0.2, scale=20),
    }


def _pole(name, a, b, r, mat, r_end=None, segments=7):
    """A round pole from `a` to `b` (points), `r` thick at `a` and `r_end` at `b`."""
    a, b = Vector(a), Vector(b)
    d = b - a
    obj = cylinder(name, r, d.length, (0, 0, 0), mat, r_top=r_end or r, segments=segments, bevel=0)
    obj.location = a
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return obj


def _branch(name, a, b, r, mat, rnd, bend=0.04, end=None):
    """A crooked branch from `a` to `b`: two lengths meeting at a bend pushed sideways by up to `bend`, a knot there,
    and a pale broken-off end in material `end` when given."""
    a, b = Vector(a), Vector(b)
    mid = a.lerp(b, rnd.uniform(0.4, 0.6))
    d = (b - a).normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(d)
    mid += side * rnd.uniform(-bend, bend) + up * rnd.uniform(-bend, bend) * 0.6
    _pole(f"{name}_a", a, mid, r, mat, r_end=r * 0.92)
    _pole(f"{name}_b", mid, b, r * 0.92, mat, r_end=r * 0.75)
    blob(f"{name}_knot", r * 1.05, mid, mat, squash=(1, 1, 1), subdiv=1, seed=rnd.randrange(999), jitter=0.12)
    if end:
        blob(f"{name}_end", r * 0.8, b, end, subdiv=1, seed=rnd.randrange(999), jitter=0.1)


def _frame(u, n):
    """A rotation whose local x is world x, local y is `u` and local z is `n`."""
    x = u.cross(n).normalized()
    return Matrix((x, u, n)).transposed().to_quaternion()


def _hide(name, centre, half, frame, spin, mat, seed):
    """A ragged hide: a thin lumpy lens `half` (x, y) half-sized around `centre`, lying in the plane of `frame`."""
    r = max(half)
    obj = blob(name, r, centre, mat, squash=(half[0] / r, half[1] / r, HIDE_T / r), subdiv=2, seed=seed, jitter=0.2)
    obj.rotation_euler = (frame @ Quaternion((0, 0, 1), math.radians(spin))).to_euler()
    return obj


def _ring(name, at, axis, r, mat):
    """A rope lashing ring of radius `r` round `axis` at `at`."""
    obj = torus(name, r, 0.011, at, mat, major=10, minor=4)
    obj.rotation_euler = Vector(axis).to_track_quat("Z", "Y").to_euler()
    return obj


@prop
def goblin_camp_lean_to():
    rnd = random.Random(2424)
    mats = _mats()

    # Forked posts at the front corners, the ridge pole lying in their forks.
    fork_z = RIDGE_Z - 0.06
    for side in (-1, 1):
        x = side * POST_X
        _branch(f"post_{side}", (x, FRONT_Y, 0.0), (x + side * 0.02, FRONT_Y, fork_z), 0.05, mats["bark"], rnd, 0.025,
                mats["pale"])
        for k, dy in enumerate((-1, 1)):
            _pole(f"fork_{side}_{k}", (x + side * 0.02, FRONT_Y, fork_z - 0.03),
                  (x + side * 0.04, FRONT_Y + dy * 0.1, RIDGE_Z + 0.09), 0.03, mats["bark"], r_end=0.02)
        _ring(f"post_lash_{side}", (x + side * 0.02, FRONT_Y, fork_z - 0.05), (0, 0, 1), 0.058, mats["rope"])
    _branch("ridge", (-RIDGE_HALF, FRONT_Y + 0.01, RIDGE_Z - 0.01), (RIDGE_HALF, FRONT_Y - 0.01, RIDGE_Z + 0.01),
            RIDGE_R, mats["bark_dark"], rnd, 0.02, mats["pale"])

    # Rafters from the ground at the back up to the ridge, running a little past it.
    top_z = RIDGE_Z + RIDGE_R + RAFTER_R
    back_y = FRONT_Y + (top_z - RAFTER_R) / math.tan(math.radians(SLOPE))
    for i, x in enumerate(RAFTER_X):
        x += rnd.uniform(-0.03, 0.03)
        g = Vector((x + rnd.uniform(-0.04, 0.04), back_y + rnd.uniform(-0.03, 0.03), RAFTER_R))
        t = Vector((x, FRONT_Y, top_z))
        u = (t - g).normalized()
        end = t + u * (OVERHANG + rnd.uniform(-0.03, 0.03))
        mat = mats["bark_dark"] if i % 2 else mats["bark"]
        _branch(f"rafter_{i}", g, end, RAFTER_R * rnd.uniform(0.9, 1.1), mat, rnd, 0.03, mats["pale"])
        if i in (0, 2, 4):
            _ring(f"rafter_lash_{i}", (x, FRONT_Y, RIDGE_Z + 0.01), (1, 0.3, 0.4), 0.06, mats["rope"])

    # The roof plane the hides lie in.
    g = Vector((0, back_y, RAFTER_R))
    t = Vector((0, FRONT_Y, top_z + RAFTER_R))
    u = (t - g).normalized()
    n = Vector((0, u.z, -u.y))
    roof = _frame(u, n)
    length = (t - g).length
    hides = [  # (centre x, share up the roof, half x, half along, material, spin)
        (-0.43, 0.24, 0.46, 0.34, "hide_dark", 8),
        (0.42, 0.22, 0.46, 0.32, "hide", -6),
        (-0.42, 0.52, 0.46, 0.36, "hide", -10),
        (0.44, 0.54, 0.44, 0.36, "hide_grey", 12),
        (-0.4, 0.8, 0.46, 0.3, "hide_grey", 5),
        (0.38, 0.82, 0.48, 0.31, "hide_dark", -4),
        (0.0, 0.66, 0.32, 0.28, "hide", 30),
    ]
    for i, (x, s, hx, hy, mat, spin) in enumerate(hides):
        s = 0.3 + 0.62 * s  # rows from just off the ground to the ridge
        at = g + u * (s * length) + n * (RAFTER_R + HIDE_T * (1.5 + 2.2 * (i % 3))) + Vector((x, 0, 0))
        _hide(f"hide_{i}", at, (hx, hy), roof, spin, mats[mat], 70 + i)
    # A flap hanging over the front from the ridge, leaning out a little.
    flap = _frame(Vector((0, -0.25, -1)).normalized(), Vector((0, -1, 0.25)).normalized())
    _hide("hide_flap", Vector((0.42, FRONT_Y - 0.1, RIDGE_Z - 0.2)), (0.3, 0.24), flap, 8, mats["hide"], 79)
    _ring("flap_tie", (0.42, FRONT_Y - 0.01, RIDGE_Z + 0.005), (1, 0, 0), 0.055, mats["rope"])

    # Hides hanging off the outer rafters down the open sides.
    for side, mat, seed in ((-1, "hide_grey", 81), (1, "hide", 82)):
        hang = _frame(u, Vector((side, 0, 0)))
        at = g + u * (0.5 * length) - n * 0.24 + Vector((side * (abs(RAFTER_X[0 if side < 0 else -1]) + 0.05), 0, 0))
        _hide(f"hide_side_{side}", at, (0.56, 0.26), hang, side * 4, mats[mat], seed)
    # Hides spread on the ground behind, where the roof meets it, weighed down with stones.
    for i, (x, hx, mat) in enumerate(((-0.45, 0.5, "hide_dark"), (0.44, 0.5, "hide"))):
        _hide(f"hide_skirt_{i}", Vector((x, SKIRT_Y, HIDE_T * 1.25)), (hx, 0.36), _frame(Vector((0, 1, 0)),
              Vector((0, 0, 1))), rnd.uniform(-8, 8), mats[mat], 85 + i)
    for i, (x, y) in enumerate(((-0.72, 0.62), (-0.2, 0.78), (0.3, 0.5), (0.75, 0.72), (-0.5, 0.3))):
        r = rnd.uniform(0.07, 0.095)
        blob(f"weight_{i}", r, (x, y, 2 * HIDE_T + r * 0.62), mats["stone"], squash=(1.2, 1, 0.7), subdiv=1,
             seed=95 + i, jitter=0.12)

    # The straw bed: a trodden mound, loose stalks over it and a matted fur on top.
    bx, by, rx, ry = BED
    bed = blob("bed", rx, (bx, by, BED_H / 2 + 0.004), mats["straw_damp"], squash=(1, ry / rx, BED_H / 2 / rx * 1.05),
               subdiv=2, seed=101, jitter=0.08)
    bed.rotation_euler = (0, 0, 0)
    for i in range(70):
        a = rnd.uniform(0, 2 * math.pi)
        d = math.sqrt(rnd.random())
        x, y = bx + rx * 1.05 * d * math.cos(a), by + ry * 1.05 * d * math.sin(a)
        z = BED_H * (1 - d * d) * 0.95 + 0.004
        mat = mats[rnd.choice(("straw", "straw", "straw_old", "straw_old", "straw_damp"))]
        box(f"stalk_{i}", (rnd.uniform(0.12, 0.22), 0.011, 0.005), (x, y, z), mat,
            rot=(rnd.uniform(-8, 8), rnd.uniform(-8, 8), rnd.uniform(0, 180)), bevel=0)
    fur = blob("fur", 0.36, (0.08, 0.12, BED_H + 0.01), mats["fur"], squash=(1, 0.68, 0.07), subdiv=2, seed=111,
               jitter=0.18)
    fur.rotation_euler = (math.radians(3), math.radians(-2), math.radians(18))

    # Gnawed bones beside the bed.
    for i, (x, y, yaw, ln) in enumerate(((-0.5, -0.78, 20, 0.24), (-0.3, -0.85, 115, 0.18), (0.66, -0.72, 70, 0.2))):
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        a = Vector((x - c * ln / 2, y - s * ln / 2, 0.016))
        b = Vector((x + c * ln / 2, y + s * ln / 2, 0.016))
        _pole(f"bone_{i}", a, b, 0.014, mats["bone"], segments=6)
        for k, p in enumerate((a, b)):
            blob(f"bone_{i}_knob_{k}", 0.024, (p.x, p.y, 0.022), mats["bone"], squash=(1, 0.8, 0.9), subdiv=1,
                 seed=120 + 2 * i + k, jitter=0.12)

    # A stick by the entrance with a small horned skull on top.
    sx, sy = 0.84, -0.94
    _branch("totem", (sx, sy, 0.0), (sx + 0.03, sy, 1.12), 0.022, mats["bark_dark"], rnd, 0.03)
    skull_at = Vector((sx + 0.03, sy, 1.2))
    blob("skull", 0.075, skull_at, mats["bone"], squash=(0.85, 1.25, 0.85), subdiv=2, seed=131, jitter=0.06)
    blob("skull_snout", 0.045, skull_at + Vector((0, -0.09, -0.03)), mats["bone"], squash=(0.8, 1.2, 0.75),
         subdiv=1, seed=132, jitter=0.05)
    for k, side in enumerate((-1, 1)):
        blob(f"skull_eye_{k}", 0.018, skull_at + Vector((side * 0.038, -0.06, 0.012)), mats["flint"], subdiv=1,
             seed=133 + k, jitter=0.05)
        _pole(f"skull_horn_{k}", skull_at + Vector((side * 0.045, 0.02, 0.04)),
              skull_at + Vector((side * 0.14, 0.06, 0.15)), 0.018, mats["bone"], r_end=0.004, segments=6)

    # A crude spear leaning on the left post, its flint head up.
    foot = Vector((-POST_X - 0.16, FRONT_Y - 0.12, 0.012))
    head = Vector((-POST_X + 0.02, FRONT_Y - 0.04, 1.36))
    _pole("spear_shaft", foot, head, 0.014, mats["pale"], segments=6)
    d = (head - foot).normalized()
    tip = _pole("spear_head", head - d * 0.02, head + d * 0.11, 0.028, mats["flint"], r_end=0.002, segments=4)
    tip.scale = (1, 0.35, 1)
    _ring("spear_bind", head - d * 0.01, d, 0.02, mats["rope"])
