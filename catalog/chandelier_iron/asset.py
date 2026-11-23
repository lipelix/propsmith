"""A wrought iron ring chandelier: a heavy flat-hung iron ring about 1.4 m across carrying eight ivory candles in drip
pans, held to a central hub by four spokes with a pointed drop finial under it and small scrolls between the candles,
hung on three chains that gather at a ring and run up a short chain to a hook on a round ceiling plate. The model
stands on the tip of its finial; a game hangs it at the height it wants (the ring about 2.6 m above the floor puts
the plate at about 3.6 m)."""
import math

from mathutils import Quaternion, Vector

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, cylinder, torus

# Overall size: about 1.4 m across the ring's candle pans, 1.3 m from the finial's tip to the ceiling plate.
RING_R, RING_T = 0.64, 0.026  # ring radius and tube radius
RING_Z = 0.25  # centre of the ring above the finial's tip
HUB_Z = 0.22
CANDLES = 8
PAN_R, PAN_H = 0.045, 0.014
CANDLE_R, CANDLE_H = 0.026, 0.13
WICK_H = 0.015
FLAME_H = 0.045
CHAINS = 3
GATHER_Z = 1.06  # the ring where the three chains meet
LINK_R, LINK_T = 0.032, 0.007  # chain link radius and wire
LINK_PITCH = 0.05
PLATE_Z, PLATE_R, PLATE_H = 1.27, 0.1, 0.03  # the ceiling plate's underside, radius, thickness

IRON = (0.045, 0.044, 0.042)  # linear RGB
IRON_WORN = (0.11, 0.1, 0.09)
WAX = (0.5, 0.44, 0.32)
WICK = (0.06, 0.05, 0.04)
FLAME = (0.5, 0.3, 0.06)


def _euler(q):
    return tuple(math.degrees(a) for a in q.to_euler("XYZ"))


def _rod(name, r, a, b, mat, segments=8, bevel=0.003):
    """A round rod from point `a` to point `b`."""
    d = Vector(b) - Vector(a)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return cylinder(name, r, d.length, a, mat, segments=segments, rot=_euler(q), bevel=bevel)


def _chain(name, a, b, mat):
    """A chain of round links from `a` to `b`, each link turned a quarter turn from the last."""
    a, b = Vector(a), Vector(b)
    d = b - a
    n = max(2, round(d.length / LINK_PITCH))
    q = Vector((1, 0, 0)).rotation_difference(d.normalized())
    for i in range(n):
        at = a + d * ((i + 0.5) / n)
        qi = q @ Quaternion((1, 0, 0), math.pi / 2) if i % 2 else q
        torus(f"{name}_{i}", LINK_R, LINK_T, tuple(at), mat, rot=_euler(qi), major=6, minor=4)


