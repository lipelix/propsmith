# propsmith

Text to game props. A coding agent writes a Blender `bpy` model, the tools build, measure and check it, and finished
props are published in an open catalogue.

- Design: `docs/plans/2026-11-14-propsmith-design.md`
- Current plan: `docs/plans/2026-11-14-plan-1-generator-catalogue-pilot.md` (GitHub plan issue with sub-issues)

## Rules

- Units are metres, z up. Nothing game-specific (tiles, gameplay facts, game cameras) belongs here.
- The canonical asset is `catalog/<id>/asset.py` + `asset.json`. GLBs, thumbnails, `catalog/index.json` and
  `catalog/measurements.json` are generated; never edit them by hand.
- Code is MIT. Catalogue assets are CC0-1.0. Textures come only from the CC0 ledger `catalog/textures.json`.
- `npm run check` must pass before every commit: format, lint, types, tests, catalogue checks. It needs no Blender.
- A check result is `OK`, `FAILED` or `NOT CHECKED`. `NOT CHECKED` is a failure.
- No secrets in the repo. A missing environment variable is an error, never a default.
- Conventional Commits, in English.
- A PR that adds or changes an asset shows it: `npm run shots -- <id>… --push <branch-slug>` renders every variant
  large (the review rig, framed to fill 1024 px), pushes the pictures to the `pr-assets` branch under `<branch-slug>/`
  and prints the "What it looks like" table to paste into the PR body.
- When that PR closes a plan item (a sub-issue of a `plan` issue), append the same table to the item's body too,
  after a `<!-- hq:renders -->` marker, with the heading `## What it looks like (from #<PR>)`, so the plan shows
  every prop it produced. Leave the item's own text above it unchanged.

## Site

`site/` is a static Vite + Preact app (design: `PRODUCT.md`, `DESIGN.md`). It reads `site/public/data/`, which is
not committed: `npm run bake && npm run site:data` (needs Blender), then `npm run site:dev`. `npm run test:e2e`
drives it in a browser and needs that data too, so it runs locally, not in CI.

## Deploy

`infra/` (OpenTofu, applied by the owner) creates the Cloudflare Pages project, Web Analytics and the repo secret and
variables CI reads. `.github/workflows/publish.yml` builds, bakes, runs the e2e tests and uploads the site on every
push to `main` (a PR that touches the pipeline runs it without the upload). The site is on `<project>.pages.dev` only.
`./infra/apply.sh` asks for the tokens in the terminal once, keeps them in the macOS Keychain (service
`propsmith-infra`; `--reset` asks again, `--forget` removes them), applies the stack and starts the first publish
(`--plan` only shows the plan).

## Plan sessions

One session takes one plan item on its own branch and PR. When CI is green, squash-merge, close the item with a handoff
comment, and label the next item `ready`. Items marked "stop and show" wait for the owner.
