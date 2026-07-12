#!/usr/bin/env python3
"""
Deficiency analysis: what can still be filled with STRONG, source-grounded questions
vs. what is genuinely unfillable (thin/missing sources -> needs new material).

Classifies every covered/strong-partial blueprint entity as:
  - already covered by an existing question
  - FILLABLE: real source depth, no question yet -> gap-fill candidate
  - marginal: covered but single/thin source (lower priority)
And reports the UNFILLABLE roadmap (thin/missing leaf topics) per domain.

Emits a quality-gated gap-fill plan (scratch_gapfill_args.json) for fillable entities
with genuine depth, deduped against the existing bank + review queue.
"""
from __future__ import annotations
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
M = json.load(open(ROOT / "content/coverage/coverage_matrix.json"))
IDX = json.load(open(ROOT / "content/normalized/source_index.json"))
ONT = json.load(open(ROOT / "content/blueprint/bbtm_blueprint_ontology.json"))
QBANK = json.load(open(ROOT / "content/questions/questions_pilot.json"))["questions"]
REVIEW = json.load(open(ROOT / "content/review/review_queue.json"))

SRC_PATH = {s["id"]: s["normalized_path"] for s in IDX["approved_sources"]}
WORDS = {s["id"]: s["word_count"] for s in IDX["approved_sources"]}
for s in IDX["approved_sources"]:
    if s["exact_duplicate_of"]:
        SRC_PATH[s["id"]] = SRC_PATH.get(s["exact_duplicate_of"], s["normalized_path"])
        WORDS[s["id"]] = WORDS.get(s["exact_duplicate_of"], s["word_count"])
SECT_TITLE = {s["id"]: s["title"] for s in ONT["sections"]}

NODE_PATH: dict[str, str] = {}
def _idx(nodes, prefix):
    for n in nodes:
        p = prefix + [n["title"]]
        NODE_PATH[n["id"]] = " › ".join(p)
        _idx(n["children"], p)
for _s in ONT["sections"]:
    _idx(_s["children"], [f"{_s['id'][1:]}. {_s['title']}"])

DESIG_RANK = {"C": 0, "AR": 1, "F": 2, None: 3}
GENERIC = {"pathophysiology", "treatment", "management", "clinical features", "laboratory features",
           "prevention", "diagnosis", "causes", "overview", "incidence", "epidemiology",
           "general information", "general principles", "description and characteristics",
           "complications", "transfusions", "treatment/transfusion", "treatment/pharmacologic",
           "general considerations", "clinical outcomes", "clinical presentation and course"}

# Existing coverage: entity names + blueprint node ids already used by a question
existing_entities = {q["subdomain"].strip().lower() for q in QBANK}
existing_nodes = {q["blueprint_node_id"] for q in QBANK}
# also treat review-queue items as "attempted" (avoid regenerating the same thing)
for q in REVIEW.get("questions_needing_review", []):
    existing_entities.add(q.get("subdomain", "").strip().lower())
    existing_nodes.add(q.get("blueprint_node_id", ""))

# max existing question number (bank + review) to continue ids
def qnum(qid):
    m = re.match(r"Q-(\d+)", qid or "")
    return int(m.group(1)) if m else 0
max_q = max([qnum(q["id"]) for q in QBANK] + [qnum(q.get("id", "")) for q in REVIEW.get("questions_needing_review", [])] + [0])


def entity_groups(section_id):
    groups = {}
    for n in M["nodes"]:
        if n["section"] != section_id or n["status"] not in ("covered", "strong-partial"):
            continue
        a = n["anchor_phrase"].strip()
        if a.lower() in GENERIC or len(a) < 4:
            continue
        g = groups.setdefault(a, {"entity": a, "section": section_id, "srcs": set(),
                                  "best": 0.0, "desig": None, "node_id": None, "status": n["status"],
                                  "anchor_hits": set()})
        rank = DESIG_RANK[n["designation"]]
        if g["desig"] is None or rank < DESIG_RANK[g["desig"]]:
            g["desig"] = n["designation"]
        g["best"] = max(g["best"], n["best_support"])
        if n["status"] == "covered":
            g["status"] = "covered"
        if g["node_id"] is None or n["title"].strip().lower() == a.lower():
            g["node_id"] = n["id"]
        g["srcs"].update(n["supporting_sources"])
        g["anchor_hits"].update(n.get("anchor_source_hits", []))
    return list(groups.values())


def is_strong_fillable(g) -> bool:
    """Quality gate: only genuinely teachable entities, not lexical-mention noise.
    - the entity NAME actually appears in >=1 source (anchor_hits), and
    - >=2 supporting sources with decent support, and
    - Core/AR (high-yield) OR a very richly-sourced Fellow topic."""
    if covered_by_q(g):
        return False
    if len(g["anchor_hits"]) < 1 or len(g["srcs"]) < 2 or g["best"] < 0.6:
        return False
    if g["desig"] in ("C", "AR"):
        return True
    return richness(g) >= 3 and len(g["anchor_hits"]) >= 2  # Fellow only if strongly sourced


