"""A crossbow lying level as held, cocked with a bolt in its groove: the bolt points +x, the prod spans y at the nose,
a stirrup in front of it, the butt to -x. A wooden tiller with a pistol grip under it behind a long trigger lever; the
main hand on the grip (along +z, leaning forward), the off hand under the fore-stock (along +x), the butt set to the
shoulder. Two variants: the light crossbow, with a wooden prod and cord bindings, and the heavy crossbow, longer and
thicker, with a steel prod in iron bridles and a bigger stirrup."""
import math

from propsmith import grip, prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder, torus

# Overall: the light one 0.9 m long with a 0.7 m prod, the heavy one 1.1 m with a 0.9 m prod.
LIGHT = {"length": 0.9, "span": 0.7, "tiller": (0.042, 0.05), "prod": 0.024, "stirrup": 0.06, "steel": False}
HEAVY = {"length": 1.1, "span": 0.9, "tiller": (0.055, 0.065), "prod": 0.03, "stirrup": 0.08, "steel": True}
GRIP_L, GRIP_LEAN = 0.11, 18  # the pistol grip under the tiller, leaning its foot back this many degrees
HAND = 0.085

WOOD = (0.19, 0.115, 0.058)  # linear RGB
WOOD_DARK = (0.13, 0.075, 0.038)
IRON = (0.1, 0.1, 0.105)
STEEL = (0.32, 0.32, 0.33)
CORD = (0.3, 0.25, 0.17)
FLETCH = (0.35, 0.3, 0.22)


