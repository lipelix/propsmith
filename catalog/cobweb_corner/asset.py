"""A dusty cobweb strung across a corner, about 1 x 1 x 1 m: two short stubs of dark crypt ashlar meet in an L at the
back left, and a pale grey orb web hangs on a diagonal plane between their inner faces, facing the viewer. Radial
threads run from an off-centre hub to the two stubs, the floor and a sagging bridge thread at the top; a loose spiral
crosses them, a few strands broken and drooping, with grey clots of dust caught at the hub and the anchors."""
import math
import random

from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

SPAN = 1.0  # footprint across x and y
H = 1.0  # height of the stubs
STUB_T = 0.22  # stub thickness
CORNER = (-SPAN / 2, SPAN / 2)  # outer corner of the L (back left)
COURSES = 4
JOINT = 0.012
WEB_IN = 0.52  # the web meets each stub this far out from the inner corner
WEB_BOTTOM = 0.04  # lowest anchors, just over the floor
WEB_TOP = 0.93  # the bridge thread's ends
SAG = 0.08  # how far the bridge thread sags in the middle
HUB = (0.0, 0.56)  # hub position on the web plane: across (-1..1 of the half width) and height
RADIALS = 14
RINGS = 10
RADIAL_R = 0.006  # radial and frame thread radius
SPIRAL_R = 0.0045

# Crypt stone palette (shared with wall_crypt_* and pillar_stone): keep them equal.
STONE = (0.19, 0.195, 0.205)  # linear RGB: cool dark blue-grey ashlar
STONE_OLD = (0.145, 0.148, 0.155)
STONE_PALE = (0.24, 0.243, 0.25)
DAMP = (0.1, 0.11, 0.098)
MORTAR = (0.04, 0.04, 0.042)
SILK = (0.5, 0.49, 0.47)  # dusty grey thread
DUST = (0.3, 0.29, 0.275)


