#!/usr/bin/env python3
"""
Build a textbook-grounded gap-fill plan: for each blueprint entity NOT yet covered by a
question, retrieve the most relevant pages from the reference textbooks and write a cited
grounding passage. Topics the textbooks don't genuinely cover are SKIPPED (reported as
still-unfillable) — no fluff.
"""
from __future__ import annotations
import json
import math
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
CHUNKS = json.loads((ROOT / "scratch_textbook_chunks.json").read_text())
ONT = json.loads((ROOT / "content/blueprint/bbtm_blueprint_ontology.json").read_text())
M = json.loads((ROOT / "content/coverage/coverage_matrix.json").read_text())
QBANK = json.loads((ROOT / "content/questions/questions_pilot.json").read_text())["questions"]
REVIEW = json.loads((ROOT / "content/review/review_queue.json").read_text())

RETR_DIR = ROOT / "sources" / "reference-texts" / "retrieved"
RETR_DIR.mkdir(parents=True, exist_ok=True)

SECT_TITLE = {s["id"]: s["title"] for s in ONT["sections"]}
NODE_PATH, NODE_DESIG = {}, {}
def _idx(nodes, prefix):
    for n in nodes:
        p = prefix + [n["title"]]
        NODE_PATH[n["id"]] = " › ".join(p)
        NODE_DESIG[n["id"]] = n["designation"]
        _idx(n["children"], p)
for _s in ONT["sections"]:
    _idx(_s["children"], [f"{_s['id'][1:]}. {_s['title']}"])

SYN = {
    "htlv": "human t cell lymphotropic virus", "hbv": "hepatitis b", "hcv": "hepatitis c",
    "hav": "hepatitis a", "hdv": "hepatitis d delta", "hev": "hepatitis e", "hiv": "human immunodeficiency",
    "cmv": "cytomegalovirus", "wnv": "west nile", "vcjd": "variant creutzfeldt jakob", "cjd": "creutzfeldt jakob",
    "hpc": "hematopoietic progenitor cell", "dli": "donor lymphocyte infusion", "gvhd": "graft versus host",
    "hdfn": "hemolytic disease fetus newborn", "rhig": "rh immune globulin", "ecp": "photopheresis",
    "tpe": "plasma exchange", "hla": "human leukocyte antigen", "hpa": "human platelet antigen",
}
STOP = set("""a an the of and or to in for with on at from by as is are be this that these those it its their
general overview types type aspects aspect medical clinical features feature laboratory principle principles
treatment management causes cause diagnosis diagnostic presentation course description characteristics
information considerations methods method techniques technique tests test testing procedures risk risks
adverse effects effect indications indication use uses guidelines guideline selection role function structure
biology definition definitions common special specific standard requirements current issues system systems""".split())


def terms(title: str) -> list[str]:
    out = []
    for w in re.findall(r"[a-z0-9]+", title.lower()):
        if w in STOP or len(w) <= 2:
            continue
        out.append(w)
        if w in SYN:
            out.extend(SYN[w].split())
    return list(dict.fromkeys(out))


# ---- document frequency for IDF weighting over chunks ----
DF = defaultdict(int)
for c in CHUNKS:
    for w in set(re.findall(r"[a-z0-9]+", c["text"].lower())):
        DF[w] += 1
N = len(CHUNKS)
def idf(t): return math.log(N / (1 + DF.get(t, 0)))

# pre-tokenize chunks (lowercased text kept)
for c in CHUNKS:
    c["low"] = c["text"].lower()

# ---- entities not yet covered by a question ----
existing = {q["subdomain"].strip().lower() for q in QBANK}
existing |= {q.get("subdomain", "").strip().lower() for q in REVIEW.get("questions_needing_review", [])}
existing_nodes = {q["blueprint_node_id"] for q in QBANK} | {q.get("blueprint_node_id", "") for q in REVIEW.get("questions_needing_review", [])}

GENERIC = {"pathophysiology", "treatment", "management", "clinical features", "laboratory features",
           "prevention", "diagnosis", "causes", "overview", "incidence", "epidemiology",
           "general information", "general principles", "description and characteristics", "complications",
           "transfusions", "treatment/transfusion", "treatment/pharmacologic", "general considerations"}

entities = {}
for n in M["nodes"]:
    a = n["anchor_phrase"].strip()
    if a.lower() in GENERIC or len(a) < 4:
        continue
    if a.lower() in existing or n["id"] in existing_nodes:
        continue
    g = entities.setdefault((n["section"], a.lower()), {
        "entity": a, "section": n["section"], "node_id": n["id"], "designation": n["designation"]})
    # prefer representative node whose title == anchor
    if n["title"].strip().lower() == a.lower():
        g["node_id"] = n["id"]; g["designation"] = n["designation"]

