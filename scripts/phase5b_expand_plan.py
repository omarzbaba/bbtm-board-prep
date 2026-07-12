#!/usr/bin/env python3
"""
Phase 5b — expanded generation plan (~5x growth), breadth-first and richness-weighted.

Selects covered / strong-partial blueprint entities the pilot did NOT exhaust, allocates
1-3 questions per entity by genuine source richness (multi-source, word count, designation),
assigns a distinct board ANGLE to each question so multi-question entities aren't redundant,
and boosts currently under-represented domains. Each entity keeps its supporting source
files so generation stays grounded. New IDs continue after the existing bank.

Also builds an expanded case plan on clinically rich entities.
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
M = json.load(open(ROOT / "content/coverage/coverage_matrix.json"))
IDX = json.load(open(ROOT / "content/normalized/source_index.json"))
ONT = json.load(open(ROOT / "content/blueprint/bbtm_blueprint_ontology.json"))
QBANK = json.load(open(ROOT / "content/questions/questions_pilot.json"))["questions"]
CBANK = json.load(open(ROOT / "content/cases/cases_pilot.json"))["cases"]

SRC_PATH = {s["id"]: s["normalized_path"] for s in IDX["approved_sources"]}
for s in IDX["approved_sources"]:
    if s["exact_duplicate_of"]:
        SRC_PATH[s["id"]] = SRC_PATH.get(s["exact_duplicate_of"], s["normalized_path"])
WORDS = {s["id"]: s["word_count"] for s in IDX["approved_sources"]}
for s in IDX["approved_sources"]:
    if s["exact_duplicate_of"]:
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

ANGLES = [
    "the underlying mechanism / pathophysiology",
    "laboratory or serologic interpretation",
    "the best clinical management or transfusion decision",
    "distinguishing this entity from its close mimics",
    "recognizing a classic complication, pitfall, or board trap",
    "a classic association, buzzword, or diagnostic clue",
]

# New questions per domain (breadth-first; capped by available entities). Boosts
# under-represented domains while respecting genuine source richness. Targets sum ~395.
DOMAIN_TARGETS = {
    "S1": 32, "S2": 14, "S3": 55, "S4": 12, "S5": 28, "S6": 32, "S7": 20, "S8": 28,
    "S9": 16, "S10": 26, "S11": 8, "S12": 14, "S13": 4, "S14": 2, "S15": 22, "S16": 28, "S17": 24,
}

pilot_nodes = {q["blueprint_node_id"] for q in QBANK}
pilot_entities = {q["subdomain"].strip().lower() for q in QBANK}


def entities_for(section_id: str):
    groups: dict[str, dict] = {}
    for n in M["nodes"]:
        if n["section"] != section_id or n["status"] not in ("covered", "strong-partial"):
            continue
        a = n["anchor_phrase"].strip()
        if a.lower() in GENERIC or len(a) < 4:
            continue
        g = groups.setdefault(a, {"entity": a, "section": section_id, "srcs": set(),
                                  "best": 0.0, "desig": None, "node_id": None, "node_title": None,
                                  "status": n["status"]})
        rank = DESIG_RANK[n["designation"]]
        if g["desig"] is None or rank < DESIG_RANK[g["desig"]]:
            g["desig"] = n["designation"]
        g["best"] = max(g["best"], n["best_support"])
        if n["status"] == "covered":
            g["status"] = "covered"
        if g["node_id"] is None or n["title"].strip().lower() == a.lower():
            g["node_id"], g["node_title"] = n["id"], n["title"]
        g["srcs"].update(n["supporting_sources"])
    return list(groups.values())


def richness(g) -> int:
    ns = len(g["srcs"]); words = sum(WORDS.get(s, 0) for s in g["srcs"])
    if ns >= 3 and words >= 2500 and g["status"] == "covered":
        return 3
    if (ns >= 2 and words >= 1500) or (ns >= 2 and g["status"] == "covered"):
        return 2
    return 1


def src_files(g):
    out, seen = [], set()
    # richest sources first
    for sid in sorted(g["srcs"], key=lambda s: -WORDS.get(s, 0)):
        p = SRC_PATH.get(sid)
        if p and p not in seen:
            seen.add(p); out.append({"source_id": sid, "abs_path": str(ROOT / p)})
    return out[:4]


def priority(g):
    # new entities first (breadth), then Core-ness, then richness/support
    is_new = 0 if g["entity"].lower() not in pilot_entities and g["node_id"] not in pilot_nodes else 1
    return (is_new, DESIG_RANK[g["desig"]], -richness(g), -g["best"], g["node_id"] or "")


q_plan = []
qnum = 79  # continue after existing Q-0078
domain_report = {}
for sec, target in DOMAIN_TARGETS.items():
    ents = sorted(entities_for(sec), key=priority)
    allotted = 0
    used = 0
    for g in ents:
        if allotted >= target:
            break
        files = src_files(g)
        if not files:
            continue
        n_q = min(richness(g), target - allotted)
        n_q = max(1, n_q)
        for k in range(n_q):
            q_plan.append({
                "id": f"Q-{qnum:04d}",
                "domain": f"{sec[1:]}. {SECT_TITLE[sec]}",
                "section_id": sec,
                "entity": g["entity"],
                "blueprint_node_id": g["node_id"],
                "topic_path": NODE_PATH.get(g["node_id"], g["entity"]),
                "designation": g["desig"],
                "angle": ANGLES[k % len(ANGLES)],
                "sources": files,
            })
            qnum += 1
            allotted += 1
            if allotted >= target:
                break
        used += 1
    domain_report[sec] = {"target": target, "generated": allotted, "entities_used": used,
                          "entities_available": len(ents)}

# ---- Case plan: clinically rich entities, ~78 new (total ~95) ----
CASE_DOMAIN_TARGETS = {
    "S6": 12, "S1": 10, "S3": 10, "S5": 8, "S15": 8, "S7": 6, "S8": 6, "S16": 6,
    "S10": 6, "S12": 3, "S2": 3, "S9": 2, "S17": 2,
}
pilot_case_ent = {d.strip().lower() for c in CBANK for d in [c.get("title", "")]}
c_plan = []
cnum = 21  # continue after existing C-020
case_report = {}
for sec, target in CASE_DOMAIN_TARGETS.items():
    ents = sorted(entities_for(sec), key=priority)
    allotted = 0
    for g in ents:
        if allotted >= target:
            break
        files = src_files(g)
        if not files or len(g["srcs"]) < 1:
            continue
        c_plan.append({
            "id": f"C-{cnum:03d}",
            "domain": f"{sec[1:]}. {SECT_TITLE[sec]}",
            "section_id": sec,
            "entity": g["entity"],
            "blueprint_node_id": g["node_id"],
            "topic_path": NODE_PATH.get(g["node_id"], g["entity"]),
            "designation": g["desig"],
            "sources": files,
        })
        cnum += 1
        allotted += 1
    case_report[sec] = {"target": target, "generated": allotted}

out = {"questionPlan": q_plan, "casePlan": c_plan}
(ROOT / "content/questions/expand_plan.json").write_text(json.dumps(
    {"question_candidates": len(q_plan), "case_candidates": len(c_plan),
     "domain_report": domain_report, "case_report": case_report, **out}, indent=2))
json.dump(out, open(ROOT / "scratch_expand_args.json", "w"))

print(f"NEW question candidates: {len(q_plan)}  (existing 75 → total ~{75 + len(q_plan)})")
print(f"NEW case candidates:     {len(c_plan)}  (existing 17 → total ~{17 + len(c_plan)})")
print("\nPer-domain (new questions):")
for sec in sorted(domain_report, key=lambda x: int(x[1:])):
    r = domain_report[sec]
    print(f"  {sec:>3} target={r['target']:>3} got={r['generated']:>3} "
          f"(from {r['entities_used']}/{r['entities_available']} entities)  {SECT_TITLE[sec][:34]}")
