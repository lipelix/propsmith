"""A gibbet: a tall square oak post on a cross of sill beams with four foot braces, a heavy arm pegged through its top
and held by a diagonal brace, and from an iron staple at the arm's end a short chain to an iron body cage: hoops of flat
iron following a person's shape from the feet to a domed head, joined by vertical straps, with a ring on top."""
import math
import random

from mathutils import Quaternion, Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall dimensions (metres): about 1.5 m wide (x), 0.8 m deep, 4 m high.
POST = 0.22
POST_X = -0.5  # the post, left of centre; the arm reaches out over +x
POST_TOP = 3.93
SILL = (0.14, 0.16)  # sill beam width and height
SILL_LX, SILL_LY = 0.5, 0.8  # the cross of sills under the post
ARM = 0.18  # square arm
ARM_Z = 3.76  # arm centre height
ARM_END = 0.62
CAGE_X = 0.36  # the cage hangs here
CAGE_TOP = 3.36  # top of the cage's ring
LINK_R, LINK_T, LINK_PITCH = 0.03, 0.008, 0.05
# The cage: (height above its foot, half width in x, half depth in y) from the feet to the crown.
PROFILE = [(0.0, 0.11, 0.09), (0.45, 0.14, 0.11), (0.9, 0.19, 0.13), (1.25, 0.23, 0.15), (1.42, 0.11, 0.1),
           (1.6, 0.12, 0.12), (1.72, 0.0, 0.0)]
CAGE_H = 1.72
STRAPS = 6

OAK = (0.17, 0.11, 0.065)  # linear RGB, weathered
OAK_OLD = (0.14, 0.10, 0.07)
STONE = (0.3, 0.28, 0.25)
IRON = (0.045, 0.044, 0.042)
IRON_WORN = (0.1, 0.092, 0.082)
RUST = (0.1, 0.055, 0.033)


def _euler(q):
    return tuple(math.degrees(a) for a in q.to_euler("XYZ"))


def _rot_to(d):
    """Rotation (degrees, XYZ) that turns local +z onto direction `d`."""
    return _euler(Vector((0, 0, 1)).rotation_difference(Vector(d).normalized()))


def _bar(name, a, b, mat, w=0.022, t=0.01):
    """A flat iron strap from `a` to `b`."""
    a, b = Vector(a), Vector(b)
    d = b - a
    return box(name, (w, t, d.length), tuple((a + b) / 2), mat, rot=_rot_to(d), bevel=0)


def _chain(name, a, b, mat):
    a, b = Vector(a), Vector(b)
    d = b - a
    n = max(2, round(d.length / LINK_PITCH))
    q = Vector((1, 0, 0)).rotation_difference(d.normalized())
    for i in range(n):
        qi = q @ Quaternion((1, 0, 0), math.pi / 2) if i % 2 else q
        torus(f"{name}_{i}", LINK_R, LINK_T, tuple(a + d * ((i + 0.5) / n)), mat, rot=_euler(qi), major=8, minor=5)


