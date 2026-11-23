"""A riveted iron cage a person could crouch in: a square frame of flat iron bands on four corner posts, round bars on
every side and a barred roof with a hanging ring on top, a floor of flat iron slats on short feet, and a barred door on
the front (-y) hung on two strap hinges and standing ajar, a hasp and an open padlock hanging from the frame."""
import math
import random

import bpy

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall dimensions (metres): a 1.1 m square cage 1.45 m high to its roof, the ring on top at 1.6 m.
W = 1.1  # outside of the frame, x and y
H = 1.45  # top of the roof frame
FOOT_H = 0.06  # short feet under the corners
POST = 0.05  # square corner post
BAND_H, BAND_T = 0.055, 0.014  # flat bands round the cage
BANDS_Z = (FOOT_H + BAND_H / 2, 0.78, H - BAND_H / 2)  # floor band, middle band, top band
BAR_R = 0.011
BAR_PITCH = 0.12
DOOR_W = 0.5  # the door, centred on the front
DOOR_Z0, DOOR_Z1 = 0.12, 1.32  # bottom and top of the door
DOOR_OPEN = 18  # degrees the door stands ajar (outwards)
RING_R, RING_T = 0.042, 0.01  # the hanging ring on the roof
# The cage sits this far back (+y) of the origin, so the footprint with the open door is centred on it.
BODY_Y = 0.095

IRON = (0.045, 0.044, 0.042)  # linear RGB
IRON_WORN = (0.1, 0.092, 0.082)
RUST = (0.1, 0.055, 0.033)


def _bars(span, gap_from=None, gap_to=None):
    """Bar positions along a side of length `span` (centred on 0), a bar about every BAR_PITCH, skipping the door."""
    inner = span / 2 - POST / 2
    n = max(1, round(2 * inner / BAR_PITCH) - 1)
    step = 2 * inner / (n + 1)
    out = [-inner + step * (i + 1) for i in range(n)]
    if gap_from is not None:
        out = [p for p in out if not gap_from - 0.03 < p < gap_to + 0.03]
    return out


