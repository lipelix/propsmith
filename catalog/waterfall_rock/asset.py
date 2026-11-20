"""A small waterfall, about 1.5 x 1 m and 3 m high: a stream runs along a channel between two piles of stacked grey
rock blocks, spills over a jutting lip stone at about 2.5 m and falls as a pale sheet with foam streaks into a dark
pool held by a ring of rim stones at the front (-y), foam churning where it lands. Moss cushions sit on every
upward-facing ledge of the rock step. Its 1.5 m width matches the cliff sections, so it can stand in a cliff line.

The rocks are lumpy blobs with their bases cut flat, stacked so each rests on the one below. The falling water is one
closed ribbon mesh bent along a gentle arc from the lip; narrower ribbons in front of it are the foam streaks. Moss
is placed like `rock_mossy`'s: cushions dropped onto the finished stones by rays, only where the surface faces up."""
import math
import random

import bmesh
import bpy
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, box

# Overall dimensions (metres), from the description: about 1.5 x 1 x 3 m.
X, Y, H = 1.5, 1.2, 3.0
BACK_Y = 0.48  # back of the rock step
SIDE_X = (0.12, 0.75)  # inner and outer edge of the rock columns either side of the channel
SIDE_Z = (0.0, 0.55, 1.1, 1.64, 2.22, 2.86)  # joints between their layers
SIDE_FRONT = (-0.3, 0.09)  # front of the lowest layer, and how far each layer above sits back
MID_X = 0.32  # half width of the rock behind the fall
MID_Z = (0.0, 0.62, 1.24, 1.82)  # joints of its layers, up to the lip stone
MID_FRONT = 0.06
LIP_Y = -0.14  # front edge of the lip stone the water spills over
LIP_Z = 2.5  # top of the lip stone
LIP_T = 0.3  # its thickness
CHANNEL_W = 0.26  # width of the stream in the channel and at the lip
FALL_W = 0.34  # width of the sheet where it lands
FALL_V = 0.2  # metres per second the water leaves the lip at (how far the arc carries out)
POOL = (0.0, -0.28)  # centre of the pool
POOL_R = (0.5, 0.2)  # pool surface radii (x, y)
POOL_Z = 0.12  # pool surface height
CARD_T = 0.004  # thickness of a moss leaf card

ROCK = (0.27, 0.262, 0.245)  # linear RGB: weathered grey rock (as the cliffs)
ROCK_DARK = (0.17, 0.168, 0.16)
ROCK_WET = (0.1, 0.105, 0.1)  # rock darkened by spray and the stream
WATER = (0.03, 0.06, 0.065)  # the deep pool
FALL = (0.2, 0.27, 0.28)  # the falling sheet: pale, cool, glossy
FOAM = (0.44, 0.48, 0.48)  # foam streaks and the churn at the foot
MOSS_DEEP = (0.035, 0.055, 0.016)
MOSS_OLIVE = (0.1, 0.13, 0.035)
MOSS_LIT = (0.21, 0.25, 0.07)

# Rim stones round the front of the pool: (angle round the pool in degrees, size, seed).
RIM = [(170, 0.08, 31), (193, 0.1, 32), (216, 0.09, 33), (240, 0.11, 34), (263, 0.09, 35), (290, 0.1, 36),
       (322, 0.07, 37), (350, 0.09, 39), (12, 0.07, 40)]


def _mats():
    return {
        "rock": material("waterfall_rock_rock", ROCK, rough=0.9, vary=0.28, scale=7, crevice=0.75),
        "dark": material("waterfall_rock_rock_dark", ROCK_DARK, rough=0.9, vary=0.28, scale=8, crevice=0.75),
        "wet": material("waterfall_rock_rock_wet", ROCK_WET, rough=0.35, vary=0.25, scale=9, crevice=0.7),
        "water": material("waterfall_rock_water", WATER, rough=0.05, vary=0.1, scale=3, crevice=0.0),
        "fall": material("waterfall_rock_fall", FALL, rough=0.12, vary=0.2, scale=5, crevice=0.0),
        "foam": material("waterfall_rock_foam", FOAM, rough=0.45, vary=0.15, scale=12, crevice=0.0),
        "deep": material("waterfall_rock_moss_deep", MOSS_DEEP, rough=0.95, vary=0.3, scale=40, crevice=0.6),
        "olive": material("waterfall_rock_moss_olive", MOSS_OLIVE, rough=0.95, vary=0.3, scale=40, crevice=0.5),
        "lit": material("waterfall_rock_moss_lit", MOSS_LIT, rough=0.9, vary=0.25, scale=40, crevice=0.35),
    }


