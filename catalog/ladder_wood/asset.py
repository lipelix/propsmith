"""A pole ladder leaning as against a wall: two peeled, slightly crooked poles that narrow towards the top, with ten
round rungs set through them and lashed with rope at every joint. Its feet stand on the ground at the -y side and its
top rests at the +y side, about 3 m up (plan 3, item 17)."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import cylinder

# Overall dimensions (metres): the ladder rises along +y and +z, its rails spread along x.
TOP_Z = 2.97  # top of the rails
FOOT_Y, TOP_Y = -0.42, 0.42  # where the rails stand and where they rest against the wall
HALF_FOOT, HALF_TOP = 0.26, 0.2  # half the rail spread at the foot and at the top
RAIL_R, RAIL_R_TOP = 0.045, 0.036  # tapering poles
RUNGS = 10
RUNG_R = 0.022
RUNG_OUT = 0.035  # rung ends showing outside the rails
FIRST_RUNG = 0.3  # height of the lowest rung
LASH_R, LASH_H = 0.012, 0.06  # rope bands round the rails at each rung

WOOD = (0.22, 0.165, 0.105)  # peeled, sun-greyed poles
WOOD_OLD = (0.16, 0.12, 0.08)
RUNG = (0.25, 0.19, 0.12)
ROPE = (0.32, 0.25, 0.15)


def _segment(name, p, q, r, mat, r_top=None, segments=10, bevel=0.006):
    """A cylinder from point p to point q."""
    d = [q[i] - p[i] for i in range(3)]
    length = math.sqrt(sum(c * c for c in d))
    tilt = math.degrees(math.acos(max(-1.0, min(1.0, d[2] / length))))
    yaw = math.degrees(math.atan2(d[1], d[0]))
    return cylinder(name, r, length, p, mat, r_top=r_top, segments=segments, rot=(tilt, 0, yaw + 90), bevel=bevel)


def _lerp(p, q, t):
    return tuple(p[i] + (q[i] - p[i]) * t for i in range(3))


@prop
def ladder_wood():
    rnd = random.Random(17)
    wood = material("ladder_wood_rails", WOOD, vary=0.3, scale=12)
    wood_old = material("ladder_wood_rails_old", WOOD_OLD, vary=0.3, scale=12)
    rung_mat = material("ladder_wood_rungs", RUNG, vary=0.28, scale=16)
    rope = material("ladder_wood_rope", ROPE, vary=0.22, scale=40, crevice=0.7)

    # The rails: their foot discs lean, so lift the foot by the radius times the lean to keep the rim on the ground.
    lean = math.atan2(TOP_Y - FOOT_Y, TOP_Z)
    lift = RAIL_R * math.sin(lean) + 0.002
    rails = []
    for s in (-1, 1):
        foot = (s * HALF_FOOT + rnd.uniform(-0.01, 0.01), FOOT_Y, lift)
        top = (s * HALF_TOP + rnd.uniform(-0.015, 0.015), TOP_Y, TOP_Z - RAIL_R_TOP * math.sin(lean))
        # A slight crook: two pieces meeting a little off the straight line.
        mid = _lerp(foot, top, 0.55)
        mid = (mid[0] + s * rnd.uniform(0.008, 0.018), mid[1] + rnd.uniform(-0.01, 0.01), mid[2])
        r_mid = RAIL_R + (RAIL_R_TOP - RAIL_R) * 0.55
        mat = wood if s < 0 else wood_old
        _segment(f"rail_{s}_low", foot, mid, RAIL_R, mat, r_top=r_mid)
        _segment(f"rail_{s}_high", mid, top, r_mid, mat, r_top=RAIL_R_TOP)
        rails.append((foot, mid, top))

    def on_rail(rail, z):
        foot, mid, top = rail
        if z <= mid[2]:
            return _lerp(foot, mid, (z - foot[2]) / (mid[2] - foot[2]))
        return _lerp(mid, top, (z - mid[2]) / (top[2] - mid[2]))

    # Rungs through the rails, each a touch out of level, with a rope lashing at both ends.
    step = (TOP_Z - 0.25 - FIRST_RUNG) / (RUNGS - 1)
    for k in range(RUNGS):
        z = FIRST_RUNG + k * step + rnd.uniform(-0.015, 0.015)
        a = on_rail(rails[0], z + rnd.uniform(-0.01, 0.01))
        b = on_rail(rails[1], z + rnd.uniform(-0.01, 0.01))
        span = b[0] - a[0]
        out = RUNG_OUT / span
        p = _lerp(a, b, -out)
        q = _lerp(a, b, 1 + out)
        _segment(f"rung_{k}", p, q, RUNG_R * rnd.uniform(0.92, 1.08), rung_mat, segments=8, bevel=0.004)
        for j, c in enumerate((a, b)):
            rail = rails[j]
            r = RAIL_R + (RAIL_R_TOP - RAIL_R) * (c[2] / TOP_Z) + LASH_R
            # A band round the rail, centred on the rung, following the rail's lean.
            d = [rail[2][i] - rail[0][i] for i in range(3)]
            n = math.sqrt(sum(v * v for v in d))
            u = [v / n * LASH_H / 2 for v in d]
            _segment(f"lash_{k}_{j}", (c[0] - u[0], c[1] - u[1], c[2] - u[2]), (c[0] + u[0], c[1] + u[1], c[2] + u[2]),
                     r, rope, segments=8, bevel=0)
