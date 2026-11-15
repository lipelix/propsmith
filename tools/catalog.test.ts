import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  buildIndex,
  declaredVariants,
  formatIndex,
  inputHash,
  sourceProblems,
  usedTextures,
} from "./catalog.ts";
import { assetJson, TAGS } from "./testing.ts";

let root: string;

function write(path: string, content: string): void {
  mkdirSync(dirname(join(root, path)), { recursive: true });
  writeFileSync(join(root, path), content);
}

function addAsset(
  id: string,
  over: Record<string, unknown> = {},
  py = `from propsmith import prop\n\n@prop\ndef ${id}():\n    pass\n`,
): void {
  write(`catalog/${id}/asset.json`, JSON.stringify(assetJson(id, over)));
  write(`catalog/${id}/asset.py`, py);
}

beforeEach(() => {
  root = mkdtempSync(join(tmpdir(), "propsmith-catalog-"));
  write("catalog/tags.json", JSON.stringify(TAGS));
  write("lib/propsmith/__init__.py", "VARIANTS = []\n");
  write("tools/blender/build.py", "# build\n");
});

afterEach(() => {
  rmSync(root, { recursive: true, force: true });
});

describe("buildIndex", () => {
  it("is empty for an empty catalogue", () => {
    expect(buildIndex(root).assets).toEqual([]);
  });

  it("sorts assets by id and normalises tags, aliases and anchors", () => {
    addAsset("well_stone", {
      tags: ["village", "stone"],
      aliases: ["wishing well", "water well"],
      anchors: ["water:basin", "light:lamp"],
    });
    addAsset("barrel_wood", {
      provenance: { source: "generated", prompt: "x" },
    });
    const index = buildIndex(root);
    expect(index.assets.map((a) => a.id)).toEqual([
      "barrel_wood",
      "well_stone",
    ]);
    const well = index.assets[1];
    expect(well?.tags).toEqual(["stone", "village"]);
    expect(well?.aliases).toEqual(["water well", "wishing well"]);
    expect(well?.anchors).toEqual(["light:lamp", "water:basin"]);
    expect(well?.source).toBe("handwritten");
    expect(index.assets[0]?.source).toBe("generated");
    expect(well?.inputHash).toMatch(/^[0-9a-f]{64}$/);
  });

  it("reports every problem at once", () => {
    addAsset("barrel_wood", {
      id: "barrel",
      variants: ["barrel"],
      family: "cask",
    });
    addAsset("crate_wood", { tags: ["oak"] });
    addAsset("well_stone", { variants: ["well_stone", "well_stone_dry"] });
    mkdirSync(join(root, "catalog/empty"));
    let message = "";
    try {
      buildIndex(root);
    } catch (error) {
      message = error instanceof Error ? error.message : "";
    }
    expect(message).toContain('barrel_wood: asset.json says id "barrel"');
    expect(message).toContain('unknown tag "oak"');
    expect(message).toContain("empty: needs both asset.json and asset.py");
    expect(message).toContain(
      "well_stone: asset.json lists variants [well_stone, well_stone_dry], asset.py registers [well_stone]",
    );
  });
});

describe("inputHash", () => {
  it("is stable, and changes with the asset, the library and the build script", () => {
    addAsset("barrel_wood");
    const before = inputHash(root, "barrel_wood");
    expect(inputHash(root, "barrel_wood")).toBe(before);
    write("catalog/barrel_wood/__pycache__/asset.pyc", "junk");
    write("catalog/barrel_wood/.DS_Store", "junk");
    expect(inputHash(root, "barrel_wood")).toBe(before);

    write("lib/propsmith/shapes.py", "def box(): pass\n");
    const lib = inputHash(root, "barrel_wood");
    expect(lib).not.toBe(before);
    write("tools/blender/build.py", "# build 2\n");
    const build = inputHash(root, "barrel_wood");
    expect(build).not.toBe(lib);
    write("catalog/barrel_wood/asset.py", "# changed\n");
    expect(inputHash(root, "barrel_wood")).not.toBe(build);
  });

  it("covers the texture ledger only for textured assets", () => {
    addAsset("barrel_wood");
    addAsset(
      "wall_stone",
      {},
      'from propsmith import prop\nm = texture("wall", "ambientcg:Rock1")\n\n@prop\ndef wall_stone():\n    pass\n',
    );
    const plain = inputHash(root, "barrel_wood");
    const textured = inputHash(root, "wall_stone");
    write("catalog/textures.json", '{"schema":1}');
    expect(inputHash(root, "barrel_wood")).toBe(plain);
    expect(inputHash(root, "wall_stone")).not.toBe(textured);
  });
});

describe("source scanning", () => {
  it("finds @prop variants in file order", () => {
    expect(
      declaredVariants(
        "@prop\ndef a():\n    pass\n\ndef helper():\n    pass\n\n@prop\ndef a_open():\n    pass\n",
      ),
    ).toEqual(["a", "a_open"]);
  });

  it("finds texture ids once each, sorted", () => {
    expect(
      usedTextures(
        'texture("a", "x:B")\nmaps("x:A")\ntexture(\'c\', \'x:B\', 2)\nmaterial("m", C)\n',
      ),
    ).toEqual(["x:A", "x:B"]);
  });
});

describe("sourceProblems", () => {
  it("accepts the library, math and random", () => {
    expect(
      sourceProblems(
        "import math\nimport random\nfrom propsmith import anchor, prop\nfrom propsmith.shapes import box\n\n@prop\ndef a():\n    box('a', (1, 1, 1), (0, 0, 0.5), None)\n",
      ),
    ).toEqual([]);
  });

  it("names imports and names that reach beyond the model", () => {
    expect(
      sourceProblems(
        "import os, math\nfrom urllib.request import urlopen\nimport bpy\nx = open('/etc/passwd')\ny = __import__('socket')\n",
      ),
    ).toEqual([
      'line 1: import of "os" (only math, random and propsmith)',
      'line 2: import of "urllib.request" (only math, random and propsmith)',
      'line 3: import of "bpy" (only math, random and propsmith)',
      'line 4: "open" is not allowed in an asset',
      'line 5: "__import__" is not allowed in an asset',
    ]);
  });

  it("fails the index for an asset that breaks the rule", () => {
    addAsset(
      "bad_wood",
      {},
      "import subprocess\nfrom propsmith import prop\n\n@prop\ndef bad_wood():\n    pass\n",
    );
    expect(() => buildIndex(root)).toThrow(
      'bad_wood/asset.py line 1: import of "subprocess"',
    );
  });
});

describe("formatIndex", () => {
  it("ends with a newline and round-trips", async () => {
    addAsset("barrel_wood");
    const index = buildIndex(root);
    const text = await formatIndex(index, root);
    expect(text.endsWith("}\n")).toBe(true);
    expect(JSON.parse(text)).toEqual(index);
  });
});
