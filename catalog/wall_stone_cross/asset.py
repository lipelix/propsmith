"""A crossing of village fieldstone wall: arms running 0.75 m to +x, -x, +y and -y from a pier at the origin; rough
stone blocks in staggered courses over a recessed mortar core, flat capstones on top
(by hand from wall_stone_corner). The `_rubble` variants (two seeded layouts) are the same crossing in rubble
stone, see the rubble block below."""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box

MODULE = 1.5  # metres: the length wall and fence sections join at
EDGE = MODULE / 2  # the arms end half a module out, where straight sections centred a module away begin
T = 0.45  # wall thickness, metres
H = 2.4  # overall height including the capstones
# The `_low` variant: a cutaway wall for buildings shown without a roof.
LOW_H = 1.38
CAP_H = 0.08  # capstone thickness
CAP_OVER = 0.025  # capstone overhang on each face
COURSE_H_FULL = (H - CAP_H - 0.01) / 8  # 8 courses at full height; lower walls keep fewer of the same height
GAP = 0.026  # mortar joint between blocks
INSET = 0.025  # how far the mortar core sits behind the block faces
QUOIN = 0.62  # length of the corner quoin block that ties the two arms together

# Shared stone palette of the village wall set (wall_stone_straight, _corner, _tee, _cross, _doorframe): keep them equal.
STONE = (0.34, 0.295, 0.235)
STONE_OLD = (0.27, 0.235, 0.19)
STONE_PALE = (0.40, 0.36, 0.29)
MORTAR = (0.11, 0.10, 0.085)
CAP = (0.27, 0.255, 0.23)


def _run(rnd, start, end, lo=0.3, hi=0.46):
    """Split [start, end] into block spans of lo..hi metres with mortar gaps; the last block ends at `end`."""
    spans, a = [], start
    while end - a > 0:
        length = rnd.uniform(lo, hi)
        if end - a - length < lo * 0.7:
            length = end - a
        spans.append((a, min(a + length, end)))
        a += length
    return spans


# The arms, as turns about z of an arm that runs to +x (0: +x, 90: +y, 180: -x, 270: -y).
ARMS = (0, 90, 180, 270)


def _turn(objs, deg):
    """Turns `objs` `deg` degrees about the z axis through the origin (an arm built along +x put in its place)."""
    rot = Matrix.Rotation(math.radians(deg), 4, "Z")
    for obj in objs:
        obj.matrix_basis = rot @ obj.matrix_basis  # basis, not world: a new object's world matrix is not evaluated yet
    return objs


def _through(rnd, q_len):
    """How far a course's through stone reaches on each side of the pier along its axis: into an arm on that side
    (a long stone tying the arms together), else to the pier's face."""
    return [q_len * rnd.uniform(0.9, 1.05) - T / 2, q_len * rnd.uniform(0.9, 1.05) - T / 2]