qnum = max([int(re.match(r"Q-(\d+)", q["id"]).group(1)) for q in QBANK]
           + [int(re.match(r"Q-(\d+)", q.get("id", "Q-0000")).group(1)) for q in REVIEW.get("questions_needing_review", [])] + [0])

DESIG_RANK = {"C": 0, "AR": 1, "F": 2, None: 3}
ANGLES = ["the underlying mechanism / pathophysiology", "laboratory or serologic interpretation",
          "the best clinical management or transfusion decision", "recognizing a classic complication or pitfall"]


def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def retrieve(entity: str, topic_path: str):
    ent_q = terms(entity)                       # the entity's OWN distinctive terms
    ctx = [t for t in terms(topic_path) if t not in ent_q]
    if not ent_q:
        return None, 0.0, None, 0
    key_term = max(ent_q, key=idf)              # single most distinctive own-term
    scored = []
    for c in CHUNKS:
        low = c["low"]
        kt = low.count(key_term)                                 # topical dominance signal
        if kt == 0 and entity.lower() not in low:
            continue
        base = sum(idf(t) * low.count(t) for t in ent_q)
        base += 0.15 * sum(idf(t) * min(low.count(t), 3) for t in ctx)
        if entity.lower() in low:
            base += 5.0
        # rank primarily by how often the entity's key term recurs *in this window*
        scored.append((kt, base, c))
    if not scored:
        return None, 0.0, key_term, 0
    scored.sort(key=lambda x: (-x[0], -x[1]))                    # key-term density, then score
    top = [(s, c) for _, s, c in scored[:6]]
    top_kt = scored[0][0]                                        # key-term count in the single best window
    return top, top[0][0], key_term, top_kt


plan = []
skipped = []
gap_ents = sorted(entities.values(), key=lambda g: (DESIG_RANK[g["designation"]], g["section"]))
for g in gap_ents:
    tp = NODE_PATH.get(g["node_id"], g["entity"])
    top, best, key_term, key_hits = retrieve(g["entity"], tp)
    # Gate: the single best window must be genuinely ABOUT the topic — its most distinctive
    # term must recur >=4 times there (topical dominance), not appear in passing. This is what
    # keeps grounding on-topic and prevents fluff from multi-topic pages.
    if not top or key_hits < 4:
        skipped.append({"entity": g["entity"], "section": g["section"], "designation": g["designation"],
                        "key_term": key_term, "key_hits": key_hits, "best": round(best, 1),
                        "reason": "textbooks do not substantively cover this topic"})
        continue
    # write grounding passage file with citations
    body = [f"# Reference passages for: {g['entity']}", f"_Blueprint: {tp} ({g['designation']})_", ""]
    for score, c in top:
        body.append(f"## [{c['source_name']}, p.{c['page']}]  (relevance {score:.0f})")
        body.append(c["text"][:2800])
        body.append("")
    fpath = RETR_DIR / f"{slug(g['entity'])}-{g['node_id']}.md"
    fpath.write_text("\n".join(body))
    qnum += 1
    plan.append({
        "section_id": g["section"], "domain": f"{g['section'][1:]}. {SECT_TITLE[g['section']]}",
        "entity": g["entity"], "blueprint_node_id": g["node_id"], "topic_path": tp,
        "designation": g["designation"],
        "sources": [{"source_id": top[0][1]["source_id"], "rel_path": str(fpath.relative_to(ROOT))}],
        "angles": [ANGLES[0]], "ids": [f"Q-{qnum:04d}"],
    })

json.dump({"questionGroups": plan, "casePlan": []}, open(ROOT / "scratch_textbook_args.json", "w"))
print(f"Gap entities not yet covered: {len(gap_ents)}")
print(f"  -> textbook-grounded plan: {len(plan)} questions (retrieval-backed)")
print(f"  -> skipped (textbooks don't cover): {len(skipped)}")
from collections import Counter
dom = Counter(p["section_id"] for p in plan)
print("  per-domain:", {k: dom[k] for k in sorted(dom, key=lambda x: int(x[1:]))})
des = Counter(p["designation"] for p in plan)
print("  by designation:", dict(des))
(ROOT / "logs" / "textbook_gapfill_skipped.json").write_text(json.dumps(skipped, indent=2))
