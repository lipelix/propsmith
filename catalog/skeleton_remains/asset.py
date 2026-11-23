"""The remains of an adventurer about 1.3 × 0.9 × 0.65 m: a human skeleton slumped against a small rock, sitting on
the ground with its back to the rock, its skull drooping on its chest, one leg stretched out and the other bent up,
one arm hanging to the ground and the other across its lap. A rusted sword lies by its hanging hand and a torn leather
pack spilling a rolled cloth lies at its other side.

It is built facing -y and then turned to face +x, so the rock is at the -x end, the legs reach toward +x (the long
side) and the sword lies on the -y side.

The bones (skull, spine, ribs, pelvis, limbs) are built from blobs and rods as in `bones_pile`, in its yellowed bone
palette."""
import math
import random

import bpy
from mathutils import Euler, Matrix, Vector

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder

# Overall dimensions (metres): about 1.3 wide (x) × 0.9 deep (y) × 0.65 high.
# Built facing -y: the build frame's y becomes the asset's x.
ROCK_AT, ROCK_R, ROCK_H = (0.0, 0.25), 0.24, 0.5  # the rock behind the skeleton
PELVIS = Vector((0.0, -0.08, 0.1))  # the pelvis centre, sitting on the ground
SHOULDER = Vector((0.02, 0.07, 0.46))  # the top of the spine, against the rock
SKULL_R = 0.085
SHAFT_R, KNOB_R = 0.014, 0.028
RIB_R = 0.006
SWORD_LEN = 0.82

BONE = (0.44, 0.37, 0.23)  # linear RGB, yellowed bone (as bones_pile)
BONE_OLD = (0.34, 0.27, 0.16)
HOLLOW = (0.07, 0.05, 0.035)
ROCK = (0.2, 0.19, 0.17)
ROCK_DARK = (0.12, 0.115, 0.105)
RUST = (0.22, 0.09, 0.04)
STEEL = (0.17, 0.15, 0.13)  # a little bright steel under the rust
GRIP = (0.12, 0.07, 0.04)
LEATHER = (0.2, 0.11, 0.05)
LEATHER_DARK = (0.12, 0.065, 0.03)
CLOTH = (0.27, 0.22, 0.15)


def _group(objs, at, yaw=0.0, pitch=0.0, roll=0.0):
    """Move parts built in a local frame: roll about x, pitch (nose up) about -y, yaw about z, then to `at`."""
    g = Matrix.Translation(Vector(at)) @ Euler(
        (math.radians(roll), math.radians(-pitch), math.radians(yaw))).to_matrix().to_4x4()
    for o in objs:
        o.matrix_basis = g @ o.matrix_basis
    return objs


