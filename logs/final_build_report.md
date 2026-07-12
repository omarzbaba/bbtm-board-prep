# Final Build Report — BB/TM Board Prep Platform

_Generated: 2026-07-12T17:46:09.452831+00:00_

## What was built

A complete, source-grounded study platform for the ABPath Blood Banking / Transfusion
Medicine subspecialty exam — from raw NotebookLM export to a deployed, database-backed
web app — in ten phases, all artifacts reproducible on disk.

### Sources ingested (Phase 0–1)
- Raw NotebookLM ZIP preserved intact (SHA-256 verified), **61 study documents**
  normalized (47 unique after de-duplicating 14 exact copies),
  43,376 words.
- 1 non-content artifact (a stray 814 MB presentation) excluded and documented.
- 4 reference PDFs (official ABPath blueprint + AABB Technical Manual + Harmening + AABB Standards).

### Blueprint ontology (Phase 2)
- The official ABPath BB/TM Content Specification parsed into **17 domains,
  1078 nodes, 813 leaf topics**, each tagged Core / Advanced-Resident / Fellow.

### Coverage (Phase 3)
- Every leaf topic scored for source support:
  covered **531**, strong-partial **59**, weak-partial **84**,
  thin **79**, missing **60**.
- Generation-eligible (covered + strong-partial): **590 / 813**.

### Pilot content (Phase 5–7)
- **411 board questions** accepted into the bank (200 Core / 191 AR / 20 Fellow);
  31 routed to human review.
- **23 teaching cases** accepted; 3 routed to review.
- Every item was independently re-read against its sources by an adversarial auditor.
  Question source-support: 252 pass, 180 partial. Every accepted question's auditor
  independently agreed with the keyed answer.

### Web app (Phase 8)
- Vite + React + TypeScript SPA: dashboard, domain filtering, question practice with reveal &
  per-option explanations, staged cases, source-trace display, per-item notes, weak-item marking,
  search, progress tracking, and a live blueprint-coverage view.
- **Local-first persistence** (works with zero setup) + an **optional Supabase cloud-sync** layer.

### Update pipeline (Phase 9)
- Drop a new NotebookLM ZIP and run `scripts/update_pipeline.py` to re-ingest, re-score coverage,
  detect newly-covered topics, and prepare a delta plan — without disturbing existing content.

## Remaining thin / missing blueprint areas

The corpus is richest in immunohematology, transfusion reactions, components, and clinical
practice, and thinnest in these domains (prioritise for the next source drop):

- **S12 Platelets** — coverage 0.57 (0 missing, 6 thin leaves)
- **S13 Neutrophils** — coverage 0.62 (0 missing, 1 thin leaves)
- **S15 Obstetric and Pediatric Patients** — coverage 0.66 (1 missing, 4 thin leaves)
- **S8 Infectious Hazards of Transfusion** — coverage 0.68 (16 missing, 17 thin leaves)
- **S4 Anemia and Red Blood Cell Transfusion** — coverage 0.69 (1 missing, 2 thin leaves)

Fellow-level esoterica (rare blood-group systems, tissue-type minutiae, gene-therapy vectors)
are the bulk of `missing` topics — expected, as the study corpus targets high-yield material.
See `logs/coverage_gap_report.md` for the full Core/AR gap list.

## What needs human review

31 questions and 3 cases were held back from the bank by the audit gate
(correctness-critical flags or unresolved source support). They live, with their audit verdicts,
in `content/review/review_queue.json`. Summary of flagged items:

