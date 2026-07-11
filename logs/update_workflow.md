# Update Workflow — ingesting a new NotebookLM export

When you have a fresh NotebookLM export, this is how new material flows into the app
without disturbing existing, already-audited content.

## 1. Drop the ZIP
Put the new export `.zip` in the **project root** or in
`sources/notebooklm-exports/incoming/`. The original ZIP is preserved untouched.

## 2. Re-ingest & re-score
```bash
python3 scripts/update_pipeline.py
```
This will:
- Detect the new archive by SHA-256 (never re-ingests identical bytes; ledger in `logs/ingested_archives.json`).
- Extract only **new** documents into `sources/notebooklm-exports/raw_extracted/` (no overwrite; duplicates skipped).
- Re-run normalization → coverage → gap report → generation plan.
- Diff coverage against the previous run and report **newly-covered / improved** blueprint topics.
- Write a **delta generation plan** (`content/questions/delta_plan.json`) for topics that became
  eligible and are not yet in the pilot bank. It does **not** auto-generate (the pilot gate stands).
- Append a dated entry to `logs/change_log.md`.

## 3. Generate & audit the delta (optional, when you want more content)
Re-run the generation+audit workflow against `delta_plan.json` (same workflow as the pilot),
then fold the results in:
```bash
python3 scripts/phase7_assemble.py        # merges accepted items into the banks
python3 scripts/sync_content_to_app.py    # copies content into the app
cd app && npm run build                    # rebuild
```

## 4. Deploy
Commit and push — the GitHub Actions workflow rebuilds and redeploys the Pages site
automatically. Tala's saved progress is keyed by item ID and is unaffected by new items.

## What is preserved
- Raw ZIP archives — never modified or deleted.
- Existing questions/cases and their audit state — untouched; only new items are added.
- Provenance — every ingest is hashed and logged.
