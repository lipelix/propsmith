import { useEffect, useState } from "preact/hooks";

import { type Catalogue, load } from "./data.ts";
import { Detail } from "./detail.tsx";
import { MoonIcon, SunIcon } from "./icons.tsx";
import { List } from "./list.tsx";

type Theme = "dark" | "light";
const THEME_KEY = "propsmith-theme";

function initialTheme(): Theme {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === "dark" || stored === "light") return stored;
  return matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

/** `#/` is the catalogue, `#/asset/<id>` an asset, `#/asset/<id>/<variant>` one of its variants. */
function parseRoute(
  hash: string,
): { id: string; variant: string | null } | null {
  const match = /^#\/asset\/([a-z0-9_]+)(?:\/([a-z0-9_]+))?$/.exec(hash);
  return match ? { id: match[1] ?? "", variant: match[2] ?? null } : null;
}

type State =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; catalogue: Catalogue };

export function App() {
  const [state, setState] = useState<State>({ status: "loading" });
  const [hash, setHash] = useState(location.hash);
  const [theme, setTheme] = useState<Theme>(initialTheme);

  useEffect(() => {
    load().then(
      (catalogue) => setState({ status: "ready", catalogue }),
      (error: unknown) =>
        setState({
          status: "error",
          message: error instanceof Error ? error.message : String(error),
        }),
    );
    const onHash = () => setHash(location.hash);
    addEventListener("hashchange", onHash);
    return () => removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const route = parseRoute(hash);
  const asset =
    state.status === "ready" && route
      ? state.catalogue.assets.find((a) => a.id === route.id)
      : undefined;

  return (
    <>
      <header class="bar">
        <a class="wordmark" href="#/">
          propsmith
        </a>
        <span class="bar-note">open game props, CC0</span>
        <nav class="bar-links" aria-label="Site">
          <a href="https://github.com/lipelix/propsmith">GitHub</a>
          <button
            type="button"
            class="quiet"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            aria-label={`Switch to the ${theme === "dark" ? "light" : "dark"} theme`}
          >
            {theme === "dark" ? <SunIcon /> : <MoonIcon />}
          </button>
        </nav>
      </header>
      {state.status === "loading" && (
        <main class="notice" aria-busy="true">
          <p>Loading the catalogue…</p>
        </main>
      )}
      {state.status === "error" && (
        <main class="notice">
          <h1>The catalogue did not load</h1>
          <p>{state.message}</p>
          <p>
            Reload the page. If you are running the site yourself, build its
            data first: <code>npm run bake && npm run site:data</code>.
          </p>
        </main>
      )}
      {state.status === "ready" &&
        (route === null ? (
          <List catalogue={state.catalogue} />
        ) : asset ? (
          <Detail key={asset.id} asset={asset} variant={route.variant} />
        ) : (
          <main class="notice">
            <h1>No asset “{route.id}”</h1>
            <p>
              It may have been renamed or removed.{" "}
              <a href="#/">Back to the catalogue</a>.
            </p>
          </main>
        ))}
    </>
  );
}
