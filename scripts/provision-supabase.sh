#!/usr/bin/env bash
# Fully provision cloud sync AFTER you authenticate the Supabase CLI once.
#
#   1) Run this once in your terminal (opens a browser, click Approve):
#          supabase login
#   2) Then run:
#          ./scripts/provision-supabase.sh
#
# It creates the project, applies the schema, fetches the anon key, sets the GitHub
# repo secrets, and triggers a redeploy — no dashboard clicking. Everything below uses
# only PUBLIC values in the app (the anon key is publishable by design).
set -euo pipefail

REPO="omarzbaba/bbtm-board-prep"
PROJECT_NAME="${1:-bbtm-board-prep}"
REGION="${2:-us-east-1}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

command -v supabase >/dev/null || { echo "supabase CLI not found."; exit 1; }
supabase projects list >/dev/null 2>&1 || { echo "Not logged in. Run 'supabase login' first (opens a browser)."; exit 1; }

echo "→ Selecting organization…"
ORG=$(supabase orgs list -o json 2>/dev/null | python3 -c "import sys,json;d=json.load(sys.stdin);print(d[0].get('id',''))")
[ -n "$ORG" ] || { echo "No organization found on your account."; exit 1; }

DBPASS=$(python3 -c "import secrets;print(secrets.token_urlsafe(24))")
echo "→ Creating project '$PROJECT_NAME' (region $REGION)…"
REF=$(supabase projects create "$PROJECT_NAME" --org-id "$ORG" --db-password "$DBPASS" --region "$REGION" -o json 2>/dev/null \
      | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))")
[ -n "$REF" ] || { echo "Project creation failed — create it in the dashboard and use scripts/setup-supabase.sh instead."; exit 1; }
echo "  project ref: $REF"

echo "→ Waiting for the database to come up (up to ~3 min)…"
for i in $(seq 1 36); do
  if supabase projects api-keys --project-ref "$REF" -o json >/dev/null 2>&1; then break; fi
  sleep 5
done

URL="https://${REF}.supabase.co"
ANON=$(supabase projects api-keys --project-ref "$REF" -o json 2>/dev/null \
       | python3 -c "import sys,json;ks=json.load(sys.stdin);print(next((k['api_key'] for k in ks if k.get('name')=='anon'),''))")
[ -n "$ANON" ] || { echo "Could not fetch anon key yet; re-run in a minute, or use setup-supabase.sh with values from the dashboard."; exit 1; }

echo "→ Applying schema (supabase/schema.sql)…"
if command -v psql >/dev/null; then
  PGPASSWORD="$DBPASS" psql "host=db.${REF}.supabase.co port=5432 dbname=postgres user=postgres sslmode=require" \
    -f "$ROOT/supabase/schema.sql" && echo "  schema applied via psql"
else
  echo "  psql not installed — paste supabase/schema.sql into the project's SQL editor once (1 step)."
fi

echo "→ Setting GitHub repo secrets + redeploying…"
printf '%s' "$URL"  | gh secret set VITE_SUPABASE_URL      --repo "$REPO"
printf '%s' "$ANON" | gh secret set VITE_SUPABASE_ANON_KEY --repo "$REPO"
gh workflow run deploy.yml --repo "$REPO" >/dev/null 2>&1 || echo "  (trigger a deploy manually if needed)"

echo ""
echo "✓ Done. Project: $URL"
echo "  The site rebuilds in ~1-2 min; the badge will read '● synced'."
echo "  DB password (save it somewhere safe): $DBPASS"
