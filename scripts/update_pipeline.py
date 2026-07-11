#!/usr/bin/env python3
"""
Phase 9 — Update pipeline.

Drop a new NotebookLM export ZIP into the project root (or sources/notebooklm-exports/
incoming/) and run this script. It will:
  1. Discover new archives (by sha256; never re-ingest the same bytes).
  2. Preserve the raw ZIP, extract NEW documents into raw_extracted/ (no overwrite).
  3. Re-normalize sources and re-score blueprint coverage.
  4. Diff coverage vs the previous run → report newly-covered / improved topics.
  5. Build a DELTA generation plan for newly-eligible topics that the current pilot
     bank does not yet cover (does NOT auto-generate — respects the pilot gate).
  6. Append a change-log entry.

Usage:  python3 scripts/update_pipeline.py
"""
from __future__ import annotations
import hashlib
import json
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
NB = ROOT / "sources" / "notebooklm-exports"
RAW = NB / "raw_extracted"
INCOMING = NB / "incoming"
LEDGER = ROOT / "logs" / "ingested_archives.json"
CHANGELOG = ROOT / "logs" / "change_log.md"
COV = ROOT / "content" / "coverage" / "coverage_matrix.json"
NOW = datetime.now(tz=timezone.utc).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"archives": []}


def snapshot_coverage() -> dict[str, str]:
    if not COV.exists():
        return {}
    m = json.loads(COV.read_text())
    return {n["id"]: n["status"] for n in m["nodes"]}


def discover_new_zips(ledger: dict) -> list[Path]:
    seen = {a["sha256"] for a in ledger["archives"]}
    candidates = list(ROOT.glob("*.zip")) + (list(INCOMING.glob("*.zip")) if INCOMING.exists() else [])
    new = []
    for z in candidates:
        if z.resolve() == (NB / z.name).resolve():
            continue
        if sha256(z) not in seen:
            new.append(z)
    return new


def ingest_zip(z: Path, ledger: dict) -> dict:
    digest = sha256(z)
    dest_zip = NB / z.name
    if not dest_zip.exists():
        shutil.move(str(z), str(dest_zip))
    RAW.mkdir(parents=True, exist_ok=True)
    added, skipped = [], []
    with zipfile.ZipFile(dest_zip) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = Path(info.filename).name
            if not name.lower().endswith((".docx", ".pdf", ".txt", ".md", ".csv")):
                skipped.append(name)
                continue
            target = RAW / name
            data = zf.read(info)
            if target.exists() and sha256(target) == hashlib.sha256(data).hexdigest():
                skipped.append(name)
                continue
            if target.exists():
                target = RAW / f"{target.stem}__import{len(ledger['archives'])+1}{target.suffix}"
            target.write_bytes(data)
            added.append(target.name)
    entry = {"archive": z.name, "sha256": digest, "ingested_at": NOW,
             "documents_added": added, "documents_skipped": len(skipped)}
    ledger["archives"].append(entry)
    return entry


def run(script: str):
    subprocess.run(["python3", str(ROOT / "scripts" / script)], check=True, cwd=str(ROOT))


def main():
    ledger = load_ledger()
    before = snapshot_coverage()
    new_zips = discover_new_zips(ledger)

    if not new_zips:
        print("No new archives found. (Drop a NotebookLM export .zip in the project root or "
              "sources/notebooklm-exports/incoming/ and re-run.)")
        return

    print(f"Found {len(new_zips)} new archive(s): {[z.name for z in new_zips]}")
    entries = [ingest_zip(z, ledger) for z in new_zips]
    LEDGER.write_text(json.dumps(ledger, indent=2))

    # Re-run pipeline (ontology unchanged unless the blueprint PDF changed)
    for s in ["phase1_normalize.py", "phase_reports.py", "phase3_coverage.py",
              "phase3_gap_report.py", "phase5_plan.py"]:
        print(f"→ running {s}"); run(s)

    after = snapshot_coverage()
    ORDER = ["missing", "uncertain", "thin", "weak-partial", "strong-partial", "covered"]
    rank = {s: i for i, s in enumerate(ORDER)}
    improved = []
    for nid, new_status in after.items():
        old = before.get(nid, "missing")
        if rank.get(new_status, 0) > rank.get(old, 0):
            improved.append({"node": nid, "from": old, "to": new_status})
    newly_eligible = [i for i in improved if i["to"] in ("covered", "strong-partial")
                      and before.get(i["node"], "missing") not in ("covered", "strong-partial")]

    # Delta plan = plan items whose blueprint node is newly eligible & not in the bank
    plan = json.loads((ROOT / "content" / "questions" / "generation_plan.json").read_text())["plan"]
    bank_path = ROOT / "content" / "questions" / "questions_pilot.json"
    existing_nodes = set()
    if bank_path.exists():
        for q in json.loads(bank_path.read_text()).get("questions", []):
            existing_nodes.add(q["blueprint_node_id"])
    newly_ids = {i["node"] for i in newly_eligible}
    delta = [p for p in plan if p["blueprint_node_id"] in newly_ids and p["blueprint_node_id"] not in existing_nodes]
    (ROOT / "content" / "questions" / "delta_plan.json").write_text(
        json.dumps({"generated_at": NOW, "note": "Newly-eligible topics from this update; "
                    "generate & audit via the workflow, then re-run phase7 to fold in.",
                    "count": len(delta), "plan": delta}, indent=2))

    # Change log
    lines = [f"\n## Update {NOW}", ""]
    for e in entries:
        lines.append(f"- Ingested `{e['archive']}` — {len(e['documents_added'])} new document(s), "
                     f"{e['documents_skipped']} skipped (duplicate/non-content).")
    lines.append(f"- Coverage: {len(improved)} node(s) improved, {len(newly_eligible)} newly generation-eligible.")
    if newly_eligible[:20]:
        lines.append("- Newly eligible (sample): " +
                     ", ".join(f"`{i['node']}` ({i['from']}→{i['to']})" for i in newly_eligible[:20]))
    lines.append(f"- Delta generation plan: {len(delta)} candidate topic(s) → `content/questions/delta_plan.json`.")
    header = "# Change Log\n" if not CHANGELOG.exists() else ""
    with CHANGELOG.open("a") as f:
        f.write(header + "\n".join(lines) + "\n")

    print(f"\nDone. Improved nodes: {len(improved)} | newly eligible: {len(newly_eligible)} | "
          f"delta topics: {len(delta)}")
    print("Next: generate+audit the delta_plan via the workflow, then re-run phase7_assemble.py & "
          "sync_content_to_app.py.")


if __name__ == "__main__":
    main()
