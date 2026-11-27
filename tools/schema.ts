import { z } from "zod";

import { isVariantOf, SNAKE } from "./ids.ts";

/**
 * `catalog/<id>/asset.json`: what an asset is, for search and for the checks. The geometry lives next to it in
 * `asset.py`; this file carries the facts code reads. Sizes are metres, z up. Nothing game-specific belongs here
 * (tiles, cover, hit points): a game keeps those in its own overlay. Design: `docs/plans/2026-11-14-propsmith-design.md`.
 */
const snake = z.string().regex(SNAKE, "must be snake_case");

export const CATEGORIES = [
  "structure",
  "door",
  "fence",
  "container",
  "furniture",
  "decor",
  "vegetation",
  "light",
  "weapon",
] as const;
export type Category = (typeof CATEGORIES)[number];

/** An anchor: a named point in the model for an effect, `<light|fire|smoke|water>:<name>` (read back by the build). */
export const ANCHOR = /^(light|fire|smoke|water):[a-z0-9]+(_[a-z0-9]+)*$/;

/** Every catalogue asset is dedicated to the public domain. */
export const LICENCE = "CC0-1.0";

function unique<T>(items: readonly T[]): boolean {
  return new Set(items).size === items.length;
}

const sizeSchema = z
  .object({
    /** Metres along local x, centred on the origin. */
    x: z.number().positive().max(12),
    /** Metres along local y, centred on the origin; the front faces -y. */
    y: z.number().positive().max(12),
    /** Metres up from the ground (z = 0). */
    z: z.number().positive().max(12),
  })
  .strict();

/** Where a hanging prop is fixed. The model still stands on z = 0 in the catalogue; a game lifts it by `lift`. */
export const MOUNTS = ["ceiling", "wall"] as const;
export type MountKind = (typeof MOUNTS)[number];

const mountSchema = z
  .object({
    /**
     * `ceiling`: it hangs from the top of the model, its highest point against the ceiling (chandelier, lantern on a
     * chain). `wall`: its back (the largest y, the front faces -y) lies flat on the wall (sconce, shield, sign).
     */
    kind: z.enum(MOUNTS),
    /**
     * Metres to raise the model off the floor to hang it where it was made to hang: a ceiling prop's top then meets
     * a ceiling at `lift` plus its height.
     */
    lift: z.number().positive().max(12),
  })
  .strict();

/**
 * A hand-held prop's grip points (`grip()` in asset.py, measured by the build). `main` and `off` are where each hand
 * closes round the handle, each with an axis along it; `stock` is where a crossbow sets against the shoulder and
 * `trigger` where a finger pulls.
 */
export const GRIPS = ["main", "off", "stock", "trigger"] as const;
export type GripName = (typeof GRIPS)[number];

const gripSchema = z
  .object({
    /** The grip points every variant has; `main` always, `off` for a two-handed hold. */
    points: z
      .array(z.enum(GRIPS))
      .min(1)
      .refine(unique, "grip points repeat")
      .refine((points) => points.includes("main"), "needs main"),
    /**
     * The hand the grips are laid out for: its breadth across the knuckles in metres (an adult's is about 0.085). A
     * consumer with a bigger or smaller hand scales the spacing of `main` and `off` by its own over this.
     */
    hand: z.number().min(0.05).max(0.15),
  })
  .strict();

const provenanceSchema = z.discriminatedUnion("source", [
  z
    .object({
      source: z.literal("generated"),
      /** The text the asset was generated from. */
      prompt: z.string().min(1),
    })
    .strict(),
  z.object({ source: z.literal("handwritten") }).strict(),
  z
    .object({
      source: z.literal("pack"),
      /** A CC0 asset pack and the asset's id in it. */
      pack: z.string().min(1),
      packId: z.string().min(1),
      url: z.url(),
    })
    .strict(),
]);

