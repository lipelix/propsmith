"""A large rusted iron admiralty anchor standing on its crown, front on -y: a tapered shank with a ring at the top, an
iron stock with ball ends across it under the ring, two curved arms ending in barbed flukes, tilted back to lean
on a tall coil of hemp rope behind it, the rope's end running up to the ring."""
import math
import random

from mathutils import Euler, Matrix, Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# Overall size: about 1.2 m across the arms (x), 0.8 m deep (y), 1.5 m high.
SHANK = 1.22  # crown to ring eye, along the shank
SHANK_R = (0.05, 0.034)  # shank radius at the crown and at the top
CROWN_R = 0.068
ARC_R, ARC_DEG = 0.62, 64  # the arms: a circle arc from the crown on each side
ARM_R = (0.046, 0.03)  # arm radius at the crown and at the fluke
FLUKE = (0.22, 0.24, 0.05)  # arrowhead length along the arm, width across, thickness (y)
STOCK_Z = SHANK - 0.17  # stock height along the shank
STOCK_L, STOCK_R, BALL_R = 0.66, 0.028, 0.045
RING_R, RING_T = 0.1, 0.02
TILT = 15  # degrees the anchor leans back (towards +y) onto the coil
BASE = (0.0, -0.31)  # where the crown stands (x, y)
COIL = (0.12, 0.06)  # the coil's centre (x, y)
COIL_R, ROPE_R, COIL_LAYERS = 0.25, 0.022, 8

IRON = (0.07, 0.05, 0.04)  # linear RGB: dark iron
RUST = (0.2, 0.085, 0.035)
RUST_DARK = (0.12, 0.06, 0.035)
ROPE = (0.34, 0.27, 0.16)  # hemp, as pier_wood
ROPE_OLD = (0.24, 0.19, 0.115)


def _frame():
    """The anchor's frame: local z up the shank from the crown, local x along the arms, leaning back by TILT."""
    return Matrix.Translation((BASE[0], BASE[1], CROWN_R)) @ Matrix.Rotation(math.radians(-TILT), 4, "X")


def _rod(name, m, a, b, r, mat, r_top=None, segments=10):
    """An iron rod (or rope) from local point a to local point b in the frame m."""
    pa, pb = m @ Vector(a), m @ Vector(b)
    d = pb - pa
    obj = cylinder(name, r, d.length, (0, 0, 0), mat, r_top=r_top, segments=segments, bevel=0)
    obj.location = pa
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return obj


def _orient(obj, m, local, rot):
    """Place obj at local point `local` in frame m, rotated by `rot` (degrees, XYZ) in that frame."""
    obj.location = m @ Vector(local)
    obj.rotation_euler = (m.to_3x3() @ Euler([math.radians(v) for v in rot]).to_matrix()).to_euler()
    return obj


