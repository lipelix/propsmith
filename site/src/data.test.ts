import { describe, expect, it } from "vitest";

import { type Asset, hangs, type Variant } from "./data.ts";

const variant: Variant = {
  id: "chandelier_iron",
  glb: "a.glb",
  png: "a.png",
  glbBytes: 1,
  tris: 1,
  measured: { x: 1.4, y: 1.4, z: 1.3 },
};
const asset = (mount?: Asset["mount"]): Asset => ({
  id: "chandelier_iron",
  name: "Chandelier",
  description: "",
  category: "light",
  family: "chandelier",
  tags: [],
  aliases: [],
  size: { x: 1.4, y: 1.4, z: 1.3 },
  anchors: [],
  closed: true,
  ...(mount === undefined ? {} : { mount }),
  source: "generated",
  licence: "CC0-1.0",
  variants: [variant],
});

describe("hangs", () => {
  it("is null for a prop that stands on the floor", () => {
    expect(hangs(asset(), variant)).toBeNull();
  });

  it("says how far to raise a hanging prop and where", () => {
    expect(hangs(asset({ kind: "ceiling", lift: 2.3 }), variant)).toBe(
      "from a ceiling by its top, raised 2.3 m (the ceiling at 3.6 m)",
    );
    expect(hangs(asset({ kind: "wall", lift: 1.4 }), variant)).toBe(
      "on a wall by its back, raised 1.4 m",
    );
  });
});
