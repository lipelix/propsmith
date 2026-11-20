"""A grassy hillside barrow mouth: a turf mound about 3 x 3 m and 2.5 m high with a passage cut into its front (-y),
lined with dry-stone walls, framed by two old standing stones under a heavy lintel, and worn stone steps going down
into the dark mouth.

Nothing may sink below the ground, so the descent is drawn the way the eye reads it (as in `stairs_stone_down`): the
passage walls rise as it runs into the hill, the treads thin out and darken step by step, and under the lintel they
fade into a black mouth roofed by capstones. The mound is one closed heightfield mesh, painted per facet: grass on top,
darker turf on the slopes, bare earth on the steep cuts."""
import math
import random

import bmesh
from mathutils import Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box

# Overall dimensions (metres), from the description.
X = 3.0  # footprint width
Y = 3.0  # footprint depth
HX, HY = X / 2, Y / 2
HM = 2.3  # mound crown height
CY = 0.15  # where along y the crown sits (behind the middle: a hillside, the cut on the front)
RY_FRONT = 1.65  # the mound's reach from the crown towards the front (-y)
RY_BACK = HY - CY  # and to the back, so it meets the ground at the footprint's edge
SUPER = 3.0  # superellipse power of the mound's outline: squarer than a dome
CROWN = 0.4  # the share of the outline that is flat-topped crown
CELLS = 30  # heightfield cells per side (10 cm)
FLOOR = 0.004  # the heightfield's lowest inside height, above its closing bottom face

TW = 0.55  # half the clear width of the passage
WALL_T = 0.28  # dry-stone revetment thickness beside the passage
YF = -0.42  # the portal's front face (the standing stones and lintel)
DEPTH = 0.22  # where the mouth's dark back stands behind the portal's face
CUT_SOFT = 0.2  # the mound rises from the cut to its full height over this much x, inside the wall

POST = (0.38, 0.42, 1.9)  # portal standing stones (x, y, z)
LINTEL = (2 * TW + 1.0, 0.5, 0.4)
SIDE_STONES = ((-1.17, -1.08, 1.45, 4.0), (1.2, -1.02, 1.15, -6.0))  # (x, y, height, lean deg) flanking stones

STEPS = 8  # treads from the foot of the cut into the mouth
TREAD_GAP = 0.03
TREAD_TOP = 0.08  # the first tread's height; they thin to TREAD_LOW in the dark
TREAD_LOW = 0.02
COURSE = 0.22  # dry-stone course height

GRASS = (0.085, 0.11, 0.035)  # linear RGB: turf on the crown
GRASS_LIT = (0.13, 0.15, 0.05)
TURF = (0.085, 0.1, 0.038)  # duller turf on the slopes
EARTH = (0.11, 0.075, 0.045)  # bare earth on the steep cuts
STONE = (0.27, 0.262, 0.245)  # weathered grey standing stones
STONE_OLD = (0.19, 0.188, 0.178)
STONE_PALE = (0.34, 0.33, 0.305)
LICHEN = (0.2, 0.21, 0.13)  # pale green-grey lichen and moss on the stones
MOSS = (0.075, 0.1, 0.032)
DRY = (0.22, 0.21, 0.19)  # dry-stone walling, a touch browner
STEP_LIT = (0.25, 0.243, 0.23)
STEP_DARK = (0.03, 0.03, 0.033)
SHADES = 5
VOID = (0.012, 0.012, 0.015)


