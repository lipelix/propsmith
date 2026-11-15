"""A thick round chopping block cut from a tree trunk with an axe stuck in its top, split logs and chips around it."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

R_BLOCK, H_BLOCK = 0.25, 0.45  # the trunk block: 0.5 m across, 0.45 m high
CUT = 0.02  # thickness of the pale cut face on top
HAFT_L, HAFT_R = 0.72, 0.021  # axe haft length and radius
AXE_TILT, AXE_YAW = 38.0, 40.0  # haft rise above horizontal and its heading (degrees), across the camera view
LOG_L, LOG_R = 0.42, 0.075  # split logs

BARK = (0.1, 0.068, 0.044)
CUT_WOOD = (0.44, 0.33, 0.2)
RING = (0.28, 0.19, 0.105)
SPLIT = (0.36, 0.25, 0.14)
ASH = (0.38, 0.28, 0.16)
IRON = (0.05, 0.05, 0.052)


def _log_lying(name, r, cx, cy, yaw, mat, segments, roll=0.0):
    """A cylinder lying on the ground, centred on (cx, cy), its axis heading `yaw` degrees from -y."""
    a = math.radians(yaw)
    dx, dy = math.sin(a), -math.cos(a)  # Rz(yaw) applied to (0, -1, 0)
    z = r * (0.5 if segments == 3 else 1.0)
    at = (cx - dx * LOG_L / 2, cy - dy * LOG_L / 2, z)
    return cylinder(name, r, LOG_L, at, mat, segments=segments, rot=(90, roll, yaw), bevel=0.012)


@prop
def chopping_block():
    rnd = random.Random(7)
    bark = material("chopping_block_bark", BARK, vary=0.4, scale=28, rough=1.0)
    cut = material("chopping_block_cut", CUT_WOOD, vary=0.18, scale=9)
    ring = material("chopping_block_ring", RING, vary=0.15, scale=9)
    split = material("chopping_block_split", SPLIT, vary=0.28, scale=16)
    ash = material("chopping_block_haft", ASH, vary=0.15, scale=10)
    iron = material("chopping_block_iron", IRON, rough=0.45, metal=0.8, vary=0.2, scale=20)

    # The block: a slightly flared bark trunk with a pale cut face and a few growth rings on top.
    bx, by = -0.06, 0.06
    cylinder("trunk", R_BLOCK, H_BLOCK - CUT, (bx, by, 0), bark, r_top=R_BLOCK - 0.012, segments=20, bevel=0.01)
    cylinder("cut_top", R_BLOCK - 0.022, CUT, (bx, by, H_BLOCK - CUT - 0.002), cut, segments=20, bevel=0.008)
    for i, rr in enumerate((0.2, 0.15, 0.1, 0.05)):
        torus(f"ring_{i}", rr, 0.0045, (bx + 0.006 * i, by - 0.004 * i, H_BLOCK - 0.003), ring, major=24, minor=4)

    # The axe: head sunk into the top at an angle, the ash haft rising toward the camera.
    ta, ya = math.radians(AXE_TILT), math.radians(AXE_YAW)
    hd = (math.cos(ta) * math.cos(ya), math.cos(ta) * math.sin(ya), math.sin(ta))  # haft direction
    bd = (math.sin(ta) * math.cos(ya), math.sin(ta) * math.sin(ya), -math.cos(ta))  # blade direction (down)
    p = (bx - 0.05, by - 0.04, H_BLOCK + 0.075)  # where the haft goes through the head

    def off(base, d, k):
        return tuple(base[i] + d[i] * k for i in range(3))

    head_rot = (0, -AXE_TILT, AXE_YAW)
    box("axe_head", (0.075, 0.048, 0.1), off(p, bd, 0.0), iron, rot=head_rot, bevel=0.009)
    box("axe_blade", (0.12, 0.016, 0.11), off(p, bd, 0.09), iron, rot=head_rot, bevel=0.006)
    cylinder("axe_haft", HAFT_R, HAFT_L, off(p, hd, -0.05), ash, segments=8, rot=(0, 90 - AXE_TILT, AXE_YAW), bevel=0.004)

    # Split logs and one round log lying around the block.
    _log_lying("log_split_a", LOG_R, -0.18, -0.42, 78 + rnd.uniform(-4, 4), split, 3)
    _log_lying("log_split_b", LOG_R * 0.9, 0.38, 0.3, 20 + rnd.uniform(-4, 4), split, 3)
    _log_lying("log_round", 0.065, 0.42, -0.12, -12, bark, 10)

    # Chips: small pale flakes on the ground.
    for i in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(0.3, 0.6)
        box(
            f"chip_{i}",
            (rnd.uniform(0.04, 0.08), rnd.uniform(0.02, 0.035), 0.012),
            (bx + d * math.cos(a), by + d * math.sin(a), 0.007),
            split if i % 3 else cut,
            rot=(rnd.uniform(-3, 3), rnd.uniform(-3, 3), rnd.uniform(0, 180)),
            bevel=0.003,
        )
