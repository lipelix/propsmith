import { describe, expect, it } from "vitest";

import {
  anchorsDeclared,
  boundsFit,
  CHECK_IDS,
  deltaLine,
  exitCode,
  formatReport,
  gripPoints,
  manifold,
  materialsKnown,
  originGround,
  runChecks,
  summary,
  tally,
  triBudget,
} from "./checks.ts";
import type { Measured, MeasuredVariant } from "./measurements.ts";
import { parseAsset, parseTags } from "./schema.ts";
import { assetJson, TAGS } from "./testing.ts";

const tags = parseTags(TAGS);
const asset = (over: Record<string, unknown> = {}) =>
  parseAsset(assetJson("barrel_wood", over), tags);

function variant(over: Partial<MeasuredVariant> = {}): MeasuredVariant {
  return {
    id: "barrel_wood",
    tris: 1200,
    bbox: { min: [-0.3, -0.3, 0], max: [0.3, 0.3, 0.9] },
    origin: [0, 0, 0],
    nonManifoldEdges: 0,
    materials: [{ name: "barrel_staves", source: "palette" }],
    anchors: [],
    textures: [],
    ...over,
  };
}
const measured = (...variants: MeasuredVariant[]): Measured => ({
  only: null,
  variants: variants.length > 0 ? variants : [variant()],
});

describe("bounds-fit", () => {
  it("passes inside the declared size, with slack sideways only", () => {
    const m = measured(
      variant({ bbox: { min: [-0.57, -0.5, 0], max: [0.57, 0.5, 1] } }),
    );
    expect(boundsFit(asset(), m).status).toBe("OK");
  });

  it("names the axis and the variant that sticks out", () => {
    const m = measured(
      variant({ bbox: { min: [-0.6, -0.3, 0], max: [0.3, 0.7, 1.01] } }),
    );
    const check = boundsFit(asset(), m);
    expect(check.status).toBe("FAILED");
    expect(check.detail).toBe(
      "barrel_wood: x -0.6..0.3 outside ±0.5 m; barrel_wood: y -0.3..0.7 outside ±0.5 m; barrel_wood: height 1.01 over 1 m",
    );
  });
});

describe("origin-ground", () => {
  it.each([
    [{ origin: [0.1, 0, 0] }, "origin at 0.1, 0, 0"],
    [{ bbox: { min: [0, 0, 0.02], max: [0, 0, 1] } }, "floats 0.02 m"],
    [{ bbox: { min: [0, 0, -0.05], max: [0, 0, 1] } }, "sinks 0.05 m"],
  ] as const)("fails %j", (over, detail) => {
    const check = originGround(
      asset(),
      measured(variant(over as Partial<MeasuredVariant>)),
    );
    expect(check.status).toBe("FAILED");
    expect(check.detail).toContain(detail);
  });

  it("tolerates rounding", () => {
    const m = measured(
      variant({ bbox: { min: [0, 0, 0.007], max: [0, 0, 1] } }),
    );
    expect(originGround(asset(), m).status).toBe("OK");
  });

  it("says where a hanging prop hangs", () => {
    const m = measured(
      variant({ bbox: { min: [-0.5, -0.5, 0], max: [0.5, 0.2, 1.3] } }),
    );
    const ceiling = originGround(
      asset({ mount: { kind: "ceiling", lift: 2.3 } }),
      m,
    );
    expect(ceiling.status).toBe("OK");
    expect(ceiling.detail).toBe(
      "origin at the centre of the base, standing on the ground; hung 2.3 m up, its top meets a ceiling at 3.6 m",
    );
    expect(
      originGround(asset({ mount: { kind: "wall", lift: 1.4 } }), m).detail,
    ).toContain("; hung 1.4 m up on a wall at y 0.2");
  });

  it("still fails a hanging prop that floats", () => {
    const m = measured(
      variant({ bbox: { min: [0, 0, 0.5], max: [0, 0, 1.3] } }),
    );
    expect(
      originGround(asset({ mount: { kind: "ceiling", lift: 2.3 } }), m).status,
    ).toBe("FAILED");
  });
});

describe("tri-budget and manifold", () => {
  it("holds the budget per variant", () => {
    expect(triBudget(measured(variant({ tris: 8000 }))).status).toBe("OK");
    const over = triBudget(
      measured(variant(), variant({ id: "barrel_wood_open", tris: 8001 })),
    );
    expect(over.status).toBe("FAILED");
    expect(over.detail).toBe("barrel_wood_open: 8,001 tris > 8,000");
  });

  it("needs a closed mesh only when the asset is declared closed", () => {
    const open = measured(variant({ nonManifoldEdges: 12 }));
    expect(manifold(asset(), open).status).toBe("OK");
    const check = manifold(asset({ closed: true }), open);
    expect(check.status).toBe("FAILED");
    expect(check.detail).toContain("12 non-manifold edges");
  });
});

describe("materials-known", () => {
  const ledger = new Set(["ambientcg:Wood049"]);

  it("accepts palette and ledger materials", () => {
    const m = measured(
      variant({
        materials: [
          { name: "a", source: "palette" },
          { name: "b", source: "ledger:ambientcg:Wood049" },
        ],
        textures: ["ambientcg:Wood049"],
      }),
    );
    expect(materialsKnown(m, ledger).status).toBe("OK");
  });

  it("fails a hand-made material and a texture outside the ledger", () => {
    const m = measured(
      variant({
        materials: [
          { name: "raw", source: null },
          { name: "b", source: "ledger:ambientcg:Nope" },
        ],
      }),
    );
    const check = materialsKnown(m, ledger);
    expect(check.status).toBe("FAILED");
    expect(check.detail).toContain('material "raw" is not from the palette');
    expect(check.detail).toContain(
      'texture "ambientcg:Nope" is not in the ledger',
    );
  });

  it("is NOT CHECKED when textures are used and there is no ledger", () => {
    const m = measured(variant({ textures: ["ambientcg:Wood049"] }));
    expect(materialsKnown(m, null).status).toBe("NOT CHECKED");
    expect(materialsKnown(measured(), null).status).toBe("OK");
  });
});

