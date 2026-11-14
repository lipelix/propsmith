import { createHash } from "node:crypto";
import {
  copyFileSync,
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import { join } from "node:path";
import { z } from "zod";

import { findBlender, runBlender } from "./blender.ts";
import {
  assetIds,
  buildAsset,
  buildJob,
  CACHE_DIR,
  reportAsset,
} from "./build.ts";
import { CATALOG_DIR, ROOT, usedTextures } from "./catalog.ts";
import { SNAKE } from "./ids.ts";
import { resolveTextures } from "./textures.ts";

/**
 * `npm run bake [-- <id>…] [--force]` (needs Blender): what the catalogue publishes for each asset.
 *
 * The library's materials are procedural, which glTF cannot carry, so `blender/bake.py` bakes base colour, roughness,
 * metallic and the normal of every variant into one atlas and exports a GLB with a plain PBR material any engine
 * reads. Only an asset whose build passes every check is baked. Output in `dist/catalog/<id>/`: `<variant>.glb`,
 * `<variant>.png` (the three-quarter snapshot, as a thumbnail) and `bake.json`; `dist/catalog/assets.json` lists every
 * baked asset with file sizes and SHA-256, for the site and the public index. An asset whose input hash matches its
 * `bake.json` is skipped unless `--force`.
 */
export const PUBLISH_DIR = "dist/catalog";
export const MANIFEST_FILE = "dist/catalog/assets.json";

/** Bake settings: one square atlas per variant, JPEG inside the GLB. */
export const BAKE = { resolution: 1024, samples: 16, quality: 90 } as const;

const snake = z.string().regex(SNAKE);

export const bakeResultSchema = z
  .object({
    schema: z.literal(1),
    id: snake,
    inputHash: z.string().regex(/^[0-9a-f]{64}$/),
    libVersion: z.number().int(),
    blender: z.string(),
    resolution: z.number().int().positive(),
    variants: z
      .array(
        z
          .object({
            id: snake,
            glb: z.string().min(1),
            materials: z.number().int().min(1),
            seconds: z.number().min(0),
          })
          .strict(),
      )
      .min(1),
  })
  .strict();
export type BakeResult = z.infer<typeof bakeResultSchema>;

export interface PublishedVariant {
  id: string;
  /** Paths relative to `dist/catalog/`. */
  glb: string;
  png: string;
  glbBytes: number;
  glbSha256: string;
}

export interface PublishedAsset {
  inputHash: string;
  variants: PublishedVariant[];
}

export interface Manifest {
  schema: 1;
  note: string;
  assets: Record<string, PublishedAsset>;
}

function readBake(out: string): BakeResult | undefined {
  const path = join(out, "bake.json");
  if (!existsSync(path)) return undefined;
  const parsed = bakeResultSchema.safeParse(
    JSON.parse(readFileSync(path, "utf8")),
  );
  if (!parsed.success) return undefined;
  const files = parsed.data.variants.flatMap((v) => [v.glb, `${v.id}.png`]);
  return files.every((f) => existsSync(join(out, f))) ? parsed.data : undefined;
}

export interface Baked {
  result: BakeResult;
  cached: boolean;
  seconds: number;
}

/** Builds (or reuses the build of) asset `id`, refuses it unless every check is OK, then bakes its GLBs. */
export function bakeAsset(
  root: string,
  id: string,
  options: { force?: boolean } = {},
): Baked {
  const built = buildAsset(root, id);
  const bad = reportAsset(root, id, built).checks.filter(
    (c) => c.status !== "OK",
  );
  if (bad.length > 0)
    throw new Error(
      `${id}: not baked, ${bad.map((c) => `${c.id} is ${c.status}`).join(", ")}; run npm run build -- ${id}`,
    );
  const out = join(root, PUBLISH_DIR, id);
  const job = { ...buildJob(root, id), out, ...BAKE };
  const cached = readBake(out);
  if (!options.force && cached?.inputHash === job.inputHash)
    return { result: cached, cached: true, seconds: 0 };
  job.textures = resolveTextures(
    root,
    usedTextures(readFileSync(job.asset.file, "utf8")),
  );
  mkdirSync(out, { recursive: true });
  const jobPath = join(root, CACHE_DIR, id, "bake-job.json");
  writeFileSync(jobPath, JSON.stringify(job, null, 2));
  const started = Date.now();
  runBlender("bake.py", [jobPath]);
  const seconds = (Date.now() - started) / 1000;
  for (const v of built.result.variants)
    copyFileSync(
      join(root, CACHE_DIR, id, v.review.iso),
      join(out, `${v.id}.png`),
    );
  const result = readBake(out);
  if (result?.inputHash !== job.inputHash)
    throw new Error(`${id}: bake.json is missing or not from this job`);
  return { result, cached: false, seconds };
}

/** The manifest of every baked asset under `root/dist/catalog`, sorted by id; unbaked assets are left out. */
export function buildManifest(root: string): Manifest {
  const assets: Record<string, PublishedAsset> = {};
  for (const id of assetIds(root)) {
    const out = join(root, PUBLISH_DIR, id);
    const bake = readBake(out);
    if (!bake) continue;
    assets[id] = {
      inputHash: bake.inputHash,
      variants: bake.variants.map((v) => {
        const data = readFileSync(join(out, v.glb));
        return {
          id: v.id,
          glb: `${id}/${v.glb}`,
          png: `${id}/${v.id}.png`,
          glbBytes: data.length,
          glbSha256: createHash("sha256").update(data).digest("hex"),
        };
      }),
    };
  }
  return {
    schema: 1,
    note: "Generated by npm run bake; do not edit.",
    assets,
  };
}

export interface Args {
  ids: string[];
  force: boolean;
}

export function parseArgs(argv: readonly string[]): Args {
  const args: Args = { ids: [], force: false };
  for (const a of argv) {
    if (a === "--force") args.force = true;
    else if (a.startsWith("--")) throw new Error(`unknown option ${a}`);
    else args.ids.push(a);
  }
  return args;
}

function main(): void {
  const args = parseArgs(process.argv.slice(2));
  if (findBlender() === undefined)
    throw new Error("Blender not found ($BLENDER or the macOS app)");
  const all = assetIds(ROOT);
  for (const id of args.ids)
    if (!all.includes(id))
      throw new Error(`no asset "${id}" in ${CATALOG_DIR}`);
  let errors = 0;
  for (const id of args.ids.length > 0 ? args.ids : all) {
    try {
      const baked = bakeAsset(ROOT, id, { force: args.force });
      console.log(
        `${id}: ${baked.result.variants.length} variant${baked.result.variants.length === 1 ? "" : "s"}, ${baked.cached ? "cached" : `${baked.seconds.toFixed(1)} s`}`,
      );
    } catch (error) {
      errors++;
      console.error(error instanceof Error ? error.message : String(error));
    }
  }
  const manifest = buildManifest(ROOT);
  mkdirSync(join(ROOT, PUBLISH_DIR), { recursive: true });
  writeFileSync(
    join(ROOT, MANIFEST_FILE),
    `${JSON.stringify(manifest, null, 2)}\n`,
  );
  const variants = Object.values(manifest.assets).flatMap((a) => a.variants);
  const kb = Math.ceil(variants.reduce((s, v) => s + v.glbBytes, 0) / 1024);
  console.log(
    `${MANIFEST_FILE}: ${Object.keys(manifest.assets).length} assets, ${variants.length} GLBs, ${kb} KB`,
  );
  if (errors > 0) process.exit(1);
}

if (process.argv[1]?.endsWith("tools/bake.ts") === true) {
  try {
    main();
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}