def richness(g):
    ns = len(g["srcs"]); words = sum(WORDS.get(s, 0) for s in g["srcs"])
    if ns >= 3 and words >= 2500 and g["status"] == "covered":
        return 3
    if (ns >= 2 and words >= 1500) or (ns >= 2 and g["status"] == "covered"):
        return 2
    return 1


def covered_by_q(g):
    return g["entity"].strip().lower() in existing_entities or g["node_id"] in existing_nodes


ANGLES = [
    "the underlying mechanism / pathophysiology",
    "laboratory or serologic interpretation",
    "the best clinical management or transfusion decision",
    "distinguishing this entity from its close mimics",
    "recognizing a classic complication, pitfall, or board trap",
]

report = {}
gap_groups = []
qn = max_q
for sid in [f"S{i}" for i in range(1, 18)]:
    ents = entity_groups(sid)
    done = [g for g in ents if covered_by_q(g)]
    fillable = [g for g in ents if is_strong_fillable(g)]                      # quality-gated
    marginal = [g for g in ents if not covered_by_q(g) and not is_strong_fillable(g)]
    # unfillable leaves (source gaps)
    thin_missing = [n for n in M["nodes"] if n["section"] == sid and n["is_leaf"]
                    and n["status"] in ("thin", "missing")]
    report[sid] = {"title": SECT_TITLE[sid], "total_entities": len(ents),
                   "covered_by_q": len(done), "fillable_strong": len(fillable),
                   "marginal": len(marginal), "thin_missing_leaves": len(thin_missing)}
    # build gap-fill plan from the strong fillable entities
    fillable.sort(key=lambda g: (DESIG_RANK[g["desig"]], -richness(g), -g["best"]))
    for g in fillable:
        files, seen = [], set()
        for s in sorted(g["srcs"], key=lambda s: -WORDS.get(s, 0)):
            p = SRC_PATH.get(s)
            if p and p not in seen:
                seen.add(p); files.append({"source_id": s, "rel_path": p})
        if not files:
            continue
        n_q = 1  # breadth-first: one strong question per new entity to maximise coverage
        ids, angles = [], []
        for k in range(n_q):
            qn += 1
            ids.append(f"Q-{qn:04d}")
            angles.append(ANGLES[k % len(ANGLES)])
        gap_groups.append({"section_id": sid, "domain": f"{sid[1:]}. {SECT_TITLE[sid]}",
                           "entity": g["entity"], "blueprint_node_id": g["node_id"],
                           "topic_path": NODE_PATH.get(g["node_id"], g["entity"]),
                           "designation": g["desig"], "sources": files[:4], "angles": angles, "ids": ids})

json.dump({"questionGroups": gap_groups, "casePlan": []}, open(ROOT / "scratch_gapfill_args.json", "w"))
total_gap_q = sum(len(g["ids"]) for g in gap_groups)

print("DEFICIENCY ANALYSIS (per domain)\n")
print(f"{'dom':>4} {'ents':>5} {'hasQ':>5} {'FILL':>5} {'marg':>5} {'gaps':>5}  domain")
tf = tm = tg = 0
for sid in [f"S{i}" for i in range(1, 18)]:
    r = report[sid]
    tf += r["fillable_strong"]; tm += r["marginal"]; tg += r["thin_missing_leaves"]
    print(f"{sid:>4} {r['total_entities']:>5} {r['covered_by_q']:>5} {r['fillable_strong']:>5} "
          f"{r['marginal']:>5} {r['thin_missing_leaves']:>5}  {r['title'][:40]}")
print(f"\nStrong fillable entities (multi-source depth, no question yet): {tf}")
print(f"  -> gap-fill plan: {total_gap_q} new questions across {len(gap_groups)} entities")
print(f"Marginal (single thin source): {tm}  (skipped — would risk fluff)")
print(f"UNFILLABLE thin/missing leaf topics (need new sources): {tg}")
print(f"Continuing question IDs from Q-{max_q+1:04d}")

# save the human report
lines = ["# Deficiency & Gap-Fill Analysis", "",
         f"Question bank: {len(QBANK)} · covered/strong entities analysed per domain.", "",
         "| # | Domain | Entities | Has Q | **Fillable (strong)** | Marginal | Unfillable leaves |",
         "|---|--------|---------:|------:|----------------------:|---------:|------------------:|"]
for sid in [f"S{i}" for i in range(1, 18)]:
    r = report[sid]
    lines.append(f"| {sid[1:]} | {r['title'][:34]} | {r['total_entities']} | {r['covered_by_q']} | "
                 f"**{r['fillable_strong']}** | {r['marginal']} | {r['thin_missing_leaves']} |")
lines += ["", f"- **Fillable now (strong, source-backed):** {tf} entities → generating **{total_gap_q}** more questions.",
          f"- **Marginal** (single thin source, skipped to avoid fluff): {tm} entities.",
          f"- **Unfillable** (thin/missing sources — need new NotebookLM material): {tg} leaf topics. "
          "See `logs/coverage_gap_report.md` for the itemised list — that is the roadmap for your next source drop.", ""]
(ROOT / "logs" / "deficiency_analysis.md").write_text("\n".join(lines))