describe("anchors-declared", () => {
  it("fails missing, undeclared and unsized anchors", () => {
    const m = measured(
      variant({
        anchors: [
          { name: "fire:hearth", at: [0, 0, 0.3] },
          { name: "smoke:flue", at: [0, 0, 2] },
        ],
      }),
    );
    const check = anchorsDeclared(
      asset({ anchors: ["fire:hearth", "light:lamp"] }),
      m,
    );
    expect(check.status).toBe("FAILED");
    expect(check.detail).toBe(
      "barrel_wood: declared anchor light:lamp is missing; barrel_wood: anchor smoke:flue is not declared in asset.json; barrel_wood: anchor fire:hearth needs a size (anchor(..., size=...))",
    );
  });

  it("passes declared anchors with sizes", () => {
    const m = measured(
      variant({
        anchors: [
          { name: "fire:hearth", at: [0, 0, 0.3], size: [0.2, 0.2, 0.4] },
        ],
      }),
    );
    expect(anchorsDeclared(asset({ anchors: ["fire:hearth"] }), m).status).toBe(
      "OK",
    );
  });
});

describe("grip-points", () => {
  const weapon = (points: string[]) =>
    asset({ category: "weapon", grip: { points, hand: 0.085 } });
  const hand = (name: string, z: number, over = {}) => ({
    name,
    at: [0, 0, z] as [number, number, number],
    axis: [0, 0, 1] as [number, number, number],
    radius: 0.016,
    ...over,
  });

  it("passes a prop with no grips", () => {
    expect(gripPoints(asset(), measured()).detail).toBe(
      "no grip points, none declared",
    );
  });

  it("passes two hands on a handle along +z", () => {
    const m = measured(
      variant({
        grips: [hand("main", 0.3), hand("off", 0.15, { radius: 0.018 })],
      }),
    );
    const check = gripPoints(weapon(["main", "off"]), m);
    expect(check.status).toBe("OK");
    expect(check.detail).toBe(
      "main, off in every variant, hands on handles of 0.016–0.018 m radius",
    );
  });

  it("fails missing and undeclared grips, a hand off its handle, a lean and hands too close", () => {
    const m = measured(
      variant({
        grips: [
          hand("main", 0.3, { axis: [1, 0, 0] }),
          hand("off", 0.25, { radius: null }),
          { name: "trigger", at: [0, 0, 0.1] },
        ],
      }),
    );
    const check = gripPoints(weapon(["main", "off", "stock"]), m);
    expect(check.status).toBe("FAILED");
    expect(check.detail).toBe(
      "barrel_wood: declared grip stock is missing; barrel_wood: grip trigger is not declared in asset.json; barrel_wood: grip off is not inside a handle; barrel_wood: grip main's handle leans 90° off +z, over 45°; barrel_wood: the hands are 0.05 m apart, under a hand's breadth (0.085 m)",
    );
  });

  it("fails a handle too thick for a hand", () => {
    const m = measured(
      variant({ grips: [hand("main", 0.3, { radius: 0.05 })] }),
    );
    expect(gripPoints(weapon(["main"]), m).detail).toBe(
      "barrel_wood: grip main's handle is 0.05 m in radius, over 0.04 for a hand",
    );
  });
});

describe("the report", () => {
  it("is NOT CHECKED everywhere without a build, with the reason given", () => {
    const checks = runChecks({
      asset: asset(),
      result: null,
      ledger: null,
      noResult: "no committed measurement",
    });
    expect(checks.map((c) => c.id)).toEqual([...CHECK_IDS]);
    expect(checks.every((c) => c.status === "NOT CHECKED")).toBe(true);
    expect(checks[0]?.detail).toBe("no committed measurement");
    expect(exitCode([{ checks }])).toBe(1);
    expect(exitCode([{ checks }], true)).toBe(0);
  });

  it("prints a delta line and one line per check", () => {
    const result = measured(variant({ tris: 3084 }));
    const checks = runChecks({ asset: asset(), result, ledger: null });
    const report = {
      id: "barrel_wood",
      checks,
      result,
      cached: false,
      seconds: 4.04,
    };
    expect(deltaLine(report)).toBe(
      "barrel_wood: 1 variant, 3.1k tris, 0.6×0.6×0.9 m, 4.0 s",
    );
    expect(deltaLine({ ...report, cached: true })).toContain(", cached");
    expect(deltaLine({ ...report, committed: true })).toContain(", committed");
    expect(deltaLine({ ...report, result: null })).toBe(
      "barrel_wood: not built",
    );
    const lines = formatReport(report).split("\n");
    expect(lines).toHaveLength(1 + CHECK_IDS.length);
    expect(lines[1]).toMatch(
      /^ {2}OK {11}bounds-fit {8}within 1×1×1 m ± 0.075$/,
    );
    expect(tally([report])).toEqual({ OK: 7, FAILED: 0, "NOT CHECKED": 0 });
    expect(exitCode([report])).toBe(0);
    expect(summary([report], 1)).toBe(
      "2 assets: 7 OK, 0 FAILED, 0 NOT CHECKED, 1 not built",
    );
  });

  it("notes a single-variant build", () => {
    const result: Measured = { only: "barrel_wood", variants: [variant()] };
    expect(triBudget(result).detail).toContain("(only barrel_wood built)");
  });
});
