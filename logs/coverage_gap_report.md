# Coverage Gap Report — ABPath BB/TM Blueprint vs. Approved Sources

_Generated: 2026-07-11T22:45:30.206283+00:00_

## Method & honest caveat
Coverage is scored by **lexical support** (IDF-weighted distinctive-term matching + entity-phrase presence, with medical synonym expansion). It measures whether approved source text **discusses** a blueprint topic — **not** whether any statement is correct, and not the pedagogical depth of that discussion.

- A rarely-mentioned Fellow-level entity that appears once in a blood-group-system table may register as `covered` lexically while being too thin to teach from. Depth is enforced **downstream**: question/case generation is additionally gated by per-item source grounding and an adversarial source-support audit (Phase 7).
- Truly unsupported topics correctly score `missing` and are excluded from generation.

## Overall (leaf topics)

| Status | Count | % |
|--------|------:|--:|
| covered | 531 | 65% |
| strong-partial | 59 | 7% |
| weak-partial | 84 | 10% |
| thin | 79 | 10% |
| uncertain | 0 | 0% |
| missing | 60 | 7% |
| **Total leaves** | **813** | |

**Generation-eligible** (covered + strong-partial): **590 / 813 (73%)**.

## Per-domain coverage

`Coverage score` = mean status weight over leaf topics (covered=1.0 … missing=0.0). `Core score` weights only Core (`C`) leaves — the foundational must-knows.

| Domain | Leaves | Coverage | Core leaves | Core score |
|--------|-------:|:--------:|------------:|:----------:|
| S1 Clinical Practice | 97 | 0.93 | 34 | 0.94 |
| S2 Cell and Tissue Therapy | 57 | 0.73 | 0 | — |
| S3 RBCs and RBC Components | 91 | 0.82 | 40 | 0.79 |
| S4 Anemia and Red Blood Cell Transfusion | 13 | 0.69 | 13 | 0.69 |
| S5 Apheresis | 66 | 0.73 | 5 | 0.40 |
| S6 Hazards of Transfusion: Specific Adverse Eve | 72 | 0.86 | 36 | 0.96 |
| S7 Plasma Components and Derivatives | 39 | 0.73 | 18 | 0.78 |
| S8 Infectious Hazards of Transfusion | 119 | 0.68 | 31 | 0.76 |
| S9 Blood Donors and Blood Collection | 31 | 0.88 | 1 | 0.25 |
| S10 Surgery Patients | 64 | 0.73 | 12 | 0.98 |
| S11 Biovigilance and Transfusion-Related Immunom | 8 | 0.72 | 0 | — |
| S12 Platelets | 15 | 0.57 | 9 | 0.50 |
| S13 Neutrophils | 2 | 0.62 | 0 | — |
| S14 Intravascular Cell Kinetics | 1 | 1.00 | 0 | — |
| S15 Obstetric and Pediatric Patients | 20 | 0.66 | 10 | 0.68 |
| S16 Hematopoietic Progenitor Cell (HPC) Transpla | 68 | 0.79 | 0 | — |
| S17 Blood Bank/Transfusion Medicine-Specific Adm | 50 | 0.89 | 3 | 0.92 |

## Priority gaps — **Core (`C`)** topics that are weak/thin/missing

These are foundational must-knows the corpus under-supports. Prioritise for the next NotebookLM source drop.

