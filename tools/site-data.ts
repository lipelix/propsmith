import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { join } from "node:path";

import { MANIFEST_FILE, PUBLISH_DIR } from "./bake.ts";
import { INDEX_FILE, ROOT } from "./catalog.ts";
import { MEASUREMENTS_FILE } from "./measurements.ts";

/**
 * `npm run site:data`: puts what the site reads into `site/public/data/` (not committed): the index, the
 * measurements, the tag vocabulary and the baked assets (`npm run bake`).
 */
const OUT = "site/public/data";

if (!existsSync(join(ROOT, MANIFEST_FILE))) {
  console.error(`no ${MANIFEST_FILE}: run npm run bake first`);
  process.exit(1);
}
rmSync(join(ROOT, OUT), { recursive: true, force: true });
mkdirSync(join(ROOT, OUT), { recursive: true });
cpSync(join(ROOT, PUBLISH_DIR), join(ROOT, OUT), {
  recursive: true,
  filter: (source) => !source.endsWith("bake.json"),
});
cpSync(join(ROOT, INDEX_FILE), join(ROOT, OUT, "index.json"));
cpSync(join(ROOT, MEASUREMENTS_FILE), join(ROOT, OUT, "measurements.json"));
cpSync(join(ROOT, "catalog/tags.json"), join(ROOT, OUT, "tags.json"));
console.log(`wrote ${OUT}`);
