import type { Measured, MeasuredVariant } from "./measurements.ts";
import type { Asset } from "./schema.ts";

/**
 * Asset checks: pure functions over an asset's `asset.json` and what its build measured. Each check is `OK`, `FAILED`
 * or `NOT CHECKED`; a check that cannot run (no build result, no ledger) reports `NOT CHECKED`, which is never a pass:
 * `exitCode` fails on it unless the run allows unchecked assets. Numbers come from the measurements, never from
 * pictures. All lengths are metres.
 */
export type Status = "OK" | "FAILED" | "NOT CHECKED";

export const CHECK_IDS = [
  "bounds-fit",
  "origin-ground",
  "tri-budget",
  "manifold",
  "materials-known",
  "anchors-declared",
] as const;
export type CheckId = (typeof CHECK_IDS)[number];

export interface Check {
  id: CheckId;
  status: Status;
  detail: string;
}

export const BUDGET = {
  /** Triangles per variant. */
  tris: 8000,
  /** How far the bounding box may stick out of the declared size sideways, in metres. */
  boundsSlack: 0.075,
  /** How far the origin and the lowest point may sit off the ground, in metres (measurements are rounded to 1e-4). */
  ground: 0.0075,
} as const;

/** Anchors whose effect has an extent (`anchor(..., size=...)` in asset.py): fires, water spouts and basins. */
export const needsSize = (anchor: string): boolean =>
  /^(fire:|water:spout|water:basin)/.test(anchor);

/** What the checks read. `null` means the input is missing, so the checks that need it report `NOT CHECKED`. */
export interface CheckInput {
  asset: Asset;
  /** The build's result or its committed measurement; null when there is neither (no Blender). */
  result: Measured | null;
  /** Texture ids of `catalog/textures.json`; null when there is no ledger. */
  ledger: ReadonlySet<string> | null;
  /** Why `result` is null, for the `NOT CHECKED` lines (default: Blender did not run). */
  noResult?: string;
}

const ok = (id: CheckId, detail: string): Check => ({
  id,
  status: "OK",
  detail,
});
const failed = (id: CheckId, problems: readonly string[]): Check => ({
  id,
  status: "FAILED",
  detail: problems.join("; "),
});
const unchecked = (id: CheckId, detail: string): Check => ({
  id,
  status: "NOT CHECKED",
  detail,
});

/** Shortest form of a measurement: `1.2`, `0.05`, `-0.3`. */
const n = (x: number): string => String(Number(x.toFixed(3)));

const variantsNote = (r: Measured): string =>
  r.only === null ? "" : ` (only ${r.only} built)`;

/** Runs `check` on each variant; problems are prefixed with the variant id. */
function perVariant(
  id: CheckId,
  result: Measured,
  check: (v: MeasuredVariant) => string[],
  okDetail: string,
): Check {
  const problems = result.variants.flatMap((v) =>
    check(v).map((p) => `${v.id}: ${p}`),
  );
  return problems.length > 0
    ? failed(id, problems)
    : ok(id, okDetail + variantsNote(result));
}

/** The bounding box stays within the declared size (± `boundsSlack` sideways) and under its height. */
export function boundsFit(asset: Asset, result: Measured): Check {
  const { x, y, z } = asset.size;
  const slack = BUDGET.boundsSlack;
  const eps = 1e-4;
  return perVariant(
    "bounds-fit",
    result,
    (v) => {
      const problems: string[] = [];
      const [x0, y0] = v.bbox.min;
      const [x1, y1, z1] = v.bbox.max;
      if (x0 < -x / 2 - slack - eps || x1 > x / 2 + slack + eps)
        problems.push(`x ${n(x0)}..${n(x1)} outside ±${n(x / 2)} m`);
      if (y0 < -y / 2 - slack - eps || y1 > y / 2 + slack + eps)
        problems.push(`y ${n(y0)}..${n(y1)} outside ±${n(y / 2)} m`);
      if (z1 > z + eps) problems.push(`height ${n(z1)} over ${n(z)} m`);
      return problems;
    },
    `within ${n(x)}×${n(y)}×${n(z)} m ± ${slack}`,
  );
}

/**
 * The origin is the centre of the base on the ground and the model stands on it (neither floats nor sinks). A hanging
 * prop (`mount`) stands on its lowest point too; the detail says where it hangs: a ceiling prop's top meets the
 * ceiling at `lift` plus its height, a wall prop's back (its largest y) lies on the wall.
 */
