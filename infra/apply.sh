#!/usr/bin/env bash
# Applies infra/ (the Cloudflare Pages project, Web Analytics, the repository secret and variables) and starts the
# first publish. It asks for the four values one by one, hides the tokens while you type and keeps them in the macOS
# Keychain (service "propsmith-infra"), so the next run asks nothing. They reach OpenTofu through the environment of
# the run only: nothing is written to a file in the repository and nothing lands in the shell history.
#
#   ./infra/apply.sh            use the saved values (ask for missing ones), show the plan, ask, apply, offer to publish
#   ./infra/apply.sh --plan     show the plan only
#   ./infra/apply.sh --reset    forget the saved values and ask for all four again
#   ./infra/apply.sh --forget   forget the saved values and stop
set -euo pipefail

cd "$(dirname "$0")"
REPO="lipelix/propsmith"
SERVICE="propsmith-infra"
NAMES="cloudflare_account_id cloudflare_api_token pages_deploy_token github_token"
PLAN_ONLY=0
RESET=0
FORGET=0
case "${1:-}" in
  "") ;;
  --plan) PLAN_ONLY=1 ;;
  --reset) RESET=1 ;;
  --forget) FORGET=1 ;;
  *) echo "usage: $0 [--plan | --reset | --forget]" >&2; exit 2 ;;
esac

# The Keychain is the store; without it (not macOS, or a terminal that may not use it) every run asks.
KEYCHAIN=0
if command -v security >/dev/null 2>&1; then KEYCHAIN=1; fi
# A terminal outside the desktop session (ssh, tmux started by a service) finds the login Keychain locked and fails
# with "User interaction is not allowed". Unlock it once, with the macOS password, or go on without saving.
keychain_works() {
  security add-generic-password -U -s "$SERVICE-probe" -a probe -w probe >/dev/null 2>&1 &&
    security delete-generic-password -s "$SERVICE-probe" -a probe >/dev/null 2>&1
}
if [ "$KEYCHAIN" = 1 ] && ! keychain_works; then
  echo "The login Keychain is locked in this terminal. Unlock it to keep the values (your macOS password):"
  if security unlock-keychain && keychain_works; then
    echo "Unlocked."
  else
    echo "The Keychain stays unavailable: this run asks for every value and saves nothing."
    KEYCHAIN=0
  fi
fi
saved() { [ "$KEYCHAIN" = 1 ] && security find-generic-password -s "$SERVICE" -a "$1" -w 2>/dev/null; }
save() { [ "$KEYCHAIN" = 1 ] && security add-generic-password -U -s "$SERVICE" -a "$1" -w "$2" 2>/dev/null; }
forget() {
  local name
  for name in $NAMES; do
    if [ "$KEYCHAIN" = 1 ]; then security delete-generic-password -s "$SERVICE" -a "$name" >/dev/null 2>&1 || true; fi
  done
}

if [ "$FORGET" = 1 ]; then
  forget
  echo "Forgot the saved values."
  exit 0
fi
if [ "$RESET" = 1 ]; then forget; fi

for tool in tofu gh curl; do
  command -v "$tool" >/dev/null 2>&1 || { echo "Missing required tool: $tool" >&2; exit 1; }
done

# Cloudflare tokens of other accounts in this shell must not leak into the provider: every value comes from the
# prompts below. GitHub's variables stay: the provider is given its token explicitly, and gh (which starts the
# publish at the end) may be logged in through them.
unset CF_API_TOKEN CLOUDFLARE_API_TOKEN CLOUDFLARE_API_KEY CLOUDFLARE_EMAIL TF_VAR_github_token

# ask <variable> <label> <hint> <pattern> <what the pattern means> [secret]
ask() {
  local name="$1" label="$2" hint="$3" pattern="$4" meaning="$5" secret="${6:-}" value=""
  value="$(saved "$name" || true)"
  if [ -n "$value" ] && printf '%s' "$value" | grep -Eq "$pattern"; then
    echo "$label: saved in the Keychain"
    export "TF_VAR_$name=$value"
    return
  fi
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
  if save "$name" "$value"; then echo "  Saved in the Keychain."; fi
  export "TF_VAR_$name=$value"
}

