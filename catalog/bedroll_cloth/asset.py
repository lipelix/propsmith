"""A worn bedroll laid out on the floor, about 2 x 0.8 m: a padded canvas mat with quilting seams and a sewn-on patch,
a rolled cloak for a pillow tied with two cords at the head (+x), a rumpled dull red wool blanket with dark stripes
thrown over the lower two thirds with its top edge folded back and its sides hanging to the floor, and a leather pack
with a buckled flap and a rolled bundle on top standing beside the head."""
import random

from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import blob, box, cylinder, torus

X, Y = 2.0, 0.8  # overall footprint
MAT_X0, MAT_X1 = -1.0, 0.66  # mat ends: foot (-x) and head (+x)
MAT_W = 0.68  # mat width (y)
MAT_T = 0.045  # mat thickness
PILLOW_R = 0.065
PILLOW_X = 0.56
BLANKET_X1 = 0.22  # the blanket's folded-back top edge
BLANKET_W = 0.74
BLANKET_T = 0.022
DRAPE = MAT_T + 0.012  # how far the blanket's sides hang down
PACK = (0.24, 0.32, 0.42)  # pack body x, y, z
PACK_AT = (0.84, 0.13)

CANVAS = (0.19, 0.16, 0.115)  # linear RGB: worn undyed canvas
CANVAS_OLD = (0.14, 0.12, 0.085)
WOOL = (0.15, 0.055, 0.042)  # dull red wool
WOOL_DARK = (0.06, 0.035, 0.028)
CLOAK = (0.09, 0.1, 0.07)  # grey-green cloak
LEATHER = (0.16, 0.088, 0.045)
LEATHER_DARK = (0.075, 0.043, 0.024)
CORD = (0.25, 0.2, 0.13)
IRON = (0.05, 0.048, 0.045)


