import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";

/** Blender scripts of the build. */
export const BLENDER_SCRIPTS = join(import.meta.dirname, "blender");

const MAC_BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender";

/** `$BLENDER`, else the macOS app; undefined when neither exists (CI). */
export function findBlender(
  env: NodeJS.ProcessEnv = process.env,
  exists: (path: string) => boolean = existsSync,
): string | undefined {
  if (env.BLENDER) return env.BLENDER;
  return exists(MAC_BLENDER) ? MAC_BLENDER : undefined;
}

export function requireBlender(): string {
  const blender = findBlender();
  if (!blender)
    throw new Error(
      "Blender not found: install Blender 5.2 LTS or set $BLENDER",
    );
  return blender;
}

/** Runs a script from `tools/blender/` headless; throws with Blender's output on failure. */
export function runBlender(script: string, args: string[]): string {
  const result = spawnSync(
    requireBlender(),
    [
      "-b",
      "--factory-startup",
      "--python-exit-code",
      "1",
      "--python",
      join(BLENDER_SCRIPTS, script),
      "--",
      ...args,
    ],
    { encoding: "utf8", maxBuffer: 256 * 1024 * 1024 },
  );
  const output = `${result.stdout}${result.stderr}`;
  if (result.status !== 0)
    throw new Error(
      `Blender ${script} failed (${result.status ?? result.signal}):\n${output.slice(-4000)}`,
    );
  return output;
}
