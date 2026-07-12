#!/usr/bin/env python3
"""
Deterministic option-order normalization.

Board questions must display options labelled A, B, C, D, E in sequence, but the
correct answer must NOT cluster in one position (the generator strongly favours 'A').
This orders each question's options by a stable hash of (question_id + option_text),
relabels them A..E in that order, and remaps correct_option_id + option_explanations.

Properties:
- Sequential labels (A, B, C, ...) top-to-bottom — what a learner expects.
- Correct-answer position de-biased (depends on text hash, not the authored label).
- Deterministic + idempotent (sort key uses text, which does not change on re-run).
"""
from __future__ import annotations
import hashlib

LETTERS = ["A", "B", "C", "D", "E"]


def _key(qid: str, text: str) -> str:
    return hashlib.sha256(f"{qid}|{text}".encode()).hexdigest()


def normalize_option_order(q: dict) -> dict:
    opts = q.get("options") or []
    if len(opts) < 2:
        return q
    ordered = sorted(opts, key=lambda o: _key(q.get("id", ""), o.get("text", "")))
    old_to_new = {}
    new_opts = []
    for i, o in enumerate(ordered):
        if i >= len(LETTERS):
            break
        new_opts.append({"id": LETTERS[i], "text": o["text"]})
        old_to_new[o["id"]] = LETTERS[i]
    q["options"] = new_opts
    if q.get("correct_option_id") in old_to_new:
        q["correct_option_id"] = old_to_new[q["correct_option_id"]]
    if q.get("option_explanations"):
        q["option_explanations"] = {old_to_new.get(k, k): v for k, v in q["option_explanations"].items()}
    return q


if __name__ == "__main__":
    # Apply to the existing question bank in place.
    import json
    from collections import Counter
    from pathlib import Path

    ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
    path = ROOT / "content/questions/questions_pilot.json"
    doc = json.loads(path.read_text())
    before = Counter(q["correct_option_id"] for q in doc["questions"])
    for q in doc["questions"]:
        normalize_option_order(q)
    after = Counter(q["correct_option_id"] for q in doc["questions"])
    path.write_text(json.dumps(doc, indent=2))
    print("Normalized option order for", len(doc["questions"]), "questions.")
    print("  correct-position before:", {k: before.get(k, 0) for k in LETTERS})
    print("  correct-position after :", {k: after.get(k, 0) for k in LETTERS})
