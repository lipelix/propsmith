import { describe, expect, it } from "vitest";

import {
  assetSchema,
  parseAsset,
  parseTags,
  tagsProblems,
  vocabulary,
} from "./schema.ts";
import { assetJson, TAGS } from "./testing.ts";

const tags = parseTags(TAGS);

describe("assetSchema", () => {
  it("accepts a sound asset", () => {
    expect(parseAsset(assetJson("barrel_wood"), tags).id).toBe("barrel_wood");
  });

  it.each([
    ["an unknown field", { footprint: { w: 1 } }],
    ["a game fact", { gameplay: { blocks: true } }],
    ["a bad id", { id: "Barrel-Wood" }],
    ["an unknown category", { category: "tool" }],
    ["a weapon with no grip", { category: "weapon" }],
    ["a grip with no main hand", { grip: { points: ["off"], hand: 0.085 } }],
    [
      "an unknown grip point",
      { grip: { points: ["main", "tail"], hand: 0.085 } },
    ],
    [
      "repeated grip points",
      { grip: { points: ["main", "main"], hand: 0.085 } },
    ],
    ["a grip with no hand", { grip: { points: ["main"] } }],
    ["a grip for a giant's hand", { grip: { points: ["main"], hand: 0.3 } }],
    ["repeated tags", { tags: ["wood", "wood"] }],
    ["no variants", { variants: [] }],
    ["a variant of another asset", { variants: ["crate_wood"] }],
    ["a zero size", { size: { x: 0, y: 1, z: 1 } }],
    ["a size over 12 m", { size: { x: 1, y: 1, z: 13 } }],
    ["a size with extra axes", { size: { x: 1, y: 1, z: 1, w: 1 } }],
    ["a bad anchor", { anchors: ["glow:lamp"] }],
    ["repeated anchors", { anchors: ["light:lamp", "light:lamp"] }],
    ["an unknown mount", { mount: { kind: "floor", lift: 1 } }],
    ["a mount with no lift", { mount: { kind: "wall" } }],
    ["a mount with a zero lift", { mount: { kind: "ceiling", lift: 0 } }],
    ["a mount with extra fields", { mount: { kind: "wall", lift: 1, h: 2 } }],
    ["another licence", { licence: "MIT" }],
    ["an unknown provenance", { provenance: { source: "found" } }],
    [
      "a generated asset with no prompt",
      { provenance: { source: "generated" } },
    ],
    [
      "a pack asset with a bad url",
      { provenance: { source: "pack", pack: "p", packId: "1", url: "nope" } },
    ],
  ])("rejects %s", (_, over) => {
    expect(assetSchema.safeParse(assetJson("barrel_wood", over)).success).toBe(
      false,
    );
  });

  it("accepts suffixed variants, anchors and every provenance", () => {
    for (const provenance of [
      { source: "generated", prompt: "a barrel" },
      { source: "handwritten" },
      {
        source: "pack",
        pack: "kit",
        packId: "barrel",
        url: "https://x.test/k",
      },
    ])
      expect(
        parseAsset(
          assetJson("barrel_wood", {
            variants: ["barrel_wood", "barrel_wood_open"],
            anchors: ["light:lamp", "water:spout_1"],
            provenance,
          }),
          tags,
        ).variants,
      ).toEqual(["barrel_wood", "barrel_wood_open"]);
  });
});

describe("mount", () => {
  it("is optional and accepts a ceiling and a wall", () => {
    expect(parseAsset(assetJson("barrel_wood"), tags).mount).toBeUndefined();
    for (const mount of [
      { kind: "ceiling", lift: 2.3 },
      { kind: "wall", lift: 1.4 },
    ])
      expect(
        parseAsset(assetJson("barrel_wood", { mount }), tags).mount,
      ).toEqual(mount);
  });
});

describe("grip", () => {
  it("is optional and carries the points and the hand", () => {
    expect(parseAsset(assetJson("barrel_wood"), tags).grip).toBeUndefined();
    const grip = { points: ["main", "off", "stock", "trigger"], hand: 0.085 };
    expect(
      parseAsset(assetJson("barrel_wood", { category: "weapon", grip }), tags)
        .grip,
    ).toEqual(grip);
  });
});

describe("the vocabulary", () => {
  it("lists every tag", () => {
    expect([...vocabulary(tags)].sort()).toEqual(["stone", "village", "wood"]);
  });

  it("rejects a tag in two groups and a tag that names a category", () => {
    expect(
      tagsProblems({
        schema: 1,
        note: "",
        groups: { material: ["wood", "door"], look: ["wood"] },
      }),
    ).toEqual([
      'tag "door" repeats a category',
      'tag "wood" is in both "material" and "look"',
    ]);
    expect(() =>
      parseTags({ schema: 1, note: "", groups: { a: ["x"], b: ["x"] } }),
    ).toThrow(/both/);
  });

  it("rejects unknown tags and tags repeating the family or an alias", () => {
    expect(() =>
      parseAsset(assetJson("barrel_wood", { tags: ["oak"] }), tags),
    ).toThrow('barrel_wood: unknown tag "oak"');
    expect(() =>
      parseAsset(assetJson("wood_pile", { tags: ["wood"] }), tags),
    ).toThrow("repeats the family");
    expect(() =>
      parseAsset(
        assetJson("barrel_wood", { tags: ["stone"], aliases: ["Stone"] }),
        tags,
      ),
    ).toThrow("repeats an alias");
  });

  it("reports schema errors readably", () => {
    expect(() =>
      parseAsset(assetJson("barrel_wood", { name: "" }), tags),
    ).toThrow(/name/);
  });
});
