"""A wooden armour stand, front on -y: a cross-footed base, a central post and a shoulder yoke carrying a knee-length
mail shirt with short sleeves and a leather belt, and a round iron helm with a nasal on the post's head knob."""
import math
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall size: about 0.6 × 0.6 m on the ground, 1.8 m high to the top of the helm.
FOOT_L, FOOT_W, FOOT_H = 0.58, 0.08, 0.07  # the two crossed feet
POST = 0.06
POST_H = 1.6  # top of the post (the head knob sits on it)
YOKE_Z = 1.42  # top of the shoulder yoke
YOKE_W = 0.3
# The mail shirt: (height, radius) rings from the hem to the shoulders.
MAIL = ((0.66, 0.2), (0.82, 0.19), (0.98, 0.165), (1.12, 0.175), (1.3, 0.19), (1.43, 0.13))
SLEEVE_L, SLEEVE_R = 0.24, 0.075
BELT_Z = 0.98
HELM_R = 0.11
HELM_Z = 1.54  # bottom of the helm's brim

WOOD = (0.2, 0.125, 0.065)  # linear RGB
WOOD_OLD = (0.15, 0.1, 0.06)
MAIL_C = (0.2, 0.2, 0.21)
MAIL_DARK = (0.14, 0.135, 0.13)
IRON = (0.24, 0.24, 0.25)
IRON_DARK = (0.07, 0.07, 0.07)
LEATHER = (0.13, 0.07, 0.035)
BRASS = (0.3, 0.22, 0.09)


@prop
def armour_stand():
    rnd = random.Random(23)
    wood = material("armour_stand_wood", WOOD, vary=0.28, scale=10)
    old = material("armour_stand_wood_old", WOOD_OLD, vary=0.3, scale=9)
    mail = material("armour_stand_mail", MAIL_C, rough=0.55, metal=0.8, vary=0.45, scale=160, crevice=0.8)
    mail_dark = material("armour_stand_mail_dark", MAIL_DARK, rough=0.6, metal=0.7, vary=0.45, scale=160,
                         crevice=0.8)
    iron = material("armour_stand_helm", IRON, rough=0.4, metal=0.85, vary=0.2, scale=25)
    iron_dark = material("armour_stand_iron", IRON_DARK, rough=0.5, metal=0.8, vary=0.3, scale=20)
    leather = material("armour_stand_leather", LEATHER, rough=0.7, vary=0.25, scale=30)
    brass = material("armour_stand_brass", BRASS, rough=0.4, metal=0.7, vary=0.2, scale=25)

    # The base: two crossed feet, the post with a collar, and four short braces.
    turn = 45 + rnd.uniform(-3, 3)
    box("foot_0", (FOOT_L, FOOT_W, FOOT_H), (0, 0, FOOT_H / 2), old, rot=(0, 0, turn), bevel=0.012)
    box("foot_1", (FOOT_L, FOOT_W, FOOT_H - 0.004), (0, 0, (FOOT_H - 0.004) / 2), wood, rot=(0, 0, turn + 90),
        bevel=0.012)
    box("post", (POST, POST, POST_H - FOOT_H + 0.005), (0, 0, FOOT_H + (POST_H - FOOT_H) / 2 - 0.0025), wood,
        bevel=0.01)
    box("collar", (0.1, 0.1, 0.06), (0, 0, FOOT_H + 0.03), old, rot=(0, 0, 45), bevel=0.01)
    for k in range(4):
        a = math.radians(turn + 90 * k)
        box(f"brace_{k}", (0.17, 0.04, 0.04), (0.1 * math.cos(a), 0.1 * math.sin(a), FOOT_H + 0.06), old,
            rot=(0, 35, turn + 90 * k), bevel=0.006)

    # The shoulder yoke, a rounded crossbar.
    box("yoke", (YOKE_W, 0.06, 0.05), (0, 0, YOKE_Z - 0.025), wood, bevel=0.018)

    # The mail shirt: stacked frustums from the hem to the shoulders, a rolled hem, short sleeves and a belt.
    for k in range(len(MAIL) - 1):
        (za, ra), (zb, rb) = MAIL[k], MAIL[k + 1]
        cylinder(f"mail_{k}", ra, zb - za + 0.003, (0, 0, za), mail if k % 2 == 0 else mail_dark, r_top=rb,
                 segments=16, bevel=0)
    torus("mail_hem", MAIL[0][1] - 0.004, 0.012, (0, 0, MAIL[0][0] + 0.008), mail_dark, major=18, minor=6)
    torus("mail_neck", MAIL[-1][1] - 0.03, 0.014, (0, 0, MAIL[-1][0] - 0.002), mail_dark, major=16, minor=6)
    for i, s in enumerate((-1, 1)):
        cylinder(f"sleeve_{i}", SLEEVE_R * 1.1, SLEEVE_L, (s * 0.14, 0, YOKE_Z - 0.07), mail, r_top=SLEEVE_R * 0.9,
                 segments=12, rot=(0, s * 150, 0), bevel=0)
    torus("belt", MAIL[2][1] + 0.004, 0.018, (0, 0, BELT_Z), leather, major=20, minor=6)
    box("belt_buckle", (0.05, 0.02, 0.045), (0, -(MAIL[2][1] + 0.02), BELT_Z), brass, bevel=0.004)
    box("belt_tail", (0.03, 0.012, 0.16), (0.035, -(MAIL[2][1] + 0.022), BELT_Z - 0.09), leather,
        rot=(-4, 0, 0), bevel=0.003)

    # The head knob and the helm: a band, a stepped dome and a nasal on the front (-y).
    cylinder("knob", 0.05, 0.08, (0, 0, POST_H - 0.01), old, r_top=0.035, segments=10, bevel=0.008)
    cylinder("helm_band", HELM_R, 0.07, (0, 0, HELM_Z), iron, r_top=HELM_R * 0.98, segments=20, bevel=0.004)
    cylinder("helm_dome_0", HELM_R * 0.98, 0.07, (0, 0, HELM_Z + 0.068), iron, r_top=HELM_R * 0.8, segments=20,
             bevel=0)
    cylinder("helm_dome_1", HELM_R * 0.8, 0.06, (0, 0, HELM_Z + 0.136), iron, r_top=HELM_R * 0.42, segments=20,
             bevel=0)
    cylinder("helm_dome_2", HELM_R * 0.42, 0.04, (0, 0, HELM_Z + 0.194), iron, r_top=0.01, segments=20, bevel=0)
    torus("helm_rim", HELM_R + 0.002, 0.008, (0, 0, HELM_Z + 0.008), iron_dark, major=20, minor=6)
    box("helm_nasal", (0.026, 0.012, 0.1), (0, -HELM_R - 0.004, HELM_Z - 0.02), iron_dark, bevel=0.004)
