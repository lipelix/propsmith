# The catalogue site (site/, PRODUCT.md) as a Cloudflare Pages project. CI uploads builds directly
# (.github/workflows/publish.yml runs wrangler pages deploy), so the project has no git source and Cloudflare
# never builds the repository itself.
#
# The site lives on <project>.pages.dev only for now (owner's decision, 2026-11-14). A custom domain later is a
# cloudflare_pages_domain plus a proxied CNAME to cloudflare_pages_project.site.subdomain, as in lipelix/agedrop
# infra/app.tf, and a second Web Analytics host.

resource "cloudflare_pages_project" "site" {
  account_id        = var.cloudflare_account_id
  name              = "propsmith"
  production_branch = "main"
}

# Cloudflare Web Analytics: cookieless, no consent banner. A pages.dev host is not in one of the account's zones,
# so Cloudflare cannot inject the beacon itself (auto_install); the site build puts it into index.html with the
# token below (site/vite.config.ts, mode "publish").
resource "cloudflare_web_analytics_site" "site" {
  account_id   = var.cloudflare_account_id
  host         = cloudflare_pages_project.site.subdomain
  auto_install = false
}