def _slab(name, xs, ys, zs, mat, seed, yaw=0.0, cuts=3, round_=0.42, rough=0.07):
    """A rough block of rock filling about `xs` x `ys` x `zs` ((low, high) metres each): a subdivided box with its
    edges rounded (`round_`, 0 square to 1 an ellipsoid) and its vertices pushed about by up to `rough` of its size,
    top and bottom kept flat so blocks stack into a stepped face with ledges. Turned `yaw` degrees."""
    rnd = random.Random(seed)
    half = Vector(((xs[1] - xs[0]) / 2, (ys[1] - ys[0]) / 2, (zs[1] - zs[0]) / 2))
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    for v in bm.verts:
        c = v.co.copy()
        sph = c.normalized() * max(abs(c.x), abs(c.y), abs(c.z))
        c = c.lerp(sph, round_)
        c.x *= 1 - rough + rnd.uniform(-rough, rough)
        c.y *= 1 - rough + rnd.uniform(-rough, rough)
        if abs(v.co.z) < 0.999:  # flat top and bottom
            c.z += rnd.uniform(-rough, rough) * 2
        else:
            c.z = v.co.z
        v.co = Vector((c.x * half.x, c.y * half.y, c.z * half.z))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = ((xs[0] + xs[1]) / 2, (ys[0] + ys[1]) / 2, (zs[0] + zs[1]) / 2)
    obj.rotation_euler = (0, 0, math.radians(yaw))
    bpy.context.view_layer.update()
    return obj


def _rock(name, xy, half, mat, seed, yaw=0.0):
    """A rounded stone `half` (x, y, z) half-sized standing on the ground at (x, y), its base cut flat."""
    obj = blob(name, 1.0, (xy[0], xy[1], half[2] * 0.75), mat, squash=half, subdiv=1, seed=seed, jitter=0.14)
    for v in obj.data.vertices:
        v.co.z = max(v.co.z, -half[2] * 0.75)
    obj.rotation_euler = (0, 0, math.radians(yaw))
    bpy.context.view_layer.update()
    return obj


def _ribbon(name, x, path, widths, thick, mat):
    """A closed strip of water along `path` ((y, z) points) centred on `x`: `widths` and `thick` per point, its broad
    faces across x, its thickness along the path's normal in the yz plane."""
    bm = bmesh.new()
    rows = []
    n = len(path)
    for i, (y, z) in enumerate(path):
        a = path[max(0, i - 1)]
        b = path[min(n - 1, i + 1)]
        ty, tz = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(ty, tz)
        ny, nz = tz / tl, -ty / tl  # normal: the tangent turned a quarter (up in the channel, front in the fall)
        w, t = widths[i] / 2, thick[i] / 2
        rows.append([
            bm.verts.new((x - w, y + ny * t, z + nz * t)),
            bm.verts.new((x + w, y + ny * t, z + nz * t)),
            bm.verts.new((x + w, y - ny * t, z - nz * t)),
            bm.verts.new((x - w, y - ny * t, z - nz * t)),
        ])
    for a, b in zip(rows, rows[1:]):
        for j in range(4):
            bm.faces.new((a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]))
    bm.faces.new(rows[0][::-1])
    bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _stream():
    """The water's path: along the channel to the lip, then a falling arc to the pool. (y, z) points, the share of the
    fall reached at each (0 in the channel, 1 at the pool)."""
    path, share = [], []
    for y in (BACK_Y - 0.02, 0.25, 0.05, LIP_Y + 0.06):
        path.append((y, LIP_Z + 0.012))
        share.append(0.0)
    path.append((LIP_Y - 0.01, LIP_Z + 0.005))
    share.append(0.0)
    drop = LIP_Z - POOL_Z + 0.02
    t_end = math.sqrt(2 * drop / 9.81)
    steps = 11
    for k in range(1, steps + 1):
        t = t_end * k / steps
        path.append((LIP_Y - 0.01 - FALL_V * t - 0.04 * (k / steps) ** 2, LIP_Z - 4.905 * t * t))
        share.append(k / steps)
    return path, share


def _surface(objs):
    """A BVH tree of the stones in world space, for dropping moss onto them."""
    verts, polys = [], []
    for obj in objs:
        base = len(verts)
        verts += [obj.matrix_world @ v.co for v in obj.data.vertices]
        polys += [[base + i for i in p.vertices] for p in obj.data.polygons]
    return BVHTree.FromPolygons(verts, polys)