def crossbow_model(name, p):
    wood = material(f"{name}_tiller", WOOD, vary=0.22, scale=18)
    dark = material(f"{name}_prod_wood", WOOD_DARK, vary=0.2, scale=22)
    iron = material(f"{name}_iron", IRON, rough=0.5, metal=0.8, vary=0.3, scale=25)
    steel = material(f"{name}_steel", STEEL, rough=0.3, metal=0.9, vary=0.12, scale=24)
    cord = material(f"{name}_cord", CORD, rough=0.85, vary=0.2, scale=60)
    fletch = material(f"{name}_fletching", FLETCH, rough=0.9, vary=0.3, scale=40)

    length, span = p["length"], p["span"]
    tw, th = p["tiller"]
    rear, nose = -length * 0.5, length * 0.5 - 0.04  # x of the butt's end and of the tiller's nose
    tz = GRIP_L * math.cos(math.radians(GRIP_LEAN)) + th / 2  # the tiller's centre line, the grip's foot on z = 0
    grip_x = rear + length * 0.36  # where the grip meets the tiller
    prod_x = nose - 0.06

    # Tiller: a long bar, the butt behind the grip deeper and dropping a little, a wrist between them.
    box("tiller", (nose - grip_x + 0.02, tw, th), ((nose + grip_x - 0.02) / 2, 0, tz), wood, bevel=0.006)
    box("wrist", (0.12, tw * 0.95, th * 1.05), (grip_x - 0.04, 0, tz), wood, bevel=0.006)
    box("butt", (grip_x - 0.08 - rear, tw * 1.1, th * 1.7), ((grip_x - 0.08 + rear) / 2, 0, tz - th * 0.3), wood,
        rot=(0, -4, 0), bevel=0.01)
    box("butt_plate", (0.012, tw * 1.15, th * 1.75), (rear + 0.004, 0, tz - th * 0.35), iron, rot=(0, -4, 0),
        bevel=0.003)
    # The groove's two rails along the top, and the nut (the latch the string is cocked on).
    for s in (-1, 1):
        box(f"rail_{s}", (nose - grip_x - 0.05, tw * 0.3, 0.006), ((nose + grip_x) / 2 + 0.02, s * tw * 0.33,
            tz + th / 2 + 0.002), dark, bevel=0.002)
    nut_x = grip_x + 0.04
    cylinder("nut", th * 0.32, tw * 0.9, (nut_x, tw * 0.45, tz + th / 2), iron, segments=10, rot=(90, 0, 0),
             bevel=0.002)

    # Pistol grip under the wrist, its foot leaning back; the trigger lever hangs in front of it.
    lean = math.radians(GRIP_LEAN)
    gx = grip_x - 0.03 - math.sin(lean) * GRIP_L / 2
    gz = tz - th / 2 - math.cos(lean) * GRIP_L / 2 + 0.01
    box("grip", (0.036, tw * 0.8, GRIP_L + 0.02), (gx, 0, gz), wood, rot=(0, GRIP_LEAN, 0), bevel=0.008)
    trig_x = grip_x + 0.035
    box("trigger", (0.012, 0.01, 0.075), (trig_x, 0, tz - th / 2 - 0.03), iron, rot=(0, GRIP_LEAN, 0), bevel=0.003)

    # Prod across the nose, bent back to its tips, lashed (light) or held in iron bridles (heavy).
    pt = p["prod"]
    sweep = 10  # degrees the limbs sweep back
    for s in (-1, 1):
        limb = box(f"prod_{s}", (pt, span / 2, pt * 0.8), (prod_x - math.sin(math.radians(sweep)) * span / 4,
                   s * span / 4, tz + th * 0.15), steel if p["steel"] else dark, rot=(0, 0, s * sweep), bevel=0.004)
        limb.scale = (1, 1, 0.8 if p["steel"] else 1)
    box("prod_block", (0.07, tw * 1.25, th * 1.1), (prod_x, 0, tz), iron if p["steel"] else wood, bevel=0.006)
    for s in (-1, 1):
        if p["steel"]:
            box(f"bridle_{s}", (0.05, 0.012, th * 1.3), (prod_x, s * (tw * 0.62 + 0.006), tz), iron, bevel=0.003)
        else:
            torus(f"lashing_{s}", pt * 0.8, 0.005, (prod_x, s * tw * 0.75, tz + th * 0.15), cord, rot=(90, 0, 0),
                  major=10, minor=4)

    # String from each tip back to the nut.
    tip_x = prod_x - math.sin(math.radians(sweep)) * span / 2
    for s in (-1, 1):
        dx, dy = nut_x - tip_x, -s * span / 2
        run = math.hypot(dx, dy)
        cylinder(f"string_{s}", 0.0025, run, (tip_x, s * span / 2, tz + th / 2 + 0.002), cord, segments=5,
                 rot=(0, 90, math.degrees(math.atan2(dy, dx))), bevel=0)

    # The bolt in the groove: a shaft from the nut past the nose, a steel head and three vanes.
    bolt_l = nose - nut_x + 0.04
    bz = tz + th / 2 + 0.007
    cylinder("bolt", 0.0055, bolt_l, (nut_x, 0, bz), wood, segments=6, rot=(0, 90, 0), bevel=0)
    cylinder("bolt_head", 0.01, 0.045, (nut_x + bolt_l - 0.003, 0, bz), steel, r_top=0.001, segments=4,
                    rot=(0, 90, 0), bevel=0.001)
    for i, a in enumerate((90, 210, 330)):
        box(f"vane_{i}", (0.07, 0.0015, 0.012), (nut_x + 0.05, math.cos(math.radians(a)) * 0.009,
            bz + math.sin(math.radians(a)) * 0.009), fletch, rot=(a - 90, 0, 0), bevel=0)

    # Stirrup in front of the nose, an iron loop to put a foot in when spanning.
    st = p["stirrup"]
    box("stirrup_strap", (0.05, tw * 0.9, 0.01), (nose + 0.01, 0, tz - th / 2 + 0.008), iron, bevel=0.002)
    loop = torus("stirrup", st, 0.006, (nose + st, 0, tz - th / 2 + 0.01), iron, rot=(0, -70, 0), major=16, minor=5)
    loop.scale = (1, 0.7, 1)

    # Grips: the main hand round the pistol grip (along it, up and forward), the off hand under the fore-stock
    # (along the bolt), the butt's end at the shoulder and the trigger lever under the finger.
    grip("main", (gx, 0, gz), (math.sin(lean), 0, math.cos(lean)))
    grip("off", (prod_x - 0.18, 0, tz), (1, 0, 0))
    grip("stock", (rear + 0.002, 0, tz - th * 0.35))
    grip("trigger", (trig_x, 0, tz - th / 2 - 0.045))


@prop
def crossbow():
    crossbow_model("crossbow", LIGHT)


@prop
def crossbow_heavy():
    crossbow_model("crossbow_heavy", HEAVY)
