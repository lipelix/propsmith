import { useMemo, useState } from "preact/hooks";

import { type Catalogue, count, DATA, metres } from "./data.ts";
import { SearchIcon } from "./icons.tsx";
import {
  categoryFacets,
  EMPTY,
  filter,
  type Query,
  tagFacets,
  toggleTag,
} from "./search.ts";

const GROUP_ORDER = [
  "material",
  "setting",
  "use",
  "look",
  "condition",
  "other",
];

export function List({ catalogue }: { catalogue: Catalogue }) {
  const [query, setQuery] = useState<Query>(EMPTY);
  const { assets, tagGroups } = catalogue;
  const results = useMemo(() => filter(assets, query), [assets, query]);
  const categories = useMemo(
    () => categoryFacets(assets, query),
    [assets, query],
  );
  const tags = useMemo(
    () => tagFacets(assets, query, tagGroups),
    [assets, query, tagGroups],
  );
  const filtered =
    query.text !== "" || query.category !== null || query.tags.length > 0;

  return (
    <main class="catalogue">
      <aside class="facets" aria-label="Filters">
        <label class="search">
          <SearchIcon />
          <span class="visually-hidden">Search the catalogue</span>
          <input
            type="search"
            placeholder="Search props"
            value={query.text}
            onInput={(event) =>
              setQuery({ ...query, text: event.currentTarget.value })
            }
          />
        </label>
        <fieldset>
          <legend>Category</legend>
          <div class="chips">
            {categories.map((facet) => (
              <button
                type="button"
                key={facet.value}
                class="chip"
                aria-pressed={facet.selected}
                disabled={facet.count === 0 && !facet.selected}
                onClick={() =>
                  setQuery({
                    ...query,
                    category: facet.selected ? null : facet.value,
                  })
                }
              >
                {facet.value} <span class="num">{facet.count}</span>
              </button>
            ))}
          </div>
        </fieldset>
        {GROUP_ORDER.filter((group) => tags[group]).map((group) => (
          <fieldset key={group}>
            <legend>{group}</legend>
            <div class="chips">
              {(tags[group] ?? []).map((facet) => (
                <button
                  type="button"
                  key={facet.value}
                  class="chip"
                  aria-pressed={facet.selected}
                  disabled={facet.count === 0 && !facet.selected}
                  onClick={() => setQuery(toggleTag(query, facet.value))}
                >
                  {facet.value} <span class="num">{facet.count}</span>
                </button>
              ))}
            </div>
          </fieldset>
        ))}
      </aside>
      <section class="results" aria-label="Assets">
        <div class="results-head">
          <h1>
            {results.length} {results.length === 1 ? "prop" : "props"}
            {filtered && <span class="of"> of {assets.length}</span>}
          </h1>
          {filtered && (
            <button type="button" class="quiet" onClick={() => setQuery(EMPTY)}>
              Clear filters
            </button>
          )}
        </div>
        {results.length === 0 ? (
          <div class="empty">
            <p>Nothing matches these filters.</p>
            <p>
              Search looks at names, descriptions, tags and other names for the
              same thing (“cask” finds the barrel). Try fewer words, or{" "}
              <button
                type="button"
                class="link"
                onClick={() => setQuery(EMPTY)}
              >
                clear the filters
              </button>
              .
            </p>
          </div>
        ) : (
          <ul class="grid">
            {results.map((asset) => {
              const first = asset.variants[0];
              if (!first) return null;
              return (
                <li key={asset.id}>
                  <a class="tile" href={`#/asset/${asset.id}`}>
                    <span class="tile-shot">
                      <img
                        src={`${DATA}/${first.png}`}
                        alt=""
                        loading="lazy"
                        decoding="async"
                      />
                    </span>
                    <span class="tile-name">{asset.name}</span>
                    <span class="tile-facts num">
                      {metres(first.measured)} · {count(first.tris)} tris
                      {asset.variants.length > 1 &&
                        ` · ${asset.variants.length} variants`}
                    </span>
                  </a>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </main>
  );
}