@prop
def cage_iron():
    rnd = random.Random(11)
    iron = material("cage_iron_iron", IRON, rough=0.55, vary=0.25, scale=18, metal=0.6)
    worn = material("cage_iron_iron_worn", IRON_WORN, rough=0.5, vary=0.25, scale=22, metal=0.7)
    rust = material("cage_iron_rust", RUST, rough=0.85, vary=0.3, scale=24, metal=0.25)

    def metal():
        return rnd.choice((iron, iron, iron, rust))

    half = W / 2
    # Corner posts on short square feet.
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        x, y = sx * (half - POST / 2), sy * (half - POST / 2)
        box(f"foot_{i}", (POST + 0.02, POST + 0.02, FOOT_H), (x, y, FOOT_H / 2), iron, bevel=0.006)
        box(f"post_{i}", (POST, POST, H - FOOT_H), (x, y, (H + FOOT_H) / 2), iron, bevel=0.008)
        cylinder(f"post_cap_{i}", 0.032, 0.03, (x, y, H), worn, segments=8, bevel=0)

    # Flat bands round all four sides at the floor, the middle and the top; the front middle band stops at the door.
    dx0, dx1 = -DOOR_W / 2, DOOR_W / 2
    for j, z in enumerate(BANDS_Z):
        for s in (-1, 1):
            y = s * (half - BAND_T / 2)
            if s == -1 and j == 1:
                seg = half - POST - (dx1 + 0.02)
                for k in (-1, 1):
                    box(f"band_{j}_front_{k}", (seg, BAND_T, BAND_H), (k * (dx1 + 0.02 + seg / 2), y, z), iron,
                        bevel=0.004)
            else:
                box(f"band_{j}_y{s}", (W - 2 * POST + 0.004, BAND_T, BAND_H), (0, y, z), iron, bevel=0.004)
            x = s * (half - BAND_T / 2)
            box(f"band_{j}_x{s}", (BAND_T, W - 2 * POST + 0.004, BAND_H), (x, 0, z), iron, bevel=0.004)

    # Floor slats across the bottom band.
    for k in range(7):
        x = -half + POST + (W - 2 * POST) * (k + 0.5) / 7
        box(f"slat_{k}", (0.09, W - 0.03, 0.012), (x, 0, FOOT_H + 0.012), worn if k % 3 == 0 else iron,
            rot=(0, 0, rnd.uniform(-0.5, 0.5)), bevel=0)

    # Round bars between the bottom and the top bands, with a rivet where each crosses a band.
    z0, z1 = BANDS_Z[0], BANDS_Z[2]
    sides = [  # name, bar centre, rivet base on the band's outer face, rivet rotation, bar positions
        ("back", lambda p: (p, half - BAND_T / 2), lambda p: (p, half), (-90, 0, 0), _bars(W)),
        ("left", lambda p: (-half + BAND_T / 2, p), lambda p: (-half, p), (0, -90, 0), _bars(W)),
        ("right", lambda p: (half - BAND_T / 2, p), lambda p: (half, p), (0, 90, 0), _bars(W)),
        ("front", lambda p: (p, -half + BAND_T / 2), lambda p: (p, -half), (90, 0, 0), _bars(W, dx0, dx1)),
    ]
    for name, at, rivet_at, rot, ps in sides:
        for i, p in enumerate(ps):
            x, y = at(p)
            cylinder(f"bar_{name}_{i}", BAR_R, z1 - z0, (x, y, z0), metal(), segments=8,
                     rot=(rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), 0), bevel=0)
            rx, ry = rivet_at(p)
            for j, z in enumerate(BANDS_Z):
                if name == "front" and j == 1:
                    continue
                cylinder(f"rivet_{name}_{i}_{j}", 0.011, 0.008, (rx, ry, z), worn, segments=6, rot=rot, bevel=0)

    # Barred roof: bars both ways over the top band, a crossed pair of straps and the hanging ring.
    for i, p in enumerate(_bars(W)):
        if i % 2:
            continue
        cylinder(f"roof_x_{i}", BAR_R, W - 0.04, (-half + 0.02, p, H - 0.012), iron, segments=8, rot=(0, 90, 0),
                 bevel=0)
        cylinder(f"roof_y_{i}", BAR_R, W - 0.04, (p, -half + 0.02, H - 0.012), iron, segments=8, rot=(-90, 0, 0),
                 bevel=0)
    for k, a in enumerate((45, -45)):
        box(f"roof_strap_{k}", (W * math.sqrt(2) - 0.12, 0.05, 0.012), (0, 0, H + 0.006), iron, rot=(0, 0, a),
            bevel=0)
    box("roof_boss", (0.12, 0.12, 0.02), (0, 0, H + 0.02), worn, rot=(0, 0, 45), bevel=0.006)
    box("ring_eye", (0.03, 0.03, 0.04), (0, 0, H + 0.045), iron, bevel=0.005)
    torus("ring", RING_R, RING_T, (0, 0, H + 0.065 + RING_R - RING_T), worn, rot=(90, 0, 0), major=16, minor=6)

    # Door frame posts either side of the opening.
    fy = -half + BAND_T / 2
    for k, x in enumerate((dx0 - 0.02, dx1 + 0.02)):
        box(f"door_post_{k}", (0.03, 0.03, z1 - z0), (x, fy, (z0 + z1) / 2), iron, bevel=0.005)

    # The door, hinged on its left edge, swung out (towards -y) by DOOR_OPEN degrees.
    hx, hy = dx0 - 0.002, -half - 0.03
    a = math.radians(DOOR_OPEN)
    ux, uy = math.cos(a), -math.sin(a)  # along the door from the hinge

    def door(t, n=0.0):
        """A point `t` metres along the door from the hinge, `n` metres in front of (-) or behind (+) it."""
        return (hx + ux * t - uy * n, hy + uy * t + ux * n)

    dw = DOOR_W - 0.01
    for k, z in enumerate((DOOR_Z0 + 0.025, 0.72, DOOR_Z1 - 0.025)):
        x, y = door(dw / 2)
        box(f"door_rail_{k}", (dw, 0.014, 0.05), (x, y, z), iron, rot=(0, 0, -DOOR_OPEN), bevel=0)
    for k, t in enumerate((0.015, dw - 0.015)):
        x, y = door(t)
        box(f"door_stile_{k}", (0.03, 0.022, DOOR_Z1 - DOOR_Z0), (x, y, (DOOR_Z0 + DOOR_Z1) / 2), iron,
            rot=(0, 0, -DOOR_OPEN), bevel=0.005)
    nb = 3
    for i in range(nb):
        t = 0.015 + (dw - 0.03) * (i + 1) / (nb + 1)
        x, y = door(t, 0.012)
        cylinder(f"door_bar_{i}", BAR_R, DOOR_Z1 - DOOR_Z0 - 0.04, (x, y, DOOR_Z0 + 0.02), metal(), segments=8,
                 bevel=0)
        for k, z in enumerate((DOOR_Z0 + 0.025, 0.72, DOOR_Z1 - 0.025)):
            rx, ry = door(t, -0.01)
            cylinder(f"door_rivet_{i}_{k}", 0.011, 0.012, (rx, ry, z), worn, segments=6,
                     rot=(90, 0, -DOOR_OPEN), bevel=0)

    # Strap hinges: a knuckle on the frame post, a strap along the door's outer face.
    for k, z in enumerate((DOOR_Z0 + 0.16, DOOR_Z1 - 0.16)):
        cylinder(f"knuckle_{k}", 0.02, 0.12, (hx, hy + 0.008, z - 0.06), iron, segments=8, bevel=0.004)
        x, y = door(0.13, -0.016)
        box(f"hinge_strap_{k}", (0.24, 0.01, 0.05), (x, y, z), worn, rot=(0, 0, -DOOR_OPEN), bevel=0)

    # Latch on the free edge of the door, a staple on the frame and an open padlock hanging from it.
    x, y = door(dw - 0.05, -0.016)
    box("latch", (0.1, 0.012, 0.045), (x, y, 0.8), worn, rot=(0, 0, -DOOR_OPEN), bevel=0.003)
    sx = dx1 + 0.02
    box("staple_plate", (0.05, 0.02, 0.07), (sx, -half - 0.02, 0.8), iron, bevel=0.004)
    torus("staple", 0.022, 0.006, (sx, -half - 0.035, 0.8), iron, rot=(0, 90, 0), major=10, minor=6)
    torus("padlock_shackle", 0.03, 0.008, (sx + 0.012, -half - 0.05, 0.76), iron, rot=(90, 0, 20), major=12,
          minor=6)
    box("padlock", (0.08, 0.035, 0.09), (sx + 0.03, -half - 0.05, 0.69), rust, rot=(0, 20, 0), bevel=0.01)

    for o in bpy.context.scene.objects:
        o.location.y += BODY_Y
