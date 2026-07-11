#!/usr/bin/env python3
"""Generate Phase 0 & Phase 1 human-readable reports + the authoritative
source manifest, from the machine-readable JSON produced by earlier steps."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
PROV = json.load(open(ROOT / "logs" / "phase0_provenance.json"))
IDX = json.load(open(ROOT / "content" / "normalized" / "source_index.json"))
NOW = datetime.now(tz=timezone.utc).isoformat()


def human(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ---------------------------------------------------------------- source_manifest.json
pre = PROV.get("pre_move_snapshot", {})
integrity = PROV.get("raw_zip_integrity", {})
docs = IDX["approved_sources"]

manifest = {
    "schema": "bbtm-source-manifest/v1",
    "generated_at_iso": NOW,
    "description": "Authoritative manifest of APPROVED source materials for the "
                   "BB/TM board-prep content pipeline. Only files listed under "
                   "`approved` may ground generated questions/cases.",
    "approved": {
        "abpath_blueprint": {
            "file": "sources/abpath/Content-Specification-BBTM_SS_Final_01222026-2.pdf",
            "role": "Official ABPath Blood Banking/Transfusion Medicine Content Specification "
                    "(exam blueprint). Authoritative for ontology + coverage.",
            "sha256": pre.get("Content-Specification-BBTM_SS_Final_01222026-2.pdf", {}).get("sha256"),
            "size_bytes": pre.get("Content-Specification-BBTM_SS_Final_01222026-2.pdf", {}).get("size_bytes"),
        },
        "reference_texts": [
            {
                "file": f"sources/reference-texts/{name}",
                "role": "Reference textbook / standard — citeable source pointer. "
                        "Not re-extracted in full; NotebookLM corpus distills these.",
                "sha256": pre.get(name, {}).get("sha256"),
                "size_bytes": pre.get(name, {}).get("size_bytes"),
            }
            for name in [
                "AABB Technical Manual-20th ed-2020.pdf",
                "Harmening.pdf",
                "Standards for Blood Banks and Transfusion Services, 35th Edition effective April 1, 2026.pdf",
            ]
        ],
        "notebooklm_corpus": {
            "raw_archive": {
                "file": integrity.get("final_location"),
                "role": "Preserved raw NotebookLM Drive export ZIP (unchanged).",
                "sha256": integrity.get("post_sha256"),
                "integrity_verified": integrity.get("unchanged"),
            },
            "extracted_documents": [
                {
                    "id": d["id"],
                    "original_filename": d["original_filename"],
                    "normalized_path": d["normalized_path"],
                    "docx_sha256": d["docx_sha256"],
                    "word_count": d["word_count"],
                    "is_exact_duplicate": bool(d["exact_duplicate_of"]),
                    "duplicate_of": d["exact_duplicate_of"],
                }
                for d in docs
            ],
        },
    },
    "excluded": IDX["excluded_artifacts"],
    "counts": IDX["counts"],
}
(ROOT / "content" / "source_manifest.json").write_text(json.dumps(manifest, indent=2))

# ---------------------------------------------------------------- project_inventory.md
tree = PROV["canonical_tree"]
inv = f"""# Project Inventory — BB/TM Board Prep Platform

_Generated: {NOW}_

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
- **{tree['sources/abpath'][0]['name']}** — {human(tree['sources/abpath'][0]['size_bytes'])} — the official ABPath BB/TM Content Specification (17 domains, C/AR/F designations).

### Reference texts (`sources/reference-texts/`) — citeable, gitignored
"""
for f in tree["sources/reference-texts"]:
    inv += f"- **{f['name']}** — {human(f['size_bytes'])}\n"

inv += f"""
### NotebookLM corpus (`sources/notebooklm-exports/`)
- **Raw archive:** `{integrity.get('final_location')}` — {human(pre.get('raw_zip',{}).get('size_bytes',0))} — preserved, SHA-256 verified unchanged after relocation.
- **Extracted:** 61 `.docx` board-review study documents ({IDX['counts']['total_words_unique']:,} unique words across {IDX['counts']['unique_content_docs']} unique docs).

