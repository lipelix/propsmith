terraform {
  required_version = ">= 1.6"

  required_providers {
    cloudflare = {
      source = "cloudflare/cloudflare"
      # v4 like the other lipelix stacks: v5 renames most resources, a deliberate migration.
      version = "~> 4.52"
    }
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }

  # State in Terraform Cloud (organization lipelix), local execution, like lipelix/agedrop.
  backend "remote" {
    hostname     = "app.terraform.io"
    organization = "lipelix"

    workspaces {
      name = "propsmith"
    }
  }
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

provider "github" {
  owner = var.github_owner
  token = var.github_token
}
