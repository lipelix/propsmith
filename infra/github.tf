# What .github/workflows/publish.yml reads, derived from this stack.

resource "github_actions_secret" "cloudflare_api_token" {
  repository      = var.github_repo
  secret_name     = "CLOUDFLARE_API_TOKEN"
  plaintext_value = var.pages_deploy_token
}

resource "github_actions_variable" "cloudflare_account_id" {
  repository    = var.github_repo
  variable_name = "CLOUDFLARE_ACCOUNT_ID"
  value         = var.cloudflare_account_id
}

resource "github_actions_variable" "pages_project" {
  repository    = var.github_repo
  variable_name = "PAGES_PROJECT"
  value         = cloudflare_pages_project.site.name
}

resource "github_actions_variable" "site_url" {
  repository    = var.github_repo
  variable_name = "SITE_URL"
  value         = local.site_url
}

# Public by design: it ends up in every page's HTML. A variable, not a secret, so the build log shows what was used.
resource "github_actions_variable" "web_analytics_token" {
  repository    = var.github_repo
  variable_name = "CF_WEB_ANALYTICS_TOKEN"
  value         = cloudflare_web_analytics_site.site.site_token
}