def _lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _smooth(e0, e1, v):
    t = max(0.0, min(1.0, (v - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def _mats():
    m = {
        "grass": material("crypt_entrance_grass", GRASS, rough=0.95, vary=0.3, scale=10, crevice=0.5),
        "grass_lit": material("crypt_entrance_grass_lit", GRASS_LIT, rough=0.95, vary=0.3, scale=12, crevice=0.45),
        "turf": material("crypt_entrance_turf", TURF, rough=0.95, vary=0.3, scale=9, crevice=0.55),
        "earth": material("crypt_entrance_earth", EARTH, rough=0.95, vary=0.3, scale=8, crevice=0.6),
        "stone": material("crypt_entrance_stone", STONE, rough=0.9, vary=0.25, scale=5, crevice=0.8),
        "old": material("crypt_entrance_stone_old", STONE_OLD, rough=0.9, vary=0.25, scale=6, crevice=0.8),
        "pale": material("crypt_entrance_stone_pale", STONE_PALE, rough=0.9, vary=0.22, scale=7, crevice=0.75),
        "lichen": material("crypt_entrance_lichen", LICHEN, rough=0.95, vary=0.35, scale=9, crevice=0.6),
        "moss": material("crypt_entrance_moss", MOSS, rough=0.95, vary=0.35, scale=9, crevice=0.6),
        "dry": material("crypt_entrance_drystone", DRY, rough=0.9, vary=0.25, scale=7, crevice=0.8),
        "void": material("crypt_entrance_void", VOID, rough=1.0, vary=0.05, scale=4, crevice=0.2),
    }
    m["steps"] = [
        material(f"crypt_entrance_step_{i}", _lerp(STEP_LIT, STEP_DARK, (i / (SHADES - 1)) ** 1.3), vary=0.2,
                 scale=8, crevice=0.75)
        for i in range(SHADES)
    ]
    return m


def _mound_h(x, y, rnd_waves):
    """The turf's height at (x, y): a squarish dome, its crown behind the middle, with gentle lumps."""
    ry = RY_FRONT if y < CY else RY_BACK
    d = (abs(x / HX) ** SUPER + abs((y - CY) / ry) ** SUPER) ** (1 / SUPER)
    if d >= 1:
        return 0.0
    h = HM * (0.5 + 0.5 * math.cos(math.pi * max(0.0, d - CROWN) / (1 - CROWN)))  # a broad crown easing out at the foot
    lump = sum(a * math.sin(kx * x + ky * y + ph) for kx, ky, ph, a in rnd_waves)
    return max(0.0, h + lump * min(1.0, 4 * (1 - d)))


def _cut(x, y):
    """1 where the turf stands, 0 in the passage: the cut runs from the front edge to the back of the mouth."""
    if y > YF + DEPTH:  # behind the mouth's dark back
        return 1.0
    return _smooth(TW + 0.04, TW + 0.04 + CUT_SOFT, abs(x))


def _waves(seed):
    rnd = random.Random(seed)
    return [(rnd.uniform(-4, 4), rnd.uniform(-4, 4), rnd.uniform(0, 6.3), rnd.uniform(0.015, 0.035))
            for _ in range(5)]


def _mound(mats, waves):
    """The turf as one closed mesh: a heightfield over the footprint, closed by a flat bottom n-gon, and painted per
    facet."""
    bm = bmesh.new()
    grid = []
    for j in range(CELLS + 1):
        row = []
        for i in range(CELLS + 1):
            x = -HX + X * i / CELLS
            y = -HY + Y * j / CELLS
            edge = i in (0, CELLS) or j in (0, CELLS)
            z = 0.0 if edge else max(FLOOR, _mound_h(x, y, waves) * _cut(x, y))
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for j in range(CELLS):
        for i in range(CELLS):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    ring = ([grid[0][i] for i in range(CELLS + 1)] + [grid[j][CELLS] for j in range(1, CELLS + 1)]
            + [grid[CELLS][i] for i in range(CELLS - 1, -1, -1)] + [grid[j][0] for j in range(CELLS - 1, 0, -1)])
    bm.faces.new(list(reversed(ring)))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) == 4], quad_method="SHORT_EDGE")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    obj = box("crypt_entrance_mound", (1, 1, 1), (0, 0, 0), mats["grass"], bevel=0)
    mesh = obj.data
    bm.to_mesh(mesh)
    bm.free()
    for name in ("grass_lit", "turf", "earth"):
        mesh.materials.append(mats[name])
    mesh.shade_smooth()
    rnd = random.Random(5)
    for poly in mesh.polygons:
        x, y, z = poly.center
        nz = poly.normal.z
        if nz < -0.5:
            slot = 0  # the bottom
        elif nz < 0.35 and abs(poly.normal.x) > abs(poly.normal.y) and abs(x) < TW + WALL_T + 0.25 and y < YF + DEPTH:
            slot = 3  # the bare cut beside the passage
        elif nz < 0.55:
            slot = 2 if rnd.random() < 0.6 else 0
        else:
            r = math.sin(2.3 * x + 1.1 * y) + math.sin(1.7 * y - 2.9 * x + 1.0) + 0.3 * rnd.random()
            slot = 1 if r > 0.6 else 0 if r > -1.1 else 2  # lit and darker patches of turf
        poly.material_index = slot
    return obj


