#!/usr/bin/env bash
# Applies infra/ (the Cloudflare Pages project, Web Analytics, the repository secret and variables) and starts the
# first publish. It asks for the four values one by one, hides the tokens while you type and hands them to OpenTofu
# through the environment of this run only: nothing is written to disk and nothing lands in the shell history.
#
#   ./infra/apply.sh            ask, show the plan, ask again, apply, then offer to publish
#   ./infra/apply.sh --plan     ask and show the plan only
set -euo pipefail

cd "$(dirname "$0")"
REPO="lipelix/propsmith"
PLAN_ONLY=0
case "${1:-}" in
  "") ;;
  --plan) PLAN_ONLY=1 ;;
  *) echo "usage: $0 [--plan]" >&2; exit 2 ;;
esac

for tool in tofu gh; do
  command -v "$tool" >/dev/null 2>&1 || { echo "Missing required tool: $tool" >&2; exit 1; }
done

# Tokens of other accounts in this shell must not leak into the providers: every value comes from the prompts below.
unset CF_API_TOKEN CLOUDFLARE_API_TOKEN CLOUDFLARE_API_KEY CLOUDFLARE_EMAIL GITHUB_TOKEN GH_TOKEN TF_VAR_github_token

# ask <variable> <label> <hint> <pattern> <what the pattern means> [secret]
ask() {
  local name="$1" label="$2" hint="$3" pattern="$4" meaning="$5" secret="${6:-}" value=""
  echo
  echo "$label"
  echo "  $hint"
  while :; do
    if [ -n "$secret" ]; then
      read -r -s -p "  > (hidden) " value; echo
    else
      read -r -p "  > " value
    fi
    value="$(printf '%s' "$value" | tr -d '[:space:]')"
    if printf '%s' "$value" | grep -Eq "$pattern"; then break; fi
    echo "  That does not look right: expected $meaning. Try again (Ctrl-C to stop)."
  done
  export "TF_VAR_$name=$value"
}

echo "propsmith: deploy setup. Four values; the tokens are not shown while you type or paste."

ask cloudflare_account_id \
  "1/4  Cloudflare account ID (personal account)" \
  "dash.cloudflare.com -> the account's overview -> Account ID" \
  '^[0-9a-f]{32}$' "32 hex characters"

ask cloudflare_api_token \
  "2/4  Cloudflare ADMIN token (used by this run only)" \
  "My Profile -> API Tokens -> Create Token -> Custom: Account - Cloudflare Pages - Edit, Account - Account Settings - Edit" \
  '^[A-Za-z0-9_-]{30,}$' "a token of 30 or more letters, digits, - or _" secret

ask pages_deploy_token \
  "3/4  Cloudflare DEPLOY token (becomes the repository secret CI uses)" \
  "Same page, a second token: Account - Cloudflare Pages - Edit only" \
  '^[A-Za-z0-9_-]{30,}$' "a token of 30 or more letters, digits, - or _" secret

ask github_token \
  "4/4  GitHub token" \
  "github.com/settings/personal-access-tokens -> fine-grained, only $REPO: Secrets read/write, Variables read/write" \
  '^(github_pat_|ghp_)[A-Za-z0-9_]{20,}$' "a token starting with github_pat_ or ghp_" secret

# shellcheck disable=SC2154  # exported by ask
if [ "$TF_VAR_cloudflare_api_token" = "$TF_VAR_pages_deploy_token" ]; then
  echo
  echo "Note: the admin and the deploy token are the same. It works, but CI then holds more rights than it needs."
fi

echo
echo "State lives in Terraform Cloud (organization lipelix, workspace propsmith)."
if ! tofu init -input=false >/tmp/propsmith-tofu-init.log 2>&1; then
  if grep -qiE "token|unauthorized|credentials|login" /tmp/propsmith-tofu-init.log; then
    echo "Not logged in to Terraform Cloud. Logging in (a browser opens; paste the token it gives you):"
    tofu login app.terraform.io
    tofu init -input=false
  else
    cat /tmp/propsmith-tofu-init.log >&2
    rm -f /tmp/propsmith-tofu-init.log
    exit 1
  fi
fi
rm -f /tmp/propsmith-tofu-init.log

remote_hint() {
  cat >&2 <<'HINT'

If the error says the variables have no value or that saving a plan is not supported, the Terraform Cloud workspace
runs remotely and never sees what you typed. Set it to local execution once:
  app.terraform.io -> lipelix -> Workspaces -> propsmith -> Settings -> General -> Execution Mode: Local
then run this script again.
HINT
}

PLAN="$(mktemp -t propsmith-plan)"
trap 'rm -f "$PLAN"' EXIT
echo
if ! tofu plan -input=false -out="$PLAN"; then
  remote_hint
  exit 1
fi

if [ "$PLAN_ONLY" = 1 ]; then
  echo
  echo "Plan only: nothing was changed."
  exit 0
fi

echo
read -r -p "Apply this plan? Type yes: " answer
if [ "$answer" != "yes" ]; then
  echo "Nothing was changed."
  exit 0
fi
tofu apply -input=false "$PLAN"

SITE_URL="$(tofu output -raw site_url)"
echo
echo "Applied. The site will be at $SITE_URL once a publish has run."
read -r -p "Start the publish now (bakes every asset, about 12 minutes)? Type yes: " answer
if [ "$answer" != "yes" ]; then
  echo "Later: gh workflow run publish --repo $REPO --ref main"
  exit 0
fi

# The workflow is started with your own gh login, not with the token typed above.
gh workflow run publish --repo "$REPO" --ref main
echo "Started. Waiting for the run to appear..."
sleep 8
RUN="$(gh run list --repo "$REPO" --workflow publish --branch main --limit 1 --json databaseId -q '.[0].databaseId')"
if gh run watch "$RUN" --repo "$REPO" --exit-status; then
  echo
  echo "Published: $SITE_URL"
else
  echo
  echo "The publish failed: gh run view $RUN --repo $REPO --log-failed" >&2
  exit 1
fi
