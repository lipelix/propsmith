import { describe, expect, it } from "vitest";

import { isSnake, isVariantOf } from "./ids.ts";

describe("isSnake", () => {
  it.each(["barrel", "barrel_wood", "wall_2x1", "m3"])("accepts %s", (id) => {
    expect(isSnake(id)).toBe(true);
  });

  it.each(["", "Barrel", "barrel-wood", "_barrel", "barrel_", "a__b", "3d"])(
    "rejects %j",
    (id) => {
      expect(isSnake(id)).toBe(false);
    },
  );
});

describe("isVariantOf", () => {
  it("accepts the asset id and suffixed ids", () => {
    expect(isVariantOf("barrel_wood", "barrel_wood")).toBe(true);
    expect(isVariantOf("barrel_wood_open", "barrel_wood")).toBe(true);
  });

  it("rejects other assets and bad ids", () => {
    expect(isVariantOf("barrel_woody", "barrel_wood")).toBe(false);
    expect(isVariantOf("crate_wood", "barrel_wood")).toBe(false);
    expect(isVariantOf("barrel_wood_Open", "barrel_wood")).toBe(false);
  });
});
