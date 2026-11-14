import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { assetIds, ledgerIds, readAsset } from "./build.ts";
import {
  buildIndex,
  formatIndex,
  INDEX_FILE,
  inputHash,
  ROOT,
} from "./catalog.ts";
import {
  type AssetReport,
  exitCode,
  formatReport,
  runChecks,
  summary,
} from "./checks.ts";
import {
  asMeasured,
  MEASUREMENTS_FILE,
  readMeasurements,
} from "./measurements.ts";

/**
 * `npm run catalog:check` (part of `npm run check`, needs no Blender): every asset is valid, `catalog/index.json` is
 * fresh, and every asset passes its checks against the measurement committed in `catalog/measurements.json`. A missing
 * or stale measurement (the asset, the library or the build changed since) is `NOT CHECKED`, which fails: run
 * `npm run build` and commit the result.
 */
export interface CatalogCheck {
  reports: AssetReport[];
  /** Problems outside single assets: a stale index, measurements of assets that no longer exist. */
  problems: string[];
}

export async function checkCatalog(root: string): Promise<CatalogCheck> {
  const problems: string[] = [];
  const indexPath = join(root, INDEX_FILE);
  const index = await formatIndex(buildIndex(root), root);
  if (!existsSync(indexPath) || readFileSync(indexPath, "utf8") !== index)
    problems.push(`${INDEX_FILE} is out of date: run npm run catalog`);

  const ids = assetIds(root);
  const measurements = readMeasurements(root);
  for (const id of Object.keys(measurements.assets))
    if (!ids.includes(id))
      problems.push(
        `${MEASUREMENTS_FILE} has "${id}", which is not in the catalogue: run npm run build`,
      );

  const ledger = ledgerIds(root);
  const reports = ids.map((id): AssetReport => {
    const measured = measurements.assets[id];
    const fresh = measured?.inputHash === inputHash(root, id);
    const result = measured && fresh ? asMeasured(measured) : null;
    return {
      id,
      checks: runChecks({
        asset: readAsset(root, id),
        result,
        ledger,
        noResult: measured
          ? `the committed measurement is stale: run npm run build -- ${id}`
          : `no committed measurement: run npm run build -- ${id}`,
      }),
      result,
      cached: false,
      seconds: 0,
      committed: true,
    };
  });
  return { reports, problems };
}

if (process.argv[1]?.endsWith("tools/check.ts") === true) {
  try {
    const { reports, problems } = await checkCatalog(ROOT);
    for (const report of reports) console.log(formatReport(report));
    for (const problem of problems) console.error(problem);
    console.log(summary(reports));
    if (problems.length > 0 || exitCode(reports) !== 0) process.exit(1);
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}
