#!/usr/bin/env python3
"""
Phase 2 — Blueprint ontology builder.

Parses the layout-preserved text of the ABPath BB/TM Content Specification into a
faithful hierarchical ontology with stable node IDs and C/AR/F designations.

The outline grammar is ambiguous (letter/roman/arabic markers reused at multiple
depths; `i.` = roman-1 OR letter-9; page breaks shift absolute indentation), so we
parse by SEQUENCE CONTINUITY: a marker that continues an open list's numbering is a
sibling; a "first" marker (a / i / 1) starts a child list. Indentation is used only
as a tiebreaker when several open lists could match.
"""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
SRC = ROOT / "scratch_blueprint.txt"
OUT_JSON = ROOT / "content" / "blueprint" / "bbtm_blueprint_ontology.json"
OUT_MD = ROOT / "content" / "blueprint" / "bbtm_blueprint_human_readable.md"

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

ROMAN_MAP = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8,
             "ix": 9, "x": 10, "xi": 11, "xii": 12, "xiii": 13, "xiv": 14, "xv": 15}
INT_TO_ROMAN = {v: k for k, v in ROMAN_MAP.items()}

MARKER_RE = re.compile(r"^(\s*)([0-9]+|[a-zA-Z]+)\.\s+(.*\S)\s*$")
DESIG_RE = re.compile(r"^(.*?)\s{2,}(C|AR|F)\s*$")
FOOTER_RE = re.compile(r"American Board of Pathology")
PAGENUM_RE = re.compile(r"^\s*\d+\s*$")


def letter_val(tok: str) -> int | None:
    if len(tok) == 1 and tok.isalpha():
        return ord(tok.lower()) - ord("a") + 1
    return None


def roman_val(tok: str) -> int | None:
    return ROMAN_MAP.get(tok.lower())


def arabic_val(tok: str) -> int | None:
    return int(tok) if tok.isdigit() else None


class Node:
    __slots__ = ("id", "num", "title", "designation", "children", "marker_type",
                 "value", "indent", "parent")

    def __init__(self, node_id, num, title, marker_type, value, indent, parent):
        self.id = node_id
        self.num = num
        self.title = title
        self.designation = None
        self.children: list[Node] = []
        self.marker_type = marker_type
        self.value = value
        self.indent = indent
        self.parent = parent


def clean_lines(text: str):
    started = False
    for raw in text.splitlines():
        if not started:
            if re.match(r"^\s*1\.\s+Clinical Practice\s*$", raw):
                started = True
            else:
                continue
        if FOOTER_RE.search(raw):
            continue
        if PAGENUM_RE.match(raw):
            continue
        if not raw.strip():
            continue
        yield raw


def parse() -> Node:
    root = Node("ROOT", "", "BB/TM Blueprint", "root", 0, -1, None)
    root_sections = root
    # stack holds list "levels": each entry describes an open sibling list.
    # entry = {"type","last_value","parent":Node,"indent":int}
    stack: list[dict] = []
    next_section = 1
    last_node: Node | None = None

    def top_node() -> Node:
        return stack[-1]["parent"].children[-1] if stack and stack[-1]["parent"].children else root_sections

    for raw in clean_lines(raw_text):
        m = MARKER_RE.match(raw)
        if not m:
            # continuation of previous title (wrapped line), may carry designation
            if last_node is not None:
                body = raw.strip()
                dm = DESIG_RE.match("  " + raw.rstrip()) or DESIG_RE.match(raw.rstrip())
                if dm:
                    body = dm.group(1).strip()
                    last_node.designation = last_node.designation or dm.group(2)
                if body:
                    last_node.title = (last_node.title + " " + body).strip()
            continue

        indent = len(m.group(1))
        tok = m.group(2)
        title_raw = m.group(3)  # title text, may include trailing "   C/AR/F"
        designation = None
        dm = DESIG_RE.match(title_raw)
        if dm:
            title_raw = dm.group(1)
            designation = dm.group(2)
        title = re.sub(r"\s+", " ", title_raw).strip()

        av, lv, rv = arabic_val(tok), letter_val(tok), roman_val(tok)

        # --- Section header? arabic == next expected section, far-left indent ---
        if av is not None and av == next_section and indent <= 6:
            sect = Node(f"S{av}", f"{av}", SECTION_TITLES.get(av, title), "section", av, indent, root_sections)
            sect.designation = designation
            root_sections.children.append(sect)
            stack.clear()
            stack.append({"type": "section", "last_value": av, "parent": root_sections, "indent": indent})
            next_section += 1
            last_node = sect
            continue

        # --- Find a continuation (sibling) match among open lists (deepest first) ---
        match_idx = None
        candidates = []
        for i in range(len(stack) - 1, -1, -1):
            lvl = stack[i]
            exp = lvl["last_value"] + 1
            cont = False
            if lvl["type"] == "arabic" and av is not None and av == exp:
                cont = True
            elif lvl["type"] == "letter" and lv is not None and lv == exp:
                cont = True
            elif lvl["type"] == "roman" and rv is not None and rv == exp:
                cont = True
            if cont:
                candidates.append(i)
        if candidates:
            # tiebreak by closeness of indentation
            match_idx = min(candidates, key=lambda i: abs(stack[i]["indent"] - indent))

        if match_idx is not None:
            lvl = stack[match_idx]
            del stack[match_idx + 1:]
            parent = lvl["parent"]
            if lvl["type"] == "arabic":
                mtype, val = "arabic", av
            elif lvl["type"] == "letter":
                mtype, val = "letter", lv
            else:
                mtype, val = "roman", rv
            lvl["last_value"] = val
            lvl["indent"] = indent
        else:
            # --- New child list under current deepest node ---
            parent = top_node()
            # decide marker type of the NEW list from the token
            if len(tok) > 1 and rv is not None:      # multi-char roman (ii, iii, iv...)
                mtype, val = "roman", rv
            elif tok.isdigit():
                mtype, val = "arabic", av
            elif tok.lower() == "i":                  # fresh 'i' starts a roman list
                mtype, val = "roman", 1
            elif lv is not None:
                mtype, val = "letter", lv
            elif rv is not None:
                mtype, val = "roman", rv
            else:
                mtype, val = "letter", 1
            stack.append({"type": mtype, "last_value": val, "parent": parent, "indent": indent})

        marker_repr = tok if mtype != "roman" else (INT_TO_ROMAN.get(val, tok))
        node_id = f"{parent.id}.{marker_repr}" if parent.id != "ROOT" else marker_repr
        node = Node(node_id, marker_repr, title, mtype, val, indent, parent)
        node.designation = designation
        parent.children.append(node)
        last_node = node

    return root_sections


