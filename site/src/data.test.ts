import { describe, expect, it } from "vitest";

import { type Asset, hangs, holds, type Variant } from "./data.ts";

const variant: Variant = {
  id: "chandelier_iron",
  glb: "a.glb",
  png: "a.png",
  glbBytes: 1,
  tris: 1,
  measured: { x: 1.4, y: 1.4, z: 1.3 },
  grips: [],
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

describe("holds", () => {
  it("is null for a prop nobody holds", () => {
    expect(holds(asset(), variant)).toBeNull();
  });

  it("says how many hands, how far apart, and the other points", () => {
    const crossbow: Asset = {
      ...asset(),
      grip: { points: ["main", "off", "stock", "trigger"], hand: 0.085 },
    };
    const held: Variant = {
      ...variant,
      grips: [
        { name: "main", at: [0, 0, 0.1], axis: [0, 0, 1], radius: 0.016 },
        { name: "off", at: [0.3, 0, 0.5], axis: [1, 0, 0], radius: 0.03 },
        { name: "stock", at: [-0.4, 0, 0.1] },
        { name: "trigger", at: [0.05, 0, 0.05] },
      ],
    };
    expect(holds(crossbow, held)).toBe(
      "two hands, 0.5 m apart on a 3.2 cm handle; stock and trigger points (for a hand 0.085 m across)",
    );
    const sling: Asset = {
      ...asset(),
      grip: { points: ["main"], hand: 0.085 },
    };
    expect(holds(sling, { ...variant, grips: [held.grips[0] as never] })).toBe(
      "one hand on a 3.2 cm handle (for a hand 0.085 m across)",
    );
  });
});
