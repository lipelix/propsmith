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

import { findBlender } from "./blender.ts";
import {
  buildAsset,
  buildJob,
  formatAssetJson,
  isCached,
  parseArgs,
  parseResult,
  record,
  reportAsset,
  selectAssets,
} from "./build.ts";
import { ROOT } from "./catalog.ts";
import { checkCatalog } from "./check.ts";
import { mergeMeasurements, readMeasurements } from "./measurements.ts";
import { assetJson, TAGS } from "./testing.ts";

let root: string;

function write(path: string, content: string): void {
  mkdirSync(dirname(join(root, path)), { recursive: true });
  writeFileSync(join(root, path), content);
}

const CRATE = (id: string, size = 0.8) => `from propsmith import prop
from propsmith.materials import material
from propsmith.shapes import box


@prop
def ${id}():
    box("crate", (${size}, ${size}, ${size}), (0, 0, ${size} / 2), material("crate_planks", (0.2, 0.12, 0.06)))
`;

function addAsset(
  id: string,
  over: Record<string, unknown> = {},
  py = CRATE(id),
): void {
  write(`catalog/${id}/asset.json`, JSON.stringify(assetJson(id, over)));
  write(`catalog/${id}/asset.py`, py);
}

beforeEach(() => {
  root = mkdtempSync(join(tmpdir(), "propsmith-build-"));
  write("catalog/tags.json", JSON.stringify(TAGS));
  write(".prettierrc.json", "{}");
});

afterEach(() => {
  rmSync(root, { recursive: true, force: true });
});

describe("arguments", () => {
  it("parses ids and options", () => {
    expect(
      parseArgs(["a", "--force", "--only", "a_open", "--allow-unchecked"]),
    ).toEqual({
      ids: ["a"],
      force: true,
      only: "a_open",
      allowUnchecked: true,
    });
    expect(() => parseArgs(["--only"])).toThrow("--only needs a variant id");
    expect(() => parseArgs(["--pack"])).toThrow("unknown option --pack");
  });

  it("selects the given assets, the owner of --only, or all", () => {
    addAsset("crate_wood");
    addAsset("crate_wood_big");
    const args = (ids: string[], only: string | null = null) => ({
      ids,
      only,
      force: false,
      allowUnchecked: false,
    });
    expect(selectAssets(root, args([]))).toEqual([
      "crate_wood",
      "crate_wood_big",
    ]);
    expect(selectAssets(root, args(["crate_wood"]))).toEqual(["crate_wood"]);
    expect(selectAssets(root, args([], "crate_wood_big_open"))).toEqual([
      "crate_wood_big",
    ]);
    expect(() => selectAssets(root, args(["nope"]))).toThrow('no asset "nope"');
    expect(() => selectAssets(root, args([], "barrel"))).toThrow(
      "no asset has this variant",
    );
  });
});

describe("the job", () => {
  it("carries the asset's size and variants, and refuses a foreign variant", () => {
    addAsset("crate_wood", { size: { x: 1, y: 2, z: 3 } });
    const job = buildJob(root, "crate_wood");
    expect(job.asset.size).toEqual({ x: 1, y: 2, z: 3 });
    expect(job.asset.variants).toEqual(["crate_wood"]);
    expect(job.out).toBe(join(root, ".cache/assets/crate_wood"));
    expect(() => buildJob(root, "crate_wood", { only: "x" })).toThrow(
      'no variant "x"',
    );
    expect(() => buildJob(root, "nope")).toThrow(
      "nope: no catalog/nope/asset.json",
    );
  });

  it("reuses a cache only for the same inputs and the same or a fuller build", () => {
    addAsset("crate_wood");
    const job = buildJob(root, "crate_wood");
    const result = parseResult({
      schema: 1,
      id: "crate_wood",
      inputHash: job.inputHash,
      only: null,
      libVersion: 1,
      blender: "5.2.0",
      variants: [
        {
          id: "crate_wood",
          tris: 12,
          bbox: { min: [-0.4, -0.4, 0], max: [0.4, 0.4, 0.8] },
          origin: [0, 0, 0],
          nonManifoldEdges: 0,
          materials: [],
          anchors: [],
          textures: [],
          glb: "crate_wood.glb",
          review: { iso: "i.png", top: "t.png", front: "f.png" },
          seconds: 1,
        },
      ],
    });
    expect(isCached(job, result)).toBe(true);
    expect(isCached(job, { ...result, only: "crate_wood" })).toBe(false);
    expect(isCached(job, { ...result, inputHash: "0".repeat(64) })).toBe(false);
    expect(isCached(job, undefined)).toBe(false);
  });
});

describe("formatAssetJson", () => {
  it("rewrites asset.json in Prettier's layout once", async () => {
    addAsset("crate_wood");
    expect(await formatAssetJson(root, "crate_wood")).toBe(true);
    const text = readFileSync(
      join(root, "catalog/crate_wood/asset.json"),
      "utf8",
    );
    expect(text).toContain('\n  "id": "crate_wood",\n');
    expect(await formatAssetJson(root, "crate_wood")).toBe(false);
    expect(await formatAssetJson(root, "nope")).toBe(false);
  });
});

