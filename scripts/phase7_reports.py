#!/usr/bin/env python3
"""
Phase 5/6/7 human-readable outputs: reviewable question/case markdown, audit reports,
and the blueprint coverage summary. Run after phase7_assemble.py.
"""
from __future__ import annotations
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
NOW = datetime.now(tz=timezone.utc).isoformat()

QBANK = json.loads((ROOT / "content" / "questions" / "questions_pilot.json").read_text())["questions"]
CBANK = json.loads((ROOT / "content" / "cases" / "cases_pilot.json").read_text())["cases"]
LEDGER = json.loads((ROOT / "content" / "review" / "audit_ledger.json").read_text())
REVIEW = json.loads((ROOT / "content" / "review" / "review_queue.json").read_text())
COV = json.loads((ROOT / "content" / "coverage" / "coverage_matrix.json").read_text())


def dnum(domain: str) -> int:
    import re
    m = re.match(r"(\d+)", domain)
    return int(m.group(1)) if m else 999


# ---------------- Reviewable question markdown ----------------
def questions_reviewable():
    lines = [f"# Pilot Question Bank — reviewable ({len(QBANK)} questions)", "",
             f"_Generated {NOW}. Source-grounded, adversarially audited. "
             "Correct answers and source traces shown for review._", ""]
    for q in sorted(QBANK, key=lambda x: x["id"]):
        lines.append(f"## {q['id']} — {q['subdomain']}  `{q['designation']}` · {q['difficulty']}")
        lines.append(f"*{q['domain']}* · node `{q['blueprint_node_id']}` · support: {q['support_confidence']}")
        lines.append("")
        lines.append(q["stem"])
        lines.append("")
        for o in q["options"]:
            mark = " ✅" if o["id"] == q["correct_option_id"] else ""
            lines.append(f"- **{o['id']}.** {o['text']}{mark}")
        lines.append("")
        lines.append(f"**Correct ({q['correct_option_id']}):** {q['explanation_correct']}")
        if q.get("teaching_point"):
            lines.append(f"> Pearl: {q['teaching_point']}")
        if q.get("option_explanations"):
            lines.append("")
            for oid, why in q["option_explanations"].items():
                if oid != q["correct_option_id"]:
                    lines.append(f"- *{oid} wrong:* {why}")
        srcs = ", ".join(f"`{r['source_id']}`" for r in q["source_references"])
        lines.append(f"\n**Sources:** {srcs}")
        rv = q["review"]
        lines.append(f"**Review:** {rv['status']} · source-support: {rv['source_support']}"
                     + (f" · flags: {', '.join(rv['audit_flags'])}" if rv.get("audit_flags") else ""))
        lines.append("\n---\n")
    (ROOT / "content" / "questions" / "questions_pilot_reviewable.md").write_text("\n".join(lines))


def cases_reviewable():
    lines = [f"# Pilot Case Bank — reviewable ({len(CBANK)} cases)", "",
             f"_Generated {NOW}. Source-grounded, adversarially audited._", ""]
    for c in sorted(CBANK, key=lambda x: x["id"]):
        lines.append(f"## {c['id']} — {c['title']}  `{c.get('designation','')}`")
        lines.append(f"*{', '.join(c['domains'])}* · support: {c['support_confidence']}")
        lines.append(f"\n**Setup.** {c['clinical_setup']}")
        if c.get("findings"):
            lines.append("\n**Findings.**")
            for f in c["findings"]:
                lines.append(f"- {f['label']}: {f['value']}" + (f" ({f['flag']})" if f.get("flag") not in (None, "n/a") else ""))
        lines.append("\n**Decision points.**")
        for dp in c["decision_points"]:
            lines.append(f"{dp.get('stage','?')}. {dp['prompt']}")
            lines.append(f"   - **Answer:** {dp['answer']}")
            lines.append(f"   - {dp['rationale']}")
        if c.get("answer_key"):
            lines.append(f"\n**Key pathway.** {c['answer_key']}")
        lines.append(f"\n**Teaching.** {c['teaching_explanation']}")
        if c.get("pitfalls"):
            lines.append("\n**Pitfalls.**")
            for p in c["pitfalls"]:
                lines.append(f"- {p}")
        srcs = ", ".join(f"`{r['source_id']}`" for r in c["source_references"])
        lines.append(f"\n**Sources:** {srcs}")
        rv = c["review"]
        lines.append(f"**Review:** {rv['status']} · source-support: {rv['source_support']}")
        lines.append("\n---\n")
    (ROOT / "content" / "cases" / "cases_pilot_reviewable.md").write_text("\n".join(lines))


