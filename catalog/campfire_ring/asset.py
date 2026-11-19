"""A camp fire in a ring of rough fieldstones: a bed of grey ash and glowing embers, two split logs laid in a cross with
charred ends, three sticks leant together over them and low tongues of flame at the heart."""
import math
import random

import bpy

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, cylinder

# About 1.2 m across, flames to about 0.5 m.
RING_R = 0.49  # radius of the stone ring, to the stone centres
STONES = 13
STONE_R = (0.09, 0.12)  # half-width range of a ring stone
STONE_H = (0.12, 0.19)  # height range of a ring stone
ASH_R, ASH_H = 0.39, 0.04  # ash bed inside the ring
LOG_L, LOG_R = 0.72, 0.055  # the two crossed logs
STICK_L, STICK_R = 0.5, 0.028  # the sticks leant over them
STICK_FOOT = 0.3  # radius where the sticks rest on the ash
APEX = 0.38  # where the sticks meet
FLAME_TOP = 0.47
FLAT = 0.12  # share of a stone's height cut flat where it sits on the ground

STONE = (0.27, 0.25, 0.22)  # grey-brown fieldstone
STONE_DARK = (0.18, 0.165, 0.15)
SOOT = (0.06, 0.055, 0.05)  # fire-blackened stone
ASH = (0.15, 0.143, 0.13)
LOG = (0.15, 0.09, 0.05)
LOG_CUT = (0.3, 0.2, 0.11)  # split face and fresh ends
CHAR = (0.05, 0.042, 0.038)
EMBER = (0.5, 0.15, 0.03)
FLAME = (0.5, 0.28, 0.035)


def _settle(obj, z_min=0.0):
    """Move `obj` up or down so its lowest point is at `z_min`."""
    bpy.context.view_layer.update()
    lowest = min((obj.matrix_world @ v.co).z for v in obj.data.vertices)
    obj.location.z += z_min - lowest
    return obj


def _stone(name, r, h, at, mat, seed, stretch, yaw):
    """A rough stone `r` half-wide and `h` high with its base cut flat, standing on the ground."""
    rz = h / (2 * (1 - FLAT / 2))
    obj = blob(name, r, (at[0], at[1], 0), mat, squash=(stretch, 1 / stretch, rz / r), subdiv=2, seed=seed,
               jitter=0.14)
    verts = obj.data.vertices
    low = min(v.co.z for v in verts)
    cut = low + FLAT * (max(v.co.z for v in verts) - low)
    for v in verts:
        v.co.z = max(v.co.z, cut)
    obj.rotation_euler = (0, 0, math.radians(yaw))
    return _settle(obj)


def _rod(name, r, length, start, yaw, pitch, mat, segments=10):
    """A rod from `start`, heading `yaw` degrees round z and rising `pitch` degrees from the horizontal."""
    return cylinder(name, r, length, start, mat, segments=segments, rot=(0, 90 - pitch, yaw), bevel=0.006)


def _along(centre, yaw, pitch, d):
    """The point `d` metres from `centre` along the heading `yaw`, `pitch`."""
    y, p = math.radians(yaw), math.radians(pitch)
    return (centre[0] + d * math.cos(p) * math.cos(y), centre[1] + d * math.cos(p) * math.sin(y),
            centre[2] + d * math.sin(p))