def _junction(top):
    """The crossing, `top` metres high with its capstones."""
    body_h = top - CAP_H - 0.01  # top of the mortar core (capstones sit on it)
    courses = max(2, round(body_h / COURSE_H_FULL))
    course_h = body_h / courses
    rnd = random.Random(29)
    stones = [
        material("wall_stone_cross_stone", STONE, vary=0.28, scale=9),
        material("wall_stone_cross_old", STONE_OLD, vary=0.3, scale=8),
        material("wall_stone_cross_pale", STONE_PALE, vary=0.25, scale=10),
    ]
    mortar = material("wall_stone_cross_mortar", MORTAR, vary=0.15, scale=20)
    cap = material("wall_stone_cross_cap", CAP, vary=0.25, scale=7)

    def stone():
        r = rnd.random()
        return stones[0] if r < 0.6 else stones[1] if r < 0.85 else stones[2]

    # Mortar core: the pier and one slab per arm, a little thinner than the blocks so the joints read recessed.
    core = T - 2 * INSET
    box("core_pier", (core, core, body_h), (0, 0, body_h / 2), mortar, bevel=0)
    for k, arm in enumerate(ARMS):
        _turn([box(f"core_{k}", (EDGE - core / 2, core, body_h), ((EDGE + core / 2) / 2, 0, body_h / 2), mortar,
                   bevel=0)], arm)

    # Courses: a through stone over the pier alternates between the axes so the joints stagger round the junction.
    for c in range(courses):
        z0 = c * course_h
        h = course_h - GAP
        axis = (0, 180) if c % 2 == 0 else (90, 270)
        reach = _through(rnd, QUOIN)
        pos = reach[0] if axis[0] in ARMS else T / 2
        neg = reach[1] if axis[1] in ARMS else T / 2
        length, mid = pos + neg, (pos - neg) / 2
        size = (length, T, h) if axis[0] == 0 else (T, length, h)
        at = (mid, 0, z0 + h / 2) if axis[0] == 0 else (0, mid, z0 + h / 2)
        box(f"through_{c}", size, at, stone(), rot=(0, 0, rnd.uniform(-1, 1)), bevel=0.022)
        for k, arm in enumerate(ARMS):
            start = (pos if arm == axis[0] else neg if arm == axis[1] else T / 2) + GAP
            blocks = []
            for i, (a, b) in enumerate(_run(rnd, start, EDGE)):
                ln = b - a - GAP
                bh = h * rnd.uniform(0.9, 1.0)
                blocks.append(box(f"block_{k}_{c}_{i}", (ln, T * rnd.uniform(0.96, 1.0), bh),
                                  (a + ln / 2, rnd.uniform(-0.014, 0.014), z0 + bh / 2), stone(),
                                  rot=(0, 0, rnd.uniform(-1.2, 1.2)), bevel=rnd.uniform(0.018, 0.025)))
            _turn(blocks, arm)

    # Capstones: a square one over the pier, then flat slabs out to the end of each arm.
    cw = T + 2 * CAP_OVER
    box("cap_pier", (cw, cw, CAP_H), (0, 0, body_h + CAP_H / 2), cap, rot=(0, 0, rnd.uniform(-1.5, 1.5)),
        bevel=0.016)
    for k, arm in enumerate(ARMS):
        caps = []
        for i, (a, b) in enumerate(_run(rnd, cw / 2 + 0.012, EDGE, 0.24, 0.34)):
            ln = b - a - 0.014
            ch = CAP_H * rnd.uniform(0.85, 1.0)
            caps.append(box(f"cap_{k}_{i}", (ln, cw * rnd.uniform(0.95, 1.0), ch), (a + ln / 2, 0, body_h + ch / 2),
                            cap, rot=(0, 0, rnd.uniform(-1.2, 1.2)), bevel=0.016))
        _turn(caps, arm)


# How far moss may reach: the asset.json size and its bounds slack, a little inside.
REACH = ((-0.8, 0.8), (-0.8, 0.8))


# --- Rubble (by hand): the painted look's stone, shared by the village wall set (wall_stone_straight, _corner,
# _doorframe and wall_timber_straight's plinth); keep the block equal in each. Irregular rounded stones of mixed
# sizes in rough courses over a dark mortar core set well back, so every joint reads as a dark recess; rounded cap
# stones; on the `_moss` variants moss cushions on the caps and at the foot of both faces. A rubble wall's caps stop
# MOSS_ROOM under the plain wall's height, with or without moss, so moss and bare sections join at one height.
RUBBLE_STONE = (0.32, 0.32, 0.285)  # linear RGB: weathered olive-grey fieldstone, greyer than the blocks
RUBBLE_OLD = (0.23, 0.23, 0.205)
RUBBLE_PALE = (0.37, 0.365, 0.33)
RUBBLE_JOINT = (0.03, 0.027, 0.022)  # the mortar core: near black, so joints read as dark recesses
RUBBLE_CAP = (0.27, 0.27, 0.245)
MOSS_DEEP = (0.035, 0.055, 0.016)  # moss palette of rock_mossy: shadow green, mid olive, lit yellow-green
MOSS_OLIVE = (0.1, 0.13, 0.035)
MOSS_LIT = (0.21, 0.25, 0.07)
ROUND = 3.0  # superellipsoid exponent of a stone: 2 is an ellipsoid, higher is boxier
LUMP = 0.07  # per-vertex wobble of a stone's surface
BULGE = (0.008, 0.035)  # how far a stone's face stands proud of the wall face
OVER = 0.015  # how far a stone reaches past its cell: neighbours just touch, joints read wide and dark
JOINT_IN = 0.07  # how far the mortar core sits behind the wall faces
PAST = 0.12  # how far a stone at a section end reaches past the cut, so the cut end shows stone, not the core
MOSS_ROOM = 0.06  # metres the caps stop under the wall's height: room for the moss on top
RUBBLE_CAP_H = 0.13  # cap stone thickness
RUBBLE_CAP_OVER = 0.035  # cap overhang on each face
CARD_T = 0.004  # metres, thickness of a moss leaf card


