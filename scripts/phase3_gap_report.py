#!/usr/bin/env python3
"""Phase 3 — human-readable coverage gap report from the coverage matrix."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
M = json.load(open(ROOT / "content" / "coverage" / "coverage_matrix.json"))
ONT = json.load(open(ROOT / "content" / "blueprint" / "bbtm_blueprint_ontology.json"))
SECT_TITLE = {s["id"]: s["title"] for s in ONT["sections"]}
NOW = datetime.now(tz=timezone.utc).isoformat()

leaves = [n for n in M["nodes"] if n["is_leaf"]]
overall = M["overall_leaf_status_counts"]
tot = sum(overall.values())
elig = overall["covered"] + overall["strong-partial"]

lines = [
    "# Coverage Gap Report — ABPath BB/TM Blueprint vs. Approved Sources", "",
    f"_Generated: {NOW}_", "",
    "## Method & honest caveat",
    "Coverage is scored by **lexical support** (IDF-weighted distinctive-term matching + "
    "entity-phrase presence, with medical synonym expansion). It measures whether approved "
    "source text **discusses** a blueprint topic — **not** whether any statement is correct, "
    "and not the pedagogical depth of that discussion.",
    "",
    "- A rarely-mentioned Fellow-level entity that appears once in a blood-group-system table "
    "may register as `covered` lexically while being too thin to teach from. Depth is enforced "
    "**downstream**: question/case generation is additionally gated by per-item source grounding "
    "and an adversarial source-support audit (Phase 7).",
    "- Truly unsupported topics correctly score `missing` and are excluded from generation.",
    "",
    "## Overall (leaf topics)",
    "",
    "| Status | Count | % |",
    "|--------|------:|--:|",
]
for s in ["covered", "strong-partial", "weak-partial", "thin", "uncertain", "missing"]:
    lines.append(f"| {s} | {overall[s]} | {100*overall[s]/tot:.0f}% |")
lines += [
    f"| **Total leaves** | **{tot}** | |", "",
    f"**Generation-eligible** (covered + strong-partial): **{elig} / {tot} ({100*elig/tot:.0f}%)**.", "",
    "## Per-domain coverage",
    "",
    "`Coverage score` = mean status weight over leaf topics (covered=1.0 … missing=0.0). "
    "`Core score` weights only Core (`C`) leaves — the foundational must-knows.", "",
    "| Domain | Leaves | Coverage | Core leaves | Core score |",
    "|--------|-------:|:--------:|------------:|:----------:|",
]
for sid, s in M["section_summaries"].items():
    core = f"{s['core_coverage_score']:.2f}" if s["core_coverage_score"] is not None else "—"
    lines.append(f"| {sid} {s['title'][:44]} | {s['leaf_count']} | {s['coverage_score']:.2f} | "
                 f"{s['core_leaf_count']} | {core} |")

# Exam-relevant gaps: Core & AR leaves that are thin/missing/weak
def gap_list(desigs, statuses):
    rows = [n for n in leaves if n["designation"] in desigs and n["status"] in statuses]
    rows.sort(key=lambda n: (n["section"], n["id"]))
    return rows

core_gaps = gap_list({"C"}, {"missing", "thin", "weak-partial"})
ar_gaps = gap_list({"AR"}, {"missing", "thin"})

lines += ["", "## Priority gaps — **Core (`C`)** topics that are weak/thin/missing",
          "", "These are foundational must-knows the corpus under-supports. Prioritise for the "
          "next NotebookLM source drop.", ""]
if core_gaps:
    lines += ["| Node | Topic | Status | Domain |", "|------|-------|--------|--------|"]
    for n in core_gaps:
        lines.append(f"| `{n['id']}` | {n['title'][:50]} | {n['status']} | {n['section']} |")
else:
    lines.append("_None — all Core leaves have at least weak-partial support._")

lines += ["", "## Advanced-Resident (`AR`) topics that are thin/missing", ""]
if ar_gaps:
    lines += ["| Node | Topic | Status | Domain |", "|------|-------|--------|--------|"]
    for n in ar_gaps[:60]:
        lines.append(f"| `{n['id']}` | {n['title'][:50]} | {n['status']} | {n['section']} |")
    if len(ar_gaps) > 60:
        lines.append(f"| … | _+{len(ar_gaps)-60} more_ | | |")
else:
    lines.append("_None._")

# Domains flagged for reinforcement
weak_domains = sorted(M["section_summaries"].items(), key=lambda kv: kv[1]["coverage_score"])[:5]
lines += ["", "## Domains most in need of reinforcement", ""]
for sid, s in weak_domains:
    lines.append(f"- **{sid} {s['title']}** — coverage {s['coverage_score']:.2f} "
                 f"({s['status_distribution']['missing']} missing, {s['status_distribution']['thin']} thin leaves).")

lines += ["", "---",
          f"_Fully machine-readable data: `content/coverage/coverage_matrix.json` "
          f"({tot} leaf assessments) and `content/coverage/source_to_blueprint_map.json`._", ""]

(ROOT / "logs" / "coverage_gap_report.md").write_text("\n".join(lines) + "\n")
print("Wrote logs/coverage_gap_report.md")
print(f"Core gaps: {len(core_gaps)} | AR thin/missing: {len(ar_gaps)}")
