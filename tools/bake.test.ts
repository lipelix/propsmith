import {
  cpSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { BAKE, bakeAsset, buildManifest, parseArgs } from "./bake.ts";
import { findBlender } from "./blender.ts";
import { ROOT } from "./catalog.ts";
import { assetJson, TAGS } from "./testing.ts";

let root: string;

function write(path: string, content: string): void {
  mkdirSync(dirname(join(root, path)), { recursive: true });
  writeFileSync(join(root, path), content);
}

/** The JSON chunk of a binary glTF. */
function gltf(path: string): {
  materials: Record<string, unknown>[];
  images: { mimeType: string }[];
  meshes: { primitives: { attributes: Record<string, number> }[] }[];
  nodes: { name: string }[];
} {
  const data = readFileSync(path);
  expect(data.toString("latin1", 0, 4)).toBe("glTF");
  const length = data.readUInt32LE(12);
  return JSON.parse(data.subarray(20, 20 + length).toString("utf8"));
}

beforeEach(() => {
  root = mkdtempSync(join(tmpdir(), "propsmith-bake-"));
  write("catalog/tags.json", JSON.stringify(TAGS));
  write(".prettierrc.json", "{}");
});

afterEach(() => {
  rmSync(root, { recursive: true, force: true });
});

describe("bake arguments and manifest", () => {
  it("parses ids and --force", () => {
    expect(parseArgs(["a", "--force"])).toEqual({ ids: ["a"], force: true });
    expect(() => parseArgs(["--only"])).toThrow("unknown option --only");
  });

  it("lists nothing for a catalogue with no baked asset", () => {
    write(
      "catalog/crate_wood/asset.json",
      JSON.stringify(assetJson("crate_wood")),
    );
    expect(buildManifest(root).assets).toEqual({});
  });
});

describe.skipIf(findBlender() === undefined)("Blender bake", () => {
  beforeEach(() => {
    cpSync(join(ROOT, "lib"), join(root, "lib"), { recursive: true });
    cpSync(join(ROOT, "tools/blender"), join(root, "tools/blender"), {
      recursive: true,
    });
  });

  it("exports one plain PBR material on baked images, with the anchors, and lists it in the manifest", () => {
    write(
      "catalog/lamp_test/asset.json",
      JSON.stringify(
        assetJson("lamp_test", { anchors: ["light:lamp"], closed: true }),
      ),
    );
    write(
      "catalog/lamp_test/asset.py",
      `from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import box, cylinder


@prop
def lamp_test():
    box("post", (0.2, 0.2, 0.8), (0, 0, 0.4), material("lamp_wood", (0.2, 0.12, 0.06)))
    cylinder("cap", 0.15, 0.1, (0, 0, 0.8), material("lamp_iron", (0.05, 0.05, 0.05), metal=0.8))
    anchor("light:lamp", (0, 0, 0.95))
`,
    );
    const baked = bakeAsset(root, "lamp_test");
    expect(baked.cached).toBe(false);
    expect(baked.result.resolution).toBe(BAKE.resolution);
    expect(baked.result.variants[0]?.materials).toBe(2);

    const out = join(root, "dist/catalog/lamp_test");
    expect(existsSync(join(out, "lamp_test.png"))).toBe(true);
    const model = gltf(join(out, "lamp_test.glb"));
    expect(model.materials).toHaveLength(1);
    const material = model.materials[0] as {
      normalTexture?: unknown;
      pbrMetallicRoughness: Record<string, unknown>;
    };
    expect(material.normalTexture).toBeDefined();
    expect(material.pbrMetallicRoughness.baseColorTexture).toBeDefined();
    expect(
      material.pbrMetallicRoughness.metallicRoughnessTexture,
    ).toBeDefined();
    expect(model.images.map((i) => i.mimeType)).toEqual(
      Array(3).fill("image/jpeg"),
    );
    expect(model.meshes[0]?.primitives).toHaveLength(1);
    expect(model.meshes[0]?.primitives[0]?.attributes.TEXCOORD_0).toBeDefined();
    expect(model.nodes.map((n) => n.name).sort()).toEqual([
      "lamp_test",
      "light:lamp",
    ]);

    const manifest = buildManifest(root);
    const variant = manifest.assets.lamp_test?.variants[0];
    expect(variant?.glb).toBe("lamp_test/lamp_test.glb");
    expect(variant?.png).toBe("lamp_test/lamp_test.png");
    expect(variant?.glbSha256).toMatch(/^[0-9a-f]{64}$/);
    expect(variant?.glbBytes).toBeGreaterThan(10_000);
    expect(bakeAsset(root, "lamp_test").cached).toBe(true);
  }, 180_000);

  it("refuses an asset that fails a check", () => {
    write(
      "catalog/crate_wood/asset.json",
      JSON.stringify(
        assetJson("crate_wood", { size: { x: 0.5, y: 0.5, z: 0.5 } }),
      ),
    );
    write(
      "catalog/crate_wood/asset.py",
      `from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box


@prop
def crate_wood():
    box("crate", (0.8, 0.8, 0.8), (0, 0, 0.4), material("crate_planks", (0.2, 0.12, 0.06)))
`,
    );
    expect(() => bakeAsset(root, "crate_wood")).toThrow(
      "crate_wood: not baked, bounds-fit is FAILED",
    );
  }, 120_000);
});
