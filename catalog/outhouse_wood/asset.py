"""A plank privy about 1.1 × 1.1 × 2.2 m: a small shed of weathered vertical boards on four corner posts and two sill
beams, under a lean-to roof of boards that falls from the front to the back. The door on the front (-y) is a ledged and
braced plank door on two iron strap hinges with a wooden turn-button, and a crescent moon cut through it near the top
(plan 3, item 17)."""
import math
import random

import bmesh
import bpy

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall dimensions (metres): the shed's walls, then the roof that overhangs them.
W, D = 0.96, 0.86  # outside of the posts, x and y
SILL_H = 0.1  # sill beams on the ground; the floor sits on them
FRONT_H, BACK_H = 2.03, 1.8  # top of the walls at the front and back (the roof falls to the back)
POST = 0.08  # square corner posts
BOARD_T = 0.022  # wall boards
BOARD_W = (0.13, 0.17)
ROOF_T = 0.03
ROOF_OVER = (0.13, 0.08, 0.06)  # roof overhang at the front, the back and the sides
DOOR_W, DOOR_H = 0.6, 1.72
DOOR_T = 0.028
MOON_Z = 1.52  # height of the crescent's centre above the floor
MOON_R, MOON_R_IN, MOON_OFF = 0.115, 0.1, 0.065  # outer circle, inner circle and its offset
ARC_STEP = 12  # degrees

WOOD = (0.24, 0.2, 0.15)  # sun-greyed boards
WOOD_OLD = (0.18, 0.145, 0.105)
FRAME = (0.15, 0.105, 0.07)
ROOF = (0.17, 0.145, 0.11)
MOSS = (0.045, 0.065, 0.025)
IRON = (0.05, 0.047, 0.044)
DARK = (0.025, 0.021, 0.017)  # the shadowed inside, seen through the crescent

SLOPE = (FRONT_H - BACK_H) / D  # wall top falls this much per metre towards +y
PITCH = math.degrees(math.atan(SLOPE))


def _wall_top(y):
    return FRONT_H - (y + D / 2) * SLOPE


def _cut(obj, cutter):
    """Subtracts `cutter` from `obj` and bakes the result (bevel included) into `obj`'s mesh."""
    mod = obj.modifiers.new("cut", "BOOLEAN")
    mod.operation, mod.solver, mod.object = "DIFFERENCE", "EXACT", cutter
    mod.material_mode = "TRANSFER"
    bpy.context.view_layer.update()
    ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = bpy.data.meshes.new_from_object(ev)
    obj.modifiers.clear()
    obj.data = mesh