def _drop(tree, x, y):
    loc, normal, _, _ = tree.ray_cast(Vector((x, y, 5.0)), Vector((0, 0, -1)))
    if loc is None:
        return None
    if normal.z < 0:
        normal = -normal
    return loc, normal


def _card(name, size, at, facing, spin, mat):
    """A pointed moss leaf card: a thin bevel-free box squeezed to a point at +x, facing along `facing`."""
    obj = box(name, (size[0], size[1], CARD_T), at, mat, bevel=0)
    for v in obj.data.vertices:
        x, y = v.co.x, v.co.y
        if x > 0 and y > 0:
            v.co.y = 0.0
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
    """A moss cushion of radius `rc` at `hit`: a deep green core with leaf cards round it, lit inside, olive outside."""
    hc = rc * 0.45
    blob(f"{name}_core", rc * 0.95, hit + normal * (hc * 0.15), mats["deep"], squash=(1, 0.9, 0.42), subdiv=1,
         seed=rnd.randrange(1000), jitter=0.22)
    leaf = rc * 0.6
    yaw0 = rnd.uniform(0, 360)
    for i in range(cards):
        a = math.radians(yaw0 + 137.5 * i + rnd.uniform(-15, 15))
        rho = rc * math.sqrt((i + 0.5) / cards) * rnd.uniform(0.75, 1.05)
        got = _drop(tree, hit.x + rho * math.cos(a), hit.y + rho * math.sin(a))
        if got is None or abs(got[0].z - hit.z) > rc:
            continue
        loc, n = got
        edge = rho / rc
        lift = hc * (1 - 0.75 * edge * edge) * rnd.uniform(0.7, 1.1)
        out = Vector((math.cos(a), math.sin(a), 0))
        facing = n + out * (0.12 + 0.4 * edge) + Vector((rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25), 0))
        if edge < 0.6:
            mat = mats["lit"] if rnd.random() < 0.75 else mats["olive"]
        else:
            mat = rnd.choice([mats["lit"], mats["olive"], mats["deep"]])
        size = (leaf * rnd.uniform(0.8, 1.2), leaf * rnd.uniform(0.7, 0.95))
        _card(f"{name}_card_{i}", size, loc + n * lift, facing, rnd.uniform(0, 360), mat)


def _moss(rocks, mats, seed, rc=0.11, cards=10):
    """Cushions on the upward-facing patches of the rocks, kept out of the stream and off the pool."""
    rnd = random.Random(seed)
    tree = _surface(rocks)
    placed = []
    step = rc * 1.2
    n = 0
    y = -Y / 2 + step / 2
    while y < Y / 2:
        x = -X / 2 + step / 2
        while x < X / 2:
            px, py = x + rnd.uniform(-0.3, 0.3) * step, y + rnd.uniform(-0.3, 0.3) * step
            x += step
            if abs(px) < CHANNEL_W / 2 + 0.05 and py > LIP_Y - 0.08:
                continue  # under the stream or behind the fall
            got = _drop(tree, px, py)
            if got is None:
                continue
            loc, nrm = got
            if loc.z < POOL_Z + 0.04 or nrm.z < 0.7:
                continue
            r = rc * rnd.uniform(0.75, 1.1)
            if any((loc - p).length < (r + pr) * 0.6 for p, pr in placed):
                continue
            placed.append((loc, r))
            _cushion(f"waterfall_rock_moss_{n}", tree, loc, nrm, r, mats, rnd, cards)
            n += 1
        y += step


