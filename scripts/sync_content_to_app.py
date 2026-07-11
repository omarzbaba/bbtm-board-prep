#!/usr/bin/env python3
"""Copy pipeline content artifacts into the web app's public/content/ folder so the
static app can fetch them. Safe to run repeatedly; run after content is (re)generated."""
from __future__ import annotations
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
DEST = ROOT / "app" / "public" / "content"
DEST.mkdir(parents=True, exist_ok=True)


def copy_if(src: Path, name: str) -> bool:
    if src.exists():
        shutil.copyfile(src, DEST / name)
        return True
    return False


# Blueprint & coverage (always available)
copy_if(ROOT / "content" / "blueprint" / "bbtm_blueprint_ontology.json", "blueprint_ontology.json")
copy_if(ROOT / "content" / "coverage" / "coverage_matrix.json", "coverage_matrix.json")

# Questions / cases (present once generated; else write empty placeholders)
q_src = ROOT / "content" / "questions" / "questions_pilot.json"
c_src = ROOT / "content" / "cases" / "cases_pilot.json"
if not copy_if(q_src, "questions_pilot.json"):
    (DEST / "questions_pilot.json").write_text(json.dumps({"questions": []}, indent=2))
if not copy_if(c_src, "cases_pilot.json"):
    (DEST / "cases_pilot.json").write_text(json.dumps({"cases": []}, indent=2))

qn = len(json.loads((DEST / "questions_pilot.json").read_text()).get("questions", []))
cn = len(json.loads((DEST / "cases_pilot.json").read_text()).get("cases", []))
(DEST / "meta.json").write_text(json.dumps({
    "generated_at": datetime.now(tz=timezone.utc).isoformat(),
    "question_count": qn,
    "case_count": cn,
    "build": "pilot",
}, indent=2))

print(f"Synced content to app/public/content/  (questions={qn}, cases={cn})")
