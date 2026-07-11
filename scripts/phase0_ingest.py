#!/usr/bin/env python3
"""
Phase 0 — ZIP discovery, safe extraction bookkeeping, and provenance capture.

This script is idempotent. It:
  1. Records a provenance snapshot (path, size, mtime, sha256) of the raw ZIP
     and each root-level approved source BEFORE any move.
  2. Moves (renames — no byte copy, no re-compression) the raw sources into the
     canonical /sources tree, preserving the raw archive intact.
  3. Emits a machine-readable provenance record used by the report generators.

The raw ZIP is NEVER re-written or re-compressed; a rename preserves bytes
exactly. We record the sha256 before and (implicitly) rely on rename atomicity
to guarantee integrity.
"""
from __future__ import annotations
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
NB = ROOT / "sources" / "notebooklm-exports"
ABPATH = ROOT / "sources" / "abpath"
REFTEXTS = ROOT / "sources" / "reference-texts"

RAW_ZIP_NAME = "drive-download-20260711T222309Z-2-001.zip"
RAW_EXTRACT_NAME = "drive-download-20260711T222309Z-2-001"

# Classification of the four root PDFs
BLUEPRINT_PDF = "Content-Specification-BBTM_SS_Final_01222026-2.pdf"
REFERENCE_PDFS = [
    "AABB Technical Manual-20th ed-2020.pdf",
    "Harmening.pdf",
    "Standards for Blood Banks and Transfusion Services, 35th Edition effective April 1, 2026.pdf",
]


def sha256_of(path: Path, big_ok: bool = True) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stat_record(path: Path, with_hash: bool = True) -> dict:
    st = path.stat()
    rec = {
        "name": path.name,
        "abs_path": str(path),
        "rel_path": str(path.relative_to(ROOT)),
        "size_bytes": st.st_size,
        "mtime_iso": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
        "is_dir": path.is_dir(),
    }
    if with_hash and path.is_file():
        rec["sha256"] = sha256_of(path)
    return rec


def safe_move(src: Path, dst: Path, log: list) -> None:
    """Rename src -> dst if src exists and dst does not. Idempotent."""
    if not src.exists():
        log.append(f"SKIP move (source absent): {src.name}")
        return
    if dst.exists():
        log.append(f"SKIP move (destination exists): {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    log.append(f"MOVED {src.name} -> {dst.relative_to(ROOT)}")


def main() -> None:
    log: list[str] = []
    provenance: dict = {
        "phase": 0,
        "generated_at_iso": datetime.now(tz=timezone.utc).isoformat(),
        "project_root": str(ROOT),
        "actions": log,
    }

    # --- 1. Provenance snapshot BEFORE moving (original root locations) ---
    pre = {}
    raw_zip_src = ROOT / RAW_ZIP_NAME
    if raw_zip_src.exists():
        log.append(f"Hashing raw ZIP (integrity anchor): {RAW_ZIP_NAME} ...")
        pre["raw_zip"] = stat_record(raw_zip_src, with_hash=True)
    # already-moved case
    elif (NB / RAW_ZIP_NAME).exists():
        pre["raw_zip"] = stat_record(NB / RAW_ZIP_NAME, with_hash=True)

    for name in [BLUEPRINT_PDF] + REFERENCE_PDFS:
        p = ROOT / name
        if p.exists():
            pre[name] = stat_record(p, with_hash=True)

    provenance["pre_move_snapshot"] = pre

    # --- 2. Moves into canonical tree (renames, bytes preserved) ---
    # Raw ZIP -> sources/notebooklm-exports/
    safe_move(raw_zip_src, NB / RAW_ZIP_NAME, log)

    # Extracted dir -> sources/notebooklm-exports/raw_extracted/
    raw_extract_src = ROOT / RAW_EXTRACT_NAME
    raw_extract_dst = NB / "raw_extracted"
    if raw_extract_src.exists():
        if raw_extract_dst.exists() and not any(raw_extract_dst.iterdir()):
            raw_extract_dst.rmdir()  # remove empty scaffold placeholder
        if not raw_extract_dst.exists():
            shutil.move(str(raw_extract_src), str(raw_extract_dst))
            log.append(f"MOVED {RAW_EXTRACT_NAME}/ -> sources/notebooklm-exports/raw_extracted/")
        else:
            log.append("SKIP extracted-dir move (raw_extracted already populated)")
    else:
        log.append("SKIP extracted-dir move (already organized)")

    # Blueprint PDF -> sources/abpath/
    safe_move(ROOT / BLUEPRINT_PDF, ABPATH / BLUEPRINT_PDF, log)

    # Reference texts -> sources/reference-texts/
    for name in REFERENCE_PDFS:
        safe_move(ROOT / name, REFTEXTS / name, log)

    # --- 3. Post-move verification of raw ZIP integrity ---
    post_zip = NB / RAW_ZIP_NAME
    if post_zip.exists() and "raw_zip" in pre:
        post_hash = sha256_of(post_zip)
        provenance["raw_zip_integrity"] = {
            "pre_sha256": pre["raw_zip"].get("sha256"),
            "post_sha256": post_hash,
            "unchanged": post_hash == pre["raw_zip"].get("sha256"),
            "final_location": str(post_zip.relative_to(ROOT)),
        }

    # --- 4. Enumerate canonical tree contents ---
    def list_dir(d: Path) -> list:
        if not d.exists():
            return []
        return sorted(
            [
                {
                    "name": p.name,
                    "size_bytes": p.stat().st_size,
                    "ext": p.suffix.lower(),
                }
                for p in d.iterdir()
                if p.is_file()
            ],
            key=lambda x: x["name"],
        )

    provenance["canonical_tree"] = {
        "sources/notebooklm-exports/raw_extracted": list_dir(raw_extract_dst),
        "sources/abpath": list_dir(ABPATH),
        "sources/reference-texts": list_dir(REFTEXTS),
        "sources/notebooklm-exports": list_dir(NB),
    }

    out = ROOT / "logs" / "phase0_provenance.json"
    out.write_text(json.dumps(provenance, indent=2))
    print(f"Wrote {out.relative_to(ROOT)}")
    print("\n".join(log))


if __name__ == "__main__":
    main()
