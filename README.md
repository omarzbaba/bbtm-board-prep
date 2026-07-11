# 🩸 Blood Bank Board Prep — ABPath BB/TM

A source-grounded study platform for the American Board of Pathology **Blood Banking /
Transfusion Medicine** subspecialty exam. Practice questions, staged teaching cases,
learner notes, weak-item marking, search, and blueprint coverage tracking — every item
traceable to approved sources.

Built for **Talha's** board prep — **75 questions**, **17 cases**, all source-grounded and audited. Shareable, saves progress, works on any device.

> **Not clinical decision support.** This is an educational board-preparation aid.
> Content is generated only from approved study sources and is not institutional policy
> or a substitute for authoritative references and clinical judgment.

---

## What's inside

| Layer | What it is |
|-------|-----------|
| **Question bank** | One-best-answer board MCQs with per-option explanations, source traces, difficulty, and blueprint mapping. |
| **Case bank** | Staged transfusion-medicine teaching cases with decision points, findings, pitfalls. |
| **Blueprint ontology** | The full official ABPath BB/TM content specification parsed into 17 domains / 1,078 nodes with C/AR/F designations. |
| **Coverage matrix** | Honest, per-topic map of how well the approved sources support each blueprint node. |
| **Web app** | A fast, local-first React app (`app/`). |

All generated content is **audited** for source support before it enters the bank;
anything uncertain is routed to a review queue rather than shown as fact.

---

## Run it locally

```bash
cd app
npm install
npm run dev        # http://localhost:5173
```

Build a static bundle:

```bash
cd app
npm run build      # outputs app/dist
npm run preview    # serve the build
```

## Saving progress (the "database")

The app is **local-first**: Tala's answers, notes, and weak-marks are saved
automatically in her browser — no account, no setup. That's enough for one learner on
her own device, and it's what ships turned on.

**Optional cloud sync** (cross-device backup) is fully wired but needs credentials only
you can create — see [`supabase/README.md`](supabase/README.md). Add a Supabase URL +
anon key as repo secrets (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`) and redeploy;
the app then syncs progress by profile ID and shows a green "synced" badge.

## Deploy (GitHub Pages)

Pushing to `main` triggers [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml),
which builds `app/` and publishes to GitHub Pages. Enable Pages once:
**repo → Settings → Pages → Source: GitHub Actions**. The site serves at
`https://<user>.github.io/<repo>/`.

---

## Content pipeline (how the bank is built)

Deterministic, reproducible, and source-traceable. Scripts live in `scripts/`.

```
Phase 0  ingest ZIP + reference PDFs, preserve raw, hash provenance   → logs/, content/source_manifest.json
Phase 1  normalize .docx → Markdown, dedupe, classify                 → content/normalized/
Phase 2  parse ABPath blueprint PDF → ontology                        → content/blueprint/
Phase 3  map sources → blueprint, score coverage, gap report          → content/coverage/, logs/
Phase 4  content schemas (question/case/reference/review/learner)     → content/schemas/
Phase 5  plan + generate one-best-answer questions (grounded)         → content/questions/
Phase 6  plan + generate staged teaching cases (grounded)             → content/cases/
Phase 7  adversarial source-support audit → bank vs review queue      → content/review/, logs/
Phase 8  learner web app                                              → app/
Phase 9  update pipeline for future ZIP drops                         → scripts/update_pipeline.py
```

Regenerate everything from raw sources (requires the private source materials locally):

```bash
python3 scripts/phase0_ingest.py
python3 scripts/phase1_normalize.py
python3 scripts/phase_reports.py
python3 scripts/phase2_ontology.py
python3 scripts/phase3_coverage.py
python3 scripts/phase3_gap_report.py
python3 scripts/phase5_plan.py
#   → run the generation+audit workflow (scripts/wf_generate_audit.mjs)
python3 scripts/phase7_assemble.py
python3 scripts/phase7_reports.py
python3 scripts/sync_content_to_app.py
```

## Adding new sources later

Drop a new NotebookLM export `.zip` in the project root and run:

```bash
python3 scripts/update_pipeline.py
```

It re-scores coverage, finds newly-covered topics, and prepares a delta plan — without
disturbing existing audited content or Tala's saved progress. See
[`logs/update_workflow.md`](logs/update_workflow.md).

---

## Source & copyright

Raw copyrighted materials (reference textbooks, the NotebookLM export, the blueprint PDF)
are **git-ignored** and never published. The repo ships only transformative, cited
derivative content (questions, cases, blueprint structure, coverage metadata). See
`content/source_manifest.json` for the approved-source manifest and provenance hashes.
