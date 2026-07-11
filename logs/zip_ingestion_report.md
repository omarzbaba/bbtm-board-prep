# ZIP Ingestion Report

_Generated: 2026-07-11T22:34:34.964378+00:00_

## Discovery
A single candidate archive was found in the project root:

| File | Size | Selected |
|------|------|----------|
| `drive-download-20260711T222309Z-2-001.zip` | 777.6 MB | ✅ primary source bundle |

No other `.zip`/`.tar`/archive files were present, so selection was unambiguous. A sibling
directory of the same name already existed (a prior extraction); its contents were validated
against the archive listing (62 entries = 61 `.docx` + 1 `.pptx`) and matched.

## Integrity
The raw ZIP was **relocated by rename only** (no re-compression, no byte rewrite) into the
canonical path. SHA-256 was captured before and after:

- pre  : `11324b1848fc7d4bbd647b5b78b7fc1046f73be3fbafcca9011273354b95d3ee`
- post : `11324b1848fc7d4bbd647b5b78b7fc1046f73be3fbafcca9011273354b95d3ee`
- **unchanged: True**

## Extraction & provenance
- Raw archive preserved at: `sources/notebooklm-exports/drive-download-20260711T222309Z-2-001.zip`
- Extracted contents preserved at: `sources/notebooklm-exports/raw_extracted/`
- 61 `.docx` documents normalized to Markdown under `content/normalized/normalized_sources/`
- 1 `.pptx` recorded and excluded (non-BB/TM artifact)

## Actions log
- Hashing raw ZIP (integrity anchor): drive-download-20260711T222309Z-2-001.zip ...
- MOVED drive-download-20260711T222309Z-2-001.zip -> sources/notebooklm-exports/drive-download-20260711T222309Z-2-001.zip
- MOVED drive-download-20260711T222309Z-2-001/ -> sources/notebooklm-exports/raw_extracted/
- MOVED Content-Specification-BBTM_SS_Final_01222026-2.pdf -> sources/abpath/Content-Specification-BBTM_SS_Final_01222026-2.pdf
- MOVED AABB Technical Manual-20th ed-2020.pdf -> sources/reference-texts/AABB Technical Manual-20th ed-2020.pdf
- MOVED Harmening.pdf -> sources/reference-texts/Harmening.pdf
- MOVED Standards for Blood Banks and Transfusion Services, 35th Edition effective April 1, 2026.pdf -> sources/reference-texts/Standards for Blood Banks and Transfusion Services, 35th Edition effective April 1, 2026.pdf
