#!/usr/bin/env python3
"""
Index the approved reference textbooks into CLEAN, substantial, citable windows.

pdftotext output is noisy (running headers, filenames, timestamps, bare page numbers).
This strips that noise, tracks the printed page number, and merges cleaned prose into
~900-word windows so each retrievable chunk carries real content (not header fragments).
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path("/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank")
TEXTS = [
    ("TXT-AABB", "AABB Technical Manual, 20th ed.", ROOT / "scratch_aabb.txt"),
    ("TXT-HARM", "Harmening, Modern Blood Banking & Transfusion Practices", ROOT / "scratch_harmening.txt"),
    ("TXT-STD", "AABB Standards for Blood Banks & Transfusion Services, 35th ed.", ROOT / "scratch_std.txt" if False else ROOT / "scratch_standards.txt"),
]

# noise line patterns (PDF artifacts / running headers / footers)
NOISE = [
    re.compile(r"^\s*\d{1,4}\s*$"),                       # bare page number
    re.compile(r"\d{3,}_Ch\d+", re.I),                    # typesetter filenames (6888_Ch06...)
    re.compile(r"\d{1,2}/\d{1,2}/\d{2,4}"),               # dates/timestamps
    re.compile(r"\bAM Page\b|\bPM Page\b", re.I),
    re.compile(r"^\s*Chapter\s+\d+\s*$", re.I),
    re.compile(r"^\s*(Section|Part|Unit)\s+[IVXLC0-9]+\s*$", re.I),
    re.compile(r"^\s*Copyright|All rights reserved|AABB\s*$", re.I),
    re.compile(r"^\s*(Downloaded|Licensed|Printed) ", re.I),
]
PAGE_MARK = re.compile(r"\bPage\s+(\d{1,4})\b", re.I)
WINDOW_WORDS = 900


def clean_and_window(raw: str):
    printed_page = None
    buf, buf_words, page_at_start = [], 0, None
    windows = []

    def flush():
        nonlocal buf, buf_words, page_at_start
        text = re.sub(r"\s+", " ", " ".join(buf)).strip()
        if len(text) >= 400:  # substantial prose only
            windows.append((page_at_start, text[:5000]))
        buf, buf_words, page_at_start = [], 0, None

    for line in raw.split("\n"):
        m = PAGE_MARK.search(line)
        if m:
            printed_page = m.group(1)
        if any(p.search(line) for p in NOISE):
            continue
        s = line.strip()
        if not s:
            continue
        if page_at_start is None:
            page_at_start = printed_page
        buf.append(s)
        buf_words += len(s.split())
        if buf_words >= WINDOW_WORDS:
            flush()
    flush()
    return windows


chunks, manifest = [], []
for sid, name, path in TEXTS:
    if not path.exists():
        print(f"  ! missing {path.name}"); continue
    raw = path.read_text(errors="ignore")
    wins = clean_and_window(raw)
    for i, (pg, text) in enumerate(wins, start=1):
        chunks.append({"id": f"{sid}-w{i}", "source_id": sid, "source_name": name,
                       "page": pg or "?", "text": text})
    manifest.append({"source_id": sid, "name": name, "windows": len(wins)})
    print(f"  {sid}: {len(wins)} clean windows (~{WINDOW_WORDS}w each)")

(ROOT / "scratch_textbook_chunks.json").write_text(json.dumps(chunks))
(ROOT / "content" / "reference_source_manifest.json").write_text(json.dumps({
    "schema": "reference-source-manifest/v1",
    "note": "Authoritative reference texts (user-provided) used to ground questions for "
            "blueprint topics the NotebookLM summaries do not cover. Raw texts gitignored; "
            "only transformative, cited questions are published.",
    "sources": manifest}, indent=2))
print(f"\nTotal clean windows: {len(chunks)}")