def _rough(name, size, at, mat, rnd, taper=0.8, jitter=0.07, rot=(0, 0, 0), bevel=0.035):
    """A rough stone: a box subdivided once, narrowed towards the top, its corners jittered; its foot flat on `at`'s
    z (the base, not the centre)."""
    sx, sy, sz = size
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
    for v in bm.verts:
        u = v.co.z + 0.5  # 0 at the foot, 1 at the top
        k = 1 - (1 - taper) * u
        j = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * jitter
        x = (v.co.x + j.x) * sx * k
        y = (v.co.y + j.y) * sy * k
        z = 0.0 if u < 0.01 else (u + j.z * (0.5 if u < 0.99 else 0.7)) * sz
        v.co = Vector((x, y, z))
    obj = box(name, (1, 1, 1), at, mat, rot=rot, bevel=bevel)
    bm.to_mesh(obj.data)
    bm.free()
    m = obj.rotation_euler.to_matrix()
    low = min((m @ v.co).z for v in obj.data.vertices)
    obj.location.z -= low  # a leaning stone's foot corner would dip below the ground
    return obj


def _portal(mats, rnd):
    """Two standing stones framing the mouth, a lintel across them, capstones roofing the mouth behind it."""
    px, py, pz = POST
    tops = []
    for side in (-1, 1):
        h = pz * rnd.uniform(0.98, 1.0)
        _rough(f"post_{side}", (px, py, h), (side * (TW + px / 2 - 0.02), YF + py / 2, 0), mats["stone"], rnd,
               taper=0.88, jitter=0.05, rot=(0, side * 1.0, rnd.uniform(-3, 3)))
        tops.append(h)
    lz = min(tops) - 0.05
    lx, ly, lh = LINTEL
    _rough("lintel", (lx, ly, lh), (0, YF + ly / 2 - 0.03, lz), mats["old"], rnd, taper=0.92, jitter=0.06,
           rot=(0, rnd.uniform(-1.5, 1.5), rnd.uniform(-2, 2)))
    # Lichen on the lintel's face and the posts' shoulders.
    for i, (x, z, s) in enumerate(((-0.4, lz + 0.22, 0.14), (0.35, lz + 0.12, 0.11), (TW + 0.15, 1.2, 0.09))):
        blob(f"lichen_{i}", s, (x, YF - 0.005, z), mats["lichen"], squash=(1.4, 0.18, 0.8), subdiv=1, seed=30 + i,
             jitter=0.2)
    # The mouth: nothing but dark between the posts, under the lintel.
    box("mouth_void", (2 * TW + 0.04, 0.1, lz), (0, YF + DEPTH - 0.05, lz / 2), mats["void"], bevel=0)
    return lz


def _shade(mats, t):
    return mats["steps"][min(SHADES - 1, int(t * SHADES))]


def _steps(mats, rnd):
    """Worn treads from the foot of the cut into the mouth, thinning and darkening as they go, over a dark floor."""
    y_start = -HY + 0.02
    y_end = YF + DEPTH - 0.1
    run = (y_end - y_start) / STEPS
    box("pit", (2 * TW - 0.02, y_end - y_start - 0.3, 0.01), (0, (y_start + 0.3 + y_end) / 2, 0.006), mats["void"],
        bevel=0)
    for i in range(STEPS):
        t = i / (STEPS - 1)
        y0 = y_start + i * run + TREAD_GAP / 2
        d = run - TREAD_GAP
        h = TREAD_TOP + (TREAD_LOW - TREAD_TOP) * t
        dark = ((y0 + d / 2 - y_start) / (y_end - y_start)) ** 1.2  # darker step by step towards the mouth
        box(f"tread_{i}", ((2 * TW - 0.04) * rnd.uniform(0.96, 1.0), d, h),
            (rnd.uniform(-0.015, 0.015), y0 + d / 2, h / 2), _shade(mats, min(0.999, dark)),
            rot=(0, 0, rnd.uniform(-1.2, 1.2)), bevel=min(0.022, h * 0.45))