- **Q-0003** (1. Clinical Practice) — partial, flags: unsupported-claim, overclaims-as-policy, too-esoteric-thin-source
- **Q-0074** (17. Blood Bank/Transfusion M) — partial, flags: unsupported-claim, ambiguous-stem, multiple-defensible-answers
- **Q-0078** (17. Blood Bank/Transfusion M) — pass, flags: blueprint-mismatch
- **Q-0079** (1. Clinical Practice) — partial, flags: unsupported-claim, blueprint-mismatch, overclaims-as-policy
- **Q-0081** (1. Clinical Practice) — fail, flags: unsupported-claim, blueprint-mismatch, overclaims-as-policy
- **Q-0098** (1. Clinical Practice) — partial, flags: unsupported-claim, overclaims-as-policy
- **Q-0107** (1. Clinical Practice) — partial, flags: unsupported-claim, blueprint-mismatch
- **Q-0114** (2. Cell and Tissue Therapy) — partial, flags: blueprint-mismatch, unsupported-claim, weak-distractor, too-esoteric-thin-source
- **Q-0115** (2. Cell and Tissue Therapy) — fail, flags: blueprint-mismatch, unsupported-claim, too-esoteric-thin-source, weak-distractor, duplicate-coverage
- **Q-0116** (2. Cell and Tissue Therapy) — partial, flags: blueprint-mismatch, unsupported-claim, duplicate-coverage
- **Q-0122** (2. Cell and Tissue Therapy) — fail, flags: unsupported-claim, overclaims-as-policy, blueprint-mismatch
- **Q-0123** (2. Cell and Tissue Therapy) — fail, flags: unsupported-claim, blueprint-mismatch, too-esoteric-thin-source
- **Q-0124** (2. Cell and Tissue Therapy) — fail, flags: unsupported-claim, blueprint-mismatch, too-esoteric-thin-source, duplicate-coverage
- **Q-0161** (3. RBCs and RBC Components) — pass, flags: blueprint-mismatch, ambiguous-stem
- **Q-0162** (3. RBCs and RBC Components) — pass, flags: blueprint-mismatch
- **Q-0163** (3. RBCs and RBC Components) — pass, flags: blueprint-mismatch
- **Q-0168** (3. RBCs and RBC Components) — fail, flags: unsupported-claim, blueprint-mismatch, too-esoteric-thin-source
- **Q-0169** (3. RBCs and RBC Components) — fail, flags: unsupported-claim, blueprint-mismatch, too-esoteric-thin-source
- **Q-0222** (6. Hazards of Transfusion: S) — pass, flags: blueprint-mismatch
- **Q-0238** (6. Hazards of Transfusion: S) — partial, flags: blueprint-mismatch, unsupported-claim
- **Q-0239** (6. Hazards of Transfusion: S) — partial, flags: blueprint-mismatch, unsupported-claim
- **Q-0240** (6. Hazards of Transfusion: S) — partial, flags: blueprint-mismatch, unsupported-claim
- **Q-0242** (6. Hazards of Transfusion: S) — pass, flags: ambiguous-stem
- **Q-0243** (6. Hazards of Transfusion: S) — pass, flags: ambiguous-stem, duplicate-coverage
- **Q-0293** (8. Infectious Hazards of Tra) — partial, flags: blueprint-mismatch, unsupported-claim
- **Q-0294** (8. Infectious Hazards of Tra) — partial, flags: blueprint-mismatch, unsupported-claim
- **Q-0295** (8. Infectious Hazards of Tra) — partial, flags: blueprint-mismatch, unsupported-claim, ambiguous-stem
- **Q-0404** (16. Hematopoietic Progenitor) — fail, flags: unsupported-claim, numeric-value-unverified, too-esoteric-thin-source
- **Q-0409** (16. Hematopoietic Progenitor) — fail, flags: unsupported-claim, too-esoteric-thin-source, numeric-value-unverified
- **Q-0411** (16. Hematopoietic Progenitor) — fail, flags: unsupported-claim, overclaims-as-policy, too-esoteric-thin-source
- **Q-0432** (17. Blood Bank/Transfusion M) — pass, flags: ambiguous-stem, multiple-defensible-answers
- **C-004** (6. Hazards of Transfusion: S) — partial, flags: unrealistic-scenario, incorrect-answer-key, unsupported-claim
- **C-009** (3. RBCs and RBC Components) — partial, flags: unsupported-claim, incorrect-answer-key, missing-decision-logic
- **C-010** (3. RBCs and RBC Components) — partial, flags: incorrect-answer-key

Also note: many accepted items carry a `partial` source-support rating — solidly grounded but
with a minor unverified detail flagged by the auditor. They are safe to study from; the source
trace on each item shows exactly what backs it.

## Run instructions

```bash
cd app
npm install
npm run dev        # local dev at http://localhost:5173
npm run build      # static bundle in app/dist
```

Deployment (GitHub Pages) is automated via `.github/workflows/deploy.yml` on push to `main`.
Cloud sync is optional — see `supabase/README.md`. Full pipeline + update instructions are in
the root `README.md` and `logs/update_workflow.md`.

## Caveats

- Educational board-prep only — **not** clinical decision support or institutional policy.
- Generated content can contain errors; items flagged for review are excluded from the bank and
  surfaced with caution banners in the app.
- Coverage percentages are a lexical-support signal, not a correctness guarantee.
