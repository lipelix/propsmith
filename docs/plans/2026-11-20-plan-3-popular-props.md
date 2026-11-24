# Plan 3: the props people reach for most

**Status:** planned 2026-11-20; worked by the HQ runner on the Linux laptop (Blender 5.2.2), one kit per session. Done: item 1 (treasure, #120), item 2 (library, #122), item 3 (alchemy, #124), item 4 (throne room, #125), item 5 (prison, #127), item 6 (punishment, #108), item 7 (graveyard, #109), item 8 (mine, #110), item 9 (cave, #111), item 10 (camp, #112), item 11 (smithy and crafts, #113), item 12 (kitchen and food, #114), item 13 (training yard, #115), item 14 (farm, #116), item 15 (harbour, #117), item 16 (ruins and magic, #118), item 17 (bridges and outbuildings, #119): all 17 items done. Follow-up: hanging props declare a `mount` (#126, #141).

## Goal

Plans 1 and 2 filled the catalogue with what one game needed: a village, a forest road and a crypt. This plan widens it
to the props that fantasy games and map makers use most, whatever the game: treasure, books, potions, thrones, cages,
graves, mine carts, crystals, tents, forges, food, scarecrows, nets, ruins and bridges. 67 props in 17 kits.

## Source

A survey on 2026-11-20 of what popular prop collections contain and what their users ask for: the content lists of the
most favourited low-poly medieval and dungeon kits (Quaternius Fantasy Props MegaKit, Unity Asset Store "Low Poly
Medieval Kit", Fab and CGTrader dungeon and storage packs), virtual-tabletop decor packs (Roll20 "Dungeon Craft: Dungeon
Decor", DungeonFog "Dungeon Decor", Fantasy Grounds prop packs) and the art requests on Inkarnate's feedback board.
Reddit refuses automated reading, so its threads are not part of the survey. What the lists agree on, most common first:

- storage and treasure (chests, coin heaps, sacks), books and potions, lighting (chandeliers, candelabra, lanterns);
- dungeon set pieces: cages, bars, thrones, altars, coffins, bones, torture and punishment devices;
- themed sets: graveyard, mine, cave with crystals, camp, smithy, kitchen and food, farm, harbour, ruins.

The catalogue already has barrels, crates, plain chests, tables, beds, benches, altars, coffins, bone piles, braziers,
torches, wells, carts, market stalls, fences and trees; this plan skips those. Hand weapons are their own work
(issue #55).

## How sessions work this plan

- **One session takes one item (a kit of 3–5 props).** For each prop: write `catalog/<id>/asset.py` and `asset.json`
  following `skills/prop/SKILL.md` (style, palette, budget, `size`, tags only from `catalog/tags.json`), and loop
  `npm run build -- <id>` until every check is OK and the review snapshots match the description.
- **Nothing game-specific.** Sizes are real-world metres. Kits that join (`prison_bars_*`, `fence_iron_cemetery`,
  `rail_track_straight`) use the 1.5 m section the wall and fence kits already join at.
- **A prop that reuses a catalogue prop's look** (`chest_wood_open` and `chest_wood`, `fence_iron_cemetery` and
  `fence_wood`) reads that asset first and keeps its proportions and palette.
- **On the Linux runner, wrap every Blender command in a timeout:** `timeout 600 npm run build -- <id>`. Its GeForce
  920M (nouveau) can run out of GPU memory on a large asset. If a build of a correct model hangs there twice, keep the
  prop in the PR, say so in it and in the handoff, and label the item `review` so it is rebuilt on a Mac; never make a
  model worse to fit the GPU. Run one Blender at a time. `npm run shots` at its default 1024 px crashes nouveau there
  (SIGSEGV, then later Blender runs hang until the stale `blender` processes are killed): use `--size 512` and say so
  in the PR. Run `npm run check` with Blender off `PATH` (as in CI): its Blender tests hang on that GPU.
- **PR pictures:** `npm run shots -- <ids…> --push <branch-slug>`, the printed table goes into the PR body and into
  the item's body after `<!-- hq:renders -->` (`AGENTS.md`). `npm run check` must pass.
- **One branch and PR per item**, `Closes #<item>`. When CI is green, squash-merge, close the item with a handoff
  comment (`<!-- hq:handoff v1 -->`, format in lipelix/hq-dashboard `AGENTS.md`), then label the next item `ready`.
- **Tags:** this plan added the settings `castle`, `graveyard`, `mine`, `cave`, `camp`, `harbour`, the materials
  `glass`, `gold`, `bone`, `crystal`, `paper` and the uses `treasure`, `magic`, `study`, `punishment`, `training`.
  A tag the vocabulary still lacks is not added by a session: pick the nearest existing tags and note it in the handoff.
- **New work found on the way** becomes a new sub-issue, not scope creep. Keep this file's Status line current.

## Items

### Dungeon and castle

The props almost every dungeon and interior pack leads with.

1. **Treasure:** `treasure_pile` (a heap of gold coins with a goblet, a crown and a few gems, about 1.2 × 1.2 × 0.5 m),
   `chest_wood_open` (the catalogue's wooden chest with its lid thrown back, full of coins, about 1 × 0.7 × 1 m),
   `coin_sacks` (three tied cloth sacks, one spilling coins, about 0.8 × 0.6 × 0.4 m).
2. **Library:** `bookshelf_wood` (a tall plank bookcase packed with uneven books and a few scrolls, about 1.2 × 0.4 × 2
   m, against a wall), `books_stack` (a leaning stack of worn books with one lying open, about 0.4 × 0.4 × 0.4 m),
   `desk_writing` (a writing desk with an inkwell, quill, parchment and a candle, about 1.2 × 0.6 × 0.9 m),
   `scroll_rack` (a pigeonhole rack of rolled scrolls, about 0.9 × 0.3 × 1.2 m).
3. **Alchemy:** `cauldron_iron` (a black iron cauldron hanging from a tripod over a small fire, about 0.9 × 0.9 × 1.2 m;
   anchors `fire:hearth` and `light:fire`), `alchemy_table` (a stained workbench with a retort, flasks, a mortar and a
   small burner, about 1.5 × 0.7 × 1.3 m), `potion_bottles` (a small group of stoppered bottles and vials in red, blue
   and green, about 0.4 × 0.3 × 0.3 m), `crystal_ball_stand` (a glass orb on a clawed iron stand on a small round table,
   about 0.6 × 0.6 × 1.1 m).
4. **Throne room:** `throne_stone` (a high-backed carved stone throne on a two-step dais, about 1.4 × 1.4 × 2.4 m),
   `chandelier_iron` (an iron ring chandelier with eight candles on three chains from a short ceiling hook, about 1.4 m
   across, the ring about 2.6 m above the origin on the floor; anchors `light:*`), `candelabra_standing` (a floor
   candelabra of wrought iron with five candles, about 0.5 × 0.5 × 1.7 m; anchor `light:candle`), `carpet_runner` (a
   long red runner with a woven border, about 1.2 × 4 m, a centimetre or two high).
5. **Prison:** `cage_iron` (a riveted iron cage a person could crouch in, door ajar, about 1.2 × 1.2 × 1.6 m),
   `prison_bars_section` (a 1.5 m section of floor-to-lintel iron bars in a stone sill, about 2.4 m high, joins side by
   side), `prison_bars_door` (the matching section with a barred door and lock plate), `shackles_wall` (an iron ring
   plate with two chains and manacles for a wall, about 0.8 × 0.15 × 1 m).
6. **Punishment:** `stocks_wood` (a village pillory: two posts and a hinged board with head and hand holes on a low
   platform, about 1.6 × 1 × 1.6 m), `torture_rack` (a timber rack with rollers, ropes and a ratchet wheel, about 2.4 ×
   1 × 1 m), `gibbet_post` (a tall post with an arm and a hanging iron body cage, about 1.5 × 0.8 × 4 m), `gallows_wood`
   (a plank platform with steps, a beam and one noose, about 3 × 2.5 × 4 m; large: mind the timeout rule).

### Graveyard, mine and cave

Outdoor and underground sets asked for again and again in map-maker requests.

7. **Graveyard:** `gravestone_round` (a leaning round-topped headstone with a worn inscription and moss, about 0.6 × 0.2
   × 1 m), `gravestone_cross` (a stone cross on a stepped base, about 0.7 × 0.4 × 1.4 m), `grave_mound` (a fresh earth
   mound with a spade stuck in it, about 2 × 1 × 0.4 m), `fence_iron_cemetery` (a 1.5 m section of rusted spear-top
   railings between stone posts, about 1.3 m high, joins like `fence_wood`).
8. **Mine:** `mine_cart` (an iron-bound wooden ore cart on four flanged wheels, half full of ore, about 1.3 × 0.9 × 1
   m), `rail_track_straight` (a 1.5 m section of narrow rails on sleepers that joins end to end), `mine_support_timber`
   (a timber portal of two props and a cap beam with wedges, about 2.2 × 0.4 × 2.4 m), `ore_vein_rock` (a rock outcrop
   with glinting ore seams and a pickaxe leaning on it, about 1.2 × 1 × 1 m).
9. **Cave:** `crystal_cluster` (a cluster of tall faceted crystals growing from rock, faintly glowing, about 1 × 1 × 1.4
   m; anchor `light:crystal`), `stalagmites` (a group of four wet limestone stalagmites of different heights, about 1.2
   × 1.2 × 1.6 m), `mushroom_giant` (a giant cave toadstool with two smaller ones at its foot, about 1.5 × 1.5 × 2.2 m),
   `skeleton_remains` (a slumped human skeleton against a small rock with a rusted sword and a torn pack, about 1.2 ×
   0.8 × 0.7 m).

### Camp, crafts and food

What packs call survival, workshop and tavern props.

10. **Camp and travel:** `tent_canvas` (a ridge tent of patched canvas with one flap tied open and a bedroll visible
    inside, about 2.5 × 2 × 1.7 m), `wagon_covered` (a four-wheeled wagon with a canvas tilt on hoops and a draw pole,
    about 4 × 1.8 × 2.6 m; large: mind the timeout rule), `cooking_spit` (two forked stakes with a spit and a hanging
    pot over a small fire, about 1.2 × 0.6 × 1 m; anchors `fire:camp` and `light:fire`), `lantern_iron` (a hand lantern
    of iron and horn panes standing on the ground, about 0.2 × 0.2 × 0.4 m; anchor `light:lantern`).
11. **Smithy and crafts:** `forge_stone` (a blacksmith's stone forge with a hood, glowing coals and a bellows at the
    side, about 1.8 × 1.2 × 2.2 m; anchors `fire:hearth` and `light:fire`), `grindstone_wheel` (a sandstone wheel in a
    timber frame with a crank and a water trough, about 1 × 0.5 × 1 m), `loom_wood` (an upright weaving loom with a
    half-woven cloth and weights, about 1.4 × 0.6 × 1.8 m), `spinning_wheel` (a spinning wheel with a distaff of wool
    and a stool-height bench, about 1 × 0.5 × 1.1 m).
12. **Kitchen and food:** `oven_bread_stone` (a domed bread oven of plastered stone with an arched mouth and a peel
    leaning on it, about 1.5 × 1.5 × 1.6 m; anchors `fire:hearth` and `light:fire`), `food_platter` (a wooden board with
    a loaf, a cheese wedge, a ham and a knife, about 0.6 × 0.4 × 0.2 m), `kitchen_shelf_pots` (a wall shelf unit of
    copper pots, clay jars and hanging ladles, about 1.2 × 0.35 × 1.6 m), `vegetable_crates` (three shallow crates of
    cabbages, carrots and apples, about 1.2 × 0.8 × 0.5 m).
13. **Training yard:** `training_dummy` (a straw-stuffed sackcloth dummy on a post with a battered shield and a pot
    helm, about 0.9 × 0.5 × 1.9 m), `archery_target` (a round straw boss with painted rings on a timber tripod, two
    arrows in it, about 1.1 × 0.9 × 1.5 m), `shield_rack` (a timber rack holding three round painted shields, about 1.5
    × 0.4 × 1.2 m).

### Farm, harbour and landmarks

Village and world dressing that fills the most popular medieval kits.

14. **Farm:** `scarecrow` (a ragged scarecrow of straw and old clothes on a cross pole with a sack head and a hat, about
    1.6 × 0.4 × 2.1 m), `chicken_coop` (a small plank hen house on legs with a ramp and a thatched roof, about 1.5 × 1.2
    × 1.6 m), `water_trough` (a hollowed-log trough full of water on two blocks, about 1.8 × 0.5 × 0.5 m; anchor
    `water:basin` with size), `pumpkin_patch` (five pumpkins of different sizes among broad leaves and vines, about 1.5
    × 1.5 × 0.5 m), `plough_wood` (a wooden plough with an iron share and two handles, about 2.2 × 0.6 × 1 m).
15. **Harbour:** `fishing_nets_drying` (nets with cork floats hung over a pole frame to dry, about 2.5 × 0.8 × 2 m),
    `crane_dock_wood` (a small timber dock crane with a jib, rope, hook and a hand winch, about 2.5 × 1.5 × 3.5 m),
    `anchor_iron` (a large rusted iron anchor leaning on a coil of rope, about 1.2 × 0.8 × 1.5 m), `fish_crates` (two
    crates of silver fish and a wicker creel, about 1.2 × 0.8 × 0.5 m).
16. **Ruins and magic:** `ruin_arch_stone` (a broken free-standing stone arch with fallen blocks and ivy, about 3 × 1 ×
    3.5 m), `obelisk_rune` (a tall standing stone carved with faintly glowing runes, about 0.8 × 0.8 × 3 m; anchor
    `light:rune`), `portal_arch_stone` (a round stone ring gate on a stepped base with carved glyphs, empty inside,
    about 2.6 × 0.8 × 3 m; anchor `light:portal`), `shrine_roadside` (a small roofed wayside shrine on a stone post with
    a niche, a candle and flowers, about 0.6 × 0.5 × 1.8 m).
17. **Bridges and outbuildings:** `bridge_wood_small` (a plank footbridge with handrails on two trestles, about 4 × 1.6
    × 1.4 m, ends at ground level), `bridge_stone_arch` (a single-arch fieldstone bridge with low parapets, about 5 ×
    2.2 × 2 m, ends at ground level; large: mind the timeout rule), `ladder_wood` (a pole ladder with lashed rungs
    leaning as against a wall, about 0.6 × 1 × 3 m), `outhouse_wood` (a plank privy with a lean roof and a door with a
    cut crescent, about 1.1 × 1.1 × 2.2 m).