def to_dict(n: Node) -> dict:
    return {
        "id": n.id,
        "marker": n.num,
        "title": n.title,
        "designation": n.designation,
        "level": n.marker_type,
        "children": [to_dict(c) for c in n.children],
    }


def walk(n: Node):
    for c in n.children:
        yield c
        yield from walk(c)


if __name__ == "__main__":
    raw_text = SRC.read_text()
    tree = parse()

    all_nodes = list(walk(tree))
    leaves = [n for n in all_nodes if not n.children]
    desig_counts = {"C": 0, "AR": 0, "F": 0, None: 0}
    for n in all_nodes:
        desig_counts[n.designation] = desig_counts.get(n.designation, 0) + 1

    sections = tree.children
    ontology = {
        "schema": "bbtm-blueprint-ontology/v1",
        "generated_at_iso": datetime.now(tz=timezone.utc).isoformat(),
        "source": "sources/abpath/Content-Specification-BBTM_SS_Final_01222026-2.pdf",
        "designation_key": {"C": "Core/Foundational", "AR": "Advanced Resident",
                            "F": "Fellow/Advanced Practitioner"},
        "stats": {
            "sections": len(sections),
            "total_nodes": len(all_nodes),
            "leaf_nodes": len(leaves),
            "designation_counts": {("unspecified" if k is None else k): v
                                    for k, v in desig_counts.items()},
        },
        "sections": [to_dict(s) for s in sections],
    }
    OUT_JSON.write_text(json.dumps(ontology, indent=2))

    # Human-readable
    lines = ["# ABPath Blood Banking / Transfusion Medicine — Blueprint Ontology", "",
             f"_Parsed from the official Content Specification. "
             f"{len(sections)} domains · {len(all_nodes)} nodes · {len(leaves)} leaf topics._", "",
             "**Designations:** `C` Core · `AR` Advanced Resident · `F` Fellow", ""]
    indent_for = {"section": 0, "letter": 1, "roman": 2, "arabic": 3}

    def render(n: Node, depth: int):
        pad = "  " * depth
        d = f" `{n.designation}`" if n.designation else ""
        if n.marker_type == "section":
            lines.append(f"\n## {n.num}. {n.title}{d}\n")
        else:
            lines.append(f"{pad}- **{n.num}.** {n.title}{d}")
        for c in n.children:
            render(c, depth + 1)

    for s in sections:
        render(s, 0)
    OUT_MD.write_text("\n".join(lines) + "\n")

    print(f"Sections: {len(sections)} (expected 17)")
    print(f"Total nodes: {len(all_nodes)} | leaves: {len(leaves)}")
    print(f"Designations: {ontology['stats']['designation_counts']}")
    print("Per-section node counts:")
    for s in sections:
        cnt = len(list(walk(s)))
        print(f"  S{s.value:>2}: {cnt:3d} nodes  — {s.title[:55]}")
