import { spawnSync } from "node:child_process";
import {
  copyFileSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { deflateSync } from "node:zlib";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { ROOT } from "./catalog.ts";
import {
  cacheDir,
  cacheProblem,
  type FetchDeps,
  fetchTexture,
  type LedgerEntry,
  LEDGER_FILE,
  parseArgs,
  parseLedger,
  readLedger,
  resolveTextures,
  selectTextures,
  sha256,
} from "./textures.ts";

let root: string;

function write(path: string, content: string | Uint8Array): void {
  mkdirSync(dirname(join(root, path)), { recursive: true });
  writeFileSync(join(root, path), content);
}

/** A tiny opaque RGB PNG of `size` × `size` px in one colour. */
function png(size: number, rgb: [number, number, number]): Buffer {
  const crcTable = Array.from({ length: 256 }, (_, n) => {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    return c >>> 0;
  });
  const crc = (buf: Buffer) => {
    let c = 0xffffffff;
    for (const b of buf) c = (crcTable[(c ^ b) & 0xff] ?? 0) ^ (c >>> 8);
    return (c ^ 0xffffffff) >>> 0;
  };
  const chunk = (type: string, data: Buffer) => {
    const body = Buffer.concat([Buffer.from(type, "ascii"), data]);
    const out = Buffer.alloc(body.length + 8);
    out.writeUInt32BE(data.length, 0);
    body.copy(out, 4);
    out.writeUInt32BE(crc(body), body.length + 4);
    return out;
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0);
  ihdr.writeUInt32BE(size, 4);
  ihdr.set([8, 2, 0, 0, 0], 8);
  const row = Buffer.from([0, ...Array<number[]>(size).fill(rgb).flat()]);
  const raw = Buffer.concat(Array<Buffer>(size).fill(row));
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk("IHDR", ihdr),
    chunk("IDAT", deflateSync(raw)),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}

const hasZip = spawnSync("zip", ["-v"]).status === 0;

/** A zip like ambientCG's: the maps plus files the ledger does not ask for. */
function zipFixture(): Uint8Array {
  const dir = mkdtempSync(join(tmpdir(), "propsmith-texture-zip-"));
  try {
    writeFileSync(join(dir, "Test_Color.png"), png(8, [150, 100, 60]));
    writeFileSync(join(dir, "Test_NormalGL.png"), png(8, [128, 128, 255]));
    writeFileSync(join(dir, "Test.usdc"), "not a map");
    const run = spawnSync(
      "zip",
      [
        "-q",
        "-X",
        "out.zip",
        "Test_Color.png",
        "Test_NormalGL.png",
        "Test.usdc",
      ],
      { cwd: dir },
    );
    if (run.status !== 0) throw new Error(String(run.stderr));
    return new Uint8Array(readFileSync(join(dir, "out.zip")));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

function entry(over: Partial<LedgerEntry> = {}): LedgerEntry {
  return {
    name: "Wood 049",
    page: "https://ambientcg.com/view?id=Wood049",
    author: "ambientCG (Lennart Demes)",
    licence: "CC0-1.0",
    download: "https://ambientcg.com/get?file=Wood049_1K-JPG.zip",
    sha256: "0".repeat(64),
    maps: { color: "Test_Color.png", normal: "Test_NormalGL.png" },
    resolution: 512,
    ...over,
  };
}

function ledger(textures: Record<string, unknown>): string {
  return JSON.stringify({ schema: 1, note: "test", textures });
}

/** Downloads hand out `data`; resizing copies the map and records the edge it was asked for. */
function fakeDeps(data: Uint8Array) {
  const calls = { download: [] as string[], resize: [] as number[] };
  const deps: FetchDeps = {
    download: (url) => {
      calls.download.push(url);
      return Promise.resolve(data);
    },
    resize: (from, to, edge) => {
      calls.resize.push(edge);
      copyFileSync(from, to);
      return Promise.resolve();
    },
  };
  return { deps, calls };
}

beforeEach(() => {
  root = mkdtempSync(join(tmpdir(), "propsmith-textures-"));
});

afterEach(() => {
  rmSync(root, { recursive: true, force: true });
});

describe("ledger schema", () => {
  it("accepts the committed ledger: every entry CC0 with a pinned hash", () => {
    const committed = readLedger(ROOT);
    if (!committed) throw new Error(`no ${LEDGER_FILE}`);
    expect(Object.keys(committed.textures).length).toBeGreaterThan(0);
    for (const e of Object.values(committed.textures))
      expect(e.licence).toBe("CC0-1.0");
  });

  it("accepts a CC0 entry", () => {
    const parsed = parseLedger(
      JSON.parse(ledger({ "ambientcg:Wood049": entry() })),
    );
    expect(parsed.textures["ambientcg:Wood049"]?.resolution).toBe(512);
  });

  it("refuses any licence other than CC0-1.0", () => {
    for (const licence of ["CC-BY-4.0", "cc0", "CC0"])
      expect(() =>
        parseLedger(
          JSON.parse(
            ledger({
              "ambientcg:Wood049": { ...entry(), licence },
            }),
          ),
        ),
      ).toThrow("only CC0-1.0 textures may enter the ledger");
  });

  it("refuses a bad id, a missing colour map, a plain-http URL, a short hash and unknown fields", () => {
    const bad = (textures: Record<string, unknown>) => () =>
      parseLedger(JSON.parse(ledger(textures)));
    expect(bad({ "textures.com:Wood": entry() })).toThrow(
      "texture ids are <ambientcg|polyhaven>:<name>",
    );
    expect(
      bad({ "ambientcg:Wood049": entry({ maps: { color: "" } }) }),
    ).toThrow();
    expect(
      bad({
        "ambientcg:Wood049": { ...entry(), maps: { normal: "n.jpg" } },
      }),
    ).toThrow();
    expect(
      bad({ "ambientcg:Wood049": entry({ download: "http://x/y.zip" }) }),
    ).toThrow("must be an https URL");
    expect(bad({ "ambientcg:Wood049": entry({ sha256: "abc" }) })).toThrow();
    expect(
      bad({ "ambientcg:Wood049": { ...entry(), url: "https://x" } }),
    ).toThrow();
  });

  it("reads null without a ledger", () => {
    expect(readLedger(root)).toBeNull();
  });
});

describe.skipIf(!hasZip)("fetchTexture", () => {
  it("downloads, verifies, extracts only the maps and downsizes them to the ledger's resolution", async () => {
    const data = zipFixture();
    const e = entry({ sha256: sha256(data) });
    const { deps, calls } = fakeDeps(data);
    expect(cacheProblem(root, "ambientcg:Wood049", e)).toBe("not downloaded");

    expect(await fetchTexture(root, "ambientcg:Wood049", e, deps)).toBe(true);
    expect(calls.download).toEqual([e.download]);
    expect(calls.resize).toEqual([512, 512]);
    const dir = cacheDir(root, "ambientcg:Wood049");
    expect(dir).toBe(join(root, ".cache/textures/ambientcg_Wood049"));
    expect(existsSync(join(dir, "color.png"))).toBe(true);
    expect(existsSync(join(dir, "normal.png"))).toBe(true);
    expect(existsSync(join(dir, "Test.usdc"))).toBe(false);
    expect(cacheProblem(root, "ambientcg:Wood049", e)).toBeNull();

    // Up to date: nothing is downloaded again unless forced.
    expect(await fetchTexture(root, "ambientcg:Wood049", e, deps)).toBe(false);
    expect(await fetchTexture(root, "ambientcg:Wood049", e, deps, true)).toBe(
      true,
    );
    expect(calls.download).toHaveLength(2);

    // A changed entry makes the cache stale.
    expect(
      cacheProblem(root, "ambientcg:Wood049", { ...e, resolution: 256 }),
    ).toBe("downloaded from an older ledger entry");
  });

  it("fails on a hash mismatch and caches nothing", async () => {
    const data = zipFixture();
    const e = entry({ sha256: "f".repeat(64) });
    const { deps, calls } = fakeDeps(data);
    await expect(
      fetchTexture(root, "ambientcg:Wood049", e, deps),
    ).rejects.toThrow(
      `ambientcg:Wood049: SHA-256 of ${e.download} is ${sha256(data)}, the ledger says ${"f".repeat(64)}`,
    );
    expect(calls.resize).toEqual([]);
    expect(existsSync(cacheDir(root, "ambientcg:Wood049"))).toBe(false);
  });

  it("fails when the zip lacks a map the ledger names", async () => {
    const data = zipFixture();
    const e = entry({
      sha256: sha256(data),
      maps: { color: "Test_Color.png", ao: "Test_AO.png" },
    });
    await expect(
      fetchTexture(root, "ambientcg:Wood049", e, fakeDeps(data).deps),
    ).rejects.toThrow();
    expect(cacheProblem(root, "ambientcg:Wood049", e)).not.toBeNull();
  });
});

describe("resolveTextures", () => {
  it("needs no ledger when no texture is used", () => {
    expect(resolveTextures(root, [])).toEqual({});
  });

  it("fails on an id outside the ledger", () => {
    expect(() => resolveTextures(root, ["ambientcg:Wood049"])).toThrow(
      `unknown texture "ambientcg:Wood049": not in ${LEDGER_FILE}`,
    );
    write(LEDGER_FILE, ledger({ "ambientcg:Wood049": entry() }));
    expect(() => resolveTextures(root, ["polyhaven:rock_01"])).toThrow(
      `unknown texture "polyhaven:rock_01": not in ${LEDGER_FILE}`,
    );
  });

  it("names the command when a texture is not downloaded or a cached map is missing", () => {
    const e = entry();
    write(LEDGER_FILE, ledger({ "ambientcg:Wood049": e }));
    expect(() => resolveTextures(root, ["ambientcg:Wood049"])).toThrow(
      'texture "ambientcg:Wood049" not downloaded (.cache/textures/ambientcg_Wood049); run npm run textures -- ambientcg:Wood049',
    );
    const dir = ".cache/textures/ambientcg_Wood049";
    write(
      `${dir}/ledger.json`,
      JSON.stringify(
        { sha256: e.sha256, resolution: e.resolution, maps: e.maps },
        null,
        2,
      ),
    );
    write(`${dir}/color.png`, png(2, [0, 0, 0]));
    expect(() => resolveTextures(root, ["ambientcg:Wood049"])).toThrow(
      `texture "ambientcg:Wood049" missing ${dir}/normal.png`,
    );
    write(`${dir}/normal.png`, png(2, [0, 0, 0]));
    expect(resolveTextures(root, ["ambientcg:Wood049"])).toEqual({
      "ambientcg:Wood049": {
        color: join(root, dir, "color.png"),
        normal: join(root, dir, "normal.png"),
      },
    });
  });
});

describe("textures arguments", () => {
  it("parses ids and --force", () => {
    expect(parseArgs([])).toEqual({ ids: [], force: false });
    expect(parseArgs(["ambientcg:Wood049", "--force"])).toEqual({
      ids: ["ambientcg:Wood049"],
      force: true,
    });
    expect(() => parseArgs(["--nope"])).toThrow("unknown option --nope");
  });

  it("selects the given ids or all, and refuses one outside the ledger", () => {
    const l = parseLedger(
      JSON.parse(
        ledger({ "ambientcg:Wood049": entry(), "ambientcg:Bark001": entry() }),
      ),
    );
    expect(selectTextures(l, [])).toEqual([
      "ambientcg:Bark001",
      "ambientcg:Wood049",
    ]);
    expect(selectTextures(l, ["ambientcg:Wood049"])).toEqual([
      "ambientcg:Wood049",
    ]);
    expect(() => selectTextures(l, ["ambientcg:Nope"])).toThrow(
      'unknown texture "ambientcg:Nope"',
    );
  });
});
