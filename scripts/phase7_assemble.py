#!/usr/bin/env python3
"""
Phase 7 — assemble & audit-gate the generated content.

Reads the generation+audit workflow output (scratch_wf_output.json), assembles
schema-conformant question and case banks, routes audit failures to the review
queue, and writes audit reports.

Gate (bank vs review queue):
  QUESTION accepted if source_support in {pass, partial} AND answer_agrees AND
           single_best_answer AND severity != high.
  CASE accepted if source_support in {pass, partial} AND clinically_realistic AND
           severity != high.
Everything else is kept but routed to the review queue (never silently dropped).
"""
from __future__ import annotations
import ast
import json
from datetime import datetime, timezone
from pathlib import Path

from optnorm import normalize_option_order

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
WF = ROOT / "scratch_wf_output.json"
NOW = datetime.now(tz=timezone.utc).isoformat()
GEN_LABEL = "bbtm-generate-audit/sonnet"


def load_any(s):
    if isinstance(s, (dict, list)):
        return s
    try:
        return json.loads(s)
    except Exception:
        return ast.literal_eval(s)


def source_type(sid: str) -> str:
    if sid.startswith("SRC-"):
        return "notebooklm"
    if sid == "BLUEPRINT":
        return "blueprint"
    return "reference-text"


def norm_refs(refs, node_id):
    out = []
    for r in refs or []:
        if not isinstance(r, dict) or not r.get("source_id"):
            continue
        out.append({
            "source_id": r["source_id"],
            "source_type": source_type(r["source_id"]),
            "locator": r.get("locator", ""),
            "supports": (r.get("supports") or "")[:400],
            "blueprint_node_id": node_id,
            "confidence": r.get("confidence", "moderate"),
        })
    return out or [{"source_id": "BLUEPRINT", "source_type": "blueprint",
                    "locator": node_id, "supports": "Mapped to the ABPath blueprint node.",
                    "blueprint_node_id": node_id, "confidence": "low"}]


CRITICAL_Q_FLAGS = {"incorrect-answer-key", "multiple-defensible-answers"}
CRITICAL_C_FLAGS = {"incorrect-answer-key"}


def q_review(audit) -> tuple[dict, bool]:
    ss = audit.get("source_support", "uncertain")
    agree = bool(audit.get("answer_agrees"))
    single = bool(audit.get("single_best_answer"))
    sev = audit.get("severity", "low")
    flags = set(audit.get("flags", []))
    accept = (ss in ("pass", "partial") and agree and single and sev != "high"
              and not (flags & CRITICAL_Q_FLAGS))
    status = "auto-audited-pass" if accept else "needs-human-review"
    return {
        "status": status,
        "source_support": ss if ss in ("pass", "partial", "uncertain", "fail") else "uncertain",
        "audit_flags": audit.get("flags", []),
        "auditor": GEN_LABEL,
        "audited_at": NOW,
        "notes": audit.get("verdict_notes", "")[:600],
    }, accept


def c_review(audit) -> tuple[dict, bool]:
    ss = audit.get("source_support", "uncertain")
    real = bool(audit.get("clinically_realistic"))
    sev = audit.get("severity", "low")
    flags = set(audit.get("flags", []))
    accept = (ss in ("pass", "partial") and real and sev != "high"
              and not (flags & CRITICAL_C_FLAGS))
    status = "auto-audited-pass" if accept else "needs-human-review"
    return {
        "status": status,
        "source_support": ss if ss in ("pass", "partial", "uncertain", "fail") else "uncertain",
        "audit_flags": audit.get("flags", []),
        "auditor": GEN_LABEL,
        "audited_at": NOW,
        "notes": audit.get("verdict_notes", "")[:600],
    }, accept


def build_question(rec):
    item, q, audit = rec["item"], rec["question"], rec["audit"]
    node = item["blueprint_node_id"]
    opts = [{"id": o["id"], "text": o["text"]} for o in q.get("options", [])]
    ids = [o["id"] for o in opts]
    correct = q.get("correct_option_id")
    if correct not in ids:  # guard
        correct = ids[0] if ids else "A"
    rationales = {r["id"]: r["text"] for r in q.get("option_rationales", []) if r.get("id") in ids}
    review, accept = q_review(audit)
    subdomain = item.get("entity") or item.get("node_title") or item["domain"]
    obj = {
        "id": item["id"],
        "domain": item["domain"],
        "subdomain": subdomain,
        "blueprint_node_id": node,
        "designation": item["designation"],
        "difficulty": q.get("difficulty", "moderate"),
        "cognitive_level": q.get("cognitive_level", "application"),
        "stem": q["stem"],
        "options": opts,
        "correct_option_id": correct,
        "explanation_correct": q.get("explanation_correct", ""),
        "option_explanations": rationales,
        "teaching_point": q.get("teaching_point", ""),
        "source_references": norm_refs(q.get("source_references"), node),
        "support_confidence": q.get("support_confidence", "moderate"),
        "tags": [item["section_id"]],
        "learner_note": None,
        "review": review,
        "created_at": NOW,
        "generator": GEN_LABEL,
        "_audit": audit,
    }
    normalize_option_order(obj)
    return obj, accept


