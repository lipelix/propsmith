import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { createServer } from "node:http";
import type { AddressInfo } from "node:net";
import { extname, join } from "node:path";
import { chromium } from "@playwright/test";

import { buildManifest, PUBLISH_DIR } from "./bake.ts";
import { ROOT } from "./catalog.ts";

/**
 * `npm run bake:look [-- <id>…]`: the baked GLBs in a browser next to the Blender snapshots, as one picture
 * (`.cache/bake-look.png`), to judge what the bake keeps of the look. The GLB is shown by `<model-viewer>` from the
 * same three-quarter direction under neutral image-based light with AgX tone mapping; the snapshot is lit by the
 * review rig's low sun, so shading differs while colours and detail should agree.
 */
const OUT = ".cache/bake-look.png";
const TYPES: Record<string, string> = {
  ".js": "text/javascript",
  ".png": "image/png",
  ".glb": "model/gltf-binary",
};

function page(rows: readonly { id: string; glb: string; png: string }[]) {
  const row = (r: { id: string; glb: string; png: string }) => `
<div class="row">
  <div class="cell"><span>${r.id}: Blender snapshot</span><img src="/${PUBLISH_DIR}/${r.png}" alt=""></div>
  <div class="cell"><span>${r.id}: baked GLB in the browser</span>
    <model-viewer src="/${PUBLISH_DIR}/${r.glb}" camera-orbit="45deg 60deg auto" field-of-view="12deg"
      exposure="0.7" tone-mapping="agx" shadow-intensity="0.8" environment-image="neutral"></model-viewer></div>
</div>`;
  return `<!doctype html><meta charset="utf-8"><style>
body{margin:0;background:#8d8a80;font:14px system-ui;color:#111}
.row{display:flex;gap:8px;padding:8px 8px 0}
.cell{width:440px;height:470px;display:flex;align-items:center;justify-content:center;background:#a39f93;position:relative}
.cell span{position:absolute;top:6px;left:8px}
model-viewer{width:440px;height:470px}
img{max-width:420px;max-height:430px;margin-top:20px}
</style>
<script type="module" src="/node_modules/@google/model-viewer/dist/model-viewer.min.js"></script>
${rows.map(row).join("")}`;
}

async function main(): Promise<void> {
  const ids = process.argv.slice(2);
  const manifest = buildManifest(ROOT);
  for (const id of ids)
    if (!(id in manifest.assets))
      throw new Error(`"${id}" is not baked: run npm run bake -- ${id}`);
  const rows = Object.entries(manifest.assets)
    .filter(([id]) => ids.length === 0 || ids.includes(id))
    .flatMap(([, asset]) => asset.variants);
  if (rows.length === 0) throw new Error("nothing baked: run npm run bake");
  const html = page(rows);
  const server = createServer((request, response) => {
    const path = decodeURIComponent((request.url ?? "/").split("?")[0] ?? "/");
    if (path === "/") {
      response.writeHead(200, { "content-type": "text/html" }).end(html);
      return;
    }
    const file = join(ROOT, path);
    if (!file.startsWith(ROOT) || !existsSync(file)) {
      response.writeHead(404).end();
      return;
    }
    response
      .writeHead(200, {
        "content-type": TYPES[extname(file)] ?? "application/octet-stream",
      })
      .end(readFileSync(file));
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const { port } = server.address() as AddressInfo;
  const browser = await chromium.launch();
  try {
    const tab = await browser.newPage({
      viewport: { width: 904, height: 478 * rows.length + 8 },
      deviceScaleFactor: 2,
    });
    await tab.goto(`http://127.0.0.1:${port}/`);
    await tab.waitForFunction(
      "[...document.querySelectorAll('model-viewer')].every((m) => m.loaded)",
    );
    await tab.waitForTimeout(1500);
    mkdirSync(join(ROOT, ".cache"), { recursive: true });
    await tab.screenshot({ path: join(ROOT, OUT) });
  } finally {
    await browser.close();
    server.close();
  }
  console.log(
    `wrote ${OUT}: ${rows.length} variant${rows.length === 1 ? "" : "s"}`,
  );
}

if (process.argv[1]?.endsWith("tools/look.ts") === true) {
  try {
    await main();
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}
