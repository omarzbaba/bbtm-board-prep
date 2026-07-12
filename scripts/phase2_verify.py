#!/usr/bin/env python3
"""
Phase 2 verification — prove the parsed ontology captured every blueprint node.

Independently re-scans the layout-preserved blueprint text, counts the marker
(outline) lines per section, and compares to the parsed ontology node counts.
Any mismatch means a node was dropped, duplicated, or mis-sectioned. Also checks
section titles, designation totals, and re-parses designations directly from the
raw lines to confirm they match the ontology.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
RAW = (ROOT / "scratch_blueprint.txt").read_text()
ONT = json.loads((ROOT / "content/blueprint/bbtm_blueprint_ontology.json").read_text())

MARKER_RE = re.compile(r"^(\s*)([0-9]+|[a-zA-Z]+)\.\s+(.*\S)\s*$")
DESIG_RE = re.compile(r"\s{2,}(C|AR|F)\s*$")
FOOTER = re.compile(r"American Board of Pathology")
PAGENUM = re.compile(r"^\s*\d+\s*$")

SECTION_TITLES = {
    1: "Clinical Practice", 2: "Cell and Tissue Therapy", 3: "RBCs and RBC Components",
    4: "Anemia and Red Blood Cell Transfusion", 5: "Apheresis",
    6: "Hazards of Transfusion: Specific Adverse Events",
    7: "Plasma Components and Derivatives", 8: "Infectious Hazards of Transfusion",
    9: "Blood Donors and Blood Collection", 10: "Surgery Patients",
    11: "Biovigilance and Transfusion-Related Immunomodulation", 12: "Platelets",
    13: "Neutrophils", 14: "Intravascular Cell Kinetics",
    15: "Obstetric and Pediatric Patients",
    16: "Hematopoietic Progenitor Cell (HPC) Transplantation",
    17: "Blood Bank/Transfusion Medicine-Specific Administration and Laboratory Management",
}


def content_lines():
    started = False
    for raw in RAW.splitlines():
        if not started:
            if re.match(r"^\s*1\.\s+Clinical Practice\s*$", raw):
                started = True
            else:
                continue
        if FOOTER.search(raw) or PAGENUM.match(raw) or not raw.strip():
            continue
        yield raw


# --- Independent raw scan: count marker lines + designations per section ---
raw_counts: dict[int, int] = {}
raw_desig: dict[str, int] = {"C": 0, "AR": 0, "F": 0}
cur_section = 0
next_section = 1
raw_total = 0
for line in content_lines():
    m = MARKER_RE.match(line)
    if not m:
        continue  # wrapped continuation line — merged into previous node, not a new node
    indent, tok, rest = len(m.group(1)), m.group(2), m.group(3)
    # section header?
    if tok.isdigit() and int(tok) == next_section and indent <= 6:
        cur_section = int(tok)
        next_section += 1
    raw_counts[cur_section] = raw_counts.get(cur_section, 0) + 1
    raw_total += 1
    d = DESIG_RE.search(line)
    if d:
        raw_desig[d.group(1)] += 1

# --- Ontology counts per section ---
def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n["children"])

ont_counts, ont_desig = {}, {"C": 0, "AR": 0, "F": 0}
ont_total = 0
title_ok = True
for s in ONT["sections"]:
    sid = int(s["id"][1:])
    nodes = list(walk(s["children"])) + [s]  # include the section node itself
    # section header counts as 1 marker line in raw scan (the "N. Title" line)
    ont_counts[sid] = len(nodes)
    ont_total += len(nodes)
    if s["title"] != SECTION_TITLES.get(sid):
        title_ok = False
        print(f"  ⚠ title mismatch S{sid}: '{s['title']}' vs '{SECTION_TITLES.get(sid)}'")
    for n in walk(s["children"]):
        if n["designation"] in ont_desig:
            ont_desig[n["designation"]] += 1
    if s["designation"] in ont_desig:
        ont_desig[s["designation"]] += 1

print("Section-by-section node-count verification (raw blueprint scan vs parsed ontology):\n")
print(f"{'Sec':>4} {'raw':>5} {'ont':>5} {'match':>6}  title")
all_match = True
for sid in range(1, 18):
    rc, oc = raw_counts.get(sid, 0), ont_counts.get(sid, 0)
    ok = rc == oc
    all_match = all_match and ok
    print(f"{sid:>4} {rc:>5} {oc:>5} {'✓' if ok else '✗ MISMATCH':>6}  {SECTION_TITLES[sid][:44]}")

print(f"\nTOTALS  raw marker-lines: {raw_total}  |  ontology nodes: {ont_total}  |  "
      f"{'✓ EQUAL' if raw_total == ont_total else '✗ DIFFER'}")
print(f"Designations  raw: {raw_desig}  |  ontology: {ont_desig}  |  "
      f"{'✓' if raw_desig == ont_desig else '✗ differ (see note)'}")
print(f"All 17 section titles match official spec: {'✓' if title_ok else '✗'}")
print(f"All section node counts match: {'✓ COMPLETE — no nodes dropped' if all_match else '✗ discrepancies above'}")