@prop
def waterfall_rock():
    rnd = random.Random(1717)
    mats = _mats()

    rocks = []
    # Two columns of stacked layers either side of the channel, each layer set back from the one below.
    for side in (-1, 1):
        for k in range(len(SIDE_Z) - 1):
            x_in = SIDE_X[0] + rnd.uniform(-0.03, 0.03) + (0.05 if k == len(SIDE_Z) - 2 else 0)
            x_out = SIDE_X[1] - rnd.uniform(0.0, 0.03) - 0.06 * k
            front = SIDE_FRONT[0] + SIDE_FRONT[1] * k + rnd.uniform(-0.04, 0.04)
            xs = (x_in, x_out) if side > 0 else (-x_out, -x_in)
            zs = (SIDE_Z[k] - (0 if k == 0 else 0.03), SIDE_Z[k + 1])
            mat = mats["dark" if (k + (side > 0)) % 3 == 0 else "rock"]
            rocks.append(_slab(f"rock_{'lr'[side > 0]}_{k}", xs, (front, BACK_Y), zs, mat, 3 + 7 * k + (side > 0),
                               yaw=rnd.uniform(-6, 6)))
    # The wet rock behind the fall, and the lip stone on it.
    for k in range(len(MID_Z) - 1):
        front = MID_FRONT + rnd.uniform(-0.03, 0.03)
        zs = (MID_Z[k] - (0 if k == 0 else 0.03), MID_Z[k + 1])
        rocks.append(_slab(f"rock_mid_{k}", (-MID_X, MID_X), (front, BACK_Y - 0.05), zs, mats["wet"], 71 + k,
                           yaw=rnd.uniform(-2, 2), cuts=2))
    rocks.append(_slab("rock_mid_top", (-MID_X, MID_X), (MID_FRONT, BACK_Y - 0.05), (MID_Z[-1] - 0.03, LIP_Z - LIP_T),
                       mats["wet"], 79, cuts=2))
    rocks.append(_slab("rock_lip", (-MID_X - 0.02, MID_X + 0.02), (LIP_Y, BACK_Y), (LIP_Z - LIP_T, LIP_Z), mats["wet"],
                       83, yaw=2, round_=0.2, rough=0.03))

    # The pool: a dark lens of still water sunk into the ground, its surface at POOL_Z.
    px, py = POOL
    pool = blob("pool", POOL_R[0], (px, py, POOL_Z / 2 + 0.003), mats["water"],
                squash=(1, POOL_R[1] / POOL_R[0], POOL_Z / 2 / POOL_R[0]), subdiv=3, seed=41, jitter=0.03)
    pool.rotation_euler = (0, 0, 0)

    # Rim stones round the front and sides of the pool.
    for i, (ang, r, seed) in enumerate(RIM):
        a = math.radians(ang)
        cx = px + (POOL_R[0] + r * 0.3) * math.cos(a)
        cy = py + (POOL_R[1] + r * 0.3) * math.sin(a)
        mat = mats["wet"] if i % 3 == 1 else mats["dark" if i % 2 else "rock"]
        rocks.append(_rock(f"rim_{i}", (cx, cy), (r * rnd.uniform(1.2, 1.4), r * rnd.uniform(0.8, 0.9), r * rnd.uniform(0.55, 0.75)),
                           mat, seed, yaw=ang + 90 + rnd.uniform(-15, 15)))

    # The stream and the falling sheet, with foam streaks in front of it.
    path, share = _stream()
    widths = [CHANNEL_W + (FALL_W - CHANNEL_W) * s for s in share]
    thick = [0.035 + 0.03 * s for s in share]
    _ribbon("fall", 0.0, path, widths, thick, mats["fall"])
    for i, (dx, w) in enumerate(((-0.09, 0.035), (-0.02, 0.05), (0.07, 0.04), (0.12, 0.025))):
        start = 4 + i % 2  # streaks begin at the lip
        sub = path[start:]
        sw = [w * (1 + 0.8 * s) for s in share[start:]]
        st = [0.01] * len(sub)
        front = [(y - 0.03 - 0.02 * s, z) for (y, z), s in zip(sub, share[start:])]
        _ribbon(f"foam_streak_{i}", dx * (1 + 0.3 * share[-1]), front, sw, st, mats["foam"])

    # Churn where the fall lands, and a few foam patches drifting on the pool.
    land_y = path[-1][0]
    for i, (dx, dy, r) in enumerate(((0.0, 0.0, 0.18), (-0.15, 0.03, 0.12), (0.16, -0.02, 0.12), (0.03, -0.12, 0.1),
                                     (-0.25, -0.1, 0.06), (0.27, -0.08, 0.05))):
        blob(f"foam_{i}", r, (dx, land_y + dy, POOL_Z + 0.005), mats["foam"], squash=(1.2, 0.9, 0.28), subdiv=1,
             seed=50 + i, jitter=0.25)

    _moss(rocks, mats, 61)

    # The lip the water spills over, and the pool it falls into (the game runs its streams between them).
    anchor("water:spout", (0.0, LIP_Y, LIP_Z + 0.04), size=(CHANNEL_W / 2, CHANNEL_W / 2, CHANNEL_W / 2))
    anchor("water:basin", (px, py, POOL_Z), size=(POOL_R[0], POOL_R[1], POOL_R[1]))
