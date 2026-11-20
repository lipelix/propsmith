# Plan 2: every prop srd-iso-rpg needs

**Status:** planned 2026-11-19; worked by the HQ runner on the Asus laptop (Linux, Blender 5.2.2), one kit per session. Items 1 (crypt wall kit), 2 (rock mass and niches), 3 (fire and light), 4 (stairs), 5 (rubble and pillars), 6 (ritual hall), 7 (iron door and chest), 8 (crypt dressing), 9 (traps), 10 (thicket), 11 (cliffs), 12 (crypt entrance), 13 (forest floor), 14 (more trees) and 15 (water and camp) done 2026-11-20.

## Goal

srd-iso-rpg builds only its village from catalogue props. The forest road and both crypt levels are still Gemini
paintings; its Phase 16 rebuilds them from props and drops the painting pipeline. This plan adds every prop those areas
cannot be built without (MUST), then the dressing that makes them and the village richer (NICE), so the whole game can
be laid out from the catalogue.

## Source

An inventory of lipelix/srd-iso-rpg `main` (2026-11-19): `src/world/areas/*.ts`, `assets/locations/*`,
`assets/art/*/prompt.md` (what the paintings show), `src/world/area.ts` and `src/world/location.ts` (what the game
expects of props), `tools/locations/blender/lib/locations/terrain.py`. What it found that shapes this plan:

- The terrain is flat textured ground (grass, dirt, cobbles, flagstone, planks, water, void): no height. Walls, cliffs,
  stairs and the crypt's solid rock must be props, and `void` bakes transparent, so rock mass needs a filler prop.
- Doors and chests are props with one 1.5 m footprint (a game fact kept in srd's overlay, not here): keep an iron door
  within about 1.5 × 0.3 m on the ground.
- Light comes from props with anchors: braziers, torches, candles and fireplaces (`light:*`, `fire:*`).
- Traps are drawn by the game; a revealed pit or plate may use a prop.
- The design's "1.5 m section" is the length the wall and fence kits join at (`MODULE = 1.5` in the existing
  `wall_stone_*` assets): keep new wall-like kits on it.

## How sessions work this plan

- **One session takes one item (a kit of 2–4 props).** For each prop: write `catalog/<id>/asset.py` and `asset.json`
  following `skills/prop/SKILL.md` (style, palette, budget, `size`, tags only from `catalog/tags.json`), and loop
  `npm run build -- <id>` until every check is OK and the review snapshots match the description.
- **On the Asus, wrap every Blender command in a timeout:** `timeout 600 npm run build -- <id>`. Its GeForce 920M
  (nouveau) can run out of GPU memory on a large asset (`oak_tree` hung in the review render). If a build of a
  correct model hangs there twice, keep the prop in the PR, say so in it and in the handoff, and label the item `review`
  so it is rebuilt on a Mac; never make a model worse to fit the GPU.
  `npm run shots` at its default 1024 px crashes nouveau there (SIGSEGV, then later Blender runs hang until the stale
  `blender` processes are killed): use `--size 512` on the Asus and say so in the PR. Run `npm run check` with Blender
  off `PATH` (as in CI): its Blender tests hang on that GPU.
- **PR pictures:** `npm run shots -- <ids…> --push <branch-slug>` and paste the printed table into the PR body
  (`AGENTS.md`). `npm run check` must pass.
- **One branch and PR per item**, `Closes #<item>`. When CI is green, squash-merge, close the item with a handoff
  comment (`<!-- hq:handoff v1 -->`, format in lipelix/hq-dashboard `AGENTS.md`), then label the next item `ready`.
- **A tag the vocabulary lacks** is not added by a session: pick the nearest existing tags and note it in the handoff.
- **New work found on the way** becomes a new sub-issue, not scope creep. Keep this file's Status line current.

## Items

### Crypt (MUST first)

1. **Crypt wall kit:** `wall_crypt_straight`, `wall_crypt_corner`, `wall_crypt_doorway`: dark dressed ashlar, about 3 m
   high and 0.6 m thick, 1.5 m sections (the corner an L of two half-sections, the doorway an arched opening about
   1.1 × 2.2 m). Cooler and darker than the village fieldstone, with worn joints and a little damp staining.
2. **Rock mass and niches:** `rock_mass_block` (solid rough rock filling a 1.5 × 1.5 m footprint about 3 m high,
   seamless when repeated side by side), `wall_crypt_niche` (a 1.5 m crypt wall section with two stacked burial niches,
   one holding a shrouded body).
3. **Fire and light:** `brazier_iron` (an iron fire bowl on three legs, about 0.7 × 0.7 × 1.1 m, burning coals;
   anchors `fire:bowl` and `light:fire`), `campfire_ring` (a ring of stones with crossed logs and embers, about 1.2 m
   across; anchors `fire:camp` and `light:fire`), `torch_wall_sconce` (an iron wall bracket with a pitch torch, about
   0.3 × 0.35 × 0.6 m; anchors `fire:torch` and `light:torch`).
4. **Stairs:** `stairs_stone_down` (worn stone steps going down into darkness between two side walls, about 1.5 × 3 m,
   the deep end dark), `stairs_stone_up` (the same flight seen from below, rising to a dark opening).