def _rubble_mats(prefix):
    return {
        "stone": material(f"{prefix}_rubble", RUBBLE_STONE, vary=0.26, scale=7, crevice=0.7),
        "old": material(f"{prefix}_rubble_old", RUBBLE_OLD, vary=0.28, scale=9, crevice=0.7),
        "pale": material(f"{prefix}_rubble_pale", RUBBLE_PALE, vary=0.22, scale=8, crevice=0.7),
        "joint": material(f"{prefix}_rubble_joint", RUBBLE_JOINT, vary=0.15, scale=20, crevice=0.9),
        "cap": material(f"{prefix}_rubble_cap", RUBBLE_CAP, vary=0.25, scale=8, crevice=0.7),
        "deep": material(f"{prefix}_moss_deep", MOSS_DEEP, rough=0.95, vary=0.3, scale=40, crevice=0.6),
        "olive": material(f"{prefix}_moss_olive", MOSS_OLIVE, rough=0.95, vary=0.3, scale=40, crevice=0.5),
        "lit": material(f"{prefix}_moss_lit", MOSS_LIT, rough=0.9, vary=0.25, scale=40, crevice=0.35),
    }


def _pick(rnd, mats):
    r = rnd.random()
    return mats["stone"] if r < 0.55 else mats["old"] if r < 0.85 else mats["pale"]


