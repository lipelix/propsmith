import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join, relative } from "node:path";
import sharp from "sharp";
import { z } from "zod";

/**
 * The CC0 texture ledger: `catalog/textures.json` pins every texture an asset may use
 * by id (`ambientcg:Wood049`): where it comes from, who made it, its licence (only `CC0-1.0` validates), the SHA-256 of
 * the download and the resolution the build uses.
 *
 * `npm run textures [-- <id>…] [--force]` downloads the ledger's zips, verifies their SHA-256, extracts the maps
 * the ledger names and downsizes them to `resolution` (PNG) into `.cache/textures/<id>/`, never committed. A
 * `ledger.json` stamp there records which entry the files were made from, so a changed entry is fetched again.
 *
 * `npm run build` hands Blender the cached maps of the textures an asset.py uses (`resolveTextures`); an id outside the
 * ledger or a texture that is not downloaded fails the build with what to do.
 */
export const LEDGER_FILE = "catalog/textures.json";
export const TEXTURES_CACHE = ".cache/textures";
const STAMP = "ledger.json";

/** `<source>:<name>`: the site and its asset name, e.g. `ambientcg:Wood049`, `polyhaven:rock_01`. */
export const TEXTURE_ID = /^(ambientcg|polyhaven):[A-Za-z0-9_-]+$/;
/** The maps `materials.texture` and `rig.ground` read. */
export const MAP_KINDS = ["color", "ao", "normal", "roughness"] as const;
export type MapKind = (typeof MAP_KINDS)[number];

const https = z
  .string()
  .regex(/^https:\/\/\S+$/, { message: "must be an https URL" });

export const ledgerEntrySchema = z
  .object({
    name: z.string().min(1),
    /** The asset's page, for a human to check the licence. */
    page: https,
    author: z.string().min(1),
    licence: z.literal("CC0-1.0", {
      message: 'only CC0-1.0 textures may enter the ledger (licence "CC0-1.0")',
    }),
    /** A zip with the maps. */
    download: https,
    /** SHA-256 of the downloaded zip. */
    sha256: z.string().regex(/^[0-9a-f]{64}$/),
    /** Map kind → file name inside the zip; `color` is required. */
    maps: z
      .object({
        color: z.string().min(1),
        ao: z.string().min(1).optional(),
        normal: z.string().min(1).optional(),
        roughness: z.string().min(1).optional(),
      })
      .strict(),
    /** Edge in px the maps are downsized to (never upscaled). */
    resolution: z.number().int().min(64).max(4096),
  })
  .strict();
export type LedgerEntry = z.infer<typeof ledgerEntrySchema>;

export const ledgerSchema = z
  .object({
    schema: z.literal(1),
    note: z.string(),
    textures: z.record(z.string(), ledgerEntrySchema),
  })
  .strict()
  .superRefine((ledger, ctx) => {
    for (const id of Object.keys(ledger.textures))
      if (!TEXTURE_ID.test(id))
        ctx.addIssue({
          code: "custom",
          path: ["textures", id],
          message: `texture ids are <ambientcg|polyhaven>:<name>, not "${id}"`,
        });
  });
export type Ledger = z.infer<typeof ledgerSchema>;

/** Parses a ledger, throwing with the problems. */
export function parseLedger(json: unknown): Ledger {
  const parsed = ledgerSchema.safeParse(json);
  if (!parsed.success)
    throw new Error(`${LEDGER_FILE}: ${z.prettifyError(parsed.error)}`);
  return parsed.data;
}

/** The ledger under `root`; null when there is none. */
export function readLedger(root: string): Ledger | null {
  const path = join(root, LEDGER_FILE);
  if (!existsSync(path)) return null;
  return parseLedger(JSON.parse(readFileSync(path, "utf8")));
}

/** Cache folder of a texture: `ambientcg:Wood049` → `.cache/textures/ambientcg_Wood049`. */
export function cacheDir(root: string, id: string): string {
  return join(root, TEXTURES_CACHE, id.replace(":", "_"));
}

/** The cached map files of `entry` (kind → absolute path), whether or not they exist yet. */
export function cachedMaps(
  root: string,
  id: string,
  entry: LedgerEntry,
): Partial<Record<MapKind, string>> {
  const dir = cacheDir(root, id);
  return Object.fromEntries(
    MAP_KINDS.filter((k) => entry.maps[k] !== undefined).map((k) => [
      k,
      join(dir, `${k}.png`),
    ]),
  );
}

/** What the cached files were made from; a different stamp means the entry changed. */
function stamp(entry: LedgerEntry): string {
  return JSON.stringify(
    { sha256: entry.sha256, resolution: entry.resolution, maps: entry.maps },
    null,
    2,
  );
}

/** Why the cache of `id` cannot be used (null when it can). */
export function cacheProblem(
  root: string,
  id: string,
  entry: LedgerEntry,
): string | null {
  const dir = cacheDir(root, id);
  const stampPath = join(dir, STAMP);
  if (!existsSync(stampPath)) return "not downloaded";
  if (readFileSync(stampPath, "utf8") !== stamp(entry))
    return "downloaded from an older ledger entry";
  const missing = Object.values(cachedMaps(root, id, entry)).filter(
    (p) => !existsSync(p),
  );
  if (missing.length > 0)
    return `missing ${missing.map((p) => relative(root, p)).join(", ")}`;
  return null;
}

/**
 * The cached maps of `ids` for a Blender job ({id: {kind: file}}). Throws on an id outside the ledger or a texture
 * whose cache is missing or stale, naming the command that fixes it.
 */
