"""A hand crossbow lying level as held in one hand, cocked with a bolt in its groove: the bolt points +x, a small
steel prod spans y at the nose, a pistol grip with a pommel cap under the back of the tiller and a trigger lever in
front of it. The main hand on the grip (along +z, leaning forward), a finger on the trigger; no stock, no off hand."""
import math

from propsmith import grip, prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder

# Overall: 0.4 m long with a 0.34 m prod.
LENGTH, SPAN = 0.4, 0.34
TW, TH = 0.03, 0.036  # the tiller's width and depth
PROD = 0.014
GRIP_L, GRIP_LEAN = 0.1, 22  # the pistol grip under the tiller, leaning its foot back this many degrees
HAND = 0.085

WOOD = (0.16, 0.09, 0.045)  # linear RGB
IRON = (0.1, 0.1, 0.105)
STEEL = (0.32, 0.32, 0.33)
BRASS = (0.3, 0.22, 0.09)
CORD = (0.3, 0.25, 0.17)
FLETCH = (0.35, 0.3, 0.22)


@prop
def crossbow_hand():
    wood = material("crossbow_hand_wood", WOOD, vary=0.22, scale=24)
    iron = material("crossbow_hand_iron", IRON, rough=0.5, metal=0.8, vary=0.3, scale=30)
    steel = material("crossbow_hand_steel", STEEL, rough=0.3, metal=0.9, vary=0.12, scale=30)
    brass = material("crossbow_hand_brass", BRASS, rough=0.4, metal=0.7, vary=0.2, scale=30)
    cord = material("crossbow_hand_cord", CORD, rough=0.85, vary=0.2, scale=60)
    fletch = material("crossbow_hand_fletching", FLETCH, rough=0.9, vary=0.3, scale=40)

    lean = math.radians(GRIP_LEAN)
    rear, nose = -LENGTH / 2 + 0.04, LENGTH / 2 - 0.02
    tz = GRIP_L * math.cos(lean) + 0.012 + TH / 2  # the tiller's centre line, the grip's pommel cap on z = 0
    box("tiller", (nose - rear, TW, TH), ((nose + rear) / 2, 0, tz), wood, bevel=0.005)
    for s in (-1, 1):
        box(f"rail_{s}", (nose - rear - 0.12, TW * 0.3, 0.004), ((nose + rear) / 2 + 0.05, s * TW * 0.33,
            tz + TH / 2 + 0.0015), iron, bevel=0.001)
    nut_x = rear + 0.07
    cylinder("nut", TH * 0.3, TW * 0.9, (nut_x, TW * 0.45, tz + TH / 2), brass, segments=10, rot=(90, 0, 0),
             bevel=0.0015)

    # Pistol grip with a brass pommel cap, under the tiller's back end; the trigger lever in front of it.
    gx = rear + 0.03 - math.sin(lean) * GRIP_L / 2
    gz = tz - TH / 2 - math.cos(lean) * GRIP_L / 2 + 0.01
    box("grip", (0.03, TW * 0.9, GRIP_L + 0.02), (gx, 0, gz), wood, rot=(0, GRIP_LEAN, 0), bevel=0.007)
    fx, fz = gx - math.sin(lean) * (GRIP_L / 2 + 0.01), gz - math.cos(lean) * (GRIP_L / 2 + 0.01)
    cylinder("pommel", 0.02, 0.014, (fx, 0, fz - 0.01), brass, r_top=0.016, segments=10, rot=(0, GRIP_LEAN, 0),
             bevel=0.003)
    trig_x = rear + 0.07
    box("trigger", (0.008, 0.008, 0.05), (trig_x, 0, tz - TH / 2 - 0.02), iron, rot=(0, GRIP_LEAN, 0), bevel=0.002)

    # Steel prod in a brass block at the nose, its limbs swept back a little; the string back to the nut.
    sweep = 10
    prod_x = nose - 0.03
    for s in (-1, 1):
        box(f"prod_{s}", (PROD, SPAN / 2, PROD * 0.6), (prod_x - math.sin(math.radians(sweep)) * SPAN / 4,
            s * SPAN / 4, tz + TH * 0.15), steel, rot=(0, 0, s * sweep), bevel=0.002)
    box("prod_block", (0.04, TW * 1.3, TH * 1.1), (prod_x, 0, tz), brass, bevel=0.004)
    tip_x = prod_x - math.sin(math.radians(sweep)) * SPAN / 2
    for s in (-1, 1):
        dx, dy = nut_x - tip_x, -s * SPAN / 2
        cylinder(f"string_{s}", 0.0018, math.hypot(dx, dy), (tip_x, s * SPAN / 2, tz + TH / 2 + 0.0015), cord,
                 segments=5, rot=(0, 90, math.degrees(math.atan2(dy, dx))), bevel=0)

    # The bolt: shaft, steel head and three vanes.
    bolt_l = nose - nut_x + 0.03
    bz = tz + TH / 2 + 0.005
    cylinder("bolt", 0.004, bolt_l, (nut_x, 0, bz), wood, segments=6, rot=(0, 90, 0), bevel=0)
    cylinder("bolt_head", 0.007, 0.03, (nut_x + bolt_l - 0.002, 0, bz), steel, r_top=0.001, segments=4,
             rot=(0, 90, 0), bevel=0.001)
    for i, a in enumerate((90, 210, 330)):
        box(f"vane_{i}", (0.045, 0.0012, 0.009), (nut_x + 0.035, math.cos(math.radians(a)) * 0.0065,
            bz + math.sin(math.radians(a)) * 0.0065), fletch, rot=(a - 90, 0, 0), bevel=0)

    # The main hand round the grip (along it, up and forward), a finger on the trigger lever.
    grip("main", (gx, 0, gz), (math.sin(lean), 0, math.cos(lean)))
    grip("trigger", (trig_x, 0, tz - TH / 2 - 0.035))
