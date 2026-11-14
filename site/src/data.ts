/** What the site reads from `data/`: the catalogue index, the measurements and the bake manifest, joined per asset. */
export interface Vec3 {
  x: number;
  y: number;
  z: number;
}

export interface Variant {
  id: string;
  glb: string;
  png: string;
  glbBytes: number;
  tris: number;
  /** Measured size in metres. */
  measured: Vec3;
}

export interface Asset {
  id: string;
  name: string;
  description: string;
  category: string;
  family: string;
  tags: string[];
  aliases: string[];
  /** The declared box in metres. */
  size: Vec3;
  anchors: string[];
  closed: boolean;
  source: "generated" | "handwritten" | "pack";
  licence: string;
  variants: Variant[];
}

export interface Catalogue {
  assets: Asset[];
  /** Tag → facet group (`material`, `setting`, ...), for the facets. */
  tagGroups: Record<string, string>;
}

interface IndexFile {
  assets: (Omit<Asset, "variants"> & { variants: string[] })[];
}
interface MeasurementsFile {
  assets: Record<
    string,
    {
      variants: {
        id: string;
        tris: number;
        bbox: { min: number[]; max: number[] };
      }[];
    }
  >;
}
interface ManifestFile {
  assets: Record<
    string,
    { variants: { id: string; glb: string; png: string; glbBytes: number }[] }
  >;
}

export const DATA = "data";

async function json<T>(file: string): Promise<T> {
  const response = await fetch(`${DATA}/${file}`);
  if (!response.ok)
    throw new Error(`${file}: ${response.status} ${response.statusText}`);
  return (await response.json()) as T;
}

const round = (value: number): number => Math.round(value * 100) / 100;

/** Joins the three files; an asset with no baked variant is left out (it has nothing to show). */
export function join(
  index: IndexFile,
  measurements: MeasurementsFile,
  manifest: ManifestFile,
  tags: { groups: Record<string, string[]> },
): Catalogue {
  const assets: Asset[] = [];
  for (const entry of index.assets) {
    const baked = manifest.assets[entry.id]?.variants ?? [];
    const measured = measurements.assets[entry.id]?.variants ?? [];
    const variants = entry.variants.flatMap((id): Variant[] => {
      const b = baked.find((v) => v.id === id);
      const m = measured.find((v) => v.id === id);
      if (!b || !m) return [];
      const [x0 = 0, y0 = 0, z0 = 0] = m.bbox.min;
      const [x1 = 0, y1 = 0, z1 = 0] = m.bbox.max;
      return [
        {
          ...b,
          tris: m.tris,
          measured: { x: round(x1 - x0), y: round(y1 - y0), z: round(z1 - z0) },
        },
      ];
    });
    if (variants.length > 0) assets.push({ ...entry, variants });
  }
  const tagGroups: Record<string, string> = {};
  for (const [group, list] of Object.entries(tags.groups))
    for (const tag of list) tagGroups[tag] = group;
  return { assets, tagGroups };
}

export async function load(): Promise<Catalogue> {
  const [index, measurements, manifest, tags] = await Promise.all([
    json<IndexFile>("index.json"),
    json<MeasurementsFile>("measurements.json"),
    json<ManifestFile>("assets.json"),
    json<{ groups: Record<string, string[]> }>("tags.json"),
  ]);
  return join(index, measurements, manifest, tags);
}

/** `0.64 × 0.64 × 0.9 m` */
export const metres = (v: Vec3): string => `${v.x} × ${v.y} × ${v.z} m`;

/** `6.9k` from 6,936; plain below a thousand. */
export const count = (n: number): string =>
  n < 1000 ? String(n) : `${Number((n / 1000).toFixed(1))}k`;

/** `624 KB` */
export const kilobytes = (bytes: number): string =>
  `${Math.ceil(bytes / 1024)} KB`;