@prop
def chandelier_iron():
    iron = material("chandelier_iron_iron", IRON, rough=0.55, vary=0.25, scale=22, metal=0.6)
    worn = material("chandelier_iron_iron_worn", IRON_WORN, rough=0.4, vary=0.3, scale=30, metal=0.7)
    wax = material("chandelier_iron_wax", WAX, rough=0.5, vary=0.08, scale=10, crevice=0.12)
    wick = material("chandelier_iron_wick", WICK, rough=0.9, vary=0.1, scale=20)
    flame = material("chandelier_iron_flame", FLAME, rough=0.5, vary=0.3, scale=10, crevice=0.1)

    # The ring, with a thinner inner ring under it.
    torus("ring", RING_R, RING_T, (0, 0, RING_Z), iron, major=36, minor=6)
    torus("ring_inner", RING_R - 0.05, 0.012, (0, 0, RING_Z - 0.02), worn, major=28, minor=4)

    # Hub, four spokes and the pointed drop finial.
    cylinder("hub", 0.05, 0.07, (0, 0, HUB_Z - 0.035), worn, r_top=0.04, segments=12, bevel=0.005)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        _rod(f"spoke_{k}", 0.012, (0.04 * math.cos(a), 0.04 * math.sin(a), HUB_Z),
             ((RING_R - 0.01) * math.cos(a), (RING_R - 0.01) * math.sin(a), RING_Z), iron)
    blob("finial_ball", 0.04, (0, 0, 0.13), worn, subdiv=1, seed=3, jitter=0.03)
    cylinder("finial_point", 0.002, 0.11, (0, 0, 0), iron, r_top=0.022, segments=8, bevel=0)
    cylinder("finial_neck", 0.018, HUB_Z - 0.17, (0, 0, 0.16), iron, segments=8, bevel=0.003)

    # Eight candles in drip pans on the ring, with small scrolls hanging between them.
    pan_z = RING_Z + RING_T - 0.004
    for k in range(CANDLES):
        a = math.radians(360 * k / CANDLES)
        x, y = RING_R * math.cos(a), RING_R * math.sin(a)
        cylinder(f"pan_{k}", PAN_R - 0.01, PAN_H, (x, y, pan_z), iron, r_top=PAN_R, segments=10, bevel=0)
        h = CANDLE_H * (0.75 + 0.25 * ((k * 5) % 3) / 2)  # burnt down unevenly
        base = pan_z + PAN_H - 0.003
        cylinder(f"candle_{k}", CANDLE_R, h, (x, y, base), wax, segments=8, bevel=0)
        top = base + h
        blob(f"drip_{k}", 0.01, (x + CANDLE_R * math.cos(a + 1), y + CANDLE_R * math.sin(a + 1), top - 0.03), wax,
             squash=(0.8, 0.8, 1.8), subdiv=1, seed=20 + k, jitter=0.1)
        cylinder(f"wick_{k}", 0.003, WICK_H, (x, y, top - 0.003), wick, segments=6, bevel=0)
        blob(f"flame_{k}", 0.012, (x, y, top + WICK_H + 0.008), flame, squash=(1, 1, 2.2), subdiv=1, seed=40 + k,
             jitter=0.05)
        anchor(f"light:candle_{k + 1}", (x, y, top + WICK_H + 0.01))

        b = a + math.pi / CANDLES
        sr = RING_R + 0.004
        torus(f"scroll_{k}", 0.03, 0.006, (sr * math.cos(b), sr * math.sin(b), RING_Z - 0.04), worn,
              rot=(90, 0, math.degrees(b) + 90), major=8, minor=4)

    # Three chains from the ring up to a gathering ring, then a short chain to the hook and the ceiling plate.
    gather = Vector((0, 0, GATHER_Z))
    for k in range(CHAINS):
        a = math.radians(90 + 360 * k / CHAINS)
        foot = Vector(((RING_R) * math.cos(a), RING_R * math.sin(a), RING_Z + RING_T + 0.02))
        torus(f"eye_{k}", 0.025, 0.007, tuple(foot), worn, rot=(90, 0, math.degrees(a) + 90), major=10, minor=4)
        _chain(f"chain_{k}", foot + (gather - foot).normalized() * 0.03, gather, iron)
    torus("gather_ring", 0.045, 0.01, tuple(gather), worn, major=14, minor=5)
    hook_z = PLATE_Z - 0.07
    _chain("chain_top", gather + Vector((0, 0, 0.03)), (0, 0, hook_z - 0.03), iron)
    torus("hook", 0.032, 0.009, (0, 0, hook_z), worn, rot=(90, 0, 0), major=12, minor=5)
    cylinder("hook_stem", 0.01, PLATE_Z - hook_z - 0.03, (0, 0, hook_z + 0.03), iron, segments=8, bevel=0)
    cylinder("plate", PLATE_R, PLATE_H, (0, 0, PLATE_Z), iron, r_top=PLATE_R * 0.9, segments=16, bevel=0.005)
    for k in range(3):
        a = math.radians(30 + 120 * k)
        blob(f"rivet_{k}", 0.011, (0.07 * math.cos(a), 0.07 * math.sin(a), PLATE_Z - 0.002), worn,
             squash=(1, 1, 0.6), subdiv=1, seed=60 + k, jitter=0.02)