def _stone(name, half, at, mat, rnd, roll=0.0, yaw=0.0, clip=((-9, 9), (-9, 9), (0, 9)), cuts=1, n=ROUND):
    """A rounded rubble stone of half-sizes `half` centred on `at`: a subdivided cube pushed out to a lumpy
    superellipsoid, rolled `roll` degrees about y and turned `yaw` about z, then cut flat by the world box `clip`
    ((x0, x1), (y0, y1), (z0, z1)): section ends, the ground and the underside of the caps."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    for v in bm.verts:
        d = v.co.normalized()
        k = (abs(d.x) ** n + abs(d.y) ** n + abs(d.z) ** n) ** (-1 / n) * rnd.uniform(1 - LUMP, 1 + LUMP)
        v.co = Vector((d.x * k * half[0], d.y * k * half[1], d.z * k * half[2]))
    bm.transform(Matrix.Translation(at) @ Matrix.Rotation(math.radians(yaw), 4, "Z")
                 @ Matrix.Rotation(math.radians(roll), 4, "Y"))
    for v in bm.verts:
        v.co = Vector(tuple(min(max(c, lo), hi) for c, (lo, hi) in zip(v.co, clip)))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth()
    mesh.set_sharp_from_angle(angle=math.radians(75))
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _course_heights(rnd, body_h):
    """Rough course heights from the ground up to `body_h`: a big footing course, then mixed ones."""
    hs = [rnd.uniform(0.34, 0.42)]
    while sum(hs) < body_h - 0.2:
        hs.append(rnd.uniform(0.17, 0.36))
    k = body_h / sum(hs)
    return [h * k for h in hs]


def _spans(rnd, a0, a1, h, first=None):
    """Stone lengths along a course of height `h` from `a0` to `a1`: mixed, long stones about twice the course
    height, short ones near square; the first one is `first` long when given (staggers the joints)."""
    spans, a = [], a0
    while a1 - a > 1e-6:
        ln = first if first and not spans else h * rnd.choice((0.6, 0.9, 1.2, 1.6, 2.2)) * rnd.uniform(0.85, 1.15)
        ln = min(max(ln, 0.15), 0.62)
        if a1 - a - ln < 0.15:
            ln = a1 - a
        spans.append((a, a + ln))
        a += ln
    return spans


def _lay(rnd, prefix, mats, axis, a0, a1, depth, heights, clip_a, z_top, starts=None, across=0.0):
    """Rubble stones in courses of `heights` on a face run along `axis` ("x" or "y") from `a0` to `a1`, `depth`
    thick and centred `across` off the axis, cut flat at `clip_a` and under `z_top`. `starts` (per course) is where
    the course begins when another stone fills the start (a corner quoin). Small pinning stones fill some joints."""
    z = 0.0
    out = []
    for c, h in enumerate(heights):
        start = starts[c] if starts else a0
        spans = _spans(rnd, start, a1, h, first=rnd.uniform(0.3, 0.75) * h * 1.6 if c % 2 else None)
        for i, (s0, s1) in enumerate(spans):
            ln = s1 - s0
            hz = h * rnd.uniform(0.92, 1.08)
            mid = (s0 + s1) / 2
            zc = z + h / 2 + (rnd.uniform(-0.02, 0.02) if c else 0.0)
            bulge = rnd.uniform(*BULGE)
            half = [ln / 2 + OVER, depth / 2 + bulge, hz / 2 + OVER]
            at = [mid, across + rnd.uniform(-0.6, 0.6) * bulge, zc]
            for end, sign in ((s0 <= clip_a[0] + 1e-6, -1), (s1 >= clip_a[1] - 1e-6, 1)):
                if end:  # reach past the cut, which then shows the stone's full section
                    half[0] += PAST / 2
                    at[0] += sign * PAST / 2
            if axis == "y":
                half[0], half[1] = half[1], half[0]
                at[0], at[1] = at[1], at[0]
            clip = [(-9, 9), (-9, 9), (0, z_top)]
            # Cut a hair inside the section end, a little differently per stone, so the cut faces do not z-fight.
            clip[0 if axis == "x" else 1] = (clip_a[0] + rnd.uniform(0, 0.003), clip_a[1] - rnd.uniform(0, 0.003))
            out.append(_stone(f"{prefix}_rubble_{c}_{i}", half, at, _pick(rnd, mats), rnd,
                              roll=rnd.uniform(-5, 5) if axis == "x" else 0.0,
                              yaw=rnd.uniform(-2, 2), clip=clip))
            # A pinning stone in some joints: a small stone half sunk where the joint meets the course above.
            if i and rnd.random() < 0.45 and c < len(heights) - 1:
                r = rnd.uniform(0.045, 0.075)
                pin = [s0, across, z + h + rnd.uniform(-0.03, 0.01)]
                pdepth = [r, depth / 2 + rnd.uniform(-0.004, 0.004), r * rnd.uniform(0.7, 0.95)]
                if axis == "y":
                    pin[0], pin[1] = pin[1], pin[0]
                    pdepth[0], pdepth[1] = pdepth[1], pdepth[0]
                out.append(_stone(f"{prefix}_pin_{c}_{i}", pdepth, pin, _pick(rnd, mats), rnd, clip=clip))
        z += h
    return out


def _caps(rnd, prefix, mats, axis, a0, a1, depth, z0, z_top, across=0.0):
    """Rounded cap stones from `a0` to `a1` along `axis`, overhanging both faces, from `z0` up to `z_top`."""
    out = []
    for i, (s0, s1) in enumerate(_spans(rnd, a0, a1, 0.2)):
        hz = (z_top - z0) / 2
        half = [(s1 - s0) / 2 + 0.02, depth / 2 + RUBBLE_CAP_OVER * rnd.uniform(0.7, 1.0), hz * rnd.uniform(0.9, 1.0)]
        at = [(s0 + s1) / 2, across + rnd.uniform(-0.01, 0.01), z0 + half[2]]
        for end, sign in ((s0 <= a0 + 1e-6, -1), (s1 >= a1 - 1e-6, 1)):
            if end:
                half[0] += PAST / 2
                at[0] += sign * PAST / 2
        clip = [(-9, 9), (-9, 9), (z0 - 0.03, z_top)]
        clip[0 if axis == "x" else 1] = (a0, a1)
        if axis == "y":
            half[0], half[1] = half[1], half[0]
            at[0], at[1] = at[1], at[0]
        out.append(_stone(f"{prefix}_cap_{i}", half, at, mats["cap"], rnd, n=2.3, yaw=rnd.uniform(-3, 3), clip=clip))
    return out


def _moss_points(rnd, runs):
    """Moss cushion spots in two or three patches along the caps: `runs` are ((x0, y0), (x1, y1)) cap centre lines."""
    points = []
    for _ in range(rnd.choice((2, 3))):
        (x0, y0), (x1, y1) = rnd.choice(runs)
        length = max(abs(x1 - x0), abs(y1 - y0))
        c, half = rnd.uniform(0, 1), rnd.uniform(0.2, 0.45) / length
        t = c - half
        while t < c + half:
            u = min(max(t, 0.05), 0.95)
            side = rnd.uniform(-0.15, 0.15)
            x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
            points.append((x, y + side) if y0 == y1 else (x + side, y))
            t += rnd.uniform(0.1, 0.15) / length
    return points


def _surface(objs, ground=None):
    """A BVH tree of `objs` in world space (and a ground quad over `ground` = (x0, x1, y0, y1) when given)."""
    verts, polys = [], []
    for obj in objs:
        base = len(verts)
        verts += [obj.matrix_world @ v.co for v in obj.data.vertices]
        polys += [[base + i for i in p.vertices] for p in obj.data.polygons]
    if ground:
        x0, x1, y0, y1 = ground
        base = len(verts)
        verts += [Vector((x0, y0, 0)), Vector((x1, y0, 0)), Vector((x1, y1, 0)), Vector((x0, y1, 0))]
        polys.append([base, base + 1, base + 2, base + 3])
    return BVHTree.FromPolygons(verts, polys)


def _drop(tree, x, y, z=5.0):
    """The topmost surface point and its normal under (x, y) from height `z`, or None."""
    loc, normal, _, _ = tree.ray_cast(Vector((x, y, z)), Vector((0, 0, -1)))
    if loc is None:
        return None
    if normal.z < 0:
        normal = -normal
    return loc, normal


def _leaf(name, size, at, facing, spin, mat):
    """One moss leaf card: a thin box reshaped into a pointed leaf (tip on +x), its broad face along `facing`."""
    obj = box(name, (size[0], size[1], CARD_T), at, mat, bevel=0)
    for v in obj.data.vertices:
        x, y = v.co.x, v.co.y
        if x > 0 and y > 0:
            v.co.x, v.co.y = x, 0.0
        elif x < 0 < y:
            v.co.x = 0.0
        elif x < 0 and y < 0:
            v.co.x, v.co.y = x * 0.6, 0.0
        else:
            v.co.x = 0.0
    q = facing.normalized().to_track_quat("Z", "Y") @ Quaternion((0, 0, 1), math.radians(spin))
    obj.rotation_euler = q.to_euler("XYZ")
    return obj


def _cushion(name, tree, hit, normal, rc, mats, rnd, cards):
    """A moss cushion of radius `rc` at `hit`: a deep green core and `cards` leaf cards round it, lit inside, olive
    and deep at the rim (as rock_mossy's)."""
    hc = rc * 0.4
    objs = [blob(f"{name}_core", rc * 0.95, hit + normal * (hc * 0.1), mats["deep"], squash=(1, 0.85, 0.38),
                 subdiv=1, seed=rnd.randrange(1000), jitter=0.22)]
    yaw0 = rnd.uniform(0, 360)
    leaf = rc * 0.62
    for i in range(cards):
        a = math.radians(yaw0 + 137.5 * i + rnd.uniform(-15, 15))
        rho = rc * math.sqrt((i + 0.5) / cards) * rnd.uniform(0.75, 1.05)
        got = _drop(tree, hit.x + rho * math.cos(a), hit.y + rho * math.sin(a), hit.z + rc)
        if got is None:
            continue
        loc, n = got
        edge = rho / rc
        lift = hc * (1 - 0.75 * edge * edge) * rnd.uniform(0.7, 1.1)
        out = Vector((math.cos(a), math.sin(a), 0))
        facing = n + out * (0.12 + 0.4 * edge + rnd.uniform(-0.1, 0.1))
        facing += Vector((rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25), 0))
        if edge < 0.55:
            mat = mats["lit"] if rnd.random() < 0.75 else mats["olive"]
        else:
            mat = rnd.choice([mats["lit"], mats["olive"], mats["olive"], mats["deep"]])
        size = (leaf * rnd.uniform(0.8, 1.2), leaf * rnd.uniform(0.7, 0.95))
        objs.append(_leaf(f"{name}_card_{i}", size, loc + n * lift, facing, rnd.uniform(0, 360), mat))
    return objs


