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
Always read before making design decisions:
- `Context/ARCHITECTURE.md` — canonical layer map
- `Context/CONVENTIONS.md` — naming, import, and typing rules
- `Context/GOTCHAS.md` — known pitfalls to design around

---

## Current Architecture

```
kent-ai/
├── src/
│   ├── data/          # DB access layer (SQLite, ChromaDB ingestion)
│   ├── models/        # NER (Bio_ClinicalBERT), embeddings
│   ├── search/        # Retrieval (ChromaDB queries, ranking)
│   ├── pipeline/      # Case generation orchestration (LLaMA 3)
│   ├── chatbot/       # Dialogue interface logic
│   └── dashboard/     # Streamlit UI components
├── tests/             # pytest suite (mirrors src/ structure)
├── data/
│   ├── raw/           # repertory.sqlite (read-only)
│   ├── processed/     # ChromaDB persistent index
│   └── schemas/       # JSON schemas for generated cases
├── config/            # YAML/env config files
├── logs/              # Runtime logs (not committed)
└── Context/           # Living documentation
```

---

## Design Principles

### 1. Strict Layer Separation
| Layer | May Import From | Must NOT Import From |
|---|---|---|
| `dashboard/` | `chatbot/`, `search/` | `models/`, `data/` directly |
| `chatbot/` | `search/`, `pipeline/` | `dashboard/` |
| `pipeline/` | `models/`, `data/` | `chatbot/`, `dashboard/` |
| `search/` | `models/`, `data/` | `pipeline/`, `chatbot/` |
| `models/` | `data/` | anything above |
| `data/` | stdlib, third-party only | any `src/` module |

### 2. Single Responsibility
Each module file = one primary class or one cohesive set of functions.
If a file exceeds ~200 lines, it is a signal to split.

### 3. Configuration Over Hardcoding
All thresholds, paths, model names go in `config/`. Never hardcode:
- ChromaDB persist path
- Model checkpoint name
- Top-k retrieval count

### 4. Schema-First for Generated Data
Before writing generation code, define the JSON schema in `data/schemas/`.
Validate output with `jsonschema.validate()` in the pipeline.

---

## Design Decision Record (DDR) Template

When making a non-trivial design choice, document it briefly:

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
- [ ] No circular imports introduced (verify with `pydeps` or manual trace).
- [ ] New config values added to `config/` — not hardcoded.
- [ ] Data schema updated if output shape changes.
- [ ] `Context/ARCHITECTURE.md` updated if layer relationships change.