if [ "$KEYCHAIN" = 1 ]; then
  echo "propsmith: deploy setup. Values are kept in the Keychain; a missing one is asked for (tokens stay hidden)."
else
  echo "propsmith: deploy setup. No Keychain here, so the four values are asked for on every run (tokens stay hidden)."
fi

ask cloudflare_account_id \
  "1/4  Cloudflare account ID (personal account)" \
  "dash.cloudflare.com -> the account's overview -> Account ID" \
  '^[0-9a-f]{32}$' "32 hex characters"

ask cloudflare_api_token \
  "2/4  Cloudflare ADMIN token (only this script uses it)" \
  "My Profile -> API Tokens -> Create Token -> Custom, Account permissions: Cloudflare Pages Edit, Account Settings Edit, Account Settings Read, Account Analytics Read" \
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
# OpenTofu's remote backend creates a missing workspace with its own version number, which Terraform Cloud does not
# know ("does not resolve to a version of Terraform"). So the workspace is created here first, through the API, with
# local execution: Terraform Cloud then only keeps the state and never needs a version of its own.
create_workspace() {
  local credentials="$HOME/.terraform.d/credentials.tfrc.json" token status
  command -v python3 >/dev/null 2>&1 || { echo "Missing required tool: python3" >&2; return 1; }
  [ -f "$credentials" ] || { echo "No Terraform Cloud login found ($credentials): run tofu login app.terraform.io" >&2; return 1; }
  token="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["credentials"]["app.terraform.io"]["token"])' "$credentials")"
  status="$(curl -sS -o /tmp/propsmith-workspace.json -w '%{http_code}' \
    -X POST "https://app.terraform.io/api/v2/organizations/lipelix/workspaces" \
    -H "Authorization: Bearer $token" -H "Content-Type: application/vnd.api+json" \
    -d '{"data":{"type":"workspaces","attributes":{"name":"propsmith","execution-mode":"local"}}}')"
  if [ "$status" = "201" ]; then
    echo "Created the Terraform Cloud workspace propsmith (local execution)."
  else
    echo "Terraform Cloud refused to create the workspace (HTTP $status):" >&2
    cat /tmp/propsmith-workspace.json >&2; echo >&2
    echo "Create it by hand: app.terraform.io -> lipelix -> New -> Workspace -> CLI-driven -> name propsmith," >&2
    echo "then Settings -> General -> Execution Mode: Local. Then run this script again." >&2
    rm -f /tmp/propsmith-workspace.json
    return 1
  fi
  rm -f /tmp/propsmith-workspace.json
}

INIT_LOG="$(mktemp -t propsmith-init)"
init() { tofu init -input=false >"$INIT_LOG" 2>&1; }
if ! init; then
  if grep -q "does not resolve to a version of Terraform" "$INIT_LOG"; then
    echo "The workspace does not exist yet."
    create_workspace
    init || { cat "$INIT_LOG" >&2; rm -f "$INIT_LOG"; exit 1; }
  elif grep -qiE "token|unauthorized|credentials|login" "$INIT_LOG"; then
    echo "Not logged in to Terraform Cloud. Logging in (a browser opens; paste the token it gives you):"
    tofu login app.terraform.io
    if ! init; then
      if grep -q "does not resolve to a version of Terraform" "$INIT_LOG"; then
        create_workspace
        init || { cat "$INIT_LOG" >&2; rm -f "$INIT_LOG"; exit 1; }
      else
        cat "$INIT_LOG" >&2; rm -f "$INIT_LOG"; exit 1
      fi
    fi
  else
    cat "$INIT_LOG" >&2
    rm -f "$INIT_LOG"
    exit 1
  fi
fi
rm -f "$INIT_LOG"

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
  echo "If a token was refused (wrong, expired, missing a permission): ./infra/apply.sh --reset asks for them again." >&2
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
if ! gh workflow run publish --repo "$REPO" --ref main; then
  echo >&2
  echo "The stack is applied; only starting the publish failed. Log in (gh auth login -h github.com) and run:" >&2
  echo "  gh workflow run publish --repo $REPO --ref main" >&2
  exit 1
fi
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
