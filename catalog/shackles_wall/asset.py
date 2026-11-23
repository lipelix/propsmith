"""Wall shackles: a long riveted iron plate with two heavy rings on staples, a chain hanging from each ring to a pair
of hinged manacles: the left chain runs down the wall and along the floor to a pair lying open on the ground, the
right one hangs to a pair just clear of it. The back of the plate is flat on +y, to fix on a wall; the model stands on its lowest manacle, so the plate sits
about 0.9 m up the wall."""
import math
import random

from mathutils import Quaternion, Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall dimensions (metres): about 0.8 m wide, 0.15 m deep, 1 m high.
WALL_Y = 0.07  # the back of the plate (the wall face)
PLATE = (0.7, 0.025, 0.13)  # x, y, z
PLATE_Z = 0.9  # centre of the plate
RING_X = 0.24  # the rings, either side of the middle
RING_R, RING_T = 0.055, 0.012
LINK_R, LINK_T = 0.026, 0.007  # chain link radius and wire
LINK_PITCH = 0.044
CUFF_R, CUFF_T = 0.05, 0.012  # a manacle: inside radius and bar

IRON = (0.045, 0.044, 0.042)  # linear RGB
IRON_WORN = (0.1, 0.092, 0.082)
RUST = (0.1, 0.055, 0.033)


def _euler(q):
    return tuple(math.degrees(a) for a in q.to_euler("XYZ"))


def _chain(name, a, b, mat, r=LINK_R, t=LINK_T, pitch=LINK_PITCH):
    """A chain of round links from `a` to `b`, each link turned a quarter turn from the last."""
    a, b = Vector(a), Vector(b)
    d = b - a
    n = max(2, round(d.length / pitch))
    q = Vector((1, 0, 0)).rotation_difference(d.normalized())
    for i in range(n):
        at = a + d * ((i + 0.5) / n)
        qi = q @ Quaternion((1, 0, 0), math.pi / 2) if i % 2 else q
        torus(f"{name}_{i}", r, t, tuple(at), mat, rot=_euler(qi), major=8, minor=5)


def _cuff(name, at, mat, rot=(90, 0, 0)):
    """One manacle's ring (its hinge knuckle and lock lug are added beside it)."""
    torus(f"{name}_ring", CUFF_R + CUFF_T, CUFF_T, at, mat, rot=rot, major=14, minor=6)


@prop
def shackles_wall():
    rnd = random.Random(3)
    iron = material("shackles_wall_iron", IRON, rough=0.55, vary=0.25, scale=18, metal=0.6)
    worn = material("shackles_wall_iron_worn", IRON_WORN, rough=0.5, vary=0.25, scale=22, metal=0.7)
    rust = material("shackles_wall_rust", RUST, rough=0.85, vary=0.3, scale=24, metal=0.25)

    # The wall plate, with a row of rivet heads along top and bottom and a big bolt at each end.
    py = WALL_Y - PLATE[1] / 2
    box("plate", PLATE, (0, py, PLATE_Z), iron, rot=(0, rnd.uniform(-1, 1), 0), bevel=0.006)
    front = WALL_Y - PLATE[1]
    for k in range(6):
        x = -PLATE[0] / 2 + 0.07 + (PLATE[0] - 0.14) * k / 5
        for j, dz in enumerate((-0.042, 0.042)):
            cylinder(f"rivet_{k}_{j}", 0.011, 0.01, (x, front, PLATE_Z + dz), worn, segments=6, rot=(90, 0, 0),
                     bevel=0)
    for k, s in enumerate((-1, 1)):
        cylinder(f"bolt_{k}", 0.024, 0.018, (s * (PLATE[0] / 2 - 0.04), front, PLATE_Z), worn, segments=6,
                 rot=(90, 0, 0), bevel=0.004)

    # A staple on the plate and a heavy ring hanging from it, on each side.
    ring_y = front - 0.03
    tops = []
    for k, s in enumerate((-1, 1)):
        x = s * RING_X
        box(f"staple_plate_{k}", (0.07, 0.012, 0.07), (x, front - 0.006, PLATE_Z), iron, bevel=0.004)
        torus(f"staple_{k}", 0.024, 0.008, (x, front - 0.02, PLATE_Z + 0.005), iron, rot=(0, 90, 0), major=10,
              minor=6)
        rz = PLATE_Z - RING_R + 0.005
        torus(f"ring_{k}", RING_R, RING_T, (x, ring_y, rz), worn, rot=(90, rnd.uniform(-8, 8), 0), major=16,
              minor=6)
        tops.append((x, ring_y, rz - RING_R))

    # Left: the chain runs down the wall and along the floor to a pair of manacles lying flat.
    fy = -0.005
    fx = -0.2
    gap = 0.03  # the floor pair lies close together
    rr = CUFF_R + 2 * CUFF_T
    for k, sx in enumerate((-1, 1)):
        x = fx + sx * (gap / 2 + CUFF_R + CUFF_T)
        _cuff(f"floor_cuff_{k}", (x, fy, CUFF_T), rust if k else iron, rot=(0, 0, 0))
        box(f"floor_lug_{k}", (0.032, 0.026, 0.022), (x + sx * rr, fy, 0.011), worn, bevel=0.004)
        box(f"floor_knuckle_{k}", (0.03, 0.03, 0.022), (x - sx * (rr - 0.01), fy, 0.011), iron, bevel=0.004)
    _chain("floor_link", (fx - gap / 2 - 0.02, fy, 0.024), (fx + gap / 2 + 0.02, fy, 0.024), iron,
           r=0.018, t=0.006, pitch=0.03)
    bend = (tops[0][0] + 0.02, ring_y, LINK_R + LINK_T)
    _chain("chain_l_wall", tops[0], bend, iron)
    _chain("chain_l_floor", bend, (fx + 0.005, fy + 0.01, LINK_R + LINK_T), iron)

    # Right: the chain hangs straight to a ring, two short chains from it to a pair of cuffs hanging just clear of
    # the floor, each with its hinge knuckle up and its lock lug down.
    hx, hz = RING_X + 0.02, 0.3
    hy = ring_y
    torus("hang_ring", 0.03, 0.008, (hx, hy, hz), worn, rot=(90, 0, 0), major=12, minor=6)
    _chain("chain_r", tops[1], (hx, hy, hz + 0.03), iron)
    for k, sx in enumerate((-1, 1)):
        x = hx + sx * 0.075
        cz = hz - 0.07 - rr
        _cuff(f"hang_cuff_{k}", (x, hy, cz), iron, rot=(90, 0, 0))
        box(f"hang_knuckle_{k}", (0.03, 0.03, 0.03), (x, hy, cz + rr - 0.006), iron, bevel=0.004)
        box(f"hang_lug_{k}", (0.026, 0.032, 0.03), (x, hy, cz - rr + 0.004), rust, bevel=0.004)
        _chain(f"hang_link_{k}", (hx + sx * 0.02, hy, hz - 0.025), (x, hy, cz + rr + 0.01), iron, r=0.018, t=0.006,
               pitch=0.03)
