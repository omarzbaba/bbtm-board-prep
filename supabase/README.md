# Optional cloud sync (Supabase)

The app is **local-first** and needs nothing here to work — Tala's progress, notes, and
weak-marks are saved in her browser automatically. This folder is only for turning on
**cross-device cloud sync + backup**, which you (Omar) enable in a few minutes.

Cloud sync could not be auto-provisioned during the build because the Supabase CLI in
this environment was not logged in, and a non-interactive session can't complete the
Supabase OAuth/login step. Everything else is wired — you just add credentials.

## Enable in 4 steps

1. **Create a project** at https://supabase.com (free tier is fine).
2. **Create the table:** open the project's SQL editor and run [`schema.sql`](schema.sql).
   (Or, with the CLI: `supabase link --project-ref <ref>` then `supabase db push`.)
3. **Get credentials:** Project Settings → API → copy the **Project URL** and the
   **anon public** key.
4. **Add them and redeploy:**
   - In the GitHub repo: Settings → Secrets and variables → Actions → add
     `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`, then re-run the Pages deploy.
   - Or locally: put them in `app/.env.local` and rebuild.

Once set, the app shows a green **● synced** badge and Tala can use the same profile ID
on any device to load her progress. Without them, it stays local-first (badge reads
"saved locally").

## Security note

This is a personal board-study tool. The `learner_id` is a random handle acting as a
shared secret; the anon-key policies in `schema.sql` allow read/upsert by handle. Don't
store anything sensitive — it's only quiz progress. For real multi-user isolation,
switch to Supabase Auth (see the comment in `schema.sql`).
