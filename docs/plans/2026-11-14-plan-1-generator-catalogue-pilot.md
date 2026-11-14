# Plan 1: generator, catalogue, srd-iso-rpg pilot

Design: [`2026-11-14-propsmith-design.md`](2026-11-14-propsmith-design.md).

**Status:** Milestone A (Tasks 1–5) done 2026-11-14. The owner asked to try an asset in the game right away, so the pilot (Tasks 9–10) ran before Milestone B: `signpost_wood` stands in the srd-iso-rpg village (lipelix/srd-iso-rpg#89, approved and merged 2026-11-14). Task 6 (GLB bake) built 2026-11-14 and waits for the owner's look at `npm run bake:look`; Task 7 (site) next.

## Source material

The code to port lives in `lipelix/srd-iso-rpg` on `main`: `tools/props/` (TypeScript CLI and tests),
`tools/props/blender/` (`build.py`, `lib/props/`), `.claude/skills/prop/SKILL.md`, `src/dev/props/` (catalogue page),
`assets/props/` (27 props, `tags.json`, `textures.json`, `style.json`). Port with the tests; do not rewrite what works.

## Guardrails

- Units are metres. No tiles, gameplay facts, game camera or game post-processing in this repo.
- The same inputs build the same bytes. Generated files are written by tools only.
- A check is `OK`, `FAILED` or `NOT CHECKED`; `NOT CHECKED` fails CI.
- `npm run check` needs no Blender. Blender steps run locally and on the publish job.
- Never ship lint, format or type errors. No secrets in the repo.
- srd-iso-rpg keeps working at every step: nothing is deleted there before Task 11.

## Tasks

One session takes one task, on its own branch and PR; merge when CI is green, then label the next task `ready`.

### Milestone A: generator

1. **Scaffold.** Node + TypeScript toolchain (tsx, zod, vitest, eslint, prettier) matching srd-iso-rpg's versions,
   `npm run check`, CI on the self-hosted runner (`RUNNER_LABELS` repo variable), `AGENTS.md`.
2. **Schema, tags, index.** `asset.json` schema (design: "Asset contract"), `catalog/tags.json`, `npm run catalog`
   writing `catalog/index.json` through Prettier, with `--check`. Tests ported from `schema.test.ts`,
   `catalog.test.ts`.
3. **Library and build.** `lib/propsmith` (registry, shapes, materials, textures, measure, export, a neutral review
   rig), `npm run build -- <id>` with the input-hash cache, review snapshots (iso, top, front) in `.cache/`,
   `catalog/measurements.json`. Texture ledger and `npm run textures`. Three hand-ported assets prove it:
   `barrel_wood`, `well_stone`, `lamp_post`.
4. **Checks.** `bounds-fit`, `origin-ground`, `tri-budget`, `manifold`, `materials-known`, `anchors-declared`; the
   report in `build`; `npm run check` verifies committed measurements against input hashes without Blender.
5. **Skill and `new`.** `skills/prop/SKILL.md` (contract, style guide, loop), `npm run new -- <id> "<desc>"` driving
   `claude -p` confined to the asset folder, Claude Code plugin manifest so other repos can install the skill. Smoke:
   generate one new asset end to end.

### Milestone B: catalogue

6. **GLB with baked textures.** UV atlas + Cycles bake of base colour and normal per variant, GLB export, thumbnail.
   **Stop and show:** the GLB in a browser next to the Blender render, for three assets.
7. **Site.** Static catalogue from `index.json`: search, facets (category, family, tag groups), detail page with a GLB
   viewer, size, variants, provenance, download and "use in your game" snippets. WCAG 2.1 AA, mobile first.
8. **Deploy.** OpenTofu in `infra/`: Cloudflare Pages project, DNS, Web Analytics. CI publish job on merge to `main`
   (build changed assets, bake, upload). The owner supplies the Cloudflare token as a repo secret.

### Milestone C: pilot in srd-iso-rpg

9. **Consume one asset.** In `lipelix/srd-iso-rpg`: pin propsmith at a tag, let `props:build` load a catalogue asset
   (overlay `prop.json` names it), render its sprites with the game style. Use an asset that is new to the game,
   generated in Task 5.
10. **Place it.** Put the asset into the village location, bake, run the game. **Stop and show:** a screenshot from the
    running game.
11. **Migrate the kit.** Move the 27 srd props into the catalogue, switch srd to overlays for all of them, delete
    `tools/props/blender/lib` and the duplicated tooling there. Starts only after srd-iso-rpg #84–#87 are closed.

## Open questions

- Domain for the site (Task 8): a one-label name under an existing zone, or its own domain.
- Whether the catalogue carries more than one visual kit (the srd painterly village look is the first); decide when a
  second game needs it.
