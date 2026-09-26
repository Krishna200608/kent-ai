# Kent-AI — Project Context

> Last updated: 2026-09-26 by Antigravity (Phase 1 case generation agent)
> Phase: 1 (active)

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

---

## Phased Roadmap Summary

| Phase | Name | Status | Days |
|---|---|---|---|
| 0 | Scaffolding & Data Layer | ✅ Complete | 1–2 |
| 1 | Synthetic Case Generation (LLaMA 3) | 🔄 In Progress (Pipeline Ready) | 3–7 |
| 2 | ChromaDB Rubric Index | ⬜ Planned | 5–6 |
| 3 | ClinicalBERT NER Training | ⬜ Planned | 8–10 |
| 4 | LLaMA 3 Post-Processor | ⬜ Planned | 11–12 |
| 5 | Pipeline & Remedy Ranking | ⬜ Planned | 13–15 |
| 6 | Conversational Chatbot | ⬜ Planned | 16–19 |
| 7 | Streamlit Dashboard | ⬜ Planned | 20–24 |
| 8 | Polish, Docs & Defense | ⬜ Planned | 25–28 |

Full roadmap details: [`docs/project_foundation.md`](../docs/project_foundation.md)

---

_End of file._