def _rod(name, p0, p1, r, mat, segments=5):
    """A thin cylinder from point `p0` to point `p1`."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    yaw = math.degrees(math.atan2(d.y, d.x))
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, d.z / d.length))))
    return cylinder(name, r, d.length, p0, mat, segments=segments, rot=(0, 90 - pitch, yaw), bevel=0)


def _stub(name, x0, x1, y0, y1, along_x, mats, rnd):
    """A short wall stub of staggered ashlar courses over a dark mortar core, its top course broken unevenly."""
    ch = H / COURSES
    box(f"{name}_core", (x1 - x0 - 0.04, y1 - y0 - 0.04, H - 0.06), ((x0 + x1) / 2, (y0 + y1) / 2, (H - 0.06) / 2),
        mats["mortar"], bevel=0)
    lo, hi = (x0, x1) if along_x else (y0, y1)
    for c in range(COURSES):
        z0 = c * ch
        cuts = [lo, lo + (0.42 if c % 2 == 0 else 0.26) * (hi - lo) + rnd.uniform(-0.03, 0.03), hi]
        if c % 2:
            cuts.insert(2, lo + 0.68 * (hi - lo) + rnd.uniform(-0.03, 0.03))
        for i in range(len(cuts) - 1):
            a, b = cuts[i] + JOINT / 2, cuts[i + 1] - JOINT / 2
            h = ch - JOINT
            if c == COURSES - 1 and i == len(cuts) - 2:
                h *= rnd.uniform(0.55, 0.7)  # a broken-down top block
            mat = rnd.choice([mats["stone"], mats["stone"], mats["old"], mats["pale"]])
            if c == 0 and rnd.random() < 0.6:
                mat = mats["damp"]
            if along_x:
                size, at = (b - a, y1 - y0, h), ((a + b) / 2, (y0 + y1) / 2, z0 + JOINT / 2 + h / 2)
            else:
                size, at = (x1 - x0, b - a, h), ((x0 + x1) / 2, (a + b) / 2, z0 + JOINT / 2 + h / 2)
            box(f"{name}_{c}_{i}", size, at, mat, rot=(0, 0, rnd.uniform(-0.8, 0.8)), bevel=rnd.uniform(0.014, 0.022))


def _edge(theta, left, right):
    """Where a ray from the hub at angle `theta` (in the web plane, 0 = across to the right) meets the web's frame:
    the two stub lines, the floor and the sagging bridge thread. Returns (u, z)."""
    hu, hz = HUB[0] * right, HUB[1]
    du, dz = math.cos(theta), math.sin(theta)
    best = None
    for t in [((right - hu) / du) if du > 1e-6 else None, ((left - hu) / du) if du < -1e-6 else None,
              ((WEB_BOTTOM - hz) / dz) if dz < -1e-6 else None]:
        if t is not None and t > 0 and (best is None or t < best):
            best = t
    if dz > 1e-6:  # the bridge thread: z = WEB_TOP - SAG * (1 - (u/right)^2)
        lo, hi = 0.0, best if best is not None else 2.0
        for _ in range(40):
            mid = (lo + hi) / 2
            u, z = hu + du * mid, hz + dz * mid
            if z < WEB_TOP - SAG * (1 - (u / right) ** 2):
                lo = mid
            else:
                hi = mid
        best = lo
    return hu + du * best, hz + dz * best


@prop
def cobweb_corner():
    rnd = random.Random(808)
    mats = {
        "stone": material("cobweb_corner_stone", STONE, vary=0.22, scale=7, crevice=0.7),
        "old": material("cobweb_corner_stone_old", STONE_OLD, vary=0.25, scale=8, crevice=0.7),
        "pale": material("cobweb_corner_stone_pale", STONE_PALE, vary=0.2, scale=9, crevice=0.65),
        "damp": material("cobweb_corner_damp", DAMP, rough=0.6, vary=0.3, scale=5, crevice=0.75),
        "mortar": material("cobweb_corner_mortar", MORTAR, vary=0.12, scale=20, crevice=0.9),
    }
    silk = material("cobweb_corner_silk", SILK, rough=0.7, vary=0.15, scale=30, crevice=0.1)
    dust = material("cobweb_corner_dust", DUST, rough=0.95, vary=0.3, scale=40, crevice=0.3)

    cx, cy = CORNER
    # Back stub along x, left stub along y; they share the corner block column.
    _stub("stub_back", cx, cx + SPAN - 0.02, cy - STUB_T, cy, True, mats, rnd)
    _stub("stub_left", cx, cx + STUB_T, -SPAN / 2 + 0.02, cy - STUB_T - JOINT, False, mats, rnd)

    # The web plane: vertical, across the inner corner from the left stub's face to the back stub's face.
    ix, iy = cx + STUB_T, cy - STUB_T  # inner corner
    a = Vector((ix + WEB_IN, iy, 0))  # on the back stub's face
    b = Vector((ix, iy - WEB_IN, 0))  # on the left stub's face
    mid = (a + b) / 2
    across = (a - b).normalized()
    half = (a - b).length / 2

    def at(u, z):
        p = mid + across * u
        return (p.x, p.y, z)

    hub = (HUB[0] * half, HUB[1])
    # Radial anchors on the frame, unevenly spaced.
    thetas = sorted((2 * math.pi * (i + rnd.uniform(-0.25, 0.25)) / RADIALS) % (2 * math.pi) for i in range(RADIALS))
    ends = [_edge(t, -half, half) for t in thetas]
    for i, (u, z) in enumerate(ends):
        _rod(f"radial_{i}", at(*hub), at(u, z), RADIAL_R, silk)
    # Frame: the sagging bridge thread at the top.
    steps = 8
    for i in range(steps):
        u0, u1 = -half + 2 * half * i / steps, -half + 2 * half * (i + 1) / steps
        z0 = WEB_TOP - SAG * (1 - (u0 / half) ** 2)
        z1 = WEB_TOP - SAG * (1 - (u1 / half) ** 2)
        _rod(f"bridge_{i}", at(u0, z0), at(u1, z1), RADIAL_R, silk)

    # The spiral: rings at growing fractions of each radial, each span sagging a little; a few broken.
    for k in range(RINGS):
        f = 0.12 + 0.82 * (k + 0.5) / RINGS
        pts = []
        for (u, z) in ends:
            g = min(0.97, f * rnd.uniform(0.93, 1.05))
            pts.append((hub[0] + (u - hub[0]) * g, hub[1] + (z - hub[1]) * g))
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            if rnd.random() < 0.1:
                # A broken span: one end hangs down as a drooping strand.
                drop = rnd.uniform(0.06, 0.16)
                _rod(f"spiral_{k}_{i}_droop", at(*p), at(p[0] + rnd.uniform(-0.02, 0.02), max(0.02, p[1] - drop)),
                     SPIRAL_R, silk)
                continue
            m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 - 0.006 - 0.01 * f)
            _rod(f"spiral_{k}_{i}_a", at(*p), at(*m), SPIRAL_R, silk)
            _rod(f"spiral_{k}_{i}_b", at(*m), at(*q), SPIRAL_R, silk)

    # Loose strands hanging from the bridge thread.
    for i in range(4):
        u = rnd.uniform(-0.8, 0.8) * half
        z = WEB_TOP - SAG * (1 - (u / half) ** 2)
        _rod(f"strand_{i}", at(u, z), at(u + rnd.uniform(-0.03, 0.03), z - rnd.uniform(0.12, 0.3)), SPIRAL_R, silk)

    # Dust caught at the hub and the anchors, and a little settled on the floor in the corner.
    blob("dust_hub", 0.03, at(*hub), dust, squash=(1, 1, 0.8), subdiv=1, seed=11, jitter=0.35)
    for i, (u, z) in enumerate(ends):
        if rnd.random() < 0.55:
            blob(f"dust_{i}", rnd.uniform(0.012, 0.02), at(u * 0.97, max(0.03, z)), dust, squash=(1, 1, 0.8),
                 subdiv=1, seed=rnd.randint(0, 9999), jitter=0.35)
    for i in range(6):
        x, y = ix + rnd.uniform(0.02, 0.2), iy - rnd.uniform(0.02, 0.2)
        r = rnd.uniform(0.02, 0.04)
        blob(f"floor_dust_{i}", r, (x, y, r * 0.3), dust, squash=(1.4, 1.2, 0.3), subdiv=1, seed=rnd.randint(0, 9999),
             jitter=0.3)
