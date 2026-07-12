#!/usr/bin/env bash
# One-command activation of cloud sync for the BB/TM board-prep app.
#
# Usage:
#   ./scripts/setup-supabase.sh <SUPABASE_PROJECT_URL> <SUPABASE_ANON_KEY>
#
# Both values are the PUBLIC ones from Supabase → Project Settings → API:
#   - Project URL         e.g. https://abcdefgh.supabase.co
#   - anon / public key   (the publishable key — safe to embed in a client app)
# Do NOT use the service_role key here (that one is secret).
#
# Prereqs: `gh` authenticated (already is), and you have run supabase/schema.sql
# in your project's SQL editor.
set -euo pipefail

URL="${1:?Supabase Project URL required (e.g. https://xxxx.supabase.co)}"
KEY="${2:?Supabase anon/public key required}"
REPO="omarzbaba/bbtm-board-prep"

if [[ "$KEY" == eyJ*"service_role"* ]] || [[ "${3:-}" == "--service" ]]; then
  echo "Refusing: that looks like a service_role (secret) key. Use the anon/public key." >&2
  exit 1
fi

echo "→ Setting repo secrets on $REPO"
printf '%s' "$URL" | gh secret set VITE_SUPABASE_URL      --repo "$REPO"
printf '%s' "$KEY" | gh secret set VITE_SUPABASE_ANON_KEY --repo "$REPO"

echo "→ Triggering a redeploy so the build picks up the secrets"
gh workflow run deploy.yml --repo "$REPO" >/dev/null 2>&1 || {
  echo "  (workflow_dispatch unavailable; pushing an empty commit instead)"
  git commit --allow-empty -m "chore: enable Supabase cloud sync" && git push
}

echo ""
echo "✓ Cloud sync configured. The site rebuilds in ~1-2 min."
echo "  After it redeploys, the app badge changes from 'saved locally' to '● synced'."
echo "  Reminder: make sure you ran supabase/schema.sql in the project's SQL editor."
