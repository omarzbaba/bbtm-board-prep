#!/usr/bin/env python3
"""
Phase 7b — assemble the expansion workflow output and MERGE it into the existing
banks. Pairs each grouped question with its per-question audit verdict, applies the
same accept/reject gate as the pilot, and appends accepted items to the existing
question/case banks (existing content and IDs untouched). Flagged items and audit
verdicts accumulate in the review queue and audit ledger.
"""
from __future__ import annotations
import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
sys.path.insert(0, str(ROOT / "scripts"))
from phase7_assemble import build_question, build_case  # reuse builders + gate

WF = ROOT / "scratch_wf_expand_output.json"
NOW = datetime.now(tz=timezone.utc).isoformat()


def load_any(s):
    if isinstance(s, (dict, list)):
        return s
    try:
        return json.loads(s)
    except Exception:
        return ast.literal_eval(s)


def clean(o):
    o = dict(o); o.pop("_audit", None); return o


def main():
    data = load_any(WF.read_text())

    new_acc_q, new_flag_q, ledger_q = [], [], []
    for grp in data.get("questionGroups", []):
        if not grp:
            continue
        g, questions, verdicts = grp["group"], grp.get("questions", []), grp.get("verdicts", [])
        vmap = {v.get("question_index"): v for v in verdicts if isinstance(v, dict)}
        for i, q in enumerate(questions):
            if i >= len(g["ids"]):
                break  # agent produced more than planned; ignore extras
            audit = vmap.get(i) or {
                "source_support": "uncertain", "answer_agrees": False, "single_best_answer": False,
                "severity": "medium", "flags": ["unaudited"],
                "verdict_notes": "No audit verdict returned for this question index.",
            }
            item = {
                "id": g["ids"][i], "domain": g["domain"], "section_id": g["section_id"],
                "entity": g["entity"], "blueprint_node_id": g["blueprint_node_id"],
                "designation": g["designation"], "node_title": g["entity"],
            }
            obj, accept = build_question({"item": item, "question": q, "audit": audit})
            # Respect the agent's decline flag (textbook grounding): if the passages did not
            # cover the topic, never accept into the bank — route to review.
            if q.get("groundable") is False:
                accept = False
                obj["review"]["status"] = "needs-human-review"
                obj["review"]["audit_flags"] = list(set(obj["review"].get("audit_flags", []) + ["agent-declined-not-covered"]))
            ledger_q.append({"id": obj["id"], "accepted": accept, "domain": obj["domain"],
                             "designation": obj["designation"], "difficulty": obj["difficulty"],
                             "support_confidence": obj["support_confidence"], "audit": audit})
            (new_acc_q if accept else new_flag_q).append(obj)

    new_acc_c, new_flag_c, ledger_c = [], [], []
    for rec in data.get("cases", []):
        if not rec or not rec.get("case") or not rec.get("audit"):
            continue
        obj, accept = build_case(rec)
        ledger_c.append({"id": obj["id"], "accepted": accept, "domain": obj["domains"][0],
                         "designation": obj["designation"], "audit": rec["audit"]})
        (new_acc_c if accept else new_flag_c).append(obj)

    # ---- Merge into existing banks ----
    qpath = ROOT / "content/questions/questions_pilot.json"
    cpath = ROOT / "content/cases/cases_pilot.json"
    rpath = ROOT / "content/review/review_queue.json"
    lpath = ROOT / "content/review/audit_ledger.json"

    qbank = json.loads(qpath.read_text())["questions"]
    cbank = json.loads(cpath.read_text())["cases"]
    review = json.loads(rpath.read_text())
    ledger = json.loads(lpath.read_text())

    qids = {q["id"] for q in qbank}
    cids = {c["id"] for c in cbank}
    merged_q = qbank + [clean(o) for o in new_acc_q if o["id"] not in qids]
    merged_c = cbank + [clean(o) for o in new_acc_c if o["id"] not in cids]

    rq_ids = {q["id"] for q in review["questions_needing_review"]}
    rc_ids = {c["id"] for c in review["cases_needing_review"]}
    review["questions_needing_review"] += [o for o in new_flag_q if o["id"] not in rq_ids]
    review["cases_needing_review"] += [o for o in new_flag_c if o["id"] not in rc_ids]
    review["summary"] = {
        "questions_total": len(merged_q) + len(review["questions_needing_review"]),
        "questions_accepted": len(merged_q),
        "questions_flagged": len(review["questions_needing_review"]),
        "cases_total": len(merged_c) + len(review["cases_needing_review"]),
        "cases_accepted": len(merged_c),
        "cases_flagged": len(review["cases_needing_review"]),
    }
    review["generated_at"] = NOW

    l_qids = {x["id"] for x in ledger["questions"]}
    l_cids = {x["id"] for x in ledger["cases"]}
    ledger["questions"] += [x for x in ledger_q if x["id"] not in l_qids]
    ledger["cases"] += [x for x in ledger_c if x["id"] not in l_cids]

    qpath.write_text(json.dumps({"schema": "questions/v1", "generated_at": NOW,
                                 "count": len(merged_q), "questions": merged_q}, indent=2))
    cpath.write_text(json.dumps({"schema": "cases/v1", "generated_at": NOW,
                                 "count": len(merged_c), "cases": merged_c}, indent=2))
    rpath.write_text(json.dumps(review, indent=2))
    lpath.write_text(json.dumps(ledger, indent=2))

    print(f"NEW questions: {len(new_acc_q)} accepted, {len(new_flag_q)} flagged")
    print(f"NEW cases:     {len(new_acc_c)} accepted, {len(new_flag_c)} flagged")
    print(f"MERGED BANK → questions: {len(merged_q)} | cases: {len(merged_c)}")
    print(f"Review queue → {review['summary']['questions_flagged']} Q, {review['summary']['cases_flagged']} C")


if __name__ == "__main__":
    main()