def _walls(mats, rnd, waves):
    """Dry-stone revetments holding the cut's sides, from the front edge to the portal, as high as the turf behind."""
    y0, y1 = -HY + 0.04, YF + 0.02
    for side in (-1, 1):
        cx = side * (TW + WALL_T / 2)
        y = y0
        while y < y1 - 0.05:
            ln = min(rnd.uniform(0.22, 0.36), y1 - y)
            ym = y + ln / 2
            top = _mound_h(side * (TW + WALL_T + 0.02), ym, waves) * 0.98
            z = 0.012  # the courses' small tilts must not dip below the ground
            c = 0
            while z < top - 0.04:
                ch = min(COURSE * rnd.uniform(0.75, 1.1), top - z)
                if ch < 0.05:
                    break
                r = rnd.random()
                mat = mats["dry"] if r < 0.55 else mats["old"] if r < 0.8 else mats["moss"] if z > 0.2 else mats["old"]
                box(f"wall_{side}_{int(y * 100)}_{c}", (WALL_T * rnd.uniform(0.9, 1.0), ln - 0.02, ch - 0.015),
                    (cx + side * rnd.uniform(-0.015, 0.015), ym, z + ch / 2), mat,
                    rot=(rnd.uniform(-2, 2), rnd.uniform(-2, 2), rnd.uniform(-2.5, 2.5)), bevel=0.025)
                z += ch
                c += 1
            y += ln


def _side_stones(mats, rnd):
    for i, (x, y, h, lean) in enumerate(SIDE_STONES):
        _rough(f"standing_{i}", (0.42, 0.34, h), (x, y, 0), mats["stone" if i else "pale"], rnd, taper=0.7,
               jitter=0.08, rot=(lean * 0.5, lean, rnd.uniform(-15, 15)), bevel=0.04)
        blob(f"standing_moss_{i}", 0.12, (x, y - 0.12, h * 0.3), mats["moss"], squash=(1.6, 0.4, 1.0), subdiv=1,
             seed=50 + i, jitter=0.2)


def _dressing(mats, rnd, waves):
    """Fallen stones at the foot of the mound and grass tufts on it."""
    for i, (x, y, r) in enumerate(((-0.82, -1.3, 0.13), (0.95, -1.33, 0.1), (-1.38, -0.55, 0.11),
                                   (1.36, -0.35, 0.09), (0.72, -1.22, 0.07))):
        blob(f"stone_{i}", r, (x, y, r * 0.72), mats["old" if i % 2 else "stone"], squash=(1.3, 1.0, 0.6),
             subdiv=1, seed=60 + i, jitter=0.18)
    k = 0
    for _ in range(40):
        x = rnd.uniform(-HX + 0.2, HX - 0.2)
        y = rnd.uniform(-HY + 0.3, HY - 0.2)
        h = _mound_h(x, y, waves) * _cut(x, y)
        if h < 0.15 or (abs(x) < TW + WALL_T + 0.1 and y < YF + DEPTH + 0.2):
            continue
        r = rnd.uniform(0.07, 0.11)
        blob(f"tuft_{k}", r, (x, y, h + r * 0.15), mats["grass_lit" if k % 3 else "turf"], squash=(1.5, 1.3, 0.6),
             subdiv=1, seed=70 + k, jitter=0.25)
        k += 1
        if k >= 12:
            break


@prop
def crypt_entrance_stone():
    rnd = random.Random(12)
    mats = _mats()
    waves = _waves(9)
    _mound(mats, waves)
    _portal(mats, rnd)
    _steps(mats, rnd)
    _walls(mats, rnd, waves)
    _side_stones(mats, rnd)
    _dressing(mats, rnd, waves)
