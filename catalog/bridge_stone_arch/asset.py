"""A single-arch fieldstone bridge about 5 × 2.2 × 2 m: a humpbacked road of packed gravel rises from the ground at
both ends over a segmental arch of thirteen dressed voussoirs. The spandrels and the low parapets are faced with
rough, uneven fieldstones in rough courses, dark mortar showing between them; the parapets carry a row of flat coping
stones and end in a squat block at each corner (plan 3, item 17)."""
import math
import random

import bmesh
import bpy

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box as _box

# Overall dimensions (metres): the bridge runs along x, the road between the parapets along x too.
L = 5.0
WIDTH = 2.2
SPAN, RISE = 2.2, 0.8  # clear span and rise of the arch at its intrados
RING = 0.32  # voussoir depth
VOUSSOIRS = 13
Z_END, Z_CROWN = 0.07, 1.3  # road surface at the ends and over the crown
PARAPET_H = 0.5  # above the road
PARAPET_T = 0.3
COPING_T, COPING_OVER = 0.08, 0.03
END_BLOCK = (0.42, 0.38, 0.2)  # corner block: length, width, height above the parapet
ROAD_T = 0.06
FACE_T = 0.1  # depth of the facing stones
COURSE = (0.2, 0.3)  # course heights of the facing
STONE_W = (0.3, 0.6)
JOINT = 0.025
ARC_STEP = 6  # degrees between points of a curved edge

R_IN = (SPAN * SPAN / 4 + RISE * RISE) / (2 * RISE)
CZ = RISE - R_IN  # the arch centre, below the ground
R_OUT = R_IN + RING
HX, HY = L / 2, WIDTH / 2
CORE_Y = HY - FACE_T / 2  # the core's faces lie half way into the facing

STONE = (0.27, 0.255, 0.225)  # linear RGB: grey-brown fieldstone
STONE_OLD = (0.2, 0.19, 0.17)
STONE_PALE = (0.33, 0.315, 0.28)
STONE_WARM = (0.3, 0.25, 0.19)
DRESSED = (0.3, 0.285, 0.25)  # voussoirs and coping
MORTAR = (0.12, 0.11, 0.095)
GRAVEL = (0.17, 0.15, 0.12)
MOSS = (0.06, 0.085, 0.03)


def box(*args, **kwargs):
    """A box with a one-segment bevel (a chamfer): enough at this size, and half the triangles."""
    obj = _box(*args, **kwargs)
    if obj.modifiers:
        obj.modifiers[0].segments = 1
    return obj


def _beam(name, p, q, w, h, mat, extra=0.0, rot_x=0.0, bevel=0.02):
    """A box from p to q in the x-z plane (its length along pq, plus `extra`), `w` deep and `h` high."""
    dx, dz = q[0] - p[0], q[2] - p[2]
    mid = tuple((p[i] + q[i]) / 2 for i in range(3))
    return box(name, (math.hypot(dx, dz) + extra, w, h), mid, mat, rot=(rot_x, -math.degrees(math.atan2(dz, dx)), 0),
               bevel=bevel)


def _road(x):
    """Height of the road surface at x: a humpback easing to the ground at both ends."""
    u = min(1.0, abs(x) / HX)
    return Z_END + (Z_CROWN - Z_END) * 0.5 * (1 + math.cos(math.pi * u))


def _slope(x, h=0.01):
    return math.degrees(math.atan2(_road(x + h) - _road(x - h), 2 * h))


def _prism(name, outline, y0, y1, mat, bevel, segments=1):
    """A closed prism: the (x, z) `outline` extruded from `y0` to `y1`, its origin at the outline's centroid."""
    cx = sum(x for x, _ in outline) / len(outline)
    cz = sum(z for _, z in outline) / len(outline)
    bm = bmesh.new()
    front = [bm.verts.new((x - cx, y0, z - cz)) for x, z in outline]
    back = [bm.verts.new((x - cx, y1, z - cz)) for x, z in outline]
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
    obj.location = (cx, 0, cz)
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width, mod.segments, mod.limit_method = bevel, segments, "ANGLE"
        mod.angle_limit = math.radians(40)
    return obj


def _arc(r, a0, a1):
    """Points (x, z) on the circle of radius r round the arch centre, from angle a0 to a1 (degrees)."""
    n = max(1, round(abs(a1 - a0) / ARC_STEP))
    return [(r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), CZ + r * math.sin(math.radians(a0 + (a1 - a0) * k / n)))
            for k in range(n + 1)]


