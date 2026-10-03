---
name: improve-codebase-architecture
description: >
  Systematic codebase improvement and refactoring skill for kent-ai.
  Use when technical debt is accumulating, a module is too large,
  import cycles exist, performance is degrading, or the architecture
  has drifted from Context/ARCHITECTURE.md. Always preserves existing
  behaviour — no feature changes during architectural refactors.
---

# Improve Codebase Architecture Skill — Kent-AI

## Prime Directive
**Refactoring must not change observable behaviour.**
Every architectural improvement must be guarded by a passing test suite
before and after the change.

---

## When to Use This Skill

Trigger this skill when you observe any of the following:
- A source file is > 500 lines and handles multiple concerns (CONVENTIONS.md §5).
- An import in `src/` violates the layer hierarchy in `Context/ARCHITECTURE.md`.
- The same logic is duplicated in two or more modules.
- A function takes > 5 parameters (likely doing too much).
- A config value (path, threshold, model name) is hardcoded in source instead of `configs/*.yaml`.
- `chromadb.EphemeralClient()` or `get_connection()` is opened in multiple places instead of being centralised.
- `pytest` suite is significantly slower than the baseline (PROGRESS.md documents ~60 passing tests in ~4s).

---

## Improvement Workflow

### Step 1 — Establish Baseline

Run the full test suite and record the baseline before making any change:
```bash
.venv\Scripts\pytest.exe tests/ -v --tb=short
```
Current baseline: **60 passing tests** (as of Phase 7, PROGRESS.md).

### Step 2 — Identify the Single Worst Offender

Pick **one** improvement at a time. Use this priority order:
1. Fix import cycles (breaks builds — highest priority).
2. Extract config values to `configs/*.yaml`.
3. Extract duplicated logic into a shared utility.
4. Split oversized files (> 500 lines).
5. Improve naming and docstrings.

### Step 3 — Plan the Change

Before editing any file, write a 3-sentence plan:
- What is being moved/extracted/renamed?
- Which files will change?
- How will correctness be verified?

### Step 4 — Implement

- Make the smallest change that achieves the goal.
- Update all import paths after moving code (use `from src.<module> import ...`).
- Add/update Google-style docstrings on extracted functions.
- Ensure `from __future__ import annotations` is present in any new file.

### Step 5 — Verify

```bash
.venv\Scripts\pytest.exe tests/ -v --tb=short
```
Output must be identical to the baseline (same pass/fail counts).

### Step 6 — Document

Update `Context/ARCHITECTURE.md` if the layer structure changed.
Add a DDR entry (see `codebase-design` skill for the template).

---

## Kent-AI Specific Improvement Candidates

| Target | Improvement |
|---|---|
| `src/pipeline/orchestrator.py` | Verify all LLaMA prompt templates come from `src/chatbot/prompts.py`, not inline strings |
| `src/search/vector_store.py` | ChromaDB client should be constructed once and reused, not re-instantiated per query |
| `src/data/kent_db.py` | All connections must use `with get_connection() as conn:` context manager (currently correct — keep it) |
| `src/models/resolver.py` | Model/Ollama endpoint URL must come from `configs/chatbot.yaml`, not hardcoded |
| `src/search/embedder.py` | Embedding model name must come from `configs/chromadb.yaml`, not hardcoded (lazy load is already correct — do not break it) |
| `src/dashboard/app.py` | `src/dashboard/dimensions.py` is already the single source of truth for `DIMENSION_MAP` — ensure nothing bypasses it |

---

## Forbidden Actions During Refactoring
- Do NOT change function signatures without updating all call sites.
- Do NOT rename public functions without a deprecation shim.
- Do NOT merge unrelated changes into a refactor commit.
- Do NOT update `Context/PROGRESS.md` milestone status during a refactor — only do that when a feature phase is complete.
- Do NOT introduce relative imports (`from .module import ...`).
- Do NOT hardcode a config value that should come from `configs/*.yaml`.
