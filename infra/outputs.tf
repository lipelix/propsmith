locals {
  site_url = "https://${cloudflare_pages_project.site.subdomain}"
}

output "site_url" {
  value = local.site_url
}

output "web_analytics_site_tag" {
  value = cloudflare_web_analytics_site.site.site_tag
}
