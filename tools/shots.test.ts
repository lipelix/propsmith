import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { findBlender } from "./blender.ts";
import { ROOT } from "./catalog.ts";
import {
  parseShotsArgs,
  prMarkdown,
  RAW_BASE,
  SHOTS_DIR,
  shootAsset,
} from "./shots.ts";

/** Width and height of a PNG from its IHDR chunk. */
function pngSize(path: string): [number, number] {
  const b = readFileSync(path);
  return [b.readUInt32BE(16), b.readUInt32BE(20)];
}

describe("parseShotsArgs", () => {
  it("takes ids, a size and a push slug", () => {
    expect(
      parseShotsArgs(["a", "b", "--size", "512", "--push", "crypt-props"]),
    ).toEqual({ ids: ["a", "b"], size: 512, push: "crypt-props" });
    expect(parseShotsArgs(["a"])).toEqual({
      ids: ["a"],
      size: 1024,
      push: null,
    });
  });

  it("refuses what it cannot use", () => {
    expect(() => parseShotsArgs([])).toThrow(/at least one/);
    expect(() => parseShotsArgs(["a", "--size", "12"])).toThrow(/--size/);
    expect(() => parseShotsArgs(["a", "--push", "Bad Slug"])).toThrow(/--push/);
    expect(() => parseShotsArgs(["a", "--nope"])).toThrow(/unknown option/);
  });
});

describe("prMarkdown", () => {
  it("puts one row per variant under the section heading", () => {
    const md = prMarkdown("crypt", ["urn_funeral", "urn_funeral_open"]);
    expect(md.startsWith("## What it looks like\n")).toBe(true);
    expect(md).toContain(`${RAW_BASE}/crypt/urn_funeral_iso.png`);
    expect(md).toContain(`${RAW_BASE}/crypt/urn_funeral_open_front.png`);
    expect(md.split("\n").filter((l) => l.startsWith("| <img"))).toHaveLength(
      2,
    );
  });
});

describe.skipIf(findBlender() === undefined)("Blender shots", () => {
  it("frames a small asset to fill the picture", async () => {
    const variants = await shootAsset(ROOT, "candles_melted", 256);
    expect(variants).toEqual(["candles_melted"]);
    for (const view of ["iso", "front"]) {
      const [w, h] = pngSize(
        join(ROOT, SHOTS_DIR, "candles_melted", `candles_melted_${view}.png`),
      );
      expect(Math.max(w, h)).toBe(256);
    }
  }, 120_000);
});