5. **Rubble and pillars:** `rubble_stone` (fallen dressed masonry and grit, about 1.2 × 1.2 × 0.6 m),
   `pillar_stone` (a square crypt pillar with base and capital, about 0.7 × 0.7 × 3 m), `pillar_stone_broken` (its
   snapped stump with the fallen drum beside it).
6. **Ritual hall:** `ritual_circle_floor` (a carved and dark-painted sigil circle set flush in flagstones, about 3.5 m
   across and a few centimetres high), `altar_stone_crude` (a rough unhewn altar block with old dark stains, about
   1.5 × 0.9 × 1 m), `banner_cult` (a tattered dark cloth banner with a sigil on an iron pole and foot, about
   1 × 0.4 × 2.5 m).
7. **Iron door and chest:** `door_iron_bound` (a heavy plank door strapped with iron bands and studs in a stone frame,
   within about 1.5 × 0.3 × 2.4 m on the ground), `chest_iron_bound` (a heavy dark chest wrapped in iron with a sigil
   lock plate, about 1 × 0.7 × 0.7 m, closed).
8. **Crypt dressing:** `cobweb_corner` (a dusty web strung across a corner between two short stone stubs, about
   1 × 1 × 1 m), `puddle_water` (a shallow dark puddle with a wet rim, about 1 m across, a few centimetres high),
   `bedroll_cloth` (a rolled-out worn bedroll with a pack and a blanket, about 2 × 0.8 m).
9. **Traps:** `pressure_plate_stone` (a slightly raised square flagstone with a dark gap around it, 1.5 m),
   `pit_open_spiked` (a square pit with broken floor edges and iron spikes inside, 1.5 m, its rim at ground level),
   `net_trap_fallen` (a heavy rope net lying in a heap with weights at its corners, about 2 × 2 m).

### Forest road (MUST first)

10. **Thicket:** `thicket_bramble` (a dense, impassable mass of brambles, briars and undergrowth about 1.5 × 1.5 m and
    1.6 m high that reads as one continuous hedge when repeated), `bramble_low` (a low bramble patch, about
    1 × 1 × 0.6 m).
11. **Cliffs:** `cliff_rock_straight` (a mossy grey rock face 1.5 m long, about 3.5 m high and 1.5 m deep, ledges and
    cracks, ivy at the top), `cliff_rock_corner` (its outside corner). These are large: mind the timeout rule.
12. **Crypt entrance:** `crypt_entrance_stone` (a grassy hillside barrow mouth framed by old standing stones and a
    lintel, worn stone steps going down into it, about 3 × 3 × 2.5 m, front on -y).
13. **Forest floor:** `log_fallen` (a fallen mossy trunk with broken branch stubs, about 3 × 0.6 × 0.6 m),
    `mushrooms_cluster` (a cluster of brown and pale toadstools, about 0.3 m), `reeds_clump` (a clump of reeds and
    rushes for a pool rim, about 0.6 × 0.6 × 1.2 m).
14. **More trees:** `birch_tree` (a slender white birch, about 2 × 2 × 6 m), `tree_dead` (a bare dead snag with broken
    limbs, about 2 × 2 × 5 m), `sapling_young` (a young broadleaf, about 1 × 1 × 2 m).
15. **Water and camp:** `waterfall_rock` (a small cascade spilling over a mossy rock step into a basin, about
    1.5 × 1 × 3 m; anchors `water:spout` and `water:basin` with sizes), `goblin_camp_lean_to` (a crude lean-to of
    branches and hides over a bed of straw, about 2 × 2 × 1.5 m).

### Village dressing (NICE)

16. **Inn:** `stool_wood`, `chair_wood`, `tankards_pewter` (three tankards and a jug on a small tray), `keg_rack`
    (two kegs on a timber cradle, about 1.5 × 0.6 × 1 m).
17. **Merchant:** `weapon_rack` (a timber rack with spears, a sword and an axe, about 1.2 × 0.4 × 1.5 m),
    `armour_stand` (a wooden stand with a mail shirt and helm, about 0.6 × 0.6 × 1.8 m), `potion_shelf` (a narrow
    shelf of stoppered bottles and jars, about 1 × 0.3 × 1.5 m).
18. **Temple and house:** `lectern_wood` (a carved lectern with an open book), `tapestry_hanging` (a woven hanging on
    a rod and stand, about 1 × 0.3 × 2 m), `rug_woven` (a patterned rug, about 2 × 1.5 m), `wardrobe_wood` (a tall
    plank wardrobe, about 1.2 × 0.6 × 2 m).
19. **Village exterior:** `notice_board` (a roofed timber board with pinned notices, about 1.5 × 0.4 × 2.2 m),
    `washing_line` (a rope between two posts with hanging cloths, about 3 × 0.3 × 2 m), `gate_wood` (a plank field
    gate on posts that matches `fence_wood`, 1.5 m wide).

## Done

Every item merged; srd-iso-rpg's Phase 16 can lay out the forest road and both crypt levels from the catalogue.