@prop
def anchor_iron():
    rnd = random.Random(15)
    iron = material("anchor_iron_iron", IRON, rough=0.75, vary=0.45, scale=9, crevice=0.6, metal=0.4)
    rust = material("anchor_iron_rust", RUST, rough=0.95, vary=0.5, scale=14, crevice=0.7, metal=0.1)
    rust_dark = material("anchor_iron_rust_dark", RUST_DARK, rough=0.9, vary=0.45, scale=11, crevice=0.7, metal=0.2)
    rope = material("anchor_iron_rope", ROPE, vary=0.3, scale=30, crevice=0.6)
    rope_old = material("anchor_iron_rope_old", ROPE_OLD, vary=0.3, scale=30, crevice=0.6)
    m = _frame()

    # The coil of rope behind: rings stacked a little off true, the top one smaller and loose.
    cx, cy = COIL
    for k in range(COIL_LAYERS):
        R = COIL_R - 0.012 * (k % 3) - (0.03 if k == COIL_LAYERS - 1 else 0)
        torus(f"coil_{k}", R, ROPE_R, (cx + rnd.uniform(-0.012, 0.012), cy + rnd.uniform(-0.012, 0.012),
                                       ROPE_R + k * ROPE_R * 1.85), rope if k % 3 else rope_old,
              rot=(rnd.uniform(-2, 2), rnd.uniform(-2, 2), 0), major=24, minor=6)
    top_z = ROPE_R + (COIL_LAYERS - 1) * ROPE_R * 1.85
    cylinder("coil_core", COIL_R - 0.03, top_z - ROPE_R, (cx, cy, 0), rope_old, segments=16, bevel=0)
    for k, R in enumerate((0.17, 0.1)):  # the coil winds inwards on top
        torus(f"coil_top_{k}", R, ROPE_R, (cx + 0.01 * k, cy - 0.01 * k, top_z - 0.004), rope if k else rope_old,
              major=20 - 6 * k, minor=6)

    # The shank, the crown and the ring eye.
    _rod("shank", m, (0, 0, 0), (0, 0, SHANK), SHANK_R[0], rust, r_top=SHANK_R[1], segments=12)
    _orient(blob("crown", CROWN_R, (0, 0, 0), rust_dark, squash=(1.3, 0.85, 0.9), subdiv=2, seed=3, jitter=0.04),
            m, (0, 0, 0.0), (0, 0, 0))
    _orient(cylinder("eye", 0.05, 0.05, (0, 0, 0), iron, segments=12, bevel=0.006), m, (-0.025, 0, SHANK), (0, 90, 0))
    _orient(torus("ring", RING_R, RING_T, (0, 0, 0), iron, major=20, minor=8), m,
            (0, 0, SHANK + RING_R - 0.01), (0, 90, 0))

    # The stock across the shank under the ring, ball ends, and a collar where it passes through.
    _rod("stock", m, (0, -STOCK_L / 2, STOCK_Z), (0, STOCK_L / 2, STOCK_Z), STOCK_R, iron, segments=10)
    for s in (-1, 1):
        _orient(blob(f"stock_ball_{s}", BALL_R, (0, 0, 0), iron, subdiv=2, seed=10 + s, jitter=0.03), m,
                (0, s * STOCK_L / 2, STOCK_Z), (0, 0, 0))
    _orient(cylinder("stock_collar", 0.052, 0.07, (0, 0, 0), rust_dark, segments=12, bevel=0.006), m,
            (0, 0, STOCK_Z - 0.035), (0, 0, 0))

    # The arms: tapered rods along an arc on each side, ending in a spade fluke and a short bill.
    steps = 5
    for s in (-1, 1):
        pts = []
        for k in range(steps + 1):
            t = math.radians(ARC_DEG) * k / steps
            pts.append((s * ARC_R * math.sin(t), 0, ARC_R * (1 - math.cos(t))))
        for k in range(steps):
            r0 = ARM_R[0] + (ARM_R[1] - ARM_R[0]) * k / steps
            r1 = ARM_R[0] + (ARM_R[1] - ARM_R[0]) * (k + 1) / steps
            a, b = Vector(pts[k]), Vector(pts[k + 1])
            ext = (b - a).normalized() * r1 * 0.5
            _rod(f"arm_{s}_{k}", m, a - ext * (1 if k else 0), b + ext, r0, rust, r_top=r1)
        # The fluke: a flat barbed arrowhead in the plane of the arms, over the arm's end.
        t = math.radians(ARC_DEG)
        tip = Vector(pts[-1])
        tangent = Vector((s * math.cos(t), 0, math.sin(t)))
        ang = math.degrees(math.atan2(tangent.x, tangent.z))
        head = cylinder(f"fluke_{s}", FLUKE[1] / 2, FLUKE[0], (0, 0, 0), rust, r_top=0.004, segments=4, bevel=0.006)
        head.scale = (1, FLUKE[2] / FLUKE[1] * 2, 1)
        _orient(head, m, tip - tangent * (FLUKE[0] * 0.35), (0, ang, 0))

    # The rope's end: up from the coil's top, tied through the ring.
    top = (cx - 0.1, cy - 0.12, ROPE_R + COIL_LAYERS * ROPE_R * 1.85)
    ring_at = m @ Vector((0, 0, SHANK + 2 * RING_R - 0.02))
    mid = Vector(((top[0] + ring_at.x) / 2 + 0.06, (top[1] + ring_at.y) / 2 + 0.03, (top[2] + ring_at.z) / 2))
    path = [Vector(top), mid, ring_at]
    ident = Matrix.Identity(4)
    for k in range(len(path) - 1):
        _rod(f"rope_end_{k}", ident, path[k], path[k + 1], ROPE_R * 0.9, rope, segments=8)
    torus("rope_knot", 0.035, ROPE_R, tuple(ring_at), rope, rot=(90, 0, 90), major=12, minor=6)