def _rod(name, p0, p1, r, mat, segments=8, bevel=0.0, r_top=None):
    """A cylinder from point `p0` to point `p1`."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    yaw = math.degrees(math.atan2(d.y, d.x))
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, d.z / d.length))))
    return cylinder(name, r, d.length, p0, mat, r_top=r_top, segments=segments, rot=(0, 90 - pitch, yaw), bevel=bevel)


def _bone(name, p0, p1, mat, scale=1.0, seed=0):
    """A long bone between two joint centres: a shaft and a knobbly end at each."""
    p0, p1 = Vector(p0), Vector(p1)
    _rod(f"{name}_shaft", p0, p1, SHAFT_R * scale, mat, segments=8, bevel=0.003, r_top=SHAFT_R * scale * 0.9)
    yaw = math.degrees(math.atan2((p1 - p0).y, (p1 - p0).x))
    for i, p in enumerate((p0, p1)):
        o = blob(f"{name}_end{i}", KNOB_R * scale, p, mat, squash=(0.8, 1.15, 0.85), subdiv=1, seed=seed + i,
                 jitter=0.1)
        o.rotation_euler = (0, 0, math.radians(yaw))


def _skull(name, at, yaw, mat, hollow, pitch=0.0, roll=0.0, seed=0):
    """A skull facing local -y, its lowest point near local z = 0 (as bones_pile)."""
    r = SKULL_R
    parts = [
        blob(f"{name}_cranium", r, (0, 0.012, r * 0.98), mat, squash=(0.92, 1.2, 0.95), subdiv=2, seed=seed,
             jitter=0.035),
        blob(f"{name}_face", r * 0.55, (0, -0.06, r * 0.62), mat, squash=(1.2, 0.85, 1.0), subdiv=2, seed=seed + 1,
             jitter=0.05),
        blob(f"{name}_brow", r * 0.4, (0, -0.07, r * 1.05), mat, squash=(1.8, 0.55, 0.55), subdiv=1, seed=seed + 2,
             jitter=0.04),
    ]
    for s in (-1, 1):
        parts.append(blob(f"{name}_cheek{s}", r * 0.28, (s * 0.045, -0.055, r * 0.62), mat, squash=(0.9, 1.3, 0.8),
                          subdiv=1, seed=seed + 3 + s, jitter=0.05))
        parts.append(blob(f"{name}_eye{s}", r * 0.3, (s * 0.03, -0.094, r * 0.84), hollow, squash=(1.0, 0.5, 0.9),
                          subdiv=1, seed=seed + 6 + s, jitter=0.05))
    parts.append(blob(f"{name}_nose", r * 0.16, (0, -0.106, r * 0.6), hollow, squash=(0.8, 0.5, 1.3), subdiv=1,
                      seed=seed + 9, jitter=0.05))
    parts.append(box(f"{name}_teeth", (0.042, 0.014, 0.014), (0, -0.092, r * 0.3), mat, bevel=0.003))
    for o in parts:
        if "teeth" not in o.name:
            o.rotation_euler = (0, 0, 0)
    return _group(parts, at, yaw, pitch, roll)


def _rock(name, r, h, xy, mat, seed, stretch=1.0, subdiv=3):
    """A boulder `r` half-wide and `h` high with its base cut flat, standing on the ground."""
    flat = 0.12
    rz = h / (2 * (1 - flat / 2))
    obj = blob(name, r, (xy[0], xy[1], 0), mat, squash=(stretch, 1 / stretch ** 0.5, rz / r), subdiv=subdiv,
               seed=seed, jitter=0.16)
    verts = obj.data.vertices
    low = min(v.co.z for v in verts)
    cut = low + flat * (max(v.co.z for v in verts) - low)
    for v in verts:
        v.co.z = max(v.co.z, cut)
    obj.location.z = -cut
    return obj


@prop
def skeleton_remains():
    rnd = random.Random(23)
    bone = material("skeleton_remains_bone", BONE, rough=0.7, vary=0.22, scale=25, crevice=0.6)
    old = material("skeleton_remains_bone_old", BONE_OLD, rough=0.75, vary=0.25, scale=25, crevice=0.6)
    hollow = material("skeleton_remains_hollow", HOLLOW, rough=0.95, vary=0.2, scale=20, crevice=0.3)
    rock = material("skeleton_remains_rock", ROCK, rough=0.85, vary=0.3, scale=8, crevice=0.75)
    rock_dark = material("skeleton_remains_rock_dark", ROCK_DARK, rough=0.85, vary=0.3, scale=8, crevice=0.75)
    rust = material("skeleton_remains_rust", RUST, rough=0.8, vary=0.4, scale=25, crevice=0.6, metal=0.3)
    steel = material("skeleton_remains_steel", STEEL, rough=0.5, vary=0.35, scale=20, metal=0.7)
    grip = material("skeleton_remains_grip", GRIP, rough=0.85, vary=0.3, scale=40)
    leather = material("skeleton_remains_leather", LEATHER, rough=0.8, vary=0.3, scale=15, crevice=0.65)
    leather_dark = material("skeleton_remains_leather_dark", LEATHER_DARK, rough=0.85, vary=0.3, scale=15)
    cloth = material("skeleton_remains_cloth", CLOTH, rough=0.95, vary=0.3, scale=25, crevice=0.6)

    # The rock it leans on, and a smaller stone beside it.
    rocks = [_rock("rock", ROCK_R, ROCK_H, ROCK_AT, rock, seed=81, stretch=1.45),
             _rock("rock_side", 0.12, 0.2, (0.3, 0.3), rock_dark, seed=82, stretch=1.2, subdiv=2)]

    # Pelvis: a wide flattened bowl of bone on the ground.
    blob("pelvis", 0.1, PELVIS, bone, squash=(1.35, 0.8, 0.7), subdiv=2, seed=90, jitter=0.1)
    for s in (-1, 1):
        blob(f"hip{s}", 0.055, PELVIS + Vector((s * 0.1, 0.01, 0.03)), bone, squash=(1.0, 0.6, 1.1), subdiv=1,
             seed=91 + s, jitter=0.1)

    # The spine: a curved chain of vertebrae from the pelvis up the rock face to the shoulders.
    back = SHOULDER - PELVIS
    verts = 9
    for i in range(verts + 1):
        t = (i + 0.5) / (verts + 1)
        p = PELVIS + back * t + Vector((0, -0.04 * math.sin(math.pi * t), 0.03))
        blob(f"vertebra{i}", 0.022, p, old if i % 3 == 0 else bone, squash=(1.3, 1.0, 0.7), subdiv=1, seed=100 + i,
             jitter=0.1)

    # The rib cage: ribs curving forward (-y) round the spine, slumped with it.
    tilt = math.degrees(math.atan2(back.y, back.z))
    for k in range(6):
        t = 0.45 + 0.08 * k
        p = PELVIS + back * t + Vector((0, -0.03, 0.03))
        w = 0.09 + 0.025 * math.sin(math.pi * (k + 1) / 7)
        for s in (-1, 1):
            pts = [Vector((s * 0.01, 0.0, 0)), Vector((s * w, -0.03, -0.01)), Vector((s * w * 0.95, -0.1, -0.03)),
                   Vector((s * w * 0.4, -0.15, -0.04))]
            g = Matrix.Translation(p) @ Matrix.Rotation(math.radians(tilt), 4, "X")
            for j in range(len(pts) - 1):
                if k > 3 and j == 2 and s > 0:
                    break  # a few lower ribs broken short
                a, b = g @ pts[j], g @ pts[j + 1]
                e = (b - a).normalized() * RIB_R
                _rod(f"rib{k}_{s}_{j}", a - e, b + e, RIB_R, bone, segments=6)
    _rod("sternum", PELVIS + back * 0.58 + Vector((0, -0.17, 0.0)), PELVIS + back * 0.85 + Vector((0, -0.17, 0.0)),
         0.012, old, segments=6)

    # Collarbones and shoulder blades.
    sh = {s: SHOULDER + Vector((s * 0.17, -0.04, -0.02)) for s in (-1, 1)}
    for s in (-1, 1):
        _rod(f"collar{s}", SHOULDER + Vector((0, -0.06, 0)), sh[s], 0.01, bone, segments=6)
        blob(f"blade{s}", 0.06, SHOULDER + Vector((s * 0.1, 0.03, -0.07)), old, squash=(1.0, 0.35, 1.2), subdiv=1,
             seed=120 + s, jitter=0.12)

    # The skull: drooped forward and to one side, chin on the chest.
    _skull("skull", SHOULDER + Vector((-0.04, -0.08, 0.02)), -12, bone, hollow, pitch=-28, roll=-18, seed=130)
    _rod("neck", SHOULDER + Vector((0, 0, -0.02)), SHOULDER + Vector((-0.03, -0.05, 0.06)), 0.018, bone, segments=6)

    # Legs: the right one (+x) stretched out to the front, the left one bent up at the knee.
    hip_r, hip_l = PELVIS + Vector((0.1, -0.04, -0.02)), PELVIS + Vector((-0.1, -0.04, -0.02))
    knee_r = Vector((0.16, -0.44, KNOB_R))
    foot_r = Vector((0.24, -0.72, KNOB_R * 0.8))
    _bone("thigh_r", hip_r, knee_r, bone, seed=140)
    _bone("shin_r", knee_r, foot_r, old, scale=0.9, seed=142)
    knee_l = Vector((-0.18, -0.36, 0.3))
    foot_l = Vector((-0.14, -0.6, KNOB_R * 0.8))
    _bone("thigh_l", hip_l, knee_l, bone, seed=144)
    _bone("shin_l", knee_l, foot_l, bone, scale=0.9, seed=146)
    for name, f, yaw in (("foot_r", foot_r, -30), ("foot_l", foot_l, -75)):
        for j in range(4):
            a = math.radians(yaw + rnd.uniform(-6, 6)) + (j - 1.5) * 0.12
            p = f + Vector((0, 0, -KNOB_R * 0.5))
            _rod(f"{name}_{j}", p, p + Vector((0.1 * math.cos(a), 0.1 * math.sin(a), 0.0)), 0.007, old, segments=6)

    # Arms: the left hangs to the ground beside the sword, the right lies across the lap.
    elbow_l = sh[-1] + Vector((-0.1, -0.04, -0.24))
    hand_l = Vector((-0.3, -0.2, 0.02))
    _bone("upper_arm_l", sh[-1], elbow_l, bone, scale=0.8, seed=150)
    _bone("forearm_l", elbow_l, hand_l, old, scale=0.65, seed=152)
    elbow_r = sh[1] + Vector((0.05, -0.12, -0.24))
    hand_r = Vector((-0.04, -0.3, 0.17))
    _bone("upper_arm_r", sh[1], elbow_r, bone, scale=0.8, seed=154)
    _bone("forearm_r", elbow_r, hand_r, bone, scale=0.65, seed=156)
    for name, h, yaw in (("hand_l", hand_l, -120), ("hand_r", hand_r, 200)):
        for j in range(4):
            a = math.radians(yaw) + (j - 1.5) * 0.18
            _rod(f"{name}_{j}", h, h + Vector((0.08 * math.cos(a), 0.08 * math.sin(a), -0.01)), 0.005, old,
                 segments=6)

    # The rusted sword on the ground by the hanging hand, blade toward the feet.
    hilt = Vector((-0.36, 0.02, 0.0))
    d = Vector((0.09, -1, 0)).normalized()
    yaw = math.degrees(math.atan2(d.y, d.x))
    blade_len = SWORD_LEN * 0.8
    blade = box("sword_blade", (blade_len, 0.045, 0.008), hilt + d * (0.12 + blade_len / 2) + Vector((0, 0, 0.012)),
                rust, rot=(0, 0, yaw), bevel=0.003)
    for v in blade.data.vertices:  # taper to a point
        if v.co.x > 0:
            v.co.y *= 0.25
    box("sword_fuller", (blade_len * 0.7, 0.012, 0.009), hilt + d * (0.15 + blade_len * 0.35) + Vector((0, 0, 0.013)),
        steel, rot=(0, 0, yaw), bevel=0.002)
    box("sword_guard", (0.025, 0.19, 0.025), hilt + d * 0.11 + Vector((0, 0, 0.016)), rust, rot=(0, 0, yaw),
        bevel=0.005)
    _rod("sword_grip", hilt + d * 0.1 + Vector((0, 0, 0.016)), hilt + Vector((0, 0, 0.016)), 0.015, grip, segments=8)
    blob("sword_pommel", 0.024, hilt + Vector((0, 0, 0.022)), rust, subdiv=1, seed=160, jitter=0.08)

    # The torn pack at its other side: a slumped leather bag with its flap open, a rolled cloth spilling out.
    pack = Vector((0.3, -0.12, 0.0))
    blob("pack_body", 0.14, pack + Vector((0, 0, 0.12)), leather, squash=(0.75, 1.1, 0.85), subdiv=2, seed=170,
         jitter=0.14)
    flap = box("pack_flap", (0.2, 0.15, 0.012), pack + Vector((0.0, -0.19, 0.05)), leather_dark, rot=(38, 0, 4),
               bevel=0.004)
    for v in flap.data.vertices:  # a torn, ragged edge
        if v.co.y < 0:
            v.co.x *= 0.7 + 0.3 * rnd.random()
    for s in (-1, 1):
        _rod(f"pack_strap{s}", pack + Vector((0.08, s * 0.07, 0.22)), pack + Vector((0.12, s * 0.09, 0.02)), 0.012,
             leather_dark, segments=6)
    cylinder("pack_roll", 0.05, 0.26, pack + Vector((-0.02, -0.3, 0.05)), cloth, segments=12, rot=(0, 90, 70),
             bevel=0.006).location = pack + Vector((0.0, -0.3, 0.05))
    blob("pack_spill", 0.06, pack + Vector((0.04, -0.42, 0.02)), cloth, squash=(1.3, 1.0, 0.35), subdiv=1, seed=171,
         jitter=0.2)

    # Turn it all to face +x, then rest every loose part on the ground.
    turn = Matrix.Translation((-0.15, 0, 0)) @ Matrix.Rotation(math.radians(90), 4, "Z")  # centred on x
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            o.matrix_basis = turn @ o.matrix_basis
    bpy.context.view_layer.update()
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and o not in rocks:
            low = min((o.matrix_world @ v.co).z for v in o.data.vertices)
            if low < 0:
                o.location.z -= low
