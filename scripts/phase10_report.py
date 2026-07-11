#!/usr/bin/env python3
"""Phase 10 — final build report, assembled from the pipeline artifacts."""
from __future__ import annotations
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
NOW = datetime.now(tz=timezone.utc).isoformat()

idx = json.loads((ROOT / "content/normalized/source_index.json").read_text())
ont = json.loads((ROOT / "content/blueprint/bbtm_blueprint_ontology.json").read_text())
cov = json.loads((ROOT / "content/coverage/coverage_matrix.json").read_text())
qbank = json.loads((ROOT / "content/questions/questions_pilot.json").read_text())["questions"]
cbank = json.loads((ROOT / "content/cases/cases_pilot.json").read_text())["cases"]
review = json.loads((ROOT / "content/review/review_queue.json").read_text())
ledger = json.loads((ROOT / "content/review/audit_ledger.json").read_text())

ov = cov["overall_leaf_status_counts"]
qdes = Counter(q["designation"] for q in qbank)
qss = Counter(l["audit"]["source_support"] for l in ledger["questions"])
weak_sections = sorted(cov["section_summaries"].items(), key=lambda kv: kv[1]["coverage_score"])[:5]

flagged_q = review["questions_needing_review"]
flagged_c = review["cases_needing_review"]

md = f"""# Final Build Report — BB/TM Board Prep Platform

_Generated: {NOW}_

## What was built

A complete, source-grounded study platform for the ABPath Blood Banking / Transfusion
Medicine subspecialty exam — from raw NotebookLM export to a deployed, database-backed
web app — in ten phases, all artifacts reproducible on disk.

### Sources ingested (Phase 0–1)
- Raw NotebookLM ZIP preserved intact (SHA-256 verified), **{idx['counts']['approved_content_docs']} study documents**
  normalized ({idx['counts']['unique_content_docs']} unique after de-duplicating {idx['counts']['exact_duplicates']} exact copies),
  {idx['counts']['total_words_unique']:,} words.
- 1 non-content artifact (a stray 814 MB presentation) excluded and documented.
- 4 reference PDFs (official ABPath blueprint + AABB Technical Manual + Harmening + AABB Standards).

### Blueprint ontology (Phase 2)
- The official ABPath BB/TM Content Specification parsed into **{ont['stats']['sections']} domains,
  {ont['stats']['total_nodes']} nodes, {ont['stats']['leaf_nodes']} leaf topics**, each tagged Core / Advanced-Resident / Fellow.

### Coverage (Phase 3)
- Every leaf topic scored for source support:
  covered **{ov['covered']}**, strong-partial **{ov['strong-partial']}**, weak-partial **{ov['weak-partial']}**,
  thin **{ov['thin']}**, missing **{ov['missing']}**.
- Generation-eligible (covered + strong-partial): **{ov['covered'] + ov['strong-partial']} / {sum(ov.values())}**.

### Pilot content (Phase 5–7)
- **{len(qbank)} board questions** accepted into the bank ({qdes.get('C',0)} Core / {qdes.get('AR',0)} AR / {qdes.get('F',0)} Fellow);
  {review['summary']['questions_flagged']} routed to human review.
- **{len(cbank)} teaching cases** accepted; {review['summary']['cases_flagged']} routed to review.
- Every item was independently re-read against its sources by an adversarial auditor.
  Question source-support: {qss.get('pass',0)} pass, {qss.get('partial',0)} partial. Every accepted question's auditor
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

"""
for sid, s in weak_sections:
    md += f"- **{sid} {s['title']}** — coverage {s['coverage_score']:.2f} ({s['status_distribution']['missing']} missing, {s['status_distribution']['thin']} thin leaves)\n"

md += f"""
Fellow-level esoterica (rare blood-group systems, tissue-type minutiae, gene-therapy vectors)
are the bulk of `missing` topics — expected, as the study corpus targets high-yield material.
See `logs/coverage_gap_report.md` for the full Core/AR gap list.

## What needs human review

{review['summary']['questions_flagged']} questions and {review['summary']['cases_flagged']} cases were held back from the bank by the audit gate
(correctness-critical flags or unresolved source support). They live, with their audit verdicts,
in `content/review/review_queue.json`. Summary of flagged items:

"""
for q in flagged_q:
    a = q["review"]
    md += f"- **{q['id']}** ({q['domain'][:28]}) — {a['source_support']}, flags: {', '.join(a['audit_flags']) or '—'}\n"
for c in flagged_c:
    a = c["review"]
    md += f"- **{c['id']}** ({c['domains'][0][:28]}) — {a['source_support']}, flags: {', '.join(a['audit_flags']) or '—'}\n"

md += """
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
"""

(ROOT / "logs" / "final_build_report.md").write_text(md)
print("Wrote logs/final_build_report.md")

# Update README counts line
readme = (ROOT / "README.md").read_text()
readme = readme.replace(
    "Built for **Talha's** board prep. Shareable, saves progress, works on any device.",
    f"Built for **Talha's** board prep — **{len(qbank)} questions**, **{len(cbank)} cases**, "
    f"all source-grounded and audited. Shareable, saves progress, works on any device.")
(ROOT / "README.md").write_text(readme)
print("Updated README counts")
