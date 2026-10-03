---
name: codebase-design
description: >
  Architectural design and codebase organisation skill for kent-ai.
  Use when planning a new feature, restructuring an existing module,
  or deciding where new code should live. Enforces the layered
  architecture defined in Context/ARCHITECTURE.md and the module
  conventions in Context/CONVENTIONS.md.
---

# Codebase Design Skill — Kent-AI

## Reference Documents
Always read these before making design decisions:
- `Context/ARCHITECTURE.md` — canonical module map, data flow, API summary
- `Context/CONVENTIONS.md` — naming, import, typing, and testing rules
- `Context/GOTCHAS.md` — known pitfalls to design around

---

## Current Repository Structure (from Context/ARCHITECTURE.md)

```
kent-ai/
├── configs/                       # YAML config — all hyperparams live here
│   ├── model.yaml                 # Bio_ClinicalBERT hyperparams + BIO label schema
│   ├── generation.yaml            # LLaMA 3 case generation settings + split ratios
│   ├── chromadb.yaml              # Vector store embedding model + distance metric
│   └── chatbot.yaml               # State machine states + dialogue persona rules
│
├── data/
│   ├── raw/
│   │   ├── repertory.sqlite       # Primary data source (112 MB, read-only)
│   │   └── kent_public_edition/   # Upstream digitized repertory bundle
│   ├── processed/                 # Generated artifacts (JSONL case files, checkpoints)
│   └── embeddings/kent_rubrics/   # ChromaDB persistent HNSW index
│
├── src/
│   ├── config.py                  # YAML loader + project root detection
│   ├── data/
│   │   ├── kent_db.py             # ★ SQLite DAL — fully implemented
│   │   ├── case_generator.py      # ★ LLaMA synthetic case pipeline
│   │   ├── bio_tagger.py          # ★ BIO token tagger with offset repair
│   │   └── splitter.py            # ★ 80/10/10 stratified deficit splitter
│   ├── models/
│   │   ├── symptom_ner.py         # Stub: ClinicalBERT NER wrapper (Phase 3)
│   │   ├── trainer.py             # Stub: Training loop (Phase 3)
│   │   └── resolver.py            # ★ LLaMA post-processor & negation resolver
│   ├── search/
│   │   ├── embedder.py            # ★ Sentence-transformers embedder
│   │   ├── vector_store.py        # ★ ChromaDB HNSW cosine wrapper
│   │   └── ranker.py              # ★ Remedy intersection & grade ranker
│   ├── chatbot/
│   │   ├── state_machine.py       # ★ FSM with IntakeState enum
│   │   ├── dialogue_manager.py    # ★ Multi-turn dialogue manager
│   │   └── prompts.py             # Prompt templates
│   ├── pipeline/
│   │   ├── orchestrator.py        # ★ End-to-end transcript → report orchestrator
│   │   └── report_generator.py    # ★ JSON + Markdown report generator
│   └── dashboard/
│       ├── app.py                 # ★ Streamlit 4-workspace clinical portal
│       ├── styles.py              # CSS injection
│       ├── styles.css             # Google Stitch CSS theme
│       ├── dimensions.py          # DIMENSION_MAP single source of truth
│       └── components/
│           ├── chat_viewer.py     # Multi-turn chat HUD
│           ├── rubric_tree.py     # Rubric cards with remedy inspector
│           └── icons.py           # Icon helpers
│
├── scripts/                       # CLI entry points (import from src/)
├── tests/                         # pytest suite
├── notebooks/                     # EDA and demo notebooks
└── docs/                          # Architecture diagrams, API reference
```

**Legend**: ★ = Fully implemented and tested.

---

## Design Principles

### 1. Strict Layer Separation

| Layer | Owns | Must NOT Import From |
|---|---|---|
| `src/data/` | SQLite, file I/O, data transforms | `src/models/`, HTTP |
| `src/models/` | Model loading, inference, training | Database queries |
| `src/search/` | Embeddings, ChromaDB, ranking | Training loops |
| `src/chatbot/` | State machine, dialogue, prompts | Direct DB access |
| `src/pipeline/` | Orchestration of above modules | Implementation details of any one module |
| `src/dashboard/` | Streamlit UI rendering and UI orchestration | — see Dashboard Boundary below |
| `scripts/` | CLI entry points only | Testable logic (imports from `src/`) |

### Dashboard Boundary

`src/dashboard/` owns Streamlit presentation and UI orchestration.

The current implementation in `src/dashboard/app.py` directly coordinates
several backend services: `KentDB`, `DialogueManager`, `PipelineOrchestrator`,
`RubricVectorStore`, `RubricEmbedder`, and `RemedyRanker`. Treat this as the
current architecture, not as an automatic violation.

**Do NOT refactor these dependencies** solely to enforce a stricter
`dashboard → pipeline` boundary.

Only introduce a new boundary or move responsibilities when:
1. explicitly requested by the project owner,
2. required to fix a demonstrated defect, or
3. formally adopted through an Architecture Decision Record in `Context/ARCHITECTURE.md`.

### 2. Single Responsibility
Each module file = one primary class or one cohesive set of functions.
If a file exceeds ~500 lines, extract a helper module.

### 3. Configuration Over Hardcoding
All hyperparameters, model names, file paths, and magic numbers live in `configs/*.yaml`.
**Never hardcode** a model name, learning rate, batch size, or threshold in source code.
Load via `src.config.load_config("model")` or the typed shortcuts.

### 4. `__init__.py` Files Are Re-Exports Only
No business logic in `__init__.py`. They exist only to re-export public API names via `__all__`.

### 5. Imports: Absolute Only
Always use `from src.<module> import ...`. Never use relative imports (`from .kent_db import ...`).
Always include `from __future__ import annotations` at the top of every module.

---

## Configuration Reference

| File | Top-level Keys |
|---|---|
| `configs/model.yaml` | `model`, `training`, `labels` (15 BIO tags) |
| `configs/generation.yaml` | `generation`, `target_data`, `splits` |
| `configs/chromadb.yaml` | `vector_store`, `embedding_model`, `search` |
| `configs/chatbot.yaml` | `chatbot`, `state_machine`, `dialogue` |

---

## Design Decision Record (DDR) Template

When making a non-trivial design choice, document it:

```markdown
## DDR-<N>: <Title>

**Date**: YYYY-MM-DD
**Context**: What problem are we solving?
**Decision**: What did we decide?
**Consequences**: What are the trade-offs?
**Status**: Accepted | Superseded by DDR-<M>
```

Append DDRs to `Context/ARCHITECTURE.md`.

---

## Checklist Before Implementing

- [ ] Identified the correct `src/` layer for the new code.
- [ ] No circular imports introduced.
- [ ] New config values added to the appropriate `configs/*.yaml` — not hardcoded.
- [ ] `Context/ARCHITECTURE.md` updated if layer relationships change.
- [ ] `from __future__ import annotations` present at top of new module.