describe("measurements", () => {
  it("merges sorted and drops assets that left the catalogue", () => {
    const m = (hash: string) => ({
      inputHash: hash.repeat(64),
      libVersion: 1,
      blender: "5.2.0",
      variants: [
        {
          id: "x",
          tris: 1,
          bbox: {
            min: [0, 0, 0] as [number, number, number],
            max: [1, 1, 1] as [number, number, number],
          },
          origin: [0, 0, 0] as [number, number, number],
          nonManifoldEdges: 0,
          materials: [],
          anchors: [],
          textures: [],
        },
      ],
    });
    const merged = mergeMeasurements(
      { schema: 1, note: "", assets: { b: m("1"), gone: m("2") } },
      [
        { id: "a", measured: m("3") },
        { id: "b", measured: m("4") },
      ],
      new Set(["a", "b"]),
    );
    expect(Object.keys(merged.assets)).toEqual(["a", "b"]);
    expect(merged.assets.b?.inputHash).toBe("4".repeat(64));
  });
});

describe("catalogue check without Blender", () => {
  it("is NOT CHECKED for an asset with no committed measurement, and wants a fresh index", async () => {
    addAsset("crate_wood");
    const { reports, problems } = await checkCatalog(root);
    expect(problems).toEqual([
      "catalog/index.json is out of date: run npm run catalog",
    ]);
    expect(reports[0]?.checks[0]).toEqual({
      id: "bounds-fit",
      status: "NOT CHECKED",
      detail: "no committed measurement: run npm run build -- crate_wood",
    });
  });

  it("passes the committed catalogue", async () => {
    const { reports, problems } = await checkCatalog(ROOT);
    expect(problems).toEqual([]);
    expect(reports.length).toBeGreaterThan(0);
    for (const report of reports)
      for (const check of report.checks)
        expect(`${report.id} ${check.id} ${check.status}`).toBe(
          `${report.id} ${check.id} OK`,
        );
  });
});

describe.skipIf(findBlender() === undefined)("Blender build", () => {
  beforeEach(() => {
    // The input hash and the build read the library and the build script from the root they are given.
    cpSync(join(ROOT, "lib"), join(root, "lib"), { recursive: true });
    cpSync(join(ROOT, "tools/blender"), join(root, "tools/blender"), {
      recursive: true,
    });
  });

  it("builds, measures in metres, records and then checks from the committed measurement", async () => {
    addAsset(
      "lamp_test",
      { anchors: ["light:lamp"], closed: true },
      `from propsmith import anchor, prop
from propsmith.materials import material
from propsmith.shapes import box


@prop
def lamp_test():
    box("post", (0.2, 0.4, 0.9), (0, 0, 0.45), material("lamp_post", (0.1, 0.1, 0.1)), bevel=0)
    anchor("light:lamp", (0, -0.1, 0.8))
`,
    );
    const built = buildAsset(root, "lamp_test");
    expect(built.cached).toBe(false);
    const v = built.result.variants[0];
    expect(v?.bbox).toEqual({ min: [-0.1, -0.2, 0], max: [0.1, 0.2, 0.9] });
    expect(v?.tris).toBe(12);
    expect(v?.nonManifoldEdges).toBe(0);
    expect(v?.anchors).toEqual([{ name: "light:lamp", at: [0, -0.1, 0.8] }]);
    expect(v?.materials).toEqual([{ name: "lamp_post", source: "palette" }]);
    const out = join(root, ".cache/assets/lamp_test");
    for (const file of [v?.glb, v?.review.iso, v?.review.top, v?.review.front])
      expect(existsSync(join(out, file ?? "missing"))).toBe(true);

    const report = reportAsset(root, "lamp_test", built);
    expect(report.checks.map((c) => c.status)).toEqual(Array(7).fill("OK"));
    expect(buildAsset(root, "lamp_test").cached).toBe(true);

    await record(root, [{ id: "lamp_test", built }]);
    expect(Object.keys(readMeasurements(root).assets)).toEqual(["lamp_test"]);
    const checked = await checkCatalog(root);
    expect(checked.problems).toEqual([]);
    expect(checked.reports[0]?.checks.every((c) => c.status === "OK")).toBe(
      true,
    );

    // A changed asset makes the committed measurement stale.
    write("catalog/lamp_test/asset.py", CRATE("lamp_test"));
    const stale = await checkCatalog(root);
    expect(stale.reports[0]?.checks[0]?.detail).toBe(
      "the committed measurement is stale: run npm run build -- lamp_test",
    );
  }, 120_000);

  it("fails checks a model breaks, and a Python error with the traceback", () => {
    addAsset("crate_wood", { size: { x: 0.5, y: 0.5, z: 0.5 } });
    const report = reportAsset(
      root,
      "crate_wood",
      buildAsset(root, "crate_wood"),
    );
    expect(report.checks[0]?.status).toBe("FAILED");
    expect(report.checks[0]?.detail).toContain("height 0.8 over 0.5 m");

    addAsset(
      "bad_wood",
      {},
      "from propsmith import prop\n\n\n@prop\ndef bad_wood():\n    raise RuntimeError('boom')\n",
    );
    expect(() => buildAsset(root, "bad_wood")).toThrow(/boom/);
  }, 120_000);
});
