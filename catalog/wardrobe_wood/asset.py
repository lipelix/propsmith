"""A tall plank wardrobe, its doors on -y: a framed carcass of corner stiles and rails with board sides, standing on a
plinth with short block feet and crowned with a moulded, overhanging cornice. Two doors of vertical boards with
battens, each hung on two long iron strap hinges, meet in the middle under an iron hasp; each has a ring pull."""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall size: about 1.2 m wide (x), 0.6 m deep (y), 2 m high. The cornice gives the widest outline.
W, D, H = 1.14, 0.54, 2.0  # carcass under the cornice
PLINTH_H = 0.1
FOOT_H = 0.03
CORNICE_H = 0.1
CORNICE_OVER = 0.03  # cornice overhang on the front and sides
STILE = 0.06  # corner stiles, square
RAIL = 0.08  # front rails above and below the doors
BOARD_T = 0.022
DOOR_T = 0.03
DOOR_BOARDS = 4  # vertical boards per door
FRONT = -D / 2
BODY_Z0 = FOOT_H + PLINTH_H  # carcass bottom
BODY_Z1 = H - CORNICE_H  # carcass top
DOOR_Z0 = BODY_Z0 + RAIL
DOOR_Z1 = BODY_Z1 - RAIL
DOOR_W = (W - 2 * STILE) / 2

WOOD = (0.19, 0.11, 0.058)  # linear RGB
WOOD_OLD = (0.145, 0.085, 0.048)
WOOD_DARK = (0.11, 0.065, 0.038)
IRON = (0.05, 0.048, 0.046)