def _cap_moss(rnd, prefix, mats, caps, points, top, reach, rc=0.1, cards=9):
    """Moss cushions on the caps at `points` ((x, y) pairs), where the cap faces up or rounds over its edge, kept
    under `top` and inside `reach` ((x0, x1), (y0, y1)), the asset's size."""
    tree = _surface(caps)
    objs = []
    for i, (x, y) in enumerate(points):
        got = _drop(tree, x, y)
        if got is None or got[1].z < 0.45:
            continue
        r = rc * rnd.uniform(0.75, 1.15) * (1 if got[1].z > 0.8 else 0.7)
        objs += _cushion(f"{prefix}_capmoss_{i}", tree, got[0], got[1], r, mats, rnd, cards)
    _fit(objs, (*reach, (0.0, top)))


def _foot_moss(rnd, prefix, mats, stones, points, reach, rc=0.09, cards=8):
    """Moss cushions on the ground at the foot of the wall at `points` ((x, y) pairs, just off a face), creeping
    onto the lowest stones; each is pushed back against the wall where it would stick out of `reach`
    ((x0, x1), (y0, y1)), the asset's size."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    tree = _surface(stones, (min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1))
    objs = []
    for i, (x, y) in enumerate(points):
        got = _drop(tree, x, y, 0.15)
        if got is None:
            continue
        objs += _cushion(f"{prefix}_footmoss_{i}", tree, got[0], got[1], rc * rnd.uniform(0.7, 1.2), mats, rnd, cards)
    _fit(objs, (*reach, (0.0, 9.0)))


def _fit(objs, bounds):
    """Moves each of `objs` into `bounds` ((x0, x1), (y0, y1), (z0, z1)): moss stays out of the ground and inside
    the wall's size."""
    bpy.context.view_layer.update()
    for obj in objs:
        pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
        for k, (lo, hi) in enumerate(bounds):
            low, high = min(p[k] for p in pts), max(p[k] for p in pts)
            obj.location[k] += lo - low if low < lo else hi - high if high > hi else 0.0


