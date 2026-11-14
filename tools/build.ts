import {
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import { join, relative } from "node:path";
import { format, resolveConfig } from "prettier";
import { z } from "zod";

import { findBlender, runBlender } from "./blender.ts";
import {
  buildIndex,
  CATALOG_DIR,
  formatIndex,
  INDEX_FILE,
  inputHash,
  ROOT,
  usedTextures,
} from "./catalog.ts";
import {
  type AssetReport,
  type Check,
  exitCode,
  formatReport,
  runChecks,
  summary,
  tally,
} from "./checks.ts";
import { SNAKE } from "./ids.ts";
import {
  measuredOf,
  measuredVariantSchema,
  writeMeasurements,
} from "./measurements.ts";
import { type Asset, parseAsset, parseTags } from "./schema.ts";
import { readLedger, resolveTextures } from "./textures.ts";

/**
 * `npm run build [-- <id>…] [--force] [--only <variant>] [--allow-unchecked]` (needs Blender).
 *
 * Per asset: validates `asset.json`, writes a job, runs `blender/build.py` headless and reads back `result.json` from
 * `.cache/assets/<id>/`: per variant the GLB, the measured facts and the review snapshots. An asset whose input hash
 * (folder, the Blender library, build script and review style, textures) matches the cached result is skipped unless
 * `--force`. `--only` builds one variant (its asset is found by the variant id) and records nothing.
 *
 * Every full build's measured facts go to `catalog/measurements.json` (what `npm run check` checks in CI, without
 * Blender), and `catalog/index.json` is rewritten.
 *
 * Then `checks.ts` runs on the result and the report prints a delta line and one line per check. The exit code is
 * non-zero on a `FAILED` check, an asset that did not build, or a `NOT CHECKED` check (no Blender) unless
 * `--allow-unchecked` is given for a local look-only run.
 */
export const CACHE_DIR = ".cache/assets";
const LIB = join(import.meta.dirname, "../lib");
const TAGS_FILE = "catalog/tags.json";
const STYLE_FILE = "tools/blender/style.json";

const snake = z.string().regex(SNAKE);

export const jobSchema = z
  .object({
    lib: z.string().min(1),
    style: z.record(z.string(), z.unknown()),
    /** Ledger id → cached files by kind (`color`, `ao`, `normal`, `roughness`), from `textures.resolveTextures`. */
    textures: z.record(z.string(), z.record(z.string(), z.string())),
    asset: z
      .object({
        id: snake,
        file: z.string().min(1),
        variants: z.array(snake).min(1),
        size: z
          .object({
            x: z.number().positive(),
            y: z.number().positive(),
            z: z.number().positive(),
          })
          .strict(),
      })
      .strict(),
    only: snake.nullable(),
    inputHash: z.string().regex(/^[0-9a-f]{64}$/),
    out: z.string().min(1),
  })
  .strict()
  .refine((j) => j.only === null || j.asset.variants.includes(j.only), {
    message: "only must be one of the asset's variants",
  });
export type Job = z.infer<typeof jobSchema>;

/** One variant of a `result.json`: the measured facts (metres, asset space) and the files written. */
export const variantResultSchema = measuredVariantSchema
  .extend({
    id: snake,
    glb: z.string().min(1),
    review: z
      .object({ iso: z.string(), top: z.string(), front: z.string() })
      .strict(),
    seconds: z.number().min(0),
  })
  .strict();
export type VariantResult = z.infer<typeof variantResultSchema>;

export const resultSchema = z
  .object({
    schema: z.literal(1),
    id: snake,
    inputHash: z.string(),
    only: snake.nullable(),
    libVersion: z.number().int(),
    blender: z.string(),
    variants: z.array(variantResultSchema).min(1),
  })
  .strict();
export type BuildResult = z.infer<typeof resultSchema>;

/** Parses a `result.json`, throwing with the problems. */
export function parseResult(json: unknown): BuildResult {
  const parsed = resultSchema.safeParse(json);
  if (!parsed.success) throw new Error(z.prettifyError(parsed.error));
  return parsed.data;
}

export interface JobOptions {
  only?: string | null;
  /** Where the build writes; `<root>/.cache/assets/<id>` by default. */
  out?: string;
  /** The cached maps handed to Blender; by default those of the textures asset.py uses (`resolveTextures`). */
  textures?: Job["textures"];
}

/**
 * Rewrites asset `id`'s `asset.json` in Prettier's layout when it is not, so `npm run check` passes and the input hash
 * is taken from the file as committed: formatting it later would change the hash and force a rebuild. An agent writes
 * `asset.json` in its own layout under `npm run new`. Returns whether the file changed.
 */
export async function formatAssetJson(
  root: string,
  id: string,
): Promise<boolean> {
  const path = join(root, CATALOG_DIR, id, "asset.json");
  if (!existsSync(path)) return false;
  const text = readFileSync(path, "utf8");
  const config = (await resolveConfig(path)) ?? {};
  const formatted = await format(text, { ...config, filepath: path });
  if (formatted === text) return false;
  writeFileSync(path, formatted);
  return true;
}

/** Asset `id` under `root`, parsed against the tag vocabulary. */
export function readAsset(root: string, id: string): Asset {
  const path = join(root, CATALOG_DIR, id, "asset.json");
  if (!existsSync(path)) throw new Error(`${id}: no ${relative(root, path)}`);
  const tags = parseTags(
    JSON.parse(readFileSync(join(root, TAGS_FILE), "utf8")),
  );
  const asset = parseAsset(JSON.parse(readFileSync(path, "utf8")), tags);
  if (asset.id !== id)
    throw new Error(`${id}: asset.json says id "${asset.id}"`);
  return asset;
}

/** The build job of asset `id` under `root`: validated against `asset.json`, the tag vocabulary and `jobSchema`. */
export function buildJob(
  root: string,
  id: string,
  options: JobOptions = {},
): Job {
  const asset = readAsset(root, id);
  const only = options.only ?? null;
  if (only !== null && !asset.variants.includes(only))
    throw new Error(
      `${id}: no variant "${only}" (has ${asset.variants.join(", ")})`,
    );
  const style = JSON.parse(
    readFileSync(join(ROOT, STYLE_FILE), "utf8"),
  ) as Record<string, unknown>;
  const job = {
    lib: LIB,
    style,
    textures: options.textures ?? {},
    asset: {
      id,
      file: join(root, CATALOG_DIR, id, "asset.py"),
      variants: asset.variants,
      size: asset.size,
    },
    only,
    inputHash: inputHash(root, id),
    out: options.out ?? join(root, CACHE_DIR, id),
  };
  const parsed = jobSchema.safeParse(job);
  if (!parsed.success)
    throw new Error(`${id}: bad job\n${z.prettifyError(parsed.error)}`);
  return parsed.data;
}

/** Whether `cached` already holds what `job` would build (same inputs, a full build or the same variant). */
export function isCached(job: Job, cached: BuildResult | undefined): boolean {
  if (!cached || cached.inputHash !== job.inputHash) return false;
  return cached.only === null || cached.only === job.only;
}

function readCached(out: string): BuildResult | undefined {
  const path = join(out, "result.json");
  if (!existsSync(path)) return undefined;
  try {
    const result = parseResult(JSON.parse(readFileSync(path, "utf8")));
    const files = result.variants.flatMap((v) => [
      v.glb,
      ...Object.values(v.review),
    ]);
    return files.every((f) => existsSync(join(out, f))) ? result : undefined;
  } catch {
    return undefined;
  }
}

export interface Built {
  result: BuildResult;
  cached: boolean;
  seconds: number;
}

/** Builds one asset (or reuses the cache) and returns its parsed `result.json`. */
export function buildAsset(
  root: string,
  id: string,
  options: JobOptions & { force?: boolean } = {},
): Built {
  const job = buildJob(root, id, options);
  const cached = readCached(job.out);
  if (!options.force && isCached(job, cached) && cached)
    return { result: cached, cached: true, seconds: 0 };
  // Only a real build needs the texture files: an unknown or undownloaded texture fails here, before Blender.
  job.textures =
    options.textures ??
    resolveTextures(root, usedTextures(readFileSync(job.asset.file, "utf8")));
  mkdirSync(job.out, { recursive: true });
  const jobPath = join(job.out, "job.json");
  writeFileSync(jobPath, JSON.stringify(job, null, 2));
  const started = Date.now();
  runBlender("build.py", [jobPath]);
  const seconds = (Date.now() - started) / 1000;
  const result = parseResult(
    JSON.parse(readFileSync(join(job.out, "result.json"), "utf8")),
  );
  if (result.inputHash !== job.inputHash)
    throw new Error(`${id}: result.json is not from this job`);
  return { result, cached: false, seconds };
}

/** Texture ids of the ledger `catalog/textures.json` (validated); null when there is no ledger. */
export function ledgerIds(root: string): Set<string> | null {
  const ledger = readLedger(root);
  return ledger ? new Set(Object.keys(ledger.textures)) : null;
}

/** Checks one asset against its build (null when there is none). */
export function reportAsset(
  root: string,
  id: string,
  built: Built | null,
): AssetReport {
  const checks = runChecks({
    asset: readAsset(root, id),
    result: built?.result ?? null,
    ledger: ledgerIds(root),
  });
  return {
    id,
    checks,
    result: built?.result ?? null,
    cached: built?.cached ?? false,
    seconds: built?.seconds ?? 0,
  };
}

/** Records what the full builds measured in `catalog/measurements.json` and refreshes `catalog/index.json`. */
export async function record(
  root: string,
  builds: readonly { id: string; built: Built }[],
): Promise<void> {
  await writeMeasurements(
    root,
    builds.map(({ id, built }) => ({ id, measured: measuredOf(built.result) })),
    new Set(assetIds(root)),
  );
  writeFileSync(
    join(root, INDEX_FILE),
    await formatIndex(buildIndex(root), root),
  );
}

export interface Args {
  ids: string[];
  force: boolean;
  only: string | null;
  /** A local look-only run: `NOT CHECKED` does not fail the exit code. */
  allowUnchecked: boolean;
}

export function parseArgs(argv: readonly string[]): Args {
  const args: Args = {
    ids: [],
    force: false,
    only: null,
    allowUnchecked: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i] ?? "";
    if (a === "--force") args.force = true;
    else if (a === "--allow-unchecked") args.allowUnchecked = true;
    else if (a === "--only") {
      const v = argv[++i];
      if (!v || v.startsWith("--"))
        throw new Error("--only needs a variant id");
      args.only = v;
    } else if (a.startsWith("--")) throw new Error(`unknown option ${a}`);
    else args.ids.push(a);
  }
  return args;
}

