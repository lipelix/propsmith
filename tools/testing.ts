/** A valid `asset.json` for tests, with `over` replacing top-level fields. */
export function assetJson(
  id: string,
  over: Record<string, unknown> = {},
): Record<string, unknown> {
  return {
    schema: 1,
    id,
    name: id,
    description: `A ${id}.`,
    category: "decor",
    family: id.split("_")[0],
    tags: ["wood", "village"],
    aliases: [],
    variants: [id],
    size: { x: 1, y: 1, z: 1 },
    anchors: [],
    closed: false,
    provenance: { source: "handwritten" },
    licence: "CC0-1.0",
    ...over,
  };
}

export const TAGS = {
  schema: 1,
  note: "",
  groups: { material: ["wood", "stone"], setting: ["village"] },
} as const;