def _crescent(name, cx, cz, y0, y1):
    """A crescent-shaped prism in the x-z plane between y0 and y1: the outer circle minus an offset inner one."""
    d, r1, r2 = MOON_OFF, MOON_R, MOON_R_IN
    ix = (d * d + r1 * r1 - r2 * r2) / (2 * d)
    iz = math.sqrt(r1 * r1 - ix * ix)
    a0 = math.degrees(math.atan2(iz, ix))
    b0 = math.degrees(math.atan2(iz, ix - d))
    pts = []
    n = max(2, round((360 - 2 * a0) / ARC_STEP))
    for k in range(n + 1):
        a = math.radians(a0 + (360 - 2 * a0) * k / n)
        pts.append((r1 * math.cos(a), r1 * math.sin(a)))
    n = max(2, round((2 * b0 - 0) / ARC_STEP))
    for k in range(1, n):
        a = math.radians(360 - b0 - (360 - 2 * b0) * k / n)
        pts.append((d + r2 * math.cos(a), r2 * math.sin(a)))
    bm = bmesh.new()
    front = [bm.verts.new((x, y0, z)) for x, z in pts]
    back = [bm.verts.new((x, y1, z)) for x, z in pts]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((front[i], back[i], back[j], front[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (cx, 0, cz)
    obj.rotation_euler = (0, math.radians(-20), 0)  # horns turned up a little
    return obj


def _boards(rnd, name, x0, x1, top, y, z0, mats, along="x"):
    """Vertical boards side by side from x0 to x1 (or y0 to y1 when along="y"), from z0 up to top(u), one plank thick at
    `y` (or x). Each board's top follows the roof line under it."""
    u = x0
    k = 0
    while u < x1 - 0.02:
        w = min(rnd.uniform(*BOARD_W), x1 - u)
        if x1 - (u + w) < 0.05:
            w = x1 - u
        c = u + w / 2
        h = min(top(u), top(u + w)) - z0 - rnd.uniform(0.0, 0.015)
        size = (w - 0.006, BOARD_T, h) if along == "x" else (BOARD_T, w - 0.006, h)
        at = (c, y, z0 + h / 2) if along == "x" else (y, c, z0 + h / 2)
        box(f"{name}_{k}", size, at, rnd.choice(mats), rot=(0, 0, rnd.uniform(-0.4, 0.4)), bevel=0.006)
        u += w
        k += 1


@prop
def outhouse_wood():
    rnd = random.Random(1717)
    wood = material("outhouse_wood_boards", WOOD, vary=0.3, scale=12)
    wood_old = material("outhouse_wood_boards_old", WOOD_OLD, vary=0.32, scale=12)
    frame = material("outhouse_wood_frame", FRAME, vary=0.28, scale=10)
    roof = material("outhouse_wood_roof", ROOF, vary=0.32, scale=10)
    moss = material("outhouse_wood_moss", MOSS, rough=0.95, vary=0.35, scale=18)
    iron = material("outhouse_wood_iron", IRON, rough=0.55, vary=0.3, scale=20, metal=0.6)
    mats = (wood, wood, wood_old)

    hx, hy = W / 2, D / 2
    inner_x, inner_y = hx - POST, hy - POST

    # Two sill beams along x on the ground, a floor on them, and four corner posts up to the roof line.
    for s in (-1, 1):
        box(f"sill_{s}", (W + 0.06, POST + 0.02, SILL_H), (0, s * (hy - POST / 2), SILL_H / 2), frame, bevel=0.012)
    box("floor", (W - 0.02, D - 0.02, 0.03), (0, 0, SILL_H + 0.015), wood_old, bevel=0.004)
    for sx in (-1, 1):
        for sy in (-1, 1):
            y = sy * (hy - POST / 2)
            h = _wall_top(y + sy * POST / 2) - SILL_H
            box(f"post_{sx}_{sy}", (POST, POST, h), (sx * (hx - POST / 2), y, SILL_H + h / 2), frame,
                rot=(0, 0, rnd.uniform(-0.8, 0.8)), bevel=0.01)
    # Top plates under the roof on the front and back.
    for sy in (-1, 1):
        y = sy * (hy - POST / 2)
        z = _wall_top(y) - 0.04
        box(f"plate_{sy}", (W, POST, 0.07), (0, y, z), frame, bevel=0.01)

    # Side walls (x = ±) and back wall (+y): boards on the outside of the frame.
    for sx in (-1, 1):
        _boards(rnd, f"side_{sx}", -hy, hy, _wall_top, sx * (hx + BOARD_T / 2), 0.02, mats, along="y")
    _boards(rnd, "back", -hx, hx, lambda u: BACK_H, hy + BOARD_T / 2, 0.02, mats)

    # Front wall: a narrow board each side of the door and a header board above it.
    y_front = -hy - BOARD_T / 2
    door_x0, door_x1 = -DOOR_W / 2, DOOR_W / 2
    door_z0 = SILL_H + 0.02
    door_top = door_z0 + DOOR_H
    _boards(rnd, "front_l", -hx, door_x0 - 0.02, lambda u: FRONT_H, y_front, 0.02, mats)
    _boards(rnd, "front_r", door_x1 + 0.02, hx, lambda u: FRONT_H, y_front, 0.02, mats)
    box("header", (W, BOARD_T, FRONT_H - door_top - 0.03), (0, y_front, (FRONT_H + door_top + 0.03) / 2), wood_old,
        bevel=0.006)
    # Door frame: two jambs and a lintel.
    for s in (-1, 1):
        box(f"jamb_{s}", (0.05, 0.04, DOOR_H + 0.04), (s * (DOOR_W / 2 + 0.03), -hy - 0.02, door_z0 + DOOR_H / 2 + 0.01),
            frame, bevel=0.008)
    box("lintel", (DOOR_W + 0.12, 0.045, 0.07), (0, -hy - 0.022, door_top - 0.005), frame, bevel=0.008)

    # The door: four boards, two ledges and a brace on the outside, with the crescent cut through the boards.
    y_door = -hy - 0.045 - DOOR_T / 2
    moon = _crescent("moon_cutter", 0.0, door_z0 + MOON_Z, y_door - 0.1, y_door + 0.1)
    n = 4
    bw = DOOR_W / n
    for k in range(n):
        x = door_x0 + bw * (k + 0.5)
        board = box(f"door_{k}", (bw - 0.008, DOOR_T, DOOR_H - rnd.uniform(0, 0.02)),
                    (x, y_door, door_z0 + DOOR_H / 2), wood if k % 2 else wood_old, bevel=0.006)
        if abs(x) < bw / 2 + MOON_R + 0.02:
            _cut(board, moon)
    bpy.data.objects.remove(moon)
    dark = material("outhouse_wood_inside", DARK, rough=1.0, vary=0.1, scale=8, crevice=0.2)
    box("inside", (0.32, 0.02, 0.3), (0, y_door + DOOR_T / 2 + 0.04, door_z0 + MOON_Z), dark, bevel=0)
    y_ledge = y_door - DOOR_T / 2 - 0.012
    ledges = (door_z0 + 0.28, door_z0 + 1.28)
    for k, z in enumerate(ledges):
        box(f"ledge_{k}", (DOOR_W - 0.04, 0.024, 0.1), (0, y_ledge, z), frame, bevel=0.006)
    run = DOOR_W - 0.14
    rise = ledges[1] - ledges[0] - 0.1
    box("brace", (math.hypot(run, rise), 0.022, 0.09), (0, y_ledge + 0.001, (ledges[0] + ledges[1]) / 2), frame,
        rot=(0, -math.degrees(math.atan2(rise, run)), 0), bevel=0.006)
    # Strap hinges on the left over the ledges, and a turn-button and a pull on the right.
    for k, z in enumerate(ledges):
        box(f"hinge_{k}", (0.3, 0.008, 0.035), (door_x0 + 0.1, y_ledge - 0.016, z), iron, bevel=0.002)
        cylinder(f"hinge_pin_{k}", 0.012, 0.06, (door_x0 - 0.035, y_ledge - 0.008, z - 0.03), iron, segments=8,
                 bevel=0.002)
    box("button", (0.03, 0.025, 0.11), (door_x1 + 0.03, -hy - 0.06, door_z0 + 1.0), frame,
        rot=(0, 25, 0), bevel=0.004)
    cylinder("pull", 0.016, 0.05, (door_x1 - 0.07, y_ledge - 0.012, door_z0 + 0.95), frame, segments=8,
             rot=(90, 0, 0), bevel=0.004)

    # The lean roof: boards running front to back, laid across two rafters on the side plates, with a little moss.
    y0, y1 = -hy - ROOF_OVER[0], hy + ROOF_OVER[1]
    length = (y1 - y0) / math.cos(math.radians(PITCH))
    for s in (-1, 1):
        x = s * (hx - POST / 2)
        box(f"rafter_{s}", (POST - 0.01, length - 0.04, 0.06), (x, (y0 + y1) / 2, _wall_top((y0 + y1) / 2) + 0.03),
            frame, rot=(-PITCH, 0, 0), bevel=0.01)
    x0, x1 = -hx - ROOF_OVER[2], hx + ROOF_OVER[2]
    x = x0
    k = 0
    z_mid = _wall_top((y0 + y1) / 2) + 0.06 + ROOF_T / 2
    while x < x1 - 0.03:
        w = min(rnd.uniform(0.16, 0.22), x1 - x)
        if x1 - (x + w) < 0.06:
            w = x1 - x
        box(f"roof_{k}", (w - 0.008, length + rnd.uniform(-0.02, 0.01), ROOF_T),
            (x + w / 2, (y0 + y1) / 2 + rnd.uniform(-0.01, 0.01), z_mid + rnd.uniform(-0.003, 0.003)),
            roof if rnd.random() < 0.7 else wood_old, rot=(-PITCH, rnd.uniform(-0.5, 0.5), rnd.uniform(-0.6, 0.6)),
            bevel=0.007)
        x += w
        k += 1
    for k, (mx, my, r) in enumerate(((-0.3, 0.3, 0.13), (0.22, 0.36, 0.15), (0.4, 0.08, 0.1), (-0.06, 0.42, 0.09))):
        z = z_mid - my * math.tan(math.radians(PITCH)) + ROOF_T / 2
        blob(f"moss_{k}", r, (mx, my, z), moss, squash=(1.2, 0.9, 0.07), subdiv=1, seed=40 + k, jitter=0.25)