def audit_report(kind: str, items: list, out: Path):
    total = len(items)
    acc = sum(1 for i in items if i["accepted"])
    ss = Counter(i["audit"].get("source_support", "?") for i in items)
    sev = Counter(i["audit"].get("severity", "?") for i in items)
    flags = Counter(f for i in items for f in i["audit"].get("flags", []))
    lines = [f"# {kind.title()} Audit Report", "",
             f"_Generated {NOW}. Each item was independently re-read against its approved "
             "sources by an adversarial auditor._", "",
             "## Summary", "",
             f"- Generated: **{total}**", f"- Accepted into bank: **{acc}**",
             f"- Routed to review queue: **{total - acc}**", "",
             "### Source-support distribution", ""]
    for k in ["pass", "partial", "uncertain", "fail"]:
        if ss.get(k):
            lines.append(f"- {k}: {ss[k]}")
    lines += ["", "### Severity", ""]
    for k in ["none", "low", "medium", "high"]:
        if sev.get(k):
            lines.append(f"- {k}: {sev[k]}")
    if flags:
        lines += ["", "### Audit flags raised", ""]
        for f, n in flags.most_common():
            lines.append(f"- `{f}`: {n}")
    # flagged items detail
    flagged = [i for i in items if not i["accepted"]]
    if flagged:
        lines += ["", "## Items routed to human review", "", "| ID | Domain | source-support | severity | flags |",
                  "|----|--------|----------------|----------|-------|"]
        for i in flagged:
            a = i["audit"]
            lines.append(f"| {i['id']} | {dnum(i['domain'])} | {a.get('source_support')} | "
                         f"{a.get('severity')} | {', '.join(a.get('flags', [])) or '—'} |")
    else:
        lines += ["", "_All items passed the source-support gate._"]
    out.write_text("\n".join(lines) + "\n")


def blueprint_coverage_summary():
    # distribution of pilot questions across blueprint domains + core emphasis
    qdom = Counter(dnum(q["domain"]) for q in QBANK)
    cdom = Counter(dnum(c["domains"][0]) for c in CBANK)
    desig = Counter(q["designation"] for q in QBANK)
    sect = {s: v for s, v in COV["section_summaries"].items()}
    lines = [f"# Blueprint Coverage Summary — pilot content", "", f"_Generated {NOW}._", "",
             f"The pilot bank holds **{len(QBANK)} questions** and **{len(CBANK)} cases**, "
             f"distributed across the ABPath BB/TM blueprint as follows.", "",
             "## Question designation mix", "",
             f"- Core (C): {desig.get('C',0)}", f"- Advanced Resident (AR): {desig.get('AR',0)}",
             f"- Fellow (F): {desig.get('F',0)}", "",
             "## Per-domain content vs. source coverage", "",
             "| # | Domain | Questions | Cases | Source coverage |",
             "|---|--------|----------:|------:|:---------------:|"]
    for sid, s in sorted(sect.items(), key=lambda kv: int(kv[0][1:])):
        n = int(sid[1:])
        lines.append(f"| {n} | {s['title'][:44]} | {qdom.get(n,0)} | {cdom.get(n,0)} | "
                     f"{round(s['coverage_score']*100)}% |")
    lines += ["", "Domains with 0 questions are either thinly sourced (see the gap report) or "
              "reserved for future NotebookLM drops via the update pipeline.", ""]
    (ROOT / "logs" / "blueprint_coverage_summary.md").write_text("\n".join(lines))


if __name__ == "__main__":
    questions_reviewable()
    cases_reviewable()
    audit_report("question", LEDGER["questions"], ROOT / "logs" / "question_audit_report.md")
    audit_report("case", LEDGER["cases"], ROOT / "logs" / "case_audit_report.md")
    blueprint_coverage_summary()
    print("Wrote reviewable markdown + audit reports + coverage summary.")