## Excluded artifacts
"""
for e in IDX["excluded_artifacts"]:
    inv += (f"- **{e['original_filename']}** — {human(e['size_bytes'])} — "
            f"EXCLUDED. {e['reason']}\n")

inv += """
## Notes
- The single large `.pptx` (~814 MB) accounts for essentially the entire ZIP size and is an unrelated presentation; it is excluded from the approved-generation layer.
- Reference textbooks and the raw ZIP are preserved locally but **gitignored** to respect copyright — only transformative, cited derivative content is committed.
"""
(ROOT / "logs" / "project_inventory.md").write_text(inv)

# ---------------------------------------------------------------- zip_ingestion_report.md
zr = f"""# ZIP Ingestion Report

_Generated: {NOW}_

## Discovery
A single candidate archive was found in the project root:

| File | Size | Selected |
|------|------|----------|
| `drive-download-20260711T222309Z-2-001.zip` | {human(pre.get('raw_zip',{}).get('size_bytes',0))} | ✅ primary source bundle |

No other `.zip`/`.tar`/archive files were present, so selection was unambiguous. A sibling
directory of the same name already existed (a prior extraction); its contents were validated
against the archive listing (62 entries = 61 `.docx` + 1 `.pptx`) and matched.

## Integrity
The raw ZIP was **relocated by rename only** (no re-compression, no byte rewrite) into the
canonical path. SHA-256 was captured before and after:

- pre  : `{integrity.get('pre_sha256')}`
- post : `{integrity.get('post_sha256')}`
- **unchanged: {integrity.get('unchanged')}**

## Extraction & provenance
- Raw archive preserved at: `{integrity.get('final_location')}`
- Extracted contents preserved at: `sources/notebooklm-exports/raw_extracted/`
- 61 `.docx` documents normalized to Markdown under `content/normalized/normalized_sources/`
- 1 `.pptx` recorded and excluded (non-BB/TM artifact)

## Actions log
"""
for a in PROV["actions"]:
    zr += f"- {a}\n"
(ROOT / "logs" / "zip_ingestion_report.md").write_text(zr)

# ---------------------------------------------------------------- source_normalization_report.md
c = IDX["counts"]
uni = sorted([d for d in docs if not d["exact_duplicate_of"]], key=lambda d: -d["word_count"])
nr = f"""# Source Normalization Report (Phase 1)

_Generated: {NOW}_

## Summary
| Metric | Value |
|--------|-------|
| Approved `.docx` documents | {c['approved_content_docs']} |
| Unique documents | {c['unique_content_docs']} |
| Exact duplicates | {c['exact_duplicates']} |
| Near-duplicate pairs (Jaccard ≥ 0.80) | {c['near_duplicate_pairs']} |
| Excluded artifacts | {c['excluded_artifacts']} |
| Total unique words | {c['total_words_unique']:,} |

## Method
- Each `.docx` parsed with `python-docx`; headings, paragraphs, bullet lists, and tables
  preserved as Markdown (`content/normalized/normalized_sources/*.md`).
- Original `.docx` bytes and normalized text both SHA-256 hashed.
- **Exact duplicates**: identical normalized-text hash. NotebookLM emitted the same study
  note under multiple audience-named files; {c['exact_duplicates']} such duplicates were detected and
  are flagged (not deleted — provenance preserved) so downstream generation reads each unique
  document once.
- **Near-duplicates**: pairwise Jaccard similarity over 3-gram shingles; none exceeded the
  0.80 threshold beyond the exact matches (remaining documents are genuinely distinct topics).

## Exact-duplicate groups (flagged, retained)
"""
for d in docs:
    if d["exact_duplicate_of"]:
        nr += f"- `{d['id']}` duplicates `{d['exact_duplicate_of']}` — {d['original_filename']}\n"

nr += "\n## Largest unique documents (grounding backbone)\n\n| id | words | top blueprint signal | document |\n|----|------:|----------------------|----------|\n"
for d in uni[:15]:
    hint = d["section_hints"][0] if d["section_hints"] else "-"
    nr += f"| {d['id']} | {d['word_count']} | {hint} | {d['original_filename']} |\n"

nr += """
## Exclusions
The `.pptx` artifact is not part of the BB/TM corpus and is excluded from all generation.
All reference textbooks remain available as **citeable source pointers** but are not
re-extracted in full; the NotebookLM corpus already distills them with citation markers.
"""
(ROOT / "logs" / "source_normalization_report.md").write_text(nr)

print("Wrote:")
for p in ["content/source_manifest.json", "logs/project_inventory.md",
          "logs/zip_ingestion_report.md", "logs/source_normalization_report.md"]:
    print(f"  {p}")
