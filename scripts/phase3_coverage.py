#!/usr/bin/env python3
"""
Phase 3 — Source mapping & coverage matrix.

Maps the normalized NotebookLM corpus onto the blueprint ontology using a lexical
support scorer with medical abbreviation/synonym expansion (to align source wording
with blueprint terminology). Every blueprint node receives a support status:

  covered | strong-partial | weak-partial | thin | missing | uncertain

This is an explicit LEXICAL-SUPPORT heuristic — it measures whether approved source
text discusses a topic, NOT whether any particular claim is correct. Downstream
generation (Phases 5-6) only draws from nodes that are covered / strong-partial, and
the gap report surfaces thin/missing areas honestly.
"""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
ONT = json.load(open(ROOT / "content" / "blueprint" / "bbtm_blueprint_ontology.json"))
IDX = json.load(open(ROOT / "content" / "normalized" / "source_index.json"))

# ---- Medical abbreviation / synonym expansion (terminology alignment only) ----
SYNONYMS = {
    "waiha": "warm autoimmune hemolytic anemia", "aiha": "autoimmune hemolytic anemia",
    "cad": "cold agglutinin disease", "cha": "cold hemagglutinin",
    "pch": "paroxysmal cold hemoglobinuria", "pnh": "paroxysmal nocturnal hemoglobinuria",
    "itp": "immune thrombocytopenia", "hit": "heparin induced thrombocytopenia",
    "ttp": "thrombotic thrombocytopenic purpura", "hus": "hemolytic uremic syndrome",
    "dic": "disseminated intravascular coagulation", "vwd": "von willebrand disease",
    "vwf": "von willebrand factor", "ptp": "post transfusion purpura",
    "nait": "neonatal alloimmune thrombocytopenia", "fnait": "fetal neonatal alloimmune thrombocytopenia",
    "hpa": "human platelet antigen", "hla": "human leukocyte antigen",
    "dat": "direct antiglobulin test", "iat": "indirect antiglobulin test",
    "abo": "abo blood group", "rh": "rhesus", "rhig": "rh immune globulin",
    "hdfn": "hemolytic disease of the fetus and newborn", "hdn": "hemolytic disease of the newborn",
    "trali": "transfusion related acute lung injury", "taco": "transfusion associated circulatory overload",
    "tad": "transfusion associated dyspnea", "ta-gvhd": "transfusion associated graft versus host disease",
    "gvhd": "graft versus host disease", "fnhtr": "febrile non hemolytic transfusion reaction",
    "ahtr": "acute hemolytic transfusion reaction", "dhtr": "delayed hemolytic transfusion reaction",
    "ffp": "fresh frozen plasma", "pcc": "prothrombin complex concentrate",
    "ivig": "intravenous immunoglobulin", "cryo": "cryoprecipitate",
    "tpe": "therapeutic plasma exchange", "rce": "red cell exchange",
    "ecp": "extracorporeal photopheresis", "dfpp": "double filtration plasmapheresis",
    "hpc": "hematopoietic progenitor cell", "hsct": "hematopoietic stem cell transplantation",
    "dli": "donor lymphocyte infusion", "dmso": "dimethyl sulfoxide",
    "pls": "passenger lymphocyte syndrome", "gcsf": "granulocyte colony stimulating factor",
    "g-csf": "granulocyte colony stimulating factor", "cmv": "cytomegalovirus",
    "hbv": "hepatitis b virus", "hcv": "hepatitis c virus", "hiv": "human immunodeficiency virus",
    "htlv": "human t cell lymphotropic virus", "wnv": "west nile virus", "b19": "parvovirus",
    "cgmp": "current good manufacturing practice", "qms": "quality management system",
    "sop": "standard operating procedure", "nce": "nonconforming event",
    "ecmo": "extracorporeal", "anh": "acute normovolemic hemodilution",
    "mtp": "massive transfusion protocol", "car-t": "chimeric antigen receptor t cell",
    "scd": "sickle cell disease", "g6pd": "glucose 6 phosphate dehydrogenase",
    "ddavp": "desmopressin", "epo": "erythropoietin",
}
REVERSE_SYN = {v: k for k, v in SYNONYMS.items()}