def build_case(rec):
    item, c, audit = rec["item"], rec["case"], rec["audit"]
    node = item["blueprint_node_id"]
    review, accept = c_review(audit)
    dps = []
    for i, dp in enumerate(c.get("decision_points", []), start=1):
        dps.append({
            "stage": dp.get("stage", i),
            "prompt": dp["prompt"],
            "options": dp.get("options", []),
            "answer": dp["answer"],
            "rationale": dp["rationale"],
        })
    return {
        "id": item["id"],
        "title": c.get("title", item["entity"]),
        "domains": [item["domain"]],
        "blueprint_node_ids": [node],
        "designation": item["designation"],
        "difficulty": c.get("difficulty", "moderate"),
        "clinical_setup": c.get("clinical_setup", ""),
        "findings": [{"label": f["label"], "value": f["value"], "flag": f.get("flag", "n/a")}
                     for f in c.get("findings", []) if f.get("label")],
        "decision_points": dps,
        "answer_key": c.get("answer_key", ""),
        "teaching_explanation": c.get("teaching_explanation", ""),
        "pitfalls": c.get("pitfalls", []),
        "source_references": norm_refs(c.get("source_references"), node),
        "support_confidence": c.get("support_confidence", "moderate"),
        "tags": [item["section_id"]],
        "learner_note": None,
        "review": review,
        "created_at": NOW,
        "generator": GEN_LABEL,
        "_audit": audit,
    }, accept


def main():
    data = load_any(WF.read_text())
    q_recs = [r for r in data.get("questions", []) if r and r.get("question") and r.get("audit")]
    c_recs = [r for r in data.get("cases", []) if r and r.get("case") and r.get("audit")]

    bank_q, review_q, all_q = [], [], []
    for r in q_recs:
        obj, accept = build_question(r)
        all_q.append((obj, accept))
        (bank_q if accept else review_q).append(obj)

    bank_c, review_c, all_c = [], [], []
    for r in c_recs:
        obj, accept = build_case(r)
        all_c.append((obj, accept))
        (bank_c if accept else review_c).append(obj)

    # Strip internal _audit before writing the public banks (keep in review queue)
    def clean(o):
        o = dict(o); o.pop("_audit", None); return o

    bank_q_clean = [clean(o) for o in bank_q]
    bank_c_clean = [clean(o) for o in bank_c]

    (ROOT / "content" / "questions" / "questions_pilot.json").write_text(
        json.dumps({"schema": "questions/v1", "generated_at": NOW, "count": len(bank_q_clean),
                    "questions": bank_q_clean}, indent=2))
    (ROOT / "content" / "cases" / "cases_pilot.json").write_text(
        json.dumps({"schema": "cases/v1", "generated_at": NOW, "count": len(bank_c_clean),
                    "cases": bank_c_clean}, indent=2))

    # Review queue (items needing human review, WITH their audit verdicts)
    review_queue = {
        "schema": "review-queue/v1", "generated_at": NOW,
        "questions_needing_review": review_q,
        "cases_needing_review": review_c,
        "summary": {
            "questions_total": len(all_q), "questions_accepted": len(bank_q),
            "questions_flagged": len(review_q),
            "cases_total": len(all_c), "cases_accepted": len(bank_c),
            "cases_flagged": len(review_c),
        },
    }
    (ROOT / "content" / "review" / "review_queue.json").write_text(json.dumps(review_queue, indent=2))

    # Audit ledger (per-item verdicts for ALL generated items) — feeds the reports.
    ledger = {
        "generated_at": NOW,
        "questions": [{"id": o["id"], "accepted": acc, "domain": o["domain"],
                       "designation": o["designation"], "difficulty": o["difficulty"],
                       "support_confidence": o["support_confidence"], "audit": o["_audit"]}
                      for o, acc in all_q],
        "cases": [{"id": o["id"], "accepted": acc, "domain": o["domains"][0],
                   "designation": o["designation"], "audit": o["_audit"]}
                  for o, acc in all_c],
    }
    (ROOT / "content" / "review" / "audit_ledger.json").write_text(json.dumps(ledger, indent=2))

    print(f"Questions: {len(all_q)} generated | {len(bank_q)} accepted | {len(review_q)} flagged")
    print(f"Cases:     {len(all_c)} generated | {len(bank_c)} accepted | {len(review_c)} flagged")
    return {"all_q": all_q, "all_c": all_c, "bank_q": bank_q, "bank_c": bank_c,
            "review_q": review_q, "review_c": review_c}


if __name__ == "__main__":
    main()