export const assetSchema = z
  .object({
    schema: z.literal(1),
    // Search
    id: snake,
    name: z.string().min(1),
    description: z.string().min(1),
    category: z.enum(CATEGORIES),
    /** What kind of thing it is across materials and styles (`well`, `cart`, `pot`); tags must not repeat it. */
    family: snake,
    /** From `catalog/tags.json`, checked by `assetProblems`. */
    tags: z.array(snake).refine(unique, "tags repeat"),
    /** Other words a search should find it by. */
    aliases: z.array(z.string().min(1)).refine(unique, "aliases repeat"),
    /** Variant ids in `asset.py` order: `<id>` or `<id>_<suffix>`. The first is the default. */
    variants: z.array(snake).min(1).refine(unique, "variants repeat"),
    /** The box every variant must stay inside. */
    size: sizeSchema,
    /** Named effect points, present in every variant. */
    anchors: z
      .array(
        z
          .string()
          .regex(ANCHOR, "must be <light|fire|smoke|water>:<snake_case>"),
      )
      .refine(unique, "anchors repeat"),
    /** Every part is a closed mesh (the `manifold` check): needed for fracture or printing. */
    closed: z.boolean(),
    /** How a hanging prop is fixed; absent for a prop that stands on the floor. */
    mount: mountSchema.optional(),
    /** Where hands hold it; every weapon has one. */
    grip: gripSchema.optional(),
    provenance: provenanceSchema,
    licence: z.literal(LICENCE),
  })
  .strict()
  .superRefine((asset, ctx) => {
    if (asset.category === "weapon" && asset.grip === undefined)
      ctx.addIssue({
        code: "custom",
        path: ["grip"],
        message: "a weapon needs its grip points",
      });
    for (const [i, variant] of asset.variants.entries())
      if (!isVariantOf(variant, asset.id))
        ctx.addIssue({
          code: "custom",
          path: ["variants", i],
          message: `variant "${variant}" must be "${asset.id}" or start with "${asset.id}_"`,
        });
  });
export type Asset = z.infer<typeof assetSchema>;

/** `catalog/tags.json`: the tag vocabulary, grouped into facets for the catalogue site. */
export const tagsSchema = z
  .object({
    schema: z.literal(1),
    note: z.string(),
    groups: z.record(snake, z.array(snake).min(1)),
  })
  .strict();
export type Tags = z.infer<typeof tagsSchema>;

/** Problems in the vocabulary itself: a tag in two groups, or a tag that names a category. */
export function tagsProblems(tags: Tags): string[] {
  const problems: string[] = [];
  const seen = new Map<string, string>();
  for (const [group, list] of Object.entries(tags.groups))
    for (const tag of list) {
      const other = seen.get(tag);
      if (other !== undefined)
        problems.push(`tag "${tag}" is in both "${other}" and "${group}"`);
      seen.set(tag, group);
      if ((CATEGORIES as readonly string[]).includes(tag))
        problems.push(`tag "${tag}" repeats a category`);
    }
  return problems;
}

/** Every tag of the vocabulary. */
export const vocabulary = (tags: Tags): Set<string> =>
  new Set(Object.values(tags.groups).flat());

/** Problems of a parsed asset against the vocabulary; an empty list means it is sound. */
export function assetProblems(asset: Asset, tags: Tags): string[] {
  const known = vocabulary(tags);
  const problems: string[] = [];
  const aliases = new Set(asset.aliases.map((a) => a.toLowerCase()));
  for (const tag of asset.tags) {
    if (!known.has(tag)) problems.push(`${asset.id}: unknown tag "${tag}"`);
    if (tag === asset.family)
      problems.push(`${asset.id}: tag "${tag}" repeats the family`);
    if (aliases.has(tag))
      problems.push(`${asset.id}: tag "${tag}" repeats an alias`);
  }
  return problems;
}

/** Parses `asset.json`, throwing on a schema error or a vocabulary problem. */
export function parseAsset(json: unknown, tags: Tags): Asset {
  const parsed = assetSchema.safeParse(json);
  if (!parsed.success) throw new Error(z.prettifyError(parsed.error));
  const problems = assetProblems(parsed.data, tags);
  if (problems.length > 0) throw new Error(problems.join("\n"));
  return parsed.data;
}

/** Parses `tags.json`, throwing on a schema error or a vocabulary problem. */
export function parseTags(json: unknown): Tags {
  const parsed = tagsSchema.safeParse(json);
  if (!parsed.success) throw new Error(z.prettifyError(parsed.error));
  const problems = tagsProblems(parsed.data);
  if (problems.length > 0) throw new Error(problems.join("\n"));
  return parsed.data;
}
