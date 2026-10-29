# Kent-AI — Project Context

> Last updated: 2026-10-29 by Antigravity
> Phase: Complete through Phase 5 / Phase B & C (Two-Stage Pipeline & Evaluation Suite Operational; UI Demo & Thesis Defense Next)

---

## What This Project Is

**Kent-AI** is an AI-powered clinical assistant for homeopathic repertorization, built on the digitized version of Dr. James Tyler Kent's *Repertory of the Homoeopathic Materia Medica* (Expanded Edition).

It takes a patient's natural-language symptom description, extracts structured clinical dimensions using NLP, maps them to hierarchical repertory rubrics, and ranks candidate homeopathic remedies with full provenance.

### Team

| Name | Role | Institution |
|---|---|---|
| Krishna Sikheriya | Lead Developer | IIIT Allahabad |
| Lokesh Bawariya | Developer | IIIT Allahabad |
| Naitik Jain | Developer | IIIT Allahabad |
| Dr. Nikhilanand Arya | Project Supervisor | IIIT Allahabad |

### Core Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| NER Model | Bio_ClinicalBERT (`emilyalsentzer/Bio_ClinicalBERT`) | Token-level symptom extraction |
| Post-Processor | LLaMA 3 8B via Ollama | Negation, coreference, 7-dim JSON |
| Vector Search | ChromaDB + `all-MiniLM-L6-v2` | Semantic rubric matching |
| Text Search | SQLite FTS5 | Prefix token rubric search |
| Dashboard | Streamlit | Doctor-facing clinical UI |
| Runtime | Python 3.12 (`.venv`) | Virtual environment in project root |

### Kent's 7 Symptom Dimensions

| # | Dimension | NER Tag | Description |
|---|---|---|---|
| 1 | Location | `LOC` | Anatomical site (right temple, epigastrium) |
| 2 | Sensation | `SEN` | Pain quality (burning, stitching, throbbing) |
| 3 | Modality: Worse | `MOD_AGG` | Aggravation triggers (cold, motion, evening) |
| 4 | Modality: Better | `MOD_AMEL` | Amelioration factors (warmth, pressure, rest) |
| 5 | Concomitants | `CONC` | Co-occurring unrelated symptoms |
| 6 | Temporal | `TEMP` | Time patterns (3 AM, periodicity) |
| 7 | Mental/Emotional | `MENT` | Psychological state (fear, weeping, anger) |

---

## Context File Index

| File | Purpose |
|---|---|
| [`CONTEXT_RULES.md`](CONTEXT_RULES.md) | How to write and update context files (read this first) |
| [`PROJECT.md`](PROJECT.md) | This file — goals, team, tech stack, phase summary |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Repository tree, module responsibilities, data flow |
| [`DATA.md`](DATA.md) | Database schema, table stats, key constants, grade system |
| [`CONVENTIONS.md`](CONVENTIONS.md) | Code style, import patterns, testing patterns |
| [`PROGRESS.md`](PROGRESS.md) | Phase-by-phase status tracker with exit criteria |
| [`GOTCHAS.md`](GOTCHAS.md) | Non-obvious pitfalls, known data quirks, landmines |
| [`research_llm_comparative_study_and_ensemble_2026-10-29.md`](research_llm_comparative_study_and_ensemble_2026-10-29.md) | Multi-model comparative study design, BLURB SOTA review, ensemble formulations per supervisor guidance |

---

## Phased Roadmap Summary

| Phase | Name | Status | Days |
|---|---|---|---|
| 0 | Scaffolding & Data Layer | ✅ Complete | 1–2 |
| 1 | Synthetic Case Generation (LLaMA 3) | ✅ Complete (19,732 cases across 4,933 MIND rubrics generated & partitioned 80/10/10) | 3–7 |
| 2 | ChromaDB Rubric Index (74,513 rubrics) | ✅ Complete (74,513 rubrics indexed in persistent HNSW cosine vector store) | 5–6 |
| 3 | Bio_ClinicalBERT NER Training | ✅ Complete (Bio_ClinicalBERT fine-tuned 8 epochs on RTX 5000 Ada, 411MB weights exported) | 8–10 |
| 4 | LLaMA 3 Post-Processor & Resolver | ✅ Complete (7-dim clinical extraction, negation filtering, coreference resolution) | 11–12 |
| 5 | Pipeline & Remedy Ranking Engine | ✅ Complete (Phase B Two-Stage Pipeline & Phase C Academic Evaluation Suite operational) | 13–15 |
| 6 | Conversational Intake Chatbot | ✅ Complete (10-state FSM, adaptive slot skipping, empathetic dialogue manager) | 16–19 |
| 7 | Streamlit Clinical Dashboard (Stitch Standard) | ✅ Complete (Google Stitch UI tokens, 4 clinical workspaces, Plotly charts, Totality Matrix) | 20–24 |
| 8 | Multi-Model Comparative Benchmark & Ensembling | 🔄 Active (Supervisor directive integrated: PubMedBERT, BioLinkBERT, DeBERTa-v3, BioMistral, LLaMA 3.1, ensemble evaluation) | 25–28 |

Full roadmap & phase tracking details: [`Context/PROGRESS.md`](PROGRESS.md)

---

_End of file._
