import { spawnSync } from "node:child_process";
import {
  copyFileSync,
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import { join } from "node:path";
import sharp from "sharp";

import { runBlender } from "./blender.ts";
import { buildJob } from "./build.ts";
import { ROOT, usedTextures } from "./catalog.ts";
import { resolveTextures } from "./textures.ts";

/**
 * `npm run shots -- <id>… [--size <px>] [--push <slug>]` (needs Blender): the PR pictures of an asset.
 *
 * Renders every variant with the review rig, framed so the asset fills a `--size` px picture (1024 by default), into
 * `.cache/shots/<id>/<variant>_{iso,front}.png`. The build's review renders keep a fixed scale per metre, which leaves
 * a candle a few dozen pixels wide; these are for people looking at a PR. `--push <slug>` copies them to the
 * `pr-assets` branch under `<slug>/` (through a worktree in `.cache/pr-assets`), pushes it and prints the "What it
 * looks like" table for the PR body.
 */
export const SHOTS_DIR = ".cache/shots";
/** Outside `tools/blender/`, whose files are part of every asset's input hash: a PR picture changes no build. */
const SHOTS_SCRIPTS = join(import.meta.dirname, "shots");
export const PR_ASSETS_BRANCH = "pr-assets";
export const RAW_BASE = `https://raw.githubusercontent.com/lipelix/propsmith/${PR_ASSETS_BRANCH}`;

export interface ShotsArgs {
  ids: string[];
  size: number;
  push: string | null;
}

export function parseShotsArgs(argv: readonly string[]): ShotsArgs {
  const args: ShotsArgs = { ids: [], size: 1024, push: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i] ?? "";
    if (a === "--size") {
      const v = Number(argv[++i]);
      if (!Number.isInteger(v) || v < 128 || v > 4096)
        throw new Error("--size needs a whole number of px from 128 to 4096");
      args.size = v;
    } else if (a === "--push") {
      const v = argv[++i];
      if (!v || !/^[a-z0-9][a-z0-9-]*$/.test(v))
        throw new Error("--push needs a slug (lower case, digits, dashes)");
      args.push = v;
    } else if (a.startsWith("--")) throw new Error(`unknown option ${a}`);
    else args.ids.push(a);
  }
  if (args.ids.length === 0) throw new Error("name at least one asset id");
  return args;
}

/** The PR body section: one row per variant, three-quarter and front view side by side. */
export function prMarkdown(slug: string, variants: readonly string[]): string {
  const rows = variants.map(
    (v) =>
      `| <img src="${RAW_BASE}/${slug}/${v}_iso.png" width="420" alt="${v}, three-quarter view"> ` +
      `| <img src="${RAW_BASE}/${slug}/${v}_front.png" width="300" alt="${v}, front view"> |`,
  );
  return [
    "## What it looks like",
    "",
    "| Three-quarter view | Front (-y) |",
    "| --- | --- |",
    ...rows,
    "",
    "Rendered with `npm run shots` (the review rig, framed to fill the picture).",
  ].join("\n");
}

/** How much larger than the asked size Blender renders. */
const RENDER_OVERSIZE = 1.5;

/** Margin around the content, as a share of the longer side. */
const MARGIN = 0.04;

/**
 * Crops a render to what it draws (the framing uses bounding-box corners, so a round asset leaves empty corners) and
 * scales it back so its longer side is `size` px, with a transparent margin.
 */
export async function fitPicture(path: string, size: number): Promise<void> {
  const trimmed = await sharp(path).trim({ threshold: 1 }).toBuffer();
  const pad = Math.round(size * MARGIN);
  const inner = size - 2 * pad;
  const resized = await sharp(trimmed)
    .resize(inner, inner, { fit: "inside" })
    .extend({
      top: pad,
      bottom: pad,
      left: pad,
      right: pad,
      background: { r: 0, g: 0, b: 0, alpha: 0 },
    })
    .png()
    .toBuffer();
  writeFileSync(path, resized);
}

/** Renders the shots of asset `id`; returns its variant ids. */
export async function shootAsset(
  root: string,
  id: string,
  size: number,
): Promise<string[]> {
  const out = join(root, SHOTS_DIR, id);
  // Rendered larger than asked: the crop in fitPicture then only ever shrinks.
  const job = {
    ...buildJob(root, id),
    out,
    size: Math.ceil(size * RENDER_OVERSIZE),
  };
  job.textures = resolveTextures(
    root,
    usedTextures(readFileSync(job.asset.file, "utf8")),
  );
  mkdirSync(out, { recursive: true });
  const jobPath = join(out, "job.json");
  writeFileSync(jobPath, JSON.stringify(job, null, 2));
  runBlender("shots.py", [jobPath], SHOTS_SCRIPTS);
  for (const v of job.asset.variants)
    for (const view of ["iso", "front"]) {
      const path = join(out, `${v}_${view}.png`);
      if (!existsSync(path))
        throw new Error(`${id}: shots.py did not write ${v}_${view}.png`);
      await fitPicture(path, size);
    }
  return job.asset.variants;
}

function git(args: readonly string[], cwd: string): string {
  const result = spawnSync("git", args, { cwd, encoding: "utf8" });
  if (result.status !== 0)
    throw new Error(`git ${args.join(" ")}: ${result.stderr.trim()}`);
  return result.stdout.trim();
}

/** Copies the shots of `ids` to `pr-assets/<slug>/`, commits and pushes; a no-op commit is skipped. */
export function pushShots(
  root: string,
  slug: string,
  shots: Readonly<Record<string, readonly string[]>>,
): void {
  const tree = join(root, ".cache/pr-assets");
  git(["fetch", "-q", "origin", PR_ASSETS_BRANCH], root);
  if (existsSync(tree))
    git(["checkout", "-q", "--detach", `origin/${PR_ASSETS_BRANCH}`], tree);
  else
    git(
      ["worktree", "add", "-q", "--detach", tree, `origin/${PR_ASSETS_BRANCH}`],
      root,
    );
  mkdirSync(join(tree, slug), { recursive: true });
  for (const [id, variants] of Object.entries(shots))
    for (const v of variants)
      for (const view of ["iso", "front"])
        copyFileSync(
          join(root, SHOTS_DIR, id, `${v}_${view}.png`),
          join(tree, slug, `${v}_${view}.png`),
        );
  git(["add", slug], tree);
  if (git(["status", "--porcelain", "--", slug], tree) === "") return;
  git(
    [
      "commit",
      "-q",
      "-m",
      `chore: PR shots of ${Object.keys(shots).join(", ")}`,
    ],
    tree,
  );
  git(["push", "-q", "origin", `HEAD:${PR_ASSETS_BRANCH}`], tree);
}

async function main(): Promise<void> {
  const args = parseShotsArgs(process.argv.slice(2));
  const shots: Record<string, string[]> = {};
  for (const id of args.ids) {
    const started = Date.now();
    shots[id] = await shootAsset(ROOT, id, args.size);
    console.log(
      `${id}: ${shots[id].length} variant(s) in ${SHOTS_DIR}/${id}, ${((Date.now() - started) / 1000).toFixed(1)} s`,
    );
  }
  if (args.push === null) return;
  pushShots(ROOT, args.push, shots);
  console.log(`pushed to ${PR_ASSETS_BRANCH}/${args.push}/\n`);
  console.log(prMarkdown(args.push, Object.values(shots).flat()));
}

if (process.argv[1]?.endsWith("tools/shots.ts") === true) {
  try {
    await main();
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}