export function originGround(asset: Asset, result: Measured): Check {
  const tol = BUDGET.ground;
  const standing = "origin at the centre of the base, standing on the ground";
  const max = (i: 1 | 2) =>
    Math.max(...result.variants.map((v) => v.bbox.max[i]));
  const { mount } = asset;
  const hung =
    mount === undefined
      ? ""
      : mount.kind === "ceiling"
        ? `; hung ${n(mount.lift)} m up, its top meets a ceiling at ${n(mount.lift + max(2))} m`
        : `; hung ${n(mount.lift)} m up on a wall at y ${n(max(1))}`;
  return perVariant(
    "origin-ground",
    result,
    (v) => {
      const problems: string[] = [];
      if (v.origin.some((c) => Math.abs(c) > tol))
        problems.push(`origin at ${v.origin.map(n).join(", ")}, not 0, 0, 0`);
      const z0 = v.bbox.min[2];
      if (z0 > tol) problems.push(`floats ${n(z0)} m above the ground`);
      if (z0 < -tol) problems.push(`sinks ${n(-z0)} m below the ground`);
      return problems;
    },
    standing + hung,
  );
}

/** Every variant stays within the triangle budget. */
export function triBudget(result: Measured): Check {
  const max = Math.max(...result.variants.map((v) => v.tris));
  return perVariant(
    "tri-budget",
    result,
    (v) =>
      v.tris > BUDGET.tris
        ? [
            `${v.tris.toLocaleString("en")} tris > ${BUDGET.tris.toLocaleString("en")}`,
          ]
        : [],
    `${max.toLocaleString("en")} ≤ ${BUDGET.tris.toLocaleString("en")} tris`,
  );
}

/** An asset declared `closed` has no open edges (fracture and printing need it); others need not be closed. */
export function manifold(asset: Asset, result: Measured): Check {
  if (!asset.closed)
    return ok("manifold", "not declared closed, need not be manifold");
  return perVariant(
    "manifold",
    result,
    (v) =>
      v.nonManifoldEdges > 0
        ? [`${v.nonManifoldEdges} non-manifold edges`]
        : [],
    "manifold",
  );
}

const LEDGER = "ledger:";

/** Every material comes from the palette (`materials.material`) or the CC0 texture ledger (`materials.texture`). */
export function materialsKnown(
  result: Measured,
  ledger: ReadonlySet<string> | null,
): Check {
  const id = "materials-known";
  const problems: string[] = [];
  const needLedger: string[] = [];
  for (const v of result.variants) {
    const textures = new Set(v.textures);
    for (const m of v.materials) {
      if (m.source === "palette") continue;
      if (m.source?.startsWith(LEDGER) === true)
        textures.add(m.source.slice(LEDGER.length));
      else
        problems.push(
          `${v.id}: material "${m.name}" is not from the palette or the ledger`,
        );
    }
    for (const t of [...textures].sort()) {
      if (ledger === null) needLedger.push(`${v.id}: ${t}`);
      else if (!ledger.has(t))
        problems.push(`${v.id}: texture "${t}" is not in the ledger`);
    }
  }
  if (problems.length > 0) return failed(id, problems);
  if (needLedger.length > 0)
    return unchecked(
      id,
      `no texture ledger to check ${needLedger.join(", ")} against`,
    );
  const count = new Set(
    result.variants.flatMap((v) => v.materials.map((m) => m.name)),
  ).size;
  return ok(
    id,
    `${count} material${count === 1 ? "" : "s"}, all from the palette or the ledger${variantsNote(result)}`,
  );
}

/**
 * Every anchor `asset.json` declares is in every variant, no variant has an undeclared one, and fires, water spouts
 * and basins carry a size.
 */
export function anchorsDeclared(asset: Asset, result: Measured): Check {
  const declared = asset.anchors;
  return perVariant(
    "anchors-declared",
    result,
    (v) => {
      const found = new Set(v.anchors.map((a) => a.name));
      return [
        ...declared
          .filter((a) => !found.has(a))
          .map((a) => `declared anchor ${a} is missing`),
        ...[...found]
          .filter((a) => !declared.includes(a))
          .sort()
          .map((a) => `anchor ${a} is not declared in asset.json`),
        ...v.anchors
          .filter((a) => needsSize(a.name) && a.size === undefined)
          .map((a) => `anchor ${a.name} needs a size (anchor(..., size=...))`),
      ];
    },
    declared.length === 0
      ? "no anchors, none declared"
      : `${declared.join(", ")} in every variant`,
  );
}