| Node | Topic | Status | Domain |
|------|-------|--------|--------|
| `S1.a.i` | Classification, Epidemiology, and Causes | weak-partial | S1 |
| `S1.d.i` | Classification, Epidemiology, and Causes | weak-partial | S1 |
| `S1.e.iv.1` | Lupus Anticoagulants | weak-partial | S1 |
| `S12.a.i` | Megakaryocyte Development, Maturation, and Differe | thin | S12 |
| `S12.a.ii` | Thrombopoietic/Megakaryocyte/Hematopoietic Growth  | weak-partial | S12 |
| `S12.a.iii` | Genetic and Cellular Regulation of Thrombopoiesis | weak-partial | S12 |
| `S12.a.iv` | Platelet Production, Shedding, and Release | thin | S12 |
| `S12.b.i` | Normal Platelet Plug and Clot Formation | thin | S12 |
| `S12.c.i` | Collection and Storage of Platelet Preparations/Co | weak-partial | S12 |
| `S12.c.ii` | Clinical Platelet Transfusions (Indications, Dose, | thin | S12 |
| `S15.c.i` | Developmental Physiology of Plasma Proteins | weak-partial | S15 |
| `S15.c.ii.1` | Pathophysiology and Treatment | weak-partial | S15 |
| `S15.c.ii.2` | DDAVP | missing | S15 |
| `S15.d.iii` | Thalassemias (Pathophysiology and Treatment) | thin | S15 |
| `S3.a.i.2` | Interaction with- and Effects on Erythroid Progeni | weak-partial | S3 |
| `S3.a.ii` | Nutritional Requirements for Erythropoiesis | weak-partial | S3 |
| `S3.a.iii` | Influence of Pathologic States on Erythropoiesis | thin | S3 |
| `S3.b.iii.1` | Red Cell Transfusion and the Microcirculation | thin | S3 |
| `S3.b.iii.2` | Effect of Red Cell Storage on Microcirculation (N  | thin | S3 |
| `S3.c.i.2` | Alternative Substrates | thin | S3 |
| `S3.c.ii.3` | Anticoagulant-Nutrient Solutions | weak-partial | S3 |
| `S3.d.i.2.a` | Physical Properties & Characteristics | thin | S3 |
| `S3.d.ii.1` | Donor Testing | missing | S3 |
| `S3.d.ii.4.a` | Prior Records Check | weak-partial | S3 |
| `S3.e.i.2` | Antigenic Variants | thin | S3 |
| `S4.a.i` | Oxygen Transport to Blood Loss and Anemia | weak-partial | S4 |
| `S4.a.ii` | Adaptive Mechanisms in Anemia | thin | S4 |
| `S4.a.iii` | Microcirculatory Effects of Anemia and Red Cell Tr | thin | S4 |
| `S4.a.iv` | Pathophysiologic Processes and Anemia – Interactio | weak-partial | S4 |
| `S4.c` | Transfusion Guidelines | missing | S4 |
| `S4.d.v` | Dose and Administration | weak-partial | S4 |
| `S5.a.i` | General Information and Principles | thin | S5 |
| `S5.b.iii.1` | Thrombotic Thrombocytopenic Purpera | weak-partial | S5 |
| `S5.c.i.1` | Polycythemia Vera | weak-partial | S5 |
| `S5.c.i.2` | Secondary Erythrocytosis | thin | S5 |
| `S5.c.i.3` | Hereditary Hemochromatosis | weak-partial | S5 |
| `S6.e.iv.1` | Clinical, Physiologic, Radiologic, & Laboratory Fe | weak-partial | S6 |
| `S6.e.iv.2` | Consensus Definition | thin | S6 |
| `S7.a.i` | General Features and Factors Influencing Plasma Co | weak-partial | S7 |
| `S7.b.ii` | Adverse Effects | weak-partial | S7 |
| `S7.c.i.1` | Manufacture and Features | missing | S7 |
| `S7.c.i.5` | Pathogen-Inactivated Plasma | thin | S7 |
| `S7.c.ii.1` | Manufacture and Features | missing | S7 |
| `S8.a.ii.1` | Epidemiology | weak-partial | S8 |
| `S8.a.ii.4` | Serologic and Molecular Markers of Infection | weak-partial | S8 |
| `S8.a.ii.5` | Donor Testing and Counseling | thin | S8 |
| `S8.a.iii.1` | Epidemiology | weak-partial | S8 |
| `S8.b.ii.1` | General Information and Epidemiology | weak-partial | S8 |
| `S8.b.ii.4` | Donor Testing and Counseling | thin | S8 |
| `S8.c.1` | General Information and Epidemiology | thin | S8 |
| `S8.c.2` | Incidence and Prevalence Among Blood Donors | thin | S8 |
| `S8.d.i` | Other Herpesviruses | missing | S8 |
| `S8.i.ii.1` | Psoralen Ultraviolet Light Treatment | weak-partial | S8 |
| `S8.i.iii.1` | Psoralen Ultraviolet Light Treatment | weak-partial | S8 |
| `S9.a.i.1` | United States | thin | S9 |

## Advanced-Resident (`AR`) topics that are thin/missing

| Node | Topic | Status | Domain |
|------|-------|--------|--------|
| `S10.a.ii.1` | Acute Normovolemic Hemodilution | missing | S10 |
| `S10.b.i.2.b` | Liver Biopsy | thin | S10 |
| `S10.b.i.2.c` | Thoracentesis and Paracentesis | missing | S10 |
| `S10.b.i.2.d` | Gastrointestinal Endoscopy and Biopsy | missing | S10 |
| `S10.b.i.2.e` | Procedures on Upper Airway, Bronchoscopy, and Tran | missing | S10 |
| `S10.b.i.2.f` | Renal Biopsy | thin | S10 |
| `S10.b.i.2.g` | Epidural Anesthesia, Lumbar Puncture, and Neurosur | missing | S10 |
| `S10.b.i.2.h` | Angiography | missing | S10 |
| `S10.c.i.3.b.d` | Autotransfusion | missing | S10 |
| `S10.d.ii.a` | Across Immunologic Barriers | thin | S10 |
| `S10.d.iv.e` | Pancreas | missing | S10 |
| `S12.c.iii` | Alternatives to Platelet Transfusions (Thrombopoie | thin | S12 |
| `S12.d.iii` | Platelet Autoimmunity | thin | S12 |
| `S13.a.ii` | Alternatives to Neutrophil Transfusions (Myelopoie | thin | S13 |
| `S15.b.i` | Maternal Hematologic Disorders During Pregnancy | thin | S15 |
| `S17.b.iv` | Safety Initiatives | thin | S17 |
| `S17.b.viii` | Common Violations | thin | S17 |
| `S17.c.iv.1` | Membership | missing | S17 |
| `S17.c.iv.2` | Functions | missing | S17 |
| `S2.c.i` | Immunotherapy Targets for Cancer | thin | S2 |
| `S3.e.i.3` | Secretion | missing | S3 |
| `S5.a.iv.1.d` | Schedule of Procedures (Timing, Number, & Location | thin | S5 |
| `S5.b.i.1` | Mathematic Principles | thin | S5 |
| `S6.b.v.3` | Electrolyte and Acid/Base Disorders | thin | S6 |
| `S6.b.v.5` | Microaggregate Reactions | missing | S6 |
| `S6.c.v.2` | Malignancies | missing | S6 |
| `S6.c.vi` | Immunocompetent Patients-Risk Factors | thin | S6 |
| `S6.d.ii` | Iron Burden of Transfusions | thin | S6 |
| `S6.d.iv` | Measurement of Iron Burden | missing | S6 |
| `S7.b.iii` | Plasma Procurement | missing | S7 |
| `S7.c.iii.1` | Manufacture and Features | missing | S7 |
| `S7.c.iv.1` | Manufacture and Features | thin | S7 |
| `S7.c.v.1` | Manufacture and Features | thin | S7 |
| `S8.c.7` | Donor Testing and Counseling | missing | S8 |
| `S8.d.ii.3` | Donor Testing and Counseling | thin | S8 |
| `S8.e.i.3` | Donor Testing and Counseling | missing | S8 |
| `S8.e.ii.1` | General Information and Epidemiology | thin | S8 |
| `S8.e.ii.3` | Donor Testing and Counseling | missing | S8 |
| `S8.e.iii.3` | Donor Testing and Counseling | missing | S8 |
| `S8.f.i` | Red Blood Cells – Overview and Epidemiology | missing | S8 |
| `S8.i.ii.2` | Solvent/Detergent Treatment | missing | S8 |
| `S8.i.ii.3` | Methylene Blue Light Treatment | thin | S8 |
| `S8.i.iii.3` | Thionine Light Treatment | thin | S8 |
| `S9.a.ii` | Blood Donor Recruitment | missing | S9 |
| `S9.a.iii.5` | Source Plasma | missing | S9 |

## Domains most in need of reinforcement

- **S12 Platelets** — coverage 0.57 (0 missing, 6 thin leaves).
- **S13 Neutrophils** — coverage 0.62 (0 missing, 1 thin leaves).
- **S15 Obstetric and Pediatric Patients** — coverage 0.66 (1 missing, 4 thin leaves).
- **S8 Infectious Hazards of Transfusion** — coverage 0.68 (16 missing, 17 thin leaves).
- **S4 Anemia and Red Blood Cell Transfusion** — coverage 0.69 (1 missing, 2 thin leaves).

---
_Fully machine-readable data: `content/coverage/coverage_matrix.json` (813 leaf assessments) and `content/coverage/source_to_blueprint_map.json`._