@prop
def bedroll_cloth():
    rnd = random.Random(808)
    canvas = material("bedroll_cloth_canvas", CANVAS, rough=0.95, vary=0.3, scale=9, crevice=0.6)
    canvas_old = material("bedroll_cloth_canvas_old", CANVAS_OLD, rough=0.95, vary=0.3, scale=12, crevice=0.6)
    wool = material("bedroll_cloth_wool", WOOL, rough=0.98, vary=0.3, scale=14, crevice=0.65)
    wool_dark = material("bedroll_cloth_wool_dark", WOOL_DARK, rough=0.98, vary=0.3, scale=14, crevice=0.6)
    cloak = material("bedroll_cloth_cloak", CLOAK, rough=0.97, vary=0.3, scale=10, crevice=0.6)
    leather = material("bedroll_cloth_leather", LEATHER, rough=0.6, vary=0.3, scale=10, crevice=0.6)
    strap = material("bedroll_cloth_strap", LEATHER_DARK, rough=0.6, vary=0.25, scale=12, crevice=0.6)
    cord = material("bedroll_cloth_cord", CORD, rough=0.9, vary=0.2, scale=20, crevice=0.5)
    iron = material("bedroll_cloth_iron", IRON, rough=0.5, vary=0.25, scale=14, metal=0.6)

    # The mat: a padded canvas pad with quilting seams across it and a patch near the foot.
    mx = (MAT_X0 + MAT_X1) / 2
    box("mat", (MAT_X1 - MAT_X0, MAT_W, MAT_T), (mx, 0, MAT_T / 2), canvas, rot=(0, 0, 0.6), bevel=0.018)
    for i in range(1, 6):
        x = MAT_X0 + (MAT_X1 - MAT_X0) * i / 6
        box(f"seam_{i}", (0.012, MAT_W - 0.03, 0.006), (x, 0, MAT_T + 0.001), canvas_old, bevel=0.002)
    box("patch", (0.18, 0.16, 0.006), (MAT_X0 + 0.14, -0.2, MAT_T + 0.002), canvas_old, rot=(0, 0, 7), bevel=0.002)

    # The pillow: a rolled cloak across the head, tied with two cords.
    top = MAT_T - 0.008
    cylinder("pillow", PILLOW_R, MAT_W - 0.06, (PILLOW_X, (MAT_W - 0.06) / 2, top + PILLOW_R), cloak,
             rot=(90, 0, 0), segments=14, bevel=0.012)
    for i, y in enumerate((-0.18, 0.18)):
        torus(f"pillow_tie_{i}", PILLOW_R + 0.002, 0.007, (PILLOW_X, y, top + PILLOW_R), cord, rot=(90, 0, 0),
              major=14, minor=6)

    # The blanket: four rumpled panels over the lower part, stripes, a folded-back top edge and hanging sides.
    bz = MAT_T + BLANKET_T / 2
    x0 = MAT_X0 + 0.04
    panels = 4
    pl = (BLANKET_X1 - x0) / panels
    for i in range(panels):
        cx = x0 + pl * (i + 0.5)
        lift = rnd.uniform(0.0, 0.014)
        box(f"blanket_{i}", (pl + 0.04, BLANKET_W, BLANKET_T), (cx, rnd.uniform(-0.01, 0.01), bz + lift), wool,
            rot=(rnd.uniform(-1.5, 1.5), rnd.uniform(-2, 2), rnd.uniform(-2.5, 2.5)), bevel=0.009)
        for side in (-1, 1):
            # A side hanging down to the floor.
            box(f"blanket_{i}_side_{side}", (pl + 0.03, BLANKET_T * 0.8, DRAPE + BLANKET_T),
                (cx, side * (BLANKET_W / 2 - 0.004), (DRAPE + BLANKET_T) / 2 + 0.002), wool,
                rot=(side * rnd.uniform(4, 9), 0, rnd.uniform(-2, 2)), bevel=0.006)
    for i, x in enumerate((x0 + 0.12, x0 + 0.2, BLANKET_X1 - 0.24)):
        box(f"stripe_{i}", (0.05, BLANKET_W + 0.006, BLANKET_T + 0.004), (x, 0, bz + 0.006), wool_dark,
            rot=(0, 0, rnd.uniform(-2, 2)), bevel=0.004)
    cylinder("fold", 0.024, BLANKET_W + 0.01, (BLANKET_X1, (BLANKET_W + 0.01) / 2, MAT_T + 0.024), wool,
             rot=(90, 0, 0), segments=10, bevel=0.006)
    box("fold_back", (0.13, BLANKET_W - 0.02, 0.016), (BLANKET_X1 - 0.07, 0.0, MAT_T + BLANKET_T + 0.02), wool_dark,
        rot=(0, -6, 1), bevel=0.006)
    # A corner turned back at the foot.
    box("corner", (0.2, 0.18, 0.016), (x0 + 0.12, -BLANKET_W / 2 + 0.12, bz + 0.022), wool_dark, rot=(0, 3, 38),
        bevel=0.006)

    # The pack: a rounded leather body with a flap, two buckled straps on its +x face and a bundle on top.
    px, py = PACK_AT
    sx, sy, sz = PACK
    box("pack", (sx, sy, sz), (px, py, sz / 2), leather, rot=(0, 0, -6), bevel=0.045)
    box("pack_pocket", (0.05, sy * 0.62, sz * 0.34), (px + sx / 2 + 0.01, py, sz * 0.27), leather, rot=(0, 0, -6),
        bevel=0.02)
    box("pack_flap", (sx + 0.025, sy + 0.02, 0.05), (px + 0.008, py, sz - 0.005), strap, rot=(0, 4, -6), bevel=0.018)
    box("pack_flap_front", (0.025, sy * 0.9, sz * 0.34), (px + sx / 2 + 0.006, py, sz * 0.8), strap, rot=(0, 0, -6),
        bevel=0.01)
    for i, dy in enumerate((-0.08, 0.08)):
        box(f"pack_strap_{i}", (0.012, 0.035, sz * 0.62), (px + sx / 2 + 0.024, py + dy - 0.003, sz * 0.62),
            strap, rot=(0, 0, -6), bevel=0.003)
        box(f"pack_buckle_{i}", (0.012, 0.045, 0.04), (px + sx / 2 + 0.034, py + dy - 0.003, sz * 0.52), iron,
            rot=(0, 0, -6), bevel=0.004)
    cylinder("pack_bundle", 0.045, sy - 0.02, (px, py + (sy - 0.02) / 2, sz + 0.035), canvas_old,
             rot=(90, 0, -6), segments=12, bevel=0.01)
    blob("pack_cup", 0.035, (px + 0.02, py - sy / 2 - 0.05, 0.03), iron, squash=(1, 1, 0.85), subdiv=1, seed=3,
         jitter=0.05)
