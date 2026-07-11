#!/usr/bin/env python3
"""
Build the generation plans for the pilot question bank (Phase 5) and case bank
(Phase 6). Selects well-covered, high-yield blueprint entities balanced across
domains and attaches the approved source files that support each — so every
generated item is grounded in specific approved text.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
M = json.load(open(ROOT / "content" / "coverage" / "coverage_matrix.json"))
IDX = json.load(open(ROOT / "content" / "normalized" / "source_index.json"))
ONT = json.load(open(ROOT / "content" / "blueprint" / "bbtm_blueprint_ontology.json"))

SRC_PATH = {s["id"]: s["normalized_path"] for s in IDX["approved_sources"]}
# map exact-duplicate ids to their canonical normalized file too
for s in IDX["approved_sources"]:
    if s["exact_duplicate_of"]:
        SRC_PATH[s["id"]] = SRC_PATH.get(s["exact_duplicate_of"], s["normalized_path"])
SRC_TITLE = {s["id"]: s["original_filename"] for s in IDX["approved_sources"]}
SECT_TITLE = {s["id"]: s["title"] for s in ONT["sections"]}

# Build node_id -> full ancestor title path from the ontology
NODE_PATH: dict[str, str] = {}


def _index_paths(nodes, prefix):
    for n in nodes:
        path = prefix + [n["title"]]
        NODE_PATH[n["id"]] = " › ".join(path)
        _index_paths(n["children"], path)


for _s in ONT["sections"]:
    _index_paths(_s["children"], [f"{_s['id'][1:]}. {_s['title']}"])

DESIG_RANK = {"C": 0, "AR": 1, "F": 2, None: 3}

# Per-domain pilot question targets (reflect board emphasis AND source richness).
QUESTION_TARGETS = {
    "S1": 8, "S2": 2, "S3": 14, "S4": 3, "S5": 4, "S6": 12, "S7": 6, "S8": 7,
    "S9": 2, "S10": 3, "S11": 1, "S12": 2, "S13": 1, "S15": 5, "S16": 3, "S17": 5,
}  # sum = 78

GENERIC = {"pathophysiology", "treatment", "management", "clinical features",
           "laboratory features", "prevention", "diagnosis", "causes", "overview",
           "incidence", "epidemiology", "general information", "general principles",
           "description and characteristics", "complications", "transfusions",
           "treatment/transfusion", "treatment/pharmacologic", "general considerations"}


def entity_groups(section_id: str, eligible=("covered", "strong-partial")):
    """Group eligible nodes in a section by entity (anchor_phrase)."""
    groups: dict[str, dict] = {}
    for n in M["nodes"]:
        if n["section"] != section_id or n["status"] not in eligible:
            continue
        anchor = n["anchor_phrase"].strip()
        if anchor.lower() in GENERIC or len(anchor) < 4:
            continue
        g = groups.setdefault(anchor, {
            "entity": anchor, "section": section_id,
            "section_title": SECT_TITLE[section_id],
            "best_designation": None, "best_support": 0.0,
            "node_id": None, "node_title": None, "sources": set(),
        })
        # prefer the node whose title IS the anchor as representative
        rank = DESIG_RANK[n["designation"]]
        if (g["best_designation"] is None
                or rank < DESIG_RANK[g["best_designation"]]
                or (rank == DESIG_RANK[g["best_designation"]] and n["best_support"] > g["best_support"])):
            g["best_designation"] = n["designation"]
        g["best_support"] = max(g["best_support"], n["best_support"])
        if g["node_id"] is None or n["title"].strip().lower() == anchor.lower():
            g["node_id"] = n["id"]
            g["node_title"] = n["title"]
        for sid in n["supporting_sources"]:
            g["sources"].add(sid)
    # rank groups: Core first, then support strength
    out = list(groups.values())
    out.sort(key=lambda g: (DESIG_RANK[g["best_designation"]], -g["best_support"], g["node_id"]))
    return out


def source_files(sids: set) -> list[dict]:
    files, seen = [], set()
    for sid in sids:
        p = SRC_PATH.get(sid)
        if p and p not in seen:
            seen.add(p)
            files.append({"source_id": sid, "path": p, "title": SRC_TITLE.get(sid, "")})
    return files[:4]


# ---------------- Question plan ----------------
q_plan = []
qnum = 1
for sect_id, target in QUESTION_TARGETS.items():
    groups = entity_groups(sect_id)
    picked = groups[:target]
    for g in picked:
        srcs = source_files(g["sources"])
        if not srcs:
            continue
        q_plan.append({
            "plan_id": f"QP-{qnum:03d}",
            "question_id": f"Q-{qnum:04d}",
            "domain": f"{sect_id[1:]}. {g['section_title']}",
            "section_id": sect_id,
            "entity": g["entity"],
            "blueprint_node_id": g["node_id"],
            "node_title": g["node_title"],
            "topic_path": NODE_PATH.get(g["node_id"], g["entity"]),
            "designation": g["best_designation"],
            "coverage_support": round(g["best_support"], 2),
            "source_files": srcs,
        })
        qnum += 1

# ---------------- Case plan ----------------
# Clinical-narrative domains suited to staged teaching cases.
CASE_TARGETS = {
    "S6": 4, "S1": 3, "S3": 3, "S5": 2, "S15": 2, "S7": 2, "S16": 1, "S8": 1,
    "S10": 1, "S12": 1,
}  # sum = 20
c_plan = []
cnum = 1
used_entities = set()
for sect_id, target in CASE_TARGETS.items():
    groups = [g for g in entity_groups(sect_id) if g["entity"] not in used_entities]
    for g in groups[:target]:
        srcs = source_files(g["sources"])
        if not srcs:
            continue
        used_entities.add(g["entity"])
        c_plan.append({
            "plan_id": f"CP-{cnum:03d}",
            "case_id": f"C-{cnum:03d}",
            "domain": f"{sect_id[1:]}. {g['section_title']}",
            "section_id": sect_id,
            "entity": g["entity"],
            "blueprint_node_id": g["node_id"],
            "topic_path": NODE_PATH.get(g["node_id"], g["entity"]),
            "designation": g["best_designation"],
            "coverage_support": round(g["best_support"], 2),
            "source_files": srcs,
        })
        cnum += 1

(ROOT / "content" / "questions" / "generation_plan.json").write_text(
    json.dumps({"target": 75, "candidates": len(q_plan), "plan": q_plan}, indent=2))
(ROOT / "content" / "cases" / "case_plan.json").write_text(
    json.dumps({"target": 20, "candidates": len(c_plan), "plan": c_plan}, indent=2))

print(f"Question candidates: {len(q_plan)} (target 75)")
from collections import Counter
qc = Counter(p["section_id"] for p in q_plan)
print("  per-domain:", dict(sorted(qc.items(), key=lambda x: int(x[0][1:]))))
print(f"Case candidates: {len(c_plan)} (target 20)")
cc = Counter(p["section_id"] for p in c_plan)
print("  per-domain:", dict(sorted(cc.items(), key=lambda x: int(x[0][1:]))))
print("\nSample question topics:")
for p in q_plan[:8]:
    print(f"  {p['question_id']} [{p['designation']}] {p['entity'][:40]:40s} <- {len(p['source_files'])} src ({p['domain'][:28]})")
