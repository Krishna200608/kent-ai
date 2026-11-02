# Kent-AI — Project Context

> Last updated: 2026-11-02 by Antigravity
> Phase: Complete through Phase 21 (Repertory Scope Lock to MIND, Chat Suggestions Intent Sync, Fresh Case FSM Greeting Fix; 195 Unit & Integration Tests Passing across 22 Test Modules, 0 Errors)

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
| Biomedical Encoders | `BioLinkBERT`, `PubMedBERT`, `Bio_ClinicalBERT`, `DeBERTa-v3` | Fast token-level sequence classification (BIO tagging, ~18 ms) |
| Generative Decoders | `BioMistral 7B` (PMC-adapted), `Qwen 2.5 7B Instruct` (4-bit QLoRA) | Contextual 7-dimension structured extraction & reasoning |
| Multi-Model Ensemble | Weighted Majority Voting & Two-Stage Hybrid Arbitration | High-recall span mining + LLM contextual arbitration |
| Vector Search | ChromaDB + `all-MiniLM-L6-v2` | Semantic rubric matching (74,513 Kent rubrics) |
| Text Search | SQLite FTS5 | Prefix token rubric search |
| Dashboard | Streamlit | Doctor-facing clinical UI with Totality Matrix |
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
| 8 | Multi-Model Comparative Benchmark | ✅ Complete (PubMedBERT, BioLinkBERT, DeBERTa-v3 benchmarked over 1,973 held-out test cases) | 25–28 |
| 9 | Generative Decoders QLoRA PEFT (Qwen 2.5 & BioMistral) | ✅ Complete (4-bit NF4 QLoRA, 100% JSON validity, 99.7% grounding, SOTA extraction F1) | 29–30 |
| 10 | Multi-Model Ensembling & Hybrid Pipeline | ✅ Complete (Weighted voting, IoU span clustering, two-stage encoder-mining + LLM arbitration) | 31–32 |
| 11 | Clinician-Centric Stepper, Case Persistence & Totality Matrix | ✅ Complete (Single typed ClinicalCase, SQLite case store, 4-step stepper, Totality Matrix, ReportLab PDF) | 33–34 |
| 12 | Bedside Streaming Dialogue, Shimmer Reflection & Responsive Viewport | ✅ Complete (NDJSON chunk streaming, immediate reflection skeleton, syntax leak elimination, full-screen collapse) | 35 |
| 13 | Step 1 Clinical Narrative Intake Redesign & Accessibility Polish | ✅ Complete (Segmented mode switching, highlighted preview, safety screening, WCAG AA contrast; 133 tests) | 36 |
| 14 | Guided Conversation Chat Redesign & Case Library Bulk Actions | ✅ Complete (Deterministic openers, per-turn undo, bulk case selection & batch exports, PyMuPDF migration; 151 tests) | 37 |
| 15 | Comprehensive Clinician UI/UX Overhaul & Design System (Phases 1–10) | ✅ Complete (Single source of truth in constants.py, token palette in styles.css, 7-segment totality ring, Case Snapshot rail, dual-view Case Library with pagination, hybrid Rubric Explorer with Materia Medica dialog, split Methodology/Settings, printable reports, demo case mode; 168 tests) | 38 |
| 16 | Button Loading Feedback & Client busy.js Runtime | ✅ Complete (Vanilla client busy.js runtime, st.html twin slot, screen reader aria-busy, Streamlit 1.64 selector hardening) | 39 |
| 17 | Model Section ID Robustness & Suggestion Chip Intent Sync | ✅ Complete (Normalized section_id and scope_chapter handling, dynamic LLaMA quick replies sync, 14 new tests) | 40 |
| 20 | Repertory Scope Lock to MIND Focus & Coming Soon v2.0 Badges | ✅ Complete (Locked repertory scope strictly to Chapter 1: MIND [4,933 rubrics], disabled All 37 Chapters pills with lock icons and v2.0 roadmap tooltips) | 41 |
| 21 | Fresh Case Startup FSM Greeting Fix & Context Sync | ✅ Complete (Dialogue manager startup fix ensuring fresh cases start at IntakeState.GREETING 1/10; 195/195 tests passing) | 41 |

Full roadmap & phase tracking details: [`Context/PROGRESS.md`](PROGRESS.md)

---

_End of file._
