# Source Normalization Report (Phase 1)

_Generated: 2026-07-11T22:34:34.964378+00:00_

## Summary
| Metric | Value |
|--------|-------|
| Approved `.docx` documents | 61 |
| Unique documents | 47 |
| Exact duplicates | 14 |
| Near-duplicate pairs (Jaccard ≥ 0.80) | 0 |
| Excluded artifacts | 1 |
| Total unique words | 43,376 |

## Method
- Each `.docx` parsed with `python-docx`; headings, paragraphs, bullet lists, and tables
  preserved as Markdown (`content/normalized/normalized_sources/*.md`).
- Original `.docx` bytes and normalized text both SHA-256 hashed.
- **Exact duplicates**: identical normalized-text hash. NotebookLM emitted the same study
  note under multiple audience-named files; 14 such duplicates were detected and
  are flagged (not deleted — provenance preserved) so downstream generation reads each unique
  document once.
- **Near-duplicates**: pairwise Jaccard similarity over 3-gram shingles; none exceeded the
  0.80 threshold beyond the exact matches (remaining documents are genuinely distinct topics).

## Exact-duplicate groups (flagged, retained)
- `SRC-014` duplicates `SRC-013` — Blood Safety Protocols and Infectious Disease Look-back Standards.docx
- `SRC-016` duplicates `SRC-015` — Blood Safety and Infectious Transfusion Hazards.docx
- `SRC-018` duplicates `SRC-017` — Clinical Essentials of Obstetric and Pediatric Transfusion Medicine.docx
- `SRC-021` duplicates `SRC-019` — Clinical Immunohematology and Hemostasis Management.docx
- `SRC-029` duplicates `SRC-007` — Enzymatic Pathways of Carbohydrate Blood Group Synthesis.docx
- `SRC-030` duplicates `SRC-019` — Essentials of Immunohematology and Clinical Transfusion Practice.docx
- `SRC-036` duplicates `SRC-034` — Fundamentals of Cell and Tissue Therapy Regulation and Management.docx
- `SRC-039` duplicates `SRC-022` — Hematopoietic Progenitor Cell Transplantation Principles and Practice.docx
- `SRC-042` duplicates `SRC-015` — Infectious Hazards of Blood Transfusion and Safety Protocols.docx
- `SRC-046` duplicates `SRC-045` — Noninfectious Complications and Hazards of Blood Transfusion.docx
- `SRC-048` duplicates `SRC-024` — Principles and Pathophysiology of Erythrocyte Transfusion Medicine.docx
- `SRC-049` duplicates `SRC-033` — Principles of Blood Bank Administration and Laboratory Management.docx
- `SRC-055` duplicates `SRC-047` — The Clinician’s Essential Guide to Apheresis Principles and Practice.docx
- `SRC-057` duplicates `SRC-020` — The Rh Blood Group System_ Variants and Clinical Management.docx

## Largest unique documents (grounding backbone)

| id | words | top blueprint signal | document |
|----|------:|----------------------|----------|
| SRC-003 | 2007 | 3. RBCs and RBC Components (6) | Advanced Immunohematology and Blood Banking Operations Guide.docx |
| SRC-053 | 1797 | 17. Administration and Laboratory Management (8) | Study Guide_ Domain 3 – Regulatory, Quality, and Operations.docx |
| SRC-032 | 1766 | 3. RBCs and RBC Components (5) | Essentials of Transfusion Medicine and Blood Management.docx |
| SRC-027 | 1619 | 17. Administration and Laboratory Management (8) | Domain 2_ Clinical Practice & Patient Management Study Guide.docx |
| SRC-043 | 1447 | 3. RBCs and RBC Components (8) | Master Board-Review Guide_ Transfusion Medicine.docx |
| SRC-028 | 1402 | 17. Administration and Laboratory Management (8) | Domain 4_ Advanced Technologies & Specialized Testing Study Guide.docx |
| SRC-052 | 1351 | 17. Administration and Laboratory Management (5) | Study Guide_ Domain 1 – Technical & Serological Logic.docx |
| SRC-044 | 1295 | 3. RBCs and RBC Components (11) | Master Curriculum Map_ Blood Banking and Transfusion Medicine (Board Review Edition).docx |
| SRC-040 | 1224 | 16. HPC Transplantation (10) | Immune Hemolysis and Hematopoietic Progenitor Cell Management.docx |
| SRC-051 | 1129 | 7. Plasma Components and Derivatives (6) | Specialized Transfusion Medicine and Clinical Quality Systems.docx |
| SRC-058 | 1054 | 6. Hazards of Transfusion (6) | Transfusion Complications and Clinical Diagnostic Logic.docx |
| SRC-059 | 1021 | 5. Apheresis (7) | Transfusion Medicine Board Review_ Final High-Yield Nodes.docx |
| SRC-037 | 985 | 3. RBCs and RBC Components (4) | Gap Analysis_ BB_TM Board Content Coverage (AABB Technical Manual, 20th Ed.).docx |
| SRC-010 | 979 | 8. Infectious Hazards of Transfusion (8) | Blood Banking and Transfusion Medicine Board Curriculum.docx |
| SRC-060 | 943 | 6. Hazards of Transfusion (3) | Transfusion Medicine_ Metabolic Complications and Information Systems.docx |

## Exclusions
The `.pptx` artifact is not part of the BB/TM corpus and is excluded from all generation.
All reference textbooks remain available as **citeable source pointers** but are not
re-extracted in full; the NotebookLM corpus already distills them with citation markers.
