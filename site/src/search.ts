import type { Asset } from "./data.ts";

/** What the catalogue is filtered by: free text, one category, and tags that must all be present. */
export interface Query {
  text: string;
  category: string | null;
  tags: readonly string[];
}

export const EMPTY: Query = { text: "", category: null, tags: [] };

const words = (text: string): string[] =>
  text
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter(Boolean);

/** Everything a search may match of an asset, lower case. */
function haystack(asset: Asset): string {
  return [
    asset.id,
    asset.name,
    asset.description,
    asset.category,
    asset.family,
    ...asset.tags,
    ...asset.aliases,
  ]
    .join(" ")
    .toLowerCase();
}

/** Every word of the text is somewhere in the asset (as a prefix of a word), the category matches, every tag is there. */
export function matches(asset: Asset, query: Query): boolean {
  if (query.category !== null && asset.category !== query.category)
    return false;
  if (!query.tags.every((tag) => asset.tags.includes(tag))) return false;
  const hay = words(haystack(asset));
  return words(query.text).every((w) => hay.some((h) => h.startsWith(w)));
}

export const filter = (assets: readonly Asset[], query: Query): Asset[] =>
  assets.filter((asset) => matches(asset, query));

export interface Facet {
  value: string;
  /** Assets left if this value were added to the query. */
  count: number;
  selected: boolean;
}

/** Categories with how many assets each would leave, given the rest of the query. */
export function categoryFacets(
  assets: readonly Asset[],
  query: Query,
): Facet[] {
  const rest = filter(assets, { ...query, category: null });
  const values = [...new Set(assets.map((a) => a.category))].sort();
  return values.map((value) => ({
    value,
    count: rest.filter((a) => a.category === value).length,
    selected: query.category === value,
  }));
}

/** Tags by facet group, each with how many of the current results carry it. */
export function tagFacets(
  assets: readonly Asset[],
  query: Query,
  groups: Readonly<Record<string, string>>,
): Record<string, Facet[]> {
  const current = filter(assets, query);
  const used = [...new Set(assets.flatMap((a) => a.tags))].sort();
  const out: Record<string, Facet[]> = {};
  for (const value of used) {
    const group = groups[value] ?? "other";
    (out[group] ??= []).push({
      value,
      count: current.filter((a) => a.tags.includes(value)).length,
      selected: query.tags.includes(value),
    });
  }
  return out;
}

/** The query with `tag` switched on or off. */
export const toggleTag = (query: Query, tag: string): Query => ({
  ...query,
  tags: query.tags.includes(tag)
    ? query.tags.filter((t) => t !== tag)
    : [...query.tags, tag],
});
