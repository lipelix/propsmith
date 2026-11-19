"""A standing iron brazier: a wide hammered fire bowl with a rolled rim on three splayed legs tied by a ring brace,
heaped with black coals that glow orange at the heart and low tongues of flame."""
import math
import random

from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

# About 0.7 x 0.7 m and 1.1 m to the flame tips.
BOWL_R_TOP, BOWL_R_BOT = 0.31, 0.17  # outer radius of the bowl at the rim and at the base
BOWL_Z, BOWL_H = 0.66, 0.22  # bottom of the bowl and its height (rim at 0.88 m)
RIM_R = 0.012  # rolled rim tube
LEG_FOOT_R = 0.3  # radius where the legs meet the ground
LEG_TOP_R = 0.2  # radius where the legs meet the bowl wall
LEG_TOP_Z = 0.78  # where the legs end, clasping the bowl
LEG_W = 0.04  # square section of the legs
BRACE_Z = 0.3  # ring brace between the legs
COAL_Z = BOWL_Z + BOWL_H  # the coal heap mounds over the rim
FLAME_TOP = 1.08

IRON = (0.05, 0.047, 0.044)
IRON_WORN = (0.13, 0.115, 0.1)  # rubbed rim and feet
COAL = (0.04, 0.036, 0.034)
ASH = (0.2, 0.19, 0.17)
EMBER = (0.5, 0.15, 0.03)
FLAME = (0.5, 0.28, 0.035)


@prop
def brazier_iron():
    rnd = random.Random(7)
    iron = material("brazier_iron_iron", IRON, rough=0.6, vary=0.25, scale=18, metal=0.6)
    worn = material("brazier_iron_worn", IRON_WORN, rough=0.45, vary=0.25, scale=20, crevice=0.3, metal=0.6)
    coal = material("brazier_iron_coal", COAL, rough=0.7, vary=0.35, scale=22, crevice=0.6)
    ash = material("brazier_iron_ash", ASH, vary=0.3, scale=16, crevice=0.6)
    ember = material("brazier_iron_ember", EMBER, rough=0.6, vary=0.35, scale=14, crevice=0.2)
    flame = material("brazier_iron_flame", FLAME, rough=0.5, vary=0.3, scale=10, crevice=0.1)

    # Bowl: a frustum widening upwards, a rolled rim and a small foot ring underneath.
    cylinder("bowl", BOWL_R_BOT, BOWL_H, (0, 0, BOWL_Z), iron, r_top=BOWL_R_TOP, segments=20, bevel=0.01)
    torus("rim", BOWL_R_TOP - 0.004, RIM_R, (0, 0, COAL_Z), worn, major=28, minor=6)
    cylinder("bowl_foot", BOWL_R_BOT * 0.75, 0.04, (0, 0, BOWL_Z - 0.03), iron, segments=16, bevel=0.008)
    # Six hammered bands down the outside of the bowl.
    slope = math.degrees(math.atan2(BOWL_R_TOP - BOWL_R_BOT, BOWL_H))
    for i in range(6):
        a = math.radians(30 + 60 * i)
        r = (BOWL_R_TOP + BOWL_R_BOT) / 2 + 0.006
        box(f"bowl_band_{i}", (0.012, 0.03, BOWL_H / math.cos(math.radians(slope)) - 0.02),
            (r * math.cos(a), r * math.sin(a), BOWL_Z + BOWL_H / 2), iron,
            rot=(0, slope, math.degrees(a)), bevel=0.004)

    # Three splayed legs, each a square bar from a foot pad to a clasp under the bowl wall, ending in a curl.
    for i in range(3):
        a = 2 * math.pi * i / 3 + math.radians(90)
        dr = LEG_FOOT_R - LEG_TOP_R
        length = math.hypot(dr, LEG_TOP_Z)
        tilt = math.degrees(math.atan2(dr, LEG_TOP_Z))
        mr = (LEG_FOOT_R + LEG_TOP_R) / 2
        box(f"leg_{i}", (LEG_W, LEG_W, length), (mr * math.cos(a), mr * math.sin(a), LEG_TOP_Z / 2), iron,
            rot=(0, -tilt, math.degrees(a)), bevel=0.006)
        fx, fy = LEG_FOOT_R * math.cos(a), LEG_FOOT_R * math.sin(a)
        cylinder(f"foot_{i}", 0.045, 0.025, (fx * 1.03, fy * 1.03, 0), worn, r_top=0.03, segments=10, bevel=0.006)
        # Clasp: a short bar hugging the bowl and a curl standing above the rim.
        cr = LEG_TOP_R + 0.03
        box(f"clasp_{i}", (0.02, 0.05, 0.16), (cr * math.cos(a), cr * math.sin(a), LEG_TOP_Z + 0.03), iron,
            rot=(0, slope, math.degrees(a)), bevel=0.005)
        torus(f"curl_{i}", 0.035, 0.009, ((BOWL_R_TOP + 0.03) * math.cos(a), (BOWL_R_TOP + 0.03) * math.sin(a),
              COAL_Z + 0.02), worn, rot=(90, 0, math.degrees(a) + 90), major=12, minor=6)

    # Ring brace tying the legs together low down.
    brace_r = LEG_FOOT_R - (LEG_FOOT_R - LEG_TOP_R) * BRACE_Z / LEG_TOP_Z
    torus("brace", brace_r, 0.011, (0, 0, BRACE_Z), iron, major=30, minor=6)

    # Coals: a heap mounding over the rim, black lumps over a glowing heart, pale ash towards the edge.
    mound_r, mound_h, mound_z = BOWL_R_TOP - 0.02, 0.1, COAL_Z - 0.04
    blob("coal_bed", mound_r, (0, 0, mound_z), coal, squash=(1, 1, mound_h / mound_r), subdiv=2, seed=3,
         jitter=0.06)
    blob("ember_heart", 0.15, (0, 0, mound_z + mound_h - 0.03), ember, squash=(1.1, 1.0, 0.45), subdiv=2, seed=4,
         jitter=0.2)
    for i in range(40):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0.06, 0.25)
        x, y = r * math.cos(a), r * math.sin(a)
        z = mound_z + mound_h * math.sqrt(max(0.0, 1 - (r / mound_r) ** 2)) + rnd.uniform(-0.005, 0.01)
        lump = rnd.uniform(0.032, 0.052)
        mat = ember if rnd.random() < 0.3 and r < 0.16 else (ash if r > 0.2 and rnd.random() < 0.5 else coal)
        blob(f"coal_{i}", lump, (x, y, z), mat, squash=(1.2, 1.0, 0.7), subdiv=1, seed=30 + i, jitter=0.25)

    # A few tongues of flame rising from the heart (the fire anchor animates the rest).
    peak = mound_z + mound_h
    flames = [(-0.03, -0.02, 0.055, 1.0), (0.06, 0.04, 0.05, 0.75), (-0.06, 0.07, 0.045, 0.6), (0.07, -0.06, 0.04, 0.5)]
    for i, (fx, fy, fr, tall) in enumerate(flames):
        h = (FLAME_TOP - peak + 0.04) * tall
        blob(f"flame_{i}", fr, (fx, fy, peak - 0.04 + h / 2), flame, squash=(0.85, 0.8, h / (2 * fr)), subdiv=2,
             seed=60 + i, jitter=0.12)

    anchor("fire:bowl", (0, 0, COAL_Z + 0.06), size=(0.22, 0.22, 0.45))
    anchor("light:fire", (0, 0, COAL_Z + 0.25))
