import { createHash } from "node:crypto";
import {
  existsSync,
  readdirSync,
  readFileSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { join, relative } from "node:path";
import { format, resolveConfig } from "prettier";

import { type Asset, parseAsset, parseTags } from "./schema.ts";

/**
 * `catalog/index.json`: one sorted entry per asset folder, built from its `asset.json` and the hash of everything
 * the asset is built from. The site and consumers read it; `npm run catalog -- --check` fails when the committed
 * file is stale. Run `npm run catalog` after changing an asset.
 */
export const ROOT = join(import.meta.dirname, "..");
export const CATALOG_DIR = "catalog";
export const INDEX_FILE = "catalog/index.json";
const TAGS_FILE = "catalog/tags.json";
const LEDGER_FILE = "catalog/textures.json";
const LIB_DIR = "lib/propsmith";
const BLENDER_DIR = "tools/blender";

export interface IndexEntry {
  id: string;
  name: string;
  description: string;
  category: Asset["category"];
  family: string;
  tags: string[];
  aliases: string[];
  variants: string[];
  size: Asset["size"];
  anchors: string[];
  closed: boolean;
  source: Asset["provenance"]["source"];
  licence: Asset["licence"];
  /** SHA-256 of the asset folder, the library and the build script: what the model is built from. */
  inputHash: string;
}

export interface Index {
  schema: 1;
  note: string;
  assets: IndexEntry[];
}

const compare = (a: string, b: string): number => (a < b ? -1 : a > b ? 1 : 0);

/** Files under `dir` (relative to `root`), recursively, sorted; Python caches and dotfiles are skipped. */
export function files(root: string, dir: string): string[] {
  const abs = join(root, dir);
  if (!existsSync(abs)) return [];
  return readdirSync(abs, { recursive: true, encoding: "utf8" })
    .map((f) => join(dir, f))
    .filter(
      (f) =>
        !f.includes("__pycache__") &&
        !f.endsWith(".pyc") &&
        !f.split(/[/\\]/).some((part) => part.startsWith(".")),
    )
    .filter((f) => statSync(join(root, f)).isFile())
    .map((f) => f.split("\\").join("/"))
    .sort(compare);
}

/** Ledger ids of the CC0 textures an asset.py asks for (`texture(name, "<id>")`, `maps("<id>")`), sorted. */
export function usedTextures(source: string): string[] {
  const ids = [
    ...source.matchAll(
      /\b(?:texture\(\s*["'][^"']*["']\s*,|maps\()\s*["']([^"']+)["']/g,
    ),
  ].map((m) => m[1] ?? "");
  return [...new Set(ids)].sort(compare);
}

/**
 * Hashes the inputs of an asset: its folder, the Blender library, the build script and its review style (path and
 * bytes each); when
 * its asset.py uses textures, also the texture ledger, which pins their files by SHA-256.
 */
export function inputHash(root: string, id: string): string {
  const hash = createHash("sha256");
  const py = join(root, CATALOG_DIR, id, "asset.py");
  const textured =
    existsSync(py) && usedTextures(readFileSync(py, "utf8")).length > 0;
  const paths = [
    ...files(root, `${CATALOG_DIR}/${id}`),
    ...files(root, LIB_DIR),
    ...files(root, BLENDER_DIR),
    ...(textured ? [LEDGER_FILE] : []),
  ].filter((path) => existsSync(join(root, path)));
  for (const path of paths) {
    hash.update(`${path}\0`);
    hash.update(readFileSync(join(root, path)));
    hash.update("\0");
  }
  return hash.digest("hex");
}

/** What an `asset.py` may import: the library and two pure standard modules. */
const ALLOWED_IMPORTS = /^(math|random|propsmith(\.[a-z_]+)*)$/;
/** Names that reach the file system, the network or other code. */
const FORBIDDEN =
  /\b(__import__|importlib|eval|exec|compile|open|globals|locals|getattr|setattr|__builtins__|__subclasses__|os|sys|subprocess|socket|urllib|requests|shutil|pathlib|ctypes|bpy)\b/;

/**
 * Problems of an `asset.py` as source: an import outside the library, `math` and `random`, or a name that reaches
 * beyond the model (files, network, other code, `bpy` itself). This is a guard for review, not a sandbox: the build
 * runs the file, so a human reads every new asset before it is merged. Comments and docstrings are not exempt; write
 * them without these words.
 */
export function sourceProblems(source: string): string[] {
  const problems: string[] = [];
  for (const [i, line] of source.split("\n").entries()) {
    const where = `line ${i + 1}`;
    const imported = /^\s*(?:from\s+(\S+)\s+import\b|import\s+(.+))/.exec(line);
    if (imported) {
      const modules =
        imported[1] !== undefined
          ? [imported[1]]
          : (imported[2] ?? "")
              .split(",")
              .map((m) => m.trim().split(/\s+/)[0] ?? "");
      for (const module of modules)
        if (!ALLOWED_IMPORTS.test(module))
          problems.push(
            `${where}: import of "${module}" (only math, random and propsmith)`,
          );
      continue;
    }
    const name = FORBIDDEN.exec(line)?.[1];
    if (name !== undefined)
      problems.push(`${where}: "${name}" is not allowed in an asset`);
  }
  return problems;
}

/** The variant functions `asset.py` registers with `@prop`, in file order. */
export function declaredVariants(source: string): string[] {
  return [...source.matchAll(/^@prop\s*\n\s*def\s+([A-Za-z_]\w*)\s*\(/gm)].map(
    (m) => m[1] ?? "",
  );
}

function entry(asset: Asset, hash: string): IndexEntry {
  return {
    id: asset.id,
    name: asset.name,
    description: asset.description,
    category: asset.category,
    family: asset.family,
    tags: [...asset.tags].sort(compare),
    aliases: [...asset.aliases].sort(compare),
    variants: asset.variants,
    size: asset.size,
    anchors: [...asset.anchors].sort(compare),
    closed: asset.closed,
    source: asset.provenance.source,
    licence: asset.licence,
    inputHash: hash,
  };
}

/**
 * Reads every asset folder under `root/catalog` and returns the index, sorted by id. Throws with every problem found
 * (schema, vocabulary, folder name, variants not matching `asset.py`).
 */
export function buildIndex(root: string = ROOT): Index {
  const tags = parseTags(
    JSON.parse(readFileSync(join(root, TAGS_FILE), "utf8")),
  );
  const dir = join(root, CATALOG_DIR);
  const ids = readdirSync(dir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
    .sort(compare);
  const problems: string[] = [];
  const assets: IndexEntry[] = [];
  for (const id of ids) {
    const jsonPath = join(dir, id, "asset.json");
    const pyPath = join(dir, id, "asset.py");
    if (!existsSync(jsonPath) || !existsSync(pyPath)) {
      problems.push(`${id}: needs both asset.json and asset.py`);
      continue;
    }
    let asset: Asset;
    try {
      asset = parseAsset(JSON.parse(readFileSync(jsonPath, "utf8")), tags);
    } catch (error) {
      problems.push(
        `${relative(root, jsonPath)}: ${error instanceof Error ? error.message : String(error)}`,
      );
      continue;
    }
    if (asset.id !== id)
      problems.push(`${id}: asset.json says id "${asset.id}"`);
    const source = readFileSync(pyPath, "utf8");
    for (const problem of sourceProblems(source))
      problems.push(`${id}/asset.py ${problem}`);
    const declared = declaredVariants(source);
    if (declared.join(",") !== asset.variants.join(","))
      problems.push(
        `${id}: asset.json lists variants [${asset.variants.join(", ")}], asset.py registers [${declared.join(", ")}]`,
      );
    assets.push(entry(asset, inputHash(root, id)));
  }
  if (problems.length > 0) throw new Error(problems.join("\n"));
  return {
    schema: 1,
    note: "Generated by npm run catalog from catalog/*/asset.json; do not edit.",
    assets,
  };
}

/** The index as committed: JSON formatted by the repository's Prettier config, so `format:check` agrees. */
export async function formatIndex(
  index: Index,
  root: string = ROOT,
): Promise<string> {
  const options = await resolveConfig(join(root, INDEX_FILE));
  return format(JSON.stringify(index), { ...options, parser: "json" });
}

const isMain = process.argv[1]?.endsWith("tools/catalog.ts") === true;
if (isMain) {
  const next = await formatIndex(buildIndex());
  const path = join(ROOT, INDEX_FILE);
  if (process.argv.includes("--check")) {
    if (!existsSync(path) || readFileSync(path, "utf8") !== next) {
      console.error(`${INDEX_FILE} is out of date: run npm run catalog`);
      process.exit(1);
    }
    console.log(`${INDEX_FILE} is up to date`);
  } else {
    writeFileSync(path, next);
    console.log(`wrote ${INDEX_FILE}`);
  }
}
