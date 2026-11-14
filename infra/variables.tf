# Personal Cloudflare account (never the Heureka one): Account · Cloudflare Pages · Edit and
# Account · Account Settings · Edit (creates the Web Analytics site, API rum/site_info). Used only to apply this stack.
variable "cloudflare_api_token" {
  type      = string
  sensitive = true
}

# The personal account's id (dash.cloudflare.com, right column of any zone's overview). There is no zone
# to read it from while the site lives on pages.dev only.
variable "cloudflare_account_id" {
  type = string
}

# A second, narrower token for CI: Account · Cloudflare Pages · Edit only. Stored as the repository
# secret CLOUDFLARE_API_TOKEN, which .github/workflows/publish.yml uses.
variable "pages_deploy_token" {
  type      = string
  sensitive = true
}

# Fine-grained PAT on lipelix/propsmith only: Secrets and Variables: Read and write, Metadata: Read.
variable "github_token" {
  type      = string
  sensitive = true
}

variable "github_owner" {
  type    = string
  default = "lipelix"
}

variable "github_repo" {
  type    = string
  default = "propsmith"
}