# --- End of the rubble block.

def _rot2(p, deg):
    """Point `p` = (x, y) turned `deg` degrees about the origin (rounded, so axis runs stay exact)."""
    a = math.radians(deg)
    return (round(p[0] * math.cos(a) - p[1] * math.sin(a), 6), round(p[0] * math.sin(a) + p[1] * math.cos(a), 6))


def _rubble(top, seed, moss):
    """A rubble crossing (`_rubble` variants), caps MOSS_ROOM under `top`; `moss` adds moss on the caps and the foot.
    A long rounded through stone per course, alternating axes as the blocks' do, ties the arms together."""
    rnd = random.Random(seed)
    mats = _rubble_mats("wall_stone_cross")
    z_top = top - MOSS_ROOM
    body = z_top - RUBBLE_CAP_H + 0.02
    core = T - 2 * JOINT_IN
    box("rubble_core_pier", (core, core, body), (0, 0, body / 2), mats["joint"], bevel=0)
    for k, arm in enumerate(ARMS):
        _turn([box(f"rubble_core_{k}", (EDGE - core / 2 - 0.006, core, body),
                   ((EDGE + core / 2 - 0.006) / 2, 0, body / 2), mats["joint"], bevel=0)], arm)
    heights = _course_heights(rnd, body)
    stones = []
    starts = {arm: [] for arm in ARMS}
    z = 0.0
    for c, h in enumerate(heights):
        axis = (0, 180) if c % 2 == 0 else (90, 270)
        reach = _through(rnd, QUOIN * 0.95)
        pos = reach[0] if axis[0] in ARMS else T / 2
        neg = reach[1] if axis[1] in ARMS else T / 2
        length, mid = pos + neg, (pos - neg) / 2
        bulge = rnd.uniform(*BULGE)
        if axis[0] == 0:
            half, at = (length / 2 + OVER, T / 2 + bulge, h / 2 + OVER), (mid, 0, z + h / 2)
        else:
            half, at = (T / 2 + bulge, length / 2 + OVER, h / 2 + OVER), (0, mid, z + h / 2)
        stones.append(_stone(f"through_rubble_{c}", half, at, _pick(rnd, mats), rnd, yaw=rnd.uniform(-2, 2),
                             clip=((-EDGE, EDGE), (-EDGE, EDGE), (0, body))))
        for arm in ARMS:
            starts[arm].append(pos if arm == axis[0] else neg if arm == axis[1] else T / 2)
        z += h
    for k, arm in enumerate(ARMS):
        stones += _turn(_lay(rnd, f"arm_{k}", mats, "x", T / 2, EDGE, T, heights, (-9, EDGE), body,
                             starts=starts[arm]), arm)
    cw = T / 2 + RUBBLE_CAP_OVER
    caps = [_stone("cap_pier", (cw, cw, (z_top - body + 0.01) / 2), (0, 0, body - 0.01 + (z_top - body + 0.01) / 2),
                   mats["cap"], rnd, n=2.3, yaw=rnd.uniform(-3, 3), clip=((-9, 9), (-9, 9), (body - 0.04, z_top)))]
    for k, arm in enumerate(ARMS):
        caps += _turn(_caps(rnd, f"cap_{k}", mats, "x", cw, EDGE, T, body - 0.01, z_top), arm)
    if not moss:
        return
    bpy.context.view_layer.update()
    runs = [(_rot2((-0.1, 0), arm), _rot2((EDGE, 0), arm)) for arm in ARMS]
    _cap_moss(rnd, "cross", mats, caps, _moss_points(rnd, runs), top, REACH)
    feet = []
    for arm in ARMS:
        first = rnd.choice((-1, 1))
        for side in (first, -first):
            if side == first or rnd.random() < 0.4:
                u = rnd.uniform(T / 2 + 0.05, EDGE - 0.05)
                feet.append(_rot2((u, side * (T / 2 + rnd.uniform(0.03, 0.06))), arm))
    _foot_moss(rnd, "cross", mats, stones, feet, REACH)


@prop
def wall_stone_cross():
    _junction(H)


@prop
def wall_stone_cross_low():
    _junction(LOW_H)


@prop
def wall_stone_cross_rubble():
    _rubble(H, 3, False)


@prop
def wall_stone_cross_rubble_moss():
    _rubble(H, 3, True)


@prop
def wall_stone_cross_rubble_2():
    _rubble(H, 7, False)


@prop
def wall_stone_cross_rubble_2_moss():
    _rubble(H, 7, True)


@prop
def wall_stone_cross_low_rubble():
    _rubble(LOW_H, 3, False)


@prop
def wall_stone_cross_low_rubble_moss():
    _rubble(LOW_H, 3, True)


@prop
def wall_stone_cross_low_rubble_2():
    _rubble(LOW_H, 7, False)


@prop
def wall_stone_cross_low_rubble_2_moss():
    _rubble(LOW_H, 7, True)