export function resolveTextures(
  root: string,
  ids: readonly string[],
): Record<string, Record<string, string>> {
  if (ids.length === 0) return {};
  const ledger = readLedger(root);
  const out: Record<string, Record<string, string>> = {};
  const problems: string[] = [];
  for (const id of ids) {
    const entry = ledger?.textures[id];
    if (!entry) {
      problems.push(`unknown texture "${id}": not in ${LEDGER_FILE}`);
      continue;
    }
    const problem = cacheProblem(root, id, entry);
    if (problem !== null) {
      problems.push(
        `texture "${id}" ${problem} (${relative(root, cacheDir(root, id))}); run npm run textures -- ${id}`,
      );
      continue;
    }
    out[id] = cachedMaps(root, id, entry) as Record<string, string>;
  }
  if (problems.length > 0) throw new Error(problems.join("\n"));
  return out;
}

export const sha256 = (data: Uint8Array): string =>
  createHash("sha256").update(data).digest("hex");

/** Downsizes `from` (PNG or JPEG) to at most `edge` px on its longer side and writes a PNG to `to`. */
export type Resize = (from: string, to: string, edge: number) => Promise<void>;

export interface FetchDeps {
  download: (url: string) => Promise<Uint8Array>;
  resize: Resize;
}

async function httpDownload(url: string): Promise<Uint8Array> {
  const response = await fetch(url, { redirect: "follow" });
  if (!response.ok)
    throw new Error(
      `download failed: ${url}: ${response.status} ${response.statusText}`,
    );
  return new Uint8Array(await response.arrayBuffer());
}

/** Extracts `names` from `zip` into `dir` (flat), with the system `unzip`. */
function unzip(zip: string, names: readonly string[], dir: string): void {
  const run = spawnSync("unzip", ["-o", "-j", "-q", zip, ...names, "-d", dir]);
  if (run.error) throw new Error(`unzip: ${run.error.message}`);
  if (run.status !== 0)
    throw new Error(
      `unzip failed: ${String(run.stderr) || String(run.stdout)}`,
    );
}

/**
 * Makes the cache of one ledger entry: download, verify the SHA-256, extract the maps, downsize them to `resolution`.
 * Returns false when the cache was already up to date (and `force` is not set).
 */
export async function fetchTexture(
  root: string,
  id: string,
  entry: LedgerEntry,
  deps: FetchDeps,
  force = false,
): Promise<boolean> {
  if (!force && cacheProblem(root, id, entry) === null) return false;
  const data = await deps.download(entry.download);
  const got = sha256(data);
  if (got !== entry.sha256)
    throw new Error(
      `${id}: SHA-256 of ${entry.download} is ${got}, the ledger says ${entry.sha256}`,
    );
  const work = mkdtempSync(join(tmpdir(), "propsmith-texture-"));
  try {
    const zip = join(work, "download.zip");
    writeFileSync(zip, data);
    const kinds = MAP_KINDS.filter((k) => entry.maps[k] !== undefined);
    const names = kinds.map((k) => entry.maps[k] ?? "");
    unzip(zip, names, work);
    const dir = cacheDir(root, id);
    rmSync(dir, { recursive: true, force: true });
    mkdirSync(dir, { recursive: true });
    const targets = cachedMaps(root, id, entry);
    for (const kind of kinds) {
      const name = entry.maps[kind] ?? "";
      const from = join(work, name.split("/").pop() ?? name);
      if (!existsSync(from))
        throw new Error(`${id}: ${name} is not in ${entry.download}`);
      const to = targets[kind];
      if (to === undefined) throw new Error(`${id}: no target for ${kind}`);
      await deps.resize(from, to, entry.resolution);
    }
    writeFileSync(join(dir, STAMP), stamp(entry));
    return true;
  } finally {
    rmSync(work, { recursive: true, force: true });
  }
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

/** The ledger ids a run fetches: the ids given (each must be in the ledger), else all, sorted. */
export function selectTextures(
  ledger: Ledger,
  ids: readonly string[],
): string[] {
  for (const id of ids)
    if (!(id in ledger.textures))
      throw new Error(`unknown texture "${id}": not in ${LEDGER_FILE}`);
  return (ids.length > 0 ? [...ids] : Object.keys(ledger.textures)).sort();
}

/** Downsizes with sharp; never upscales. */
const resize: Resize = async (from, to, edge) => {
  await sharp(from)
    .resize({
      width: edge,
      height: edge,
      fit: "inside",
      withoutEnlargement: true,
    })
    .png()
    .toFile(to);
};

/**
 * Fetches `ids` of the ledger under `root` into the cache; prints one line per
 * texture. Returns the cached maps by id, like `resolveTextures`.
 */
export async function ensureTextures(
  root: string,
  ids: readonly string[],
  options: { force?: boolean; log?: (line: string) => void } = {},
): Promise<Record<string, Record<string, string>>> {
  const ledger = readLedger(root);
  if (!ledger) throw new Error(`no ${LEDGER_FILE}`);
  const selected = selectTextures(ledger, ids);
  const log = options.log ?? console.log;
  const stale = selected.filter(
    (id) =>
      options.force === true ||
      cacheProblem(root, id, ledger.textures[id] as LedgerEntry) !== null,
  );
  for (const id of stale) {
    const entry = ledger.textures[id] as LedgerEntry;
    await fetchTexture(
      root,
      id,
      entry,
      { download: httpDownload, resize },
      true,
    );
    log(`${id}: fetched, ${entry.resolution} px`);
  }
  for (const id of selected.filter((id) => !stale.includes(id)))
    log(`${id}: cached`);
  return resolveTextures(root, selected);
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  const root = join(import.meta.dirname, "..");
  await ensureTextures(root, args.ids, { force: args.force });
}

if (process.argv[1]?.endsWith("tools/textures.ts") === true) {
  try {
    await main();
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}
