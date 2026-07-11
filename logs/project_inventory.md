# Project Inventory — BB/TM Board Prep Platform

_Generated: 2026-07-11T22:34:34.964378+00:00_

## Repository layout (post-ingestion)

```
sources/
  abpath/                        official exam blueprint (1 PDF)
  reference-texts/               copyrighted reference books (3 PDFs, gitignored)
  notebooklm-exports/
    drive-download-…-001.zip     preserved raw archive (unchanged, gitignored)
    raw_extracted/               62 files (61 .docx + 1 excluded .pptx)
content/
  normalized/normalized_sources/ 61 normalized Markdown renderings of the .docx
  normalized/source_index.json   per-document normalization index
  source_manifest.json           authoritative approved-source manifest
  blueprint/                     ontology (Phase 2)
  coverage/                      coverage matrix (Phase 3)
  schemas/                       content schemas (Phase 4)
  questions/  cases/  review/    generated content (Phases 5–7)
logs/                            all pipeline reports + audit logs
scripts/                         ingestion, normalization, coverage, update pipeline
app/                             learner-facing web app (Phase 8)
```

## Approved source materials

### Exam blueprint (`sources/abpath/`)
- **Content-Specification-BBTM_SS_Final_01222026-2.pdf** — 502.8 KB — the official ABPath BB/TM Content Specification (17 domains, C/AR/F designations).

### Reference texts (`sources/reference-texts/`) — citeable, gitignored
- **AABB Technical Manual-20th ed-2020.pdf** — 20.9 MB
- **Harmening.pdf** — 21.4 MB
- **Standards for Blood Banks and Transfusion Services, 35th Edition effective April 1, 2026.pdf** — 3.9 MB

### NotebookLM corpus (`sources/notebooklm-exports/`)
- **Raw archive:** `sources/notebooklm-exports/drive-download-20260711T222309Z-2-001.zip` — 777.6 MB — preserved, SHA-256 verified unchanged after relocation.
- **Extracted:** 61 `.docx` board-review study documents (43,376 unique words across 47 unique docs).

## Excluded artifacts
- **AI_Workshop_API_Summit_v4 new.pptx** — 776.8 MB — EXCLUDED. Non-educational artifact (not part of the BB/TM study corpus); unrelated presentation file swept into the Drive export.

## Notes
- The single large `.pptx` (~814 MB) accounts for essentially the entire ZIP size and is an unrelated presentation; it is excluded from the approved-generation layer.
- Reference textbooks and the raw ZIP are preserved locally but **gitignored** to respect copyright — only transformative, cited derivative content is committed.
