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
- A source file is > 200 lines and handles multiple concerns.
- An import in `src/` violates the layer hierarchy in `Context/ARCHITECTURE.md`.
- The same logic is duplicated in two or more modules.
- A function takes > 5 parameters (likely doing too much).
- `pytest` runtime > 60 s on a developer machine (likely missing mocks).
- ChromaDB or SQLite connections are opened in multiple places (centralise in `src/data/`).

---

## Improvement Workflow

### Step 1 — Audit
Run the full test suite and record the baseline:
```bash
pytest tests/ -v --tb=short > /tmp/baseline.txt
```
Map the current import graph mentally or with `pydeps src/`.

### Step 2 — Identify the Worst Offender
Pick **one** improvement at a time. Use this priority order:
1. Fix import cycles (breaks builds).
2. Extract duplicated logic into a shared utility.
3. Split oversized files.
4. Centralise config access.
5. Improve naming and docstrings.

### Step 3 — Plan the Change
Before editing any file, write a 3-sentence plan:
- What is being moved/extracted/renamed?
- Which files will change?
- How will correctness be verified?

### Step 4 — Implement
- Make the smallest change that achieves the goal.
- Update all import paths after moving code.
- Add/update docstrings on extracted functions.

### Step 5 — Verify
```bash
pytest tests/ -v --tb=short
```
Output must be identical to the baseline (same pass/fail counts).

### Step 6 — Document
Update `Context/ARCHITECTURE.md` if the layer structure changed.
Add a DDR entry (see `codebase-design` skill for the template).

---

## Kent-AI Specific Improvement Targets

| Target | Improvement |
|---|---|
| `src/pipeline/generator.py` | Ensure LLaMA prompt templates are in `config/`, not hardcoded |
| `src/search/retriever.py` | ChromaDB client should be a singleton, not re-instantiated per query |
| `src/data/kent_db.py` | All SQLite connections must use context managers (`with conn:`) |
| `src/models/ner_model.py` | Model loading should be lazy (load once, reuse) |
| `tests/` | Any test touching real DB must be moved to `tests/integration/` |

---

## Forbidden Actions During Refactoring
- Do NOT change function signatures without updating all call sites.
- Do NOT rename public functions without a deprecation shim.
- Do NOT merge unrelated changes into a refactor commit.
- Do NOT update `Context/PROGRESS.md` milestone status during a refactor PR.
