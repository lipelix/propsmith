"""A few loose pebbles and one fist-sized stone lying half sunk in the ground, grey-brown with a little moss (generated
by npm run new). Variants: a small scatter of five or six pebbles, a larger cluster around one flat stone."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob

TILE = 1.5  # metres per tile
# Footprint 1x1 tile (1.5 x 1.5 m), height 0.1 tile (0.15 m). The stones stay well inside 0.6 m across.
SCATTER_R = 0.2  # metres, outer radius of the small scatter
CLUSTER_R = 0.24  # metres, outer radius of the cluster
FIST_R = 0.055  # metres, half-width of the fist-sized stone
FIST_H = 0.045  # metres, how far the half-sunk fist stone stands up
FLAT_R = 0.11  # metres, half-length of the flat stone
FLAT_H = 0.03  # metres, how far the flat stone stands up
PEBBLE_R = (0.016, 0.03)  # metres, half-width range of a pebble
PEBBLE_FLAT = (0.45, 0.65)  # height / width of a pebble (lying flat, half sunk)
JITTER = 0.1

STONE = (0.27, 0.24, 0.2)  # linear RGB, grey-brown
STONE_DARK = (0.21, 0.19, 0.155)
STONE_PALE = (0.34, 0.31, 0.26)
MOSS = (0.08, 0.11, 0.035)


def _stone(name, r, h, x, y, mat, subdiv, seed, stretch=1.0):
    """A stone lying on the ground: a squashed lumpy blob whose bottom sits at z = 0 (the dome reads as half sunk)."""
    blob(name, r, (x, y, h), mat, squash=(stretch, 1 / stretch, h / r), subdiv=subdiv, seed=seed, jitter=JITTER)


def _moss(name, r, x, y, top, mat, seed):
    """A thin moss cushion on the shoulder of a stone, its lower half buried in the stone."""
    h = r * 0.3
    blob(name, r, (x, y, top - h * 0.6), mat, squash=(1, 0.8, 0.3), subdiv=2, seed=seed, jitter=0.2)


def _mats():
    return (
        material("pebbles_stone", STONE, rough=0.85, vary=0.3, scale=40, crevice=0.6),
        material("pebbles_stone_dark", STONE_DARK, rough=0.85, vary=0.3, scale=40, crevice=0.6),
        material("pebbles_stone_pale", STONE_PALE, rough=0.85, vary=0.25, scale=40, crevice=0.6),
        material("pebbles_moss", MOSS, rough=0.95, vary=0.35, scale=60, crevice=0.5),
    )


def _pebbles(rnd, n, r_min, r_max, mats, seed0, avoid):
    """`n` pebbles on a ring between `r_min` and `r_max`, spread round the centre, clear of the `avoid` circles."""
    placed = list(avoid)
    yaw0 = rnd.uniform(0, 360)
    for i in range(n):
        r = rnd.uniform(*PEBBLE_R)
        for _ in range(40):
            a = math.radians(yaw0 + 360 * i / n + rnd.uniform(-25, 25))
            d = rnd.uniform(r_min, r_max)
            x, y = d * math.cos(a), d * math.sin(a)
            if all(math.hypot(x - px, y - py) > r + pr + 0.006 for px, py, pr in placed):
                break
        placed.append((x, y, r))
        h = r * rnd.uniform(*PEBBLE_FLAT)
        _stone(f"pebbles_pebble_{i}", r, h, x, y, rnd.choice(mats), 2, seed0 + i, stretch=rnd.uniform(1.0, 1.35))


@prop
def pebbles():
    rnd = random.Random(4)
    stone, dark, pale, moss = _mats()
    fx, fy = 0.02, 0.01
    _stone("pebbles_fist", FIST_R, FIST_H, fx, fy, stone, 3, 11, stretch=1.12)
    _moss("pebbles_moss_0", 0.038, fx - 0.012, fy + 0.016, 2 * FIST_H * 0.92, moss, 3)
    _pebbles(rnd, 6, FIST_R + 0.05, SCATTER_R, [stone, dark, pale, stone], 20, [(fx, fy, FIST_R * 1.15)])


@prop
def pebbles_cluster():
    rnd = random.Random(17)
    stone, dark, pale, moss = _mats()
    _stone("pebbles_flat", FLAT_R, FLAT_H, 0, 0, pale, 3, 5, stretch=1.2)
    _moss("pebbles_moss_0", 0.045, -0.04, 0.025, 2 * FLAT_H * 0.93, moss, 7)
    fx, fy = 0.13, -0.08
    _stone("pebbles_fist", FIST_R * 0.9, FIST_H * 0.9, fx, fy, stone, 3, 13, stretch=1.1)
    _moss("pebbles_moss_1", 0.025, fx - 0.01, fy + 0.012, 2 * FIST_H * 0.9 * 0.9, moss, 9)
    avoid = [(0, 0, FLAT_R * 1.35), (fx, fy, FIST_R)]
    _pebbles(rnd, 8, FLAT_R + 0.04, CLUSTER_R, [stone, dark, pale, dark], 40, avoid)
