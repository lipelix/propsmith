import { describe, expect, it } from "vitest";

import { type Asset, count, join, kilobytes, metres } from "./data.ts";
import {
  categoryFacets,
  EMPTY,
  filter,
  matches,
  tagFacets,
  toggleTag,
} from "./search.ts";

function asset(id: string, over: Partial<Asset> = {}): Asset {
  return {
    id,
    name: id,
    description: "",
    category: "decor",
    family: id.split("_")[0] ?? id,
    tags: [],
    aliases: [],
    size: { x: 1, y: 1, z: 1 },
    anchors: [],
    closed: false,
    source: "generated",
    licence: "CC0-1.0",
    variants: [],
    ...over,
  };
}

const barrel = asset("barrel_wood", {
  name: "Wooden barrel",
  category: "container",
  tags: ["wood", "iron", "storage"],
  aliases: ["cask", "keg"],
});
const well = asset("well_stone", {
  name: "Stone well",
  description: "A round drystone well with a plank roof.",
  category: "structure",
  tags: ["stone", "wood", "water"],
});
const lamp = asset("lamp_post", {
  name: "Street lamp post",
  category: "light",
  tags: ["wood", "iron", "lighting"],
});
const all = [barrel, well, lamp];

describe("search", () => {
  it("matches every word as a prefix, in names, descriptions, tags and aliases", () => {
    expect(matches(barrel, { ...EMPTY, text: "cask" })).toBe(true);
    expect(matches(barrel, { ...EMPTY, text: "Wood BAR" })).toBe(true);
    expect(matches(barrel, { ...EMPTY, text: "arrel" })).toBe(false);
    expect(matches(well, { ...EMPTY, text: "drystone roof" })).toBe(true);
    expect(matches(well, { ...EMPTY, text: "stone iron" })).toBe(false);
    expect(filter(all, { ...EMPTY, text: "  " })).toEqual(all);
  });

  it("narrows by one category and by every tag", () => {
    expect(filter(all, { ...EMPTY, category: "light" })).toEqual([lamp]);
    expect(filter(all, { ...EMPTY, tags: ["wood", "iron"] })).toEqual([
      barrel,
      lamp,
    ]);
    expect(
      filter(all, { text: "lamp", category: "container", tags: [] }),
    ).toEqual([]);
  });

  it("counts categories without the category filter, and tags within the results", () => {
    const query = { ...EMPTY, category: "light", tags: ["iron"] };
    expect(categoryFacets(all, query)).toEqual([
      { value: "container", count: 1, selected: false },
      { value: "light", count: 1, selected: true },
      { value: "structure", count: 0, selected: false },
    ]);
    const facets = tagFacets(all, query, {
      wood: "material",
      iron: "material",
    });
    expect(facets.material).toEqual([
      { value: "iron", count: 1, selected: true },
      { value: "wood", count: 1, selected: false },
    ]);
    expect(facets.other?.map((f) => `${f.value}:${f.count}`)).toEqual([
      "lighting:1",
      "stone:0",
      "storage:0",
      "water:0",
    ]);
  });

  it("toggles a tag on and off", () => {
    const on = toggleTag(EMPTY, "wood");
    expect(on.tags).toEqual(["wood"]);
    expect(toggleTag(on, "wood").tags).toEqual([]);
  });
});

describe("catalogue data", () => {
  const index = {
    assets: [
      { ...barrel, variants: ["barrel_wood", "barrel_wood_open"] },
      { ...well, variants: ["well_stone"] },
    ],
  };
  const measured = (id: string) => ({
    id,
    tris: 6936,
    bbox: { min: [-0.319, -0.319, 0], max: [0.319, 0.319, 0.9012] },
  });
  const baked = (id: string) => ({
    id,
    glb: `barrel_wood/${id}.glb`,
    png: `barrel_wood/${id}.png`,
    glbBytes: 639360,
  });

  it("joins index, measurements and bake manifest; leaves out what is not baked", () => {
    const catalogue = join(
      index,
      {
        assets: {
          barrel_wood: {
            variants: [measured("barrel_wood"), measured("barrel_wood_open")],
          },
          well_stone: { variants: [measured("well_stone")] },
        },
      },
      { assets: { barrel_wood: { variants: [baked("barrel_wood")] } } },
      { groups: { material: ["wood", "iron"] } },
    );
    expect(catalogue.assets.map((a) => a.id)).toEqual(["barrel_wood"]);
    expect(catalogue.assets[0]?.variants).toEqual([
      {
        ...baked("barrel_wood"),
        tris: 6936,
        measured: { x: 0.64, y: 0.64, z: 0.9 },
        grips: [],
      },
    ]);
    expect(catalogue.tagGroups).toEqual({ wood: "material", iron: "material" });
  });

  it("formats sizes, counts and bytes", () => {
    expect(metres({ x: 0.64, y: 0.64, z: 0.9 })).toBe("0.64 × 0.64 × 0.9 m");
    expect(count(6936)).toBe("6.9k");
    expect(count(820)).toBe("820");
    expect(kilobytes(639360)).toBe("625 KB");
  });
});