def _profile(z_off, x0=-HX, x1=HX, step=0.25):
    """Points (x, road(x) + z_off) from x0 to x1."""
    n = max(1, round((x1 - x0) / step))
    return [(x0 + (x1 - x0) * k / n, _road(x0 + (x1 - x0) * k / n) + z_off) for k in range(n + 1)]


@prop
def bridge_stone_arch():
    rnd = random.Random(1720)
    stones = [material(f"bridge_stone_arch_stone_{k}", c, vary=0.3, scale=7, crevice=0.65)
              for k, c in enumerate((STONE, STONE_OLD, STONE_PALE, STONE_WARM))]
    dressed = material("bridge_stone_arch_dressed", DRESSED, vary=0.25, scale=8, crevice=0.6)
    mortar = material("bridge_stone_arch_mortar", MORTAR, vary=0.15, scale=20, crevice=0.8)
    gravel = material("bridge_stone_arch_gravel", GRAVEL, rough=0.95, vary=0.45, scale=40, crevice=0.5)
    moss = material("bridge_stone_arch_moss", MOSS, rough=0.95, vary=0.35, scale=16)

    a_in = math.degrees(math.atan2(-CZ, math.sqrt(R_IN * R_IN - CZ * CZ)))  # where the intrados meets the ground
    a_out = math.degrees(math.atan2(-CZ, math.sqrt(R_OUT * R_OUT - CZ * CZ)))
    x_in, x_out = R_IN * math.cos(math.radians(a_in)), R_OUT * math.cos(math.radians(a_out))

    # The core: the spandrels up to just under the road, with the arch ring cut out of it.
    r_core = R_IN + 0.04
    a_core = math.degrees(math.atan2(-CZ, math.sqrt(r_core * r_core - CZ * CZ)))
    x_core = r_core * math.cos(math.radians(a_core))
    outline = [(-HX, 0.0), (-x_core, 0.0)] + _arc(r_core, 180 - a_core, a_core)[1:-1] + [(x_core, 0.0), (HX, 0.0)]
    outline += list(reversed(_profile(-ROAD_T + 0.01)))
    _prism("core", outline, -CORE_Y, CORE_Y, mortar, 0)

    # The road: packed gravel between the parapets, following the hump.
    top = _profile(0.0)
    road = top + list(reversed(_profile(-ROAD_T)))
    _prism("road", road, -(HY - PARAPET_T) - 0.01, HY - PARAPET_T + 0.01, gravel, 0.01)

    # The voussoirs, full depth: the first and last sit flat on the ground.
    span = 180 - 2 * a_in
    for k in range(VOUSSOIRS):
        a0 = a_in + span * k / VOUSSOIRS
        a1 = a_in + span * (k + 1) / VOUSSOIRS
        g = 0.35  # half a joint, in degrees
        a0, a1 = a0 + (g if k else 0), a1 - (g if k < VOUSSOIRS - 1 else 0)
        outer = _arc(R_OUT + rnd.uniform(0.0, 0.02), a1, a0)
        inner = _arc(R_IN, a0, a1)
        if k == 0:
            pts = [(x_in, 0.0), (x_out, 0.0)] + _arc(R_OUT, a_out, a1)[1:] + _arc(R_IN, a1, a0)[:-1]
        elif k == VOUSSOIRS - 1:
            pts = _arc(R_IN, a0, a1)[:-1] + [(-x_in, 0.0), (-x_out, 0.0)] + _arc(R_OUT, 180 - a_out, a0)[1:]
        else:
            pts = inner + outer
        _prism(f"voussoir_{k}", pts, -HY - 0.015, HY + 0.015, dressed, 0.02)

    # The parapets: a core wall on each side, a row of flat coping stones on it and a block at each end.
    for s in (-1, 1):
        wall = _profile(PARAPET_H - 0.01) + list(reversed(_profile(-ROAD_T)))
        y0, y1 = sorted((s * (HY - PARAPET_T), s * CORE_Y))
        _prism(f"parapet_{s}", wall, y0, y1, stones[1], 0.015)
        x = -HX + END_BLOCK[0] - 0.05
        k = 0
        while x < HX - END_BLOCK[0] + 0.05:
            w = min(rnd.uniform(0.38, 0.6), HX - END_BLOCK[0] + 0.05 - x)
            cx = x + w / 2
            xb = x + w
            y = s * (HY - PARAPET_T / 2 - 0.01)
            za, zb = _road(x) + PARAPET_H + COPING_T / 2 - 0.012, _road(xb) + PARAPET_H + COPING_T / 2 - 0.012
            _beam(f"coping_{s}_{k}", (x, y, za), (xb, y, zb), PARAPET_T + 2 * COPING_OVER, COPING_T, dressed,
                  extra=-0.015, rot_x=rnd.uniform(-1.5, 1.5))
            x += w
            k += 1
        for e in (-1, 1):
            bx = e * (HX - END_BLOCK[0] / 2)
            h = _road(bx) + PARAPET_H + END_BLOCK[2]
            box(f"end_{s}_{e}", (END_BLOCK[0], END_BLOCK[1], h), (bx, s * (HY - END_BLOCK[1] / 2), h / 2), dressed,
                rot=(0, 0, rnd.uniform(-2, 2)), bevel=0.025)

    # Facing: rough courses of fieldstones on both faces of the spandrels and parapets, clear of the arch ring.
    def top_at(x):
        return _road(x) + PARAPET_H - 0.015

    def clear(x, z):
        return abs(x) <= HX - END_BLOCK[0] - 0.01 and 0.0 <= z <= top_at(x) and math.hypot(x, z - CZ) >= R_OUT + 0.03

    def fits(x0, x1, z0, z1):
        xm = (x0 + x1) / 2
        return all(clear(x, z) for x in (x0, xm, x1) for z in (z0, z1))

    for s in (-1, 1):
        z0 = 0.0
        row = 0
        while z0 < Z_CROWN + PARAPET_H - 0.1:
            h = rnd.uniform(*COURSE)
            x = -HX + END_BLOCK[0] + rnd.uniform(0.0, 0.15)
            while x < HX - END_BLOCK[0] - 0.1:
                w = rnd.uniform(*STONE_W)
                x0, x1, z1 = x, x + w, z0 + h
                ok = fits(x0, x1, z0, z1)
                sloped = False
                if not ok:  # slope the top to the parapet, or trim the side towards the arch
                    if min(top_at(x0), top_at(x1)) - z0 > 0.1 and fits(x0, x1, z0, z0 + 0.1):
                        ok = sloped = True
                    else:
                        for _ in range(6):
                            if x1 - x0 < 0.2:
                                break
                            if abs(x0) < abs(x1):
                                x0 += 0.05
                            else:
                                x1 -= 0.05
                            if fits(x0, x1, z0, z1):
                                ok = True
                                break
                if ok and sloped:
                    j = JOINT / 2
                    quad = [(x0 + j, z0 + j), (x1 - j, z0 + j), (x1 - j, top_at(x1) - j), (x0 + j, top_at(x0) - j)]
                    d = FACE_T + rnd.uniform(0.0, 0.03)
                    yo = s * (HY + rnd.uniform(-0.005, 0.01))
                    _prism(f"face_{s}_{row}_{x:.2f}", quad, min(yo, yo - s * d), max(yo, yo - s * d),
                           rnd.choice(stones), 0.025)
                elif ok:
                    sw, sh = x1 - x0 - JOINT, z1 - z0 - JOINT
                    lift = 0.004 if z0 == 0.0 else 0.0
                    box(f"face_{s}_{row}_{x:.2f}", (sw, FACE_T + rnd.uniform(0.0, 0.03), sh * rnd.uniform(0.92, 1.0)),
                        ((x0 + x1) / 2 + rnd.uniform(-0.01, 0.01), s * (HY - FACE_T / 2 + rnd.uniform(-0.005, 0.01)),
                         z0 + sh / 2 + JOINT / 2 + lift),
                        rnd.choice(stones), rot=(rnd.uniform(-2, 2), 0, rnd.uniform(-1.5, 1.5)), bevel=0.03)
                x += w
            z0 += h
            row += 1

    # A few flat stones worked up through the gravel.
    for k in range(10):
        x = rnd.uniform(-HX + 0.3, HX - 0.3)
        y = rnd.uniform(-(HY - PARAPET_T) + 0.15, HY - PARAPET_T - 0.15)
        r = rnd.uniform(0.06, 0.11)
        blob(f"cobble_{k}", r, (x, y, _road(x) - r * 0.12), rnd.choice(stones), squash=(1.2, 1.0, 0.2), subdiv=1,
             seed=200 + k, jitter=0.2)

    # Moss in the shade at the foot of the arch and on a few coping stones.
    for k, (x, y, r) in enumerate(((-x_out - 0.15, -HY - 0.02, 0.22), (x_out + 0.2, HY + 0.02, 0.2))):
        box(f"moss_{k}", (r * 2, 0.04, r * 0.6), (x, y, r * 0.3 + 0.003), moss, rot=(0, 0, rnd.uniform(-3, 3)),
            bevel=0.01)