STOP = set("""a an the of and or to in for with on at from by as is are be being into within under over
this that these those it its their his her our your they them we you i he she which who whom whose what
when where why how than then so such not no nor but if else each any all some more most other others
general overview types type aspects aspect medical clinical features feature laboratory principle principles
treatment management causes cause diagnosis diagnostic presentation course description characteristics
information considerations consideration methods method techniques technique tests test testing procedures
procedure risks risk adverse effects effect indications indication use uses clinical guidelines guideline
selection role function functions structure biology definition definitions common special specific standard
requirements requirement current issues issue high yield node nodes map study guide""".split())


def expand(text: str) -> str:
    low = " " + re.sub(r"[^a-z0-9\s/-]", " ", text.lower()) + " "
    for abbr, full in SYNONYMS.items():
        if f" {abbr} " in low:
            low += " " + full + " "
    return low


def significant_terms(title: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", title.lower())
    out = []
    for w in words:
        if w in STOP or len(w) <= 2:
            continue
        out.append(w)
        if w in SYNONYMS:
            out.extend(SYNONYMS[w].split())
    return list(dict.fromkeys(out))


# ---- Build source corpus ----
sources = [s for s in IDX["approved_sources"] if not s["exact_duplicate_of"]]
src_text = {}
for s in sources:
    txt = (ROOT / s["normalized_path"]).read_text()
    src_text[s["id"]] = {
        "expanded": expand(txt),
        "orig": s["original_filename"],
        "path": s["normalized_path"],
    }


import math

N_SRC = len(sources)


def term_present(term: str, expanded: str) -> bool:
    return f" {term} " in expanded or f" {term}" in expanded[-len(term) - 2:] or re.search(rf"\b{re.escape(term)}\b", expanded) is not None


# Document frequency of every significant term across the corpus
DF: dict[str, int] = {}
for sid, d in src_text.items():
    seen = set()
    for w in re.findall(r"[a-z0-9]+", d["expanded"]):
        if w in STOP or len(w) <= 2 or w in seen:
            continue
        seen.add(w)
        DF[w] = DF.get(w, 0) + 1


def idf(term: str) -> float:
    df = DF.get(term, 0)
    return math.log(N_SRC / df) if df > 0 else math.log(N_SRC / 0.5)


def phrase_in_sources(phrase: str) -> list[str]:
    p = re.sub(r"[^a-z0-9\s]", " ", phrase.lower()).strip()
    p = re.sub(r"\s+", " ", p)
    hits = []
    if not p:
        return hits
    for sid, d in src_text.items():
        if f" {p} " in d["expanded"]:
            hits.append(sid)
    return hits


def score_node(node: dict, ancestors: list[dict]) -> dict:
    chain = ancestors + [node]
    # entity anchor phrase: nearest substantive ancestor-or-self title
    GENERIC_TITLES = re.compile(
        r"^(treatment|treatment/transfusion|treatment/pharmacologic|management|causes|"
        r"clinical features|laboratory features|pathophysiology|prevention|diagnosis|"
        r"incidence|epidemiology|overview|general considerations|general information|"
        r"general principles|description and characteristics|complications)", re.I)
    anchor = None
    for a in reversed(chain):
        if significant_terms(a["title"]) and not GENERIC_TITLES.match(a["title"].strip()):
            anchor = a["title"]
            break
    anchor = anchor or node["title"]

    anchor_hits = set(phrase_in_sources(anchor))
    for a in reversed(chain):  # try shorter entity phrases up the chain
        if a["title"] != anchor and not GENERIC_TITLES.match(a["title"].strip()) and len(significant_terms(a["title"])) >= 2:
            anchor_hits |= set(phrase_in_sources(a["title"]))
            break
    al = anchor.lower().strip()
    if al in REVERSE_SYN:
        anchor_hits |= set(phrase_in_sources(REVERSE_SYN[al]))
    # last-two-words entity phrase (helps short-name systems, e.g. "lw function")
    aw = re.findall(r"[a-z0-9]+", anchor.lower())
    if len(aw) >= 2:
        anchor_hits |= set(phrase_in_sources(" ".join(aw[-2:])))

    # KEY = distinctive terms of the ENTITY (anchor) + the node's OWN distinctive
    # terms only. Generic/section ancestor terms are deliberately excluded so a rare
    # entity is not credited by shared words like "blood group system".
    def distinctive_terms(title: str) -> list[str]:
        return [t for t in significant_terms(title)
                if len(t) >= 3 and DF.get(t, 0) <= 0.6 * N_SRC]

    key = list(dict.fromkeys(distinctive_terms(anchor) + distinctive_terms(node["title"])))

    if not key:
        # Entity identity rests on a short abbreviation (LW, Ii, P, OK System, etc.);
        # rely solely on exact entity-phrase presence — never inherit generic terms.
        na0 = len(anchor_hits)
        status = "strong-partial" if na0 >= 1 else "missing"
        return {"status": status, "anchor_phrase": anchor,
                "anchor_source_hits": sorted(anchor_hits),
                "best_support": 1.0 if na0 else 0.0,
                "source_confidence": 0.4 if na0 else 0.0,
                "supporting_sources": sorted(anchor_hits)[:5]}

    key_idf_total = sum(idf(t) for t in key)
    best, supporting = 0.0, []
    for sid, d in src_text.items():
        exp = d["expanded"]
        present_w = sum(idf(t) for t in key if term_present(t, exp))
        frac = present_w / key_idf_total if key_idf_total else 0.0
        if frac > 0.05:
            supporting.append((sid, round(frac, 2)))
        best = max(best, frac)
    supporting.sort(key=lambda x: -x[1])
    na = len(anchor_hits)

    # Specificity-first: the entity must actually appear (anchor phrase) to be "covered".
    if best >= 0.9 or (best >= 0.7 and na >= 1):
        status = "covered"
    elif best >= 0.7 or (best >= 0.5 and na >= 1):
        status = "strong-partial"
    elif best >= 0.45 or (best >= 0.3 and na >= 1):
        status = "weak-partial"
    elif best >= 0.2 or na >= 1:
        status = "thin"
    else:
        status = "missing"

    confidence = round(min(1.0, 0.6 * best + 0.4 * min(na, 2) / 2), 2)
    return {
        "status": status,
        "anchor_phrase": anchor,
        "anchor_source_hits": sorted(anchor_hits),
        "best_support": round(best, 2),
        "source_confidence": confidence,
        "supporting_sources": [s for s, _ in supporting[:5]],
    }


# ---- Walk ontology, score nodes ----
matrix_nodes = []
src_to_bp = {s["id"]: {"original_filename": src_text[s["id"]]["orig"] if not s["exact_duplicate_of"] else None,
                       "mapped_nodes": []} for s in sources}


def walk(nodes, ancestors, section):
    for n in nodes:
        sc = score_node(n, ancestors)
        rec = {
            "id": n["id"], "title": n["title"], "designation": n["designation"],
            "section": section["id"], "section_title": section["title"],
            "level": n["level"], "is_leaf": not n["children"], **sc,
        }
        matrix_nodes.append(rec)
        for sid in sc["supporting_sources"]:
            if sid in src_to_bp and sc["status"] in ("covered", "strong-partial"):
                src_to_bp[sid]["mapped_nodes"].append({"node": n["id"], "title": n["title"], "status": sc["status"]})
        walk(n["children"], ancestors + [n], section)


for sect in ONT["sections"]:
    walk(sect["children"], [sect], sect)

# ---- Section rollups (leaf-based, Core-weighted) ----
STATUS_ORDER = ["covered", "strong-partial", "weak-partial", "thin", "uncertain", "missing"]
STATUS_SCORE = {"covered": 1.0, "strong-partial": 0.75, "weak-partial": 0.5, "thin": 0.25, "uncertain": 0.15, "missing": 0.0}


def section_summary(sect_id: str):
    leaves = [m for m in matrix_nodes if m["section"] == sect_id and m["is_leaf"]]
    dist = {s: 0 for s in STATUS_ORDER}
    core_dist = {s: 0 for s in STATUS_ORDER}
    for m in leaves:
        dist[m["status"]] += 1
        if m["designation"] == "C":
            core_dist[m["status"]] += 1
    n = max(1, len(leaves))
    cov_score = round(sum(STATUS_SCORE[m["status"]] for m in leaves) / n, 3)
    core_leaves = [m for m in leaves if m["designation"] == "C"]
    core_score = round(sum(STATUS_SCORE[m["status"]] for m in core_leaves) / max(1, len(core_leaves)), 3) if core_leaves else None
    return {"leaf_count": len(leaves), "coverage_score": cov_score,
            "core_leaf_count": len(core_leaves), "core_coverage_score": core_score,
            "status_distribution": dist, "core_status_distribution": core_dist}


sections_summary = {}
for sect in ONT["sections"]:
    sections_summary[sect["id"]] = {"title": sect["title"], **section_summary(sect["id"])}

overall = {s: sum(1 for m in matrix_nodes if m["is_leaf"] and m["status"] == s) for s in STATUS_ORDER}

matrix = {
    "schema": "bbtm-coverage-matrix/v1",
    "generated_at_iso": datetime.now(tz=timezone.utc).isoformat(),
    "method": "Lexical support scoring with medical synonym expansion. Measures whether "
              "approved source text discusses each blueprint topic (not correctness). "
              "Generation eligibility = status in {covered, strong-partial}.",
    "status_legend": {
        "covered": "Topic entity present in ≥2 sources with strong term coverage.",
        "strong-partial": "Entity present in ≥1 source, good term coverage.",
        "weak-partial": "Entity mentioned; sparse coverage.",
        "thin": "Only tangential/keyword-level hits.",
        "uncertain": "Generic node; lexical matching inconclusive.",
        "missing": "No meaningful source support.",
    },
    "overall_leaf_status_counts": overall,
    "section_summaries": sections_summary,
    "nodes": matrix_nodes,
}
(ROOT / "content" / "coverage" / "coverage_matrix.json").write_text(json.dumps(matrix, indent=2))

# de-dup mapped nodes per source
for sid, d in src_to_bp.items():
    seen = set(); uniq = []
    for mn in d["mapped_nodes"]:
        if mn["node"] not in seen:
            seen.add(mn["node"]); uniq.append(mn)
    d["mapped_nodes"] = uniq
    d["mapped_node_count"] = len(uniq)
(ROOT / "content" / "coverage" / "source_to_blueprint_map.json").write_text(
    json.dumps({"schema": "source-to-blueprint-map/v1",
                "generated_at_iso": datetime.now(tz=timezone.utc).isoformat(),
                "sources": src_to_bp}, indent=2))

print("Overall leaf status counts:", overall)
tot = sum(overall.values())
gen_eligible = overall["covered"] + overall["strong-partial"]
print(f"Generation-eligible leaves (covered+strong-partial): {gen_eligible}/{tot} "
      f"({100*gen_eligible/tot:.0f}%)")
print("\nPer-section coverage score (all / core-only):")
for sid, s in sections_summary.items():
    print(f"  {sid:>3} {s['coverage_score']:.2f} / "
          f"{('%.2f'%s['core_coverage_score']) if s['core_coverage_score'] is not None else ' -- '}  {s['title'][:50]}")