@prop
def wardrobe_wood():
    rnd = random.Random(1202)
    wood = material("wardrobe_wood_wood", WOOD, vary=0.25, scale=12)
    old = material("wardrobe_wood_wood_old", WOOD_OLD, vary=0.3, scale=10)
    dark = material("wardrobe_wood_wood_dark", WOOD_DARK, vary=0.25, scale=12)
    iron = material("wardrobe_wood_iron", IRON, rough=0.55, vary=0.25, scale=14, metal=0.6)

    # Feet and plinth.
    for i, (sx, sy) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        box(f"foot_{i}", (0.1, 0.1, FOOT_H + 0.01), (sx * (W / 2 - 0.05), sy * (D / 2 - 0.05), (FOOT_H + 0.01) / 2),
            dark, bevel=0.008)
    box("plinth", (W + 0.02, D + 0.02, PLINTH_H), (0, 0, FOOT_H + PLINTH_H / 2), old, bevel=0.012)

    # The carcass: a box with board sides, a back and a top, framed by corner stiles.
    body_h = BODY_Z1 - BODY_Z0
    mid = (BODY_Z0 + BODY_Z1) / 2
    box("back", (W - 0.02, BOARD_T, body_h), (0, D / 2 - BOARD_T / 2 - 0.005, mid), old, bevel=0.005)
    for s in (-1, 1):
        # Side boards between the stiles, slightly irregular.
        boards = 3
        bw = (D - 2 * STILE) / boards
        for k in range(boards):
            y = -D / 2 + STILE + bw * (k + 0.5)
            box(f"side_{s}_{k}", (BOARD_T, bw - 0.003, body_h), (s * (W / 2 - BOARD_T / 2 - 0.006), y, mid),
                wood if (k + s) % 2 else old, rot=(rnd.uniform(-0.2, 0.2), 0, 0), bevel=0.004)
        for e in (-1, 1):
            box(f"stile_{s}_{e}", (STILE, STILE, body_h + 0.01), (s * (W / 2 - STILE / 2), e * (D / 2 - STILE / 2),
                                                                mid), wood, bevel=0.01)
        box(f"side_rail_{s}", (STILE * 0.7, D - 2 * STILE, 0.07), (s * (W / 2 - STILE * 0.35), 0, BODY_Z0 + 0.06),
            wood, bevel=0.008)
    box("rail_bottom", (W - 2 * STILE, STILE, RAIL), (0, FRONT + STILE / 2, BODY_Z0 + RAIL / 2), wood, bevel=0.01)
    box("rail_top", (W - 2 * STILE, STILE, RAIL), (0, FRONT + STILE / 2, BODY_Z1 - RAIL / 2), wood, bevel=0.01)
    box("muntin", (0.05, 0.03, DOOR_Z1 - DOOR_Z0), (0, FRONT + 0.03, (DOOR_Z0 + DOOR_Z1) / 2), dark, bevel=0.006)

    # The cornice: a frieze board, a projecting moulding and a cap.
    cz = BODY_Z1
    box("frieze", (W + 0.01, D + 0.01, 0.04), (0, 0, cz + 0.02), wood, bevel=0.008)
    box("cove", (W + CORNICE_OVER, D + CORNICE_OVER, 0.03), (0, CORNICE_OVER / 4, cz + 0.055), old, bevel=0.012)
    box("cap", (W + 2 * CORNICE_OVER, D + CORNICE_OVER + 0.01, 0.03), (0, CORNICE_OVER / 2 - 0.005, H - 0.015), wood,
        bevel=0.012)

    # The doors: vertical boards with top and bottom battens on the face, set in the front opening.
    door_h = DOOR_Z1 - DOOR_Z0 - 0.01
    dz = (DOOR_Z0 + DOOR_Z1) / 2
    door_y = FRONT + DOOR_T / 2 + 0.004
    for side, s in enumerate((-1, 1)):
        x0 = s * 0.025  # the meeting edge, beside the muntin
        bw = (DOOR_W - 0.03) / DOOR_BOARDS
        for k in range(DOOR_BOARDS):
            x = x0 + s * bw * (k + 0.5)
            box(f"door_{side}_board_{k}", (bw - 0.004, DOOR_T, door_h + rnd.uniform(-0.004, 0.0)),
                (x, door_y + rnd.uniform(-0.002, 0.002), dz), rnd.choice([wood, wood, old]),
                rot=(0, rnd.uniform(-0.3, 0.3), 0), bevel=0.006)
        cx = x0 + s * (DOOR_W - 0.03) / 2
        for k, z in enumerate((DOOR_Z0 + 0.18, DOOR_Z1 - 0.18)):
            box(f"door_{side}_batten_{k}", (DOOR_W - 0.06, 0.02, 0.09), (cx, door_y - DOOR_T / 2 - 0.01, z), old,
                bevel=0.006)
            # A long iron strap hinge over each batten, from the outer edge, with a rounded tip and nail heads.
            strap_l = DOOR_W * 0.7
            sx = s * (W / 2 - STILE) - s * strap_l / 2 + s * 0.03
            hy = door_y - DOOR_T / 2 - 0.024
            box(f"hinge_{side}_{k}", (strap_l, 0.006, 0.04), (sx, hy, z), iron, bevel=0.002)
            cylinder(f"hinge_{side}_{k}_tip", 0.026, 0.006, (sx - s * strap_l / 2, hy + 0.003, z), iron,
                     rot=(90, 0, 0), segments=10, bevel=0.002)
            cylinder(f"hinge_{side}_{k}_knuckle", 0.012, 0.07, (s * (W / 2 - STILE + 0.004), FRONT - 0.002, z - 0.035),
                     iron, segments=8, bevel=0.002)
            for n in range(4):
                nx = sx + s * strap_l / 2 - s * (0.04 + n * strap_l / 4.2)
                cylinder(f"hinge_{side}_{k}_nail_{n}", 0.006, 0.006, (nx, hy - 0.003, z), iron, rot=(90, 0, 0),
                         segments=6, bevel=0)
        # A ring pull on a plate near the meeting edge.
        py = door_y - DOOR_T / 2
        box(f"pull_plate_{side}", (0.04, 0.005, 0.06), (s * 0.07, py - 0.0025, dz), iron, bevel=0.002)
        torus(f"pull_ring_{side}", 0.026, 0.005, (s * 0.07, py - 0.01, dz - 0.03), iron, rot=(90, 0, 0), major=14,
              minor=6)

    # The hasp across the meeting edge, with a staple.
    hy = door_y - DOOR_T / 2
    box("hasp", (0.11, 0.006, 0.03), (0.015, hy - 0.004, dz + 0.12), iron, bevel=0.002)
    torus("staple", 0.012, 0.004, (-0.04, hy - 0.01, dz + 0.12), iron, rot=(90, 0, 0), major=10, minor=5)