@prop
def campfire_ring():
    rnd = random.Random(5)
    stone = material("campfire_ring_stone", STONE, rough=0.9, vary=0.28, scale=9, crevice=0.7)
    dark = material("campfire_ring_stone_dark", STONE_DARK, rough=0.9, vary=0.28, scale=9, crevice=0.7)
    soot = material("campfire_ring_soot", SOOT, rough=0.9, vary=0.3, scale=12, crevice=0.5)
    ash = material("campfire_ring_ash", ASH, vary=0.3, scale=16, crevice=0.6)
    log = material("campfire_ring_log", LOG, vary=0.3, scale=18)
    cut = material("campfire_ring_log_cut", LOG_CUT, vary=0.25, scale=24)
    char = material("campfire_ring_char", CHAR, rough=0.7, vary=0.3, scale=20)
    ember = material("campfire_ring_ember", EMBER, rough=0.6, vary=0.35, scale=14, crevice=0.2)
    flame = material("campfire_ring_flame", FLAME, rough=0.5, vary=0.3, scale=10, crevice=0.1)

    # Ring of stones, a few blackened by the fire.
    for i in range(STONES):
        a = 2 * math.pi * (i + rnd.uniform(-0.15, 0.15)) / STONES
        rr = RING_R + rnd.uniform(-0.025, 0.02)
        r = rnd.uniform(*STONE_R)
        mat = soot if i % 4 == 1 else (dark if rnd.random() < 0.35 else stone)
        _stone(f"stone_{i}", r, rnd.uniform(*STONE_H), (rr * math.cos(a), rr * math.sin(a)), mat, 10 + i,
               rnd.uniform(1.1, 1.35), math.degrees(a) + 90 + rnd.uniform(-15, 15))

    # Ash bed and a glowing heap of embers at its heart.
    bed = blob("ash_bed", ASH_R, (0, 0, 0), ash, squash=(1, 1, ASH_H / ASH_R), subdiv=2, seed=2, jitter=0.08)
    _settle(bed, -0.004)
    _settle(blob("scorch", 0.3, (0, 0, ASH_H), char, squash=(1.0, 1.1, 0.12), subdiv=2, seed=4, jitter=0.2), 0.004)
    _settle(blob("embers", 0.2, (0, 0, ASH_H), ember, squash=(1.1, 1.0, 0.3), subdiv=2, seed=3, jitter=0.25), 0.006)
    for i in range(16):
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(0.1, 0.3)
        blob(f"cinder_{i}", rnd.uniform(0.025, 0.04), (d * math.cos(a), d * math.sin(a), ASH_H * 0.7),
             ember if d < 0.22 else char, squash=(1.2, 1.0, 0.6), subdiv=1, seed=40 + i, jitter=0.25)

    # Two logs in a cross: the first lies on the ash, the second rests across it, its ends on the ground.
    low_yaw, top_yaw = 30, 115
    z0 = ASH_H * 0.5 + LOG_R
    centre = (0, 0, z0)
    _rod("log_low", LOG_R, LOG_L, _along(centre, low_yaw + 180, 0, LOG_L / 2), low_yaw, 0, log)
    pitch = math.degrees(math.asin(2 * LOG_R / (LOG_L / 2)))
    mid = (0, 0, z0 + 2 * LOG_R)
    top = _rod("log_top", LOG_R * 0.95, LOG_L, _along(mid, top_yaw + 180, pitch, LOG_L / 2), top_yaw, -pitch, char)
    bpy.context.view_layer.update()
    if min((top.matrix_world @ v.co).z for v in top.data.vertices) < 0:
        _settle(top)
    # Fresh pale ends on the unburnt log.
    for s in (-1, 1):
        end = _along(centre, low_yaw, 0, s * (LOG_L / 2 + 0.004) - 0.004)
        _rod(f"log_low_end_{s}", LOG_R * 0.85, 0.008, end, low_yaw, 0, cut, segments=10)

    # Three sticks leant together over the cross, their feet on the ash.
    for i in range(3):
        b = 60 + 120 * i + rnd.uniform(-12, 12)
        foot = (STICK_FOOT * math.cos(math.radians(b)), STICK_FOOT * math.sin(math.radians(b)), 0)
        rise = math.degrees(math.atan2(APEX, STICK_FOOT))
        stick = _rod(f"stick_{i}", STICK_R, STICK_L, foot, b + 180 + rnd.uniform(-6, 6), rise + rnd.uniform(-4, 4),
                     char if i == 1 else log, segments=8)
        _settle(stick, ASH_H * 0.4)

    # Tongues of flame rising through the sticks (the fire anchor animates the rest).
    for i, (fx, fy, fr, tall) in enumerate([(0.0, 0.0, 0.06, 1.0), (0.08, -0.05, 0.05, 0.7),
                                            (-0.07, 0.06, 0.05, 0.6), (-0.04, -0.09, 0.045, 0.45),
                                            (0.06, 0.08, 0.04, 0.4)]):
        h = (FLAME_TOP - 0.06) * tall
        blob(f"flame_{i}", fr, (fx, fy, 0.06 + h / 2), flame, squash=(0.85, 0.8, h / (2 * fr)), subdiv=2,
             seed=70 + i, jitter=0.12)

    anchor("fire:camp", (0, 0, ASH_H + 0.04), size=(0.25, 0.25, 0.6))
    anchor("light:fire", (0, 0, 0.45))