/** All checks of one asset, in `CHECK_IDS` order. */
export function runChecks(input: CheckInput): Check[] {
  const { asset, result } = input;
  const needsBuild = (id: CheckId, check: (r: Measured) => Check) =>
    result === null
      ? unchecked(id, input.noResult ?? "no build result (Blender not run)")
      : check(result);
  return [
    needsBuild("bounds-fit", (r) => boundsFit(asset, r)),
    needsBuild("origin-ground", (r) => originGround(asset, r)),
    needsBuild("tri-budget", triBudget),
    needsBuild("manifold", (r) => manifold(asset, r)),
    needsBuild("materials-known", (r) => materialsKnown(r, input.ledger)),
    needsBuild("anchors-declared", (r) => anchorsDeclared(asset, r)),
  ];
}

/** `3.1k` from 3,084; plain below a thousand. */
function count(x: number): string {
  return x < 1000 ? String(x) : `${Number((x / 1000).toFixed(1))}k`;
}

export interface AssetReport {
  id: string;
  checks: Check[];
  result: Measured | null;
  /** Whether the result came from the cache. */
  cached: boolean;
  /** Build time in seconds (0 when cached). */
  seconds: number;
  /** `npm run check`: the result is the committed measurement, nothing was built or read from the cache. */
  committed?: boolean;
}

/**
 * The asset's delta line: `well_stone: 2 variants, 3.1k tris, 1.8×1.8×2.4 m, 41 s`. Tris and size are the largest over
 * the variants (the budgets hold per variant).
 */
export function deltaLine(report: AssetReport): string {
  const { result } = report;
  if (result === null) return `${report.id}: not built`;
  const vs = result.variants;
  const max = (f: (v: MeasuredVariant) => number) => Math.max(...vs.map(f));
  const size = ([0, 1, 2] as const)
    .map((i) => n(max((v) => v.bbox.max[i] - v.bbox.min[i])))
    .join("×");
  return [
    `${report.id}: ${vs.length} variant${vs.length === 1 ? "" : "s"}${variantsNote(result)}`,
    `${count(max((v) => v.tris))} tris`,
    `${size} m`,
    report.committed === true
      ? "committed"
      : report.cached
        ? "cached"
        : `${report.seconds.toFixed(1)} s`,
  ].join(", ");
}

const WIDTH = Math.max(...CHECK_IDS.map((c) => c.length));

/** The report of one asset: its delta line, then one line per check. */
export function formatReport(report: AssetReport): string {
  return [
    deltaLine(report),
    ...report.checks.map(
      (c) =>
        `  ${c.status.padEnd("NOT CHECKED".length)}  ${c.id.padEnd(WIDTH)}  ${c.detail}`,
    ),
  ].join("\n");
}

/** Counts of each status over all reports, for the closing line. */
export function tally(
  reports: readonly { checks: readonly { status: Status }[] }[],
): Record<Status, number> {
  const t: Record<Status, number> = { OK: 0, FAILED: 0, "NOT CHECKED": 0 };
  for (const r of reports) for (const c of r.checks) t[c.status]++;
  return t;
}

/** 1 when a check FAILED, or one is NOT CHECKED and `allowUnchecked` is off; else 0. */
export function exitCode(
  reports: readonly { checks: readonly { status: Status }[] }[],
  allowUnchecked = false,
): 0 | 1 {
  const t = tally(reports);
  return t.FAILED > 0 || (t["NOT CHECKED"] > 0 && !allowUnchecked) ? 1 : 0;
}

/** The closing line of a run: `3 assets: 18 OK, 0 FAILED, 0 NOT CHECKED`. */
export function summary(
  reports: readonly { checks: readonly { status: Status }[] }[],
  errors = 0,
): string {
  const t = tally(reports);
  const assets = reports.length + errors;
  return [
    `${assets} asset${assets === 1 ? "" : "s"}: ${t.OK} OK`,
    `${t.FAILED} FAILED`,
    `${t["NOT CHECKED"]} NOT CHECKED`,
    ...(errors > 0 ? [`${errors} not built`] : []),
  ].join(", ");
}
