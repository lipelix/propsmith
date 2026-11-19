import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { delimiter, join } from "node:path";

/** Blender scripts of the build. */
export const BLENDER_SCRIPTS = join(import.meta.dirname, "blender");

const MAC_BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender";

/** `$BLENDER`, else the macOS app, else `blender` on `$PATH` (Linux, e.g. ~/.local/bin);
 * undefined when none exists (CI). */
export function findBlender(
  env: NodeJS.ProcessEnv = process.env,
  exists: (path: string) => boolean = existsSync,
): string | undefined {
  if (env.BLENDER) return env.BLENDER;
  if (exists(MAC_BLENDER)) return MAC_BLENDER;
  return (env.PATH ?? "")
    .split(delimiter)
    .filter(Boolean)
    .map((dir) => join(dir, "blender"))
    .find((path) => exists(path));
}

export function requireBlender(): string {
  const blender = findBlender();
  if (!blender)
    throw new Error(
      "Blender not found: install Blender 5.2 LTS or set $BLENDER",
    );
  return blender;
}

/** Runs a script from `tools/blender/` (or `dir`) headless; throws with Blender's output on failure. */
export function runBlender(
  script: string,
  args: string[],
  dir: string = BLENDER_SCRIPTS,
): string {
  const result = spawnSync(
    requireBlender(),
    [
      "-b",
      "--factory-startup",
      "--python-exit-code",
      "1",
      "--python",
      join(dir, script),
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