/** Asset folder names under `root/catalog`, sorted. */
export function assetIds(root: string): string[] {
  return readdirSync(join(root, CATALOG_DIR), { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
    .sort();
}

/** The assets a run builds: the ids given, else the one owning `--only`, else all. */
export function selectAssets(root: string, args: Args): string[] {
  const all = assetIds(root);
  for (const id of args.ids)
    if (!all.includes(id))
      throw new Error(`no asset "${id}" in ${CATALOG_DIR}`);
  if (args.only === null) return args.ids.length > 0 ? args.ids : all;
  const only = args.only;
  const owners = (args.ids.length > 0 ? args.ids : all).filter(
    (id) => only === id || only.startsWith(`${id}_`),
  );
  const owner = owners.sort((a, b) => b.length - a.length)[0];
  if (!owner) throw new Error(`--only ${only}: no asset has this variant`);
  return [owner];
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  const blender = findBlender() !== undefined;
  if (!blender)
    console.error(
      "Blender not found ($BLENDER or the macOS app): build checks are NOT CHECKED",
    );
  const builds = new Map<string, Built | null>();
  let errors = 0;
  for (const id of selectAssets(ROOT, args)) {
    try {
      if (await formatAssetJson(ROOT, id))
        console.log(`${id}: formatted ${CATALOG_DIR}/${id}/asset.json`);
      builds.set(
        id,
        blender
          ? buildAsset(ROOT, id, { force: args.force, only: args.only })
          : null,
      );
    } catch (error) {
      errors++;
      console.error(
        `${id}: FAILED\n${error instanceof Error ? error.message : String(error)}`,
      );
    }
  }
  const full = [...builds]
    .filter((e): e is [string, Built] => e[1]?.result.only === null)
    .map(([id, built]) => ({ id, built }));
  if (full.length > 0) await record(ROOT, full);
  const reports: { checks: Check[] }[] = [];
  for (const [id, built] of builds) {
    const report = reportAsset(ROOT, id, built);
    reports.push(report);
    console.log(formatReport(report));
  }
  console.log(
    summary(reports, errors) +
      (tally(reports)["NOT CHECKED"] > 0 && args.allowUnchecked
        ? " (--allow-unchecked)"
        : ""),
  );
  if (errors > 0 || exitCode(reports, args.allowUnchecked) !== 0)
    process.exit(1);
}

if (process.argv[1]?.endsWith("tools/build.ts") === true) {
  try {
    await main();
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}