@prop
def gibbet_post():
    rnd = random.Random(13)
    oak = material("gibbet_post_oak", OAK, vary=0.3, scale=12)
    old = material("gibbet_post_oak_old", OAK_OLD, vary=0.3, scale=12)
    stone = material("gibbet_post_stone", STONE, vary=0.25, scale=8)
    iron = material("gibbet_post_iron", IRON, rough=0.55, vary=0.25, scale=18, metal=0.6)
    worn = material("gibbet_post_iron_worn", IRON_WORN, rough=0.5, vary=0.25, scale=22, metal=0.7)
    rust = material("gibbet_post_rust", RUST, rough=0.85, vary=0.3, scale=24, metal=0.25)

    # Cross of sills on the ground, a few stones packed round them, four foot braces up to the post.
    sw, sh = SILL
    box("sill_x", (SILL_LX, sw, sh), (POST_X, 0, sh / 2), old, rot=(0, 0, 1), bevel=0.014)
    box("sill_y", (sw, SILL_LY, sh), (POST_X, 0, sh / 2), old, rot=(0, 0, -0.8), bevel=0.014)
    for k in range(5):
        a = math.radians(45 + 90 * k + rnd.uniform(-20, 20)) if k < 4 else math.radians(200)
        r, sr = rnd.uniform(0.17, 0.22), rnd.uniform(0.06, 0.08)
        blob(f"stone_{k}", sr, (POST_X + r * math.cos(a), r * math.sin(a), sr * 0.75 * 1.1), stone,
             squash=(1.2, 1, 0.75), subdiv=1, seed=40 + k)
    for k, (dx, dy) in enumerate(((-1, 0), (1, 0), (0, -1), (0, 1))):
        reach = SILL_LX / 2 - 0.05 if dx else SILL_LY / 2 - 0.06
        a = Vector((POST_X + dx * reach, dy * reach, sh - 0.02))
        b = Vector((POST_X + dx * (POST / 2 - 0.01), dy * (POST / 2 - 0.01), sh + 0.6))
        d = b - a
        box(f"foot_brace_{k}", (0.09, 0.09, d.length), tuple((a + b) / 2), oak, rot=_rot_to(d), bevel=0.01)

    # The post, its cap, the arm through its top and the brace under the arm.
    box("post", (POST, POST, POST_TOP - sh + 0.02), (POST_X, 0, (POST_TOP + sh - 0.02) / 2), oak,
        rot=(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0), bevel=0.02)
    box("cap", (POST + 0.05, POST + 0.05, 0.05), (POST_X, 0, POST_TOP + 0.025), old, rot=(0, 0, 3), bevel=0.012)
    x0 = POST_X - POST / 2 - 0.1
    box("arm", (ARM_END - x0, ARM, ARM), ((x0 + ARM_END) / 2, 0, ARM_Z), oak, rot=(0, 0.6, 0), bevel=0.018)
    for k, dy in enumerate((-1, 1)):
        cylinder(f"arm_peg_{k}", 0.018, 0.03, (POST_X, dy * (POST / 2), ARM_Z), old, segments=8,
                 rot=(dy * -90, 0, 0), bevel=0)
    a = Vector((POST_X + POST / 2 - 0.02, 0, ARM_Z - 0.75))
    b = Vector((0.1, 0, ARM_Z - ARM / 2 + 0.02))
    d = b - a
    box("arm_brace", (0.12, 0.12, d.length), tuple((a + b) / 2), old, rot=_rot_to(d), bevel=0.012)
    for k, p in enumerate((a + d * 0.06, a + d * 0.94)):
        cylinder(f"brace_peg_{k}", 0.016, 0.02, (p.x, -0.06, p.z), worn, segments=8, rot=(90, 0, 0), bevel=0)

    # Iron band round the arm and a staple under it, the chain down to the cage's ring.
    box("arm_band", (0.05, ARM + 0.012, ARM + 0.012), (CAGE_X, 0, ARM_Z), iron, bevel=0.003)
    torus("staple", 0.03, 0.009, (CAGE_X, 0, ARM_Z - ARM / 2 - 0.02), iron, rot=(90, 0, 0), major=10, minor=6)
    ring_z = CAGE_TOP - 0.04
    _chain("chain", (CAGE_X, 0, ARM_Z - ARM / 2 - 0.05), (CAGE_X, 0, ring_z + 0.035), iron)
    torus("cage_ring", 0.04, 0.01, (CAGE_X, 0, ring_z), worn, rot=(0, 90, 0), major=12, minor=6)

    # The cage: hoops at each profile height and straps from the feet over the head.
    foot = CAGE_TOP - 0.08 - CAGE_H
    for i, (z, hx, hy) in enumerate(PROFILE[:-1]):
        o = torus(f"hoop_{i}", hx, 0.012, (CAGE_X, 0, foot + z), rust if i in (1, 4) else iron, major=18, minor=4)
        o.scale = (1, hy / hx, 1.6)
    box("foot_plate", (2 * PROFILE[0][1] + 0.03, 2 * PROFILE[0][2] + 0.03, 0.014), (CAGE_X, 0, foot), worn,
        bevel=0.004)
    for s in range(STRAPS):
        a = 2 * math.pi * (s + 0.5) / STRAPS
        pts = [Vector((CAGE_X + hx * math.cos(a), hy * math.sin(a), foot + z)) for z, hx, hy in PROFILE]
        for i in range(len(pts) - 1):
            _bar(f"strap_{s}_{i}", pts[i], pts[i + 1], worn if (s + i) % 5 == 0 else iron)
    # A crown boss where the straps meet on top.
    cylinder("crown", 0.035, 0.03, (CAGE_X, 0, foot + CAGE_H - 0.015), iron, segments=8, bevel=0.004)
