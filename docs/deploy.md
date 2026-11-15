# Deploying the site

The site is published to Cloudflare Pages at <https://propsmith.pages.dev> by the `deploy` job of
`.github/workflows/ci.yml`, on every push to `main`, from the artifact the `assets` job built in Blender. The job is
off until the repository variable `DEPLOY` is `true`.

## One-time setup (the owner)

1. **Account ID.** Cloudflare dashboard → the account's overview → copy **Account ID**.
2. **API token.** My Profile → API Tokens → Create Token → Custom token:
   - Permissions: **Account · Cloudflare Pages · Edit**.
   - Account resources: only this account.
   - No zone permissions, no client IP filter. Copy the token; it is shown once.
3. **Web Analytics.** Analytics & Logs → Web Analytics → Add a site → hostname `propsmith.pages.dev` → choose the
   manual JS snippet → copy the `token` value (32 hex characters) from the snippet. It is public; the page carries it.
4. **GitHub.** Repository → Settings → Secrets and variables → Actions:
   - Secrets: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`.
   - Variables: `CF_BEACON_TOKEN` (the Web Analytics token), `DEPLOY` = `true`.

   Or from a shell (each command prompts for the value, so nothing lands in the shell history):

   ```sh
   gh secret set CLOUDFLARE_API_TOKEN -R lipelix/propsmith
   gh secret set CLOUDFLARE_ACCOUNT_ID -R lipelix/propsmith
   gh variable set CF_BEACON_TOKEN -R lipelix/propsmith
   gh variable set DEPLOY -R lipelix/propsmith --body true
   ```

5. **First deploy.** Actions → ci → Run workflow on `main` (or push to `main`). The job creates the Pages project
   `propsmith` on its first run. If the name is taken on pages.dev, the job fails and says so: pick another project
   name in the workflow.

## What runs

- `check`: format, lint, types, tests, catalogue checks (no Blender).
- `assets`: Blender builds every asset from source, the committed measurements must match, GLBs are baked, the site is
  built and driven in a browser. Pull requests run this without any secret.
- `deploy`: uploads `site/dist` with `wrangler pages deploy`. It fails when a setting above is missing.

## A custom domain later

Add it to the Pages project (Custom domains) and to Web Analytics; nothing in the repository changes except the
`environment.url` shown in GitHub.
