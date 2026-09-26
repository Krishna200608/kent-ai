# Kent-AI — Progress Tracker

> Last updated: 2026-09-26 by Antigravity (Phase 0 scaffolding agent)
> Phase: 0 (complete)

---

## Phase 0 — Scaffolding & Data Layer ✅

**Status**: Complete
**Date**: 2026-09-26
**Agent**: Antigravity (Gemini 3.8 Flash)

### Deliverables

| Task | Status | Key File(s) |
|---|---|---|
| Initialize repo structure | ✅ Done | All directories, `__init__.py` files |
| `pyproject.toml` with deps | ✅ Done | `pyproject.toml` |
| `.gitignore`, `LICENSE`, `Makefile` | ✅ Done | Root files |
| Python 3.12 venv | ✅ Done | `.venv/` (pyyaml, pytest installed) |
| Git initialized + first commit | ✅ Done | `a5570a5` |
| Data hardlink | ✅ Done | `data/raw/repertory.sqlite` → `kent_public_edition/repertory.sqlite` |
| Config system (YAML loader) | ✅ Done | `src/config.py`, `configs/*.yaml` |
| Kent DB reader | ✅ Done | `src/data/kent_db.py` (448 lines, fully implemented) |
| Unit tests | ✅ Done | `tests/test_kent_db.py` (13 passing tests) |
| Stub modules for all phases | ✅ Done | All `src/` modules with typed interfaces |
| EDA notebook | ✅ Done | `notebooks/01_eda_repertory.ipynb` |
| Architecture docs | ✅ Done | `docs/architecture.md`, `docs/api_reference.md` |
| Context files | ✅ Done | `Context/` directory (6 files + rules) |

### Exit Criteria Verification

```bash
python -c "from src.data.kent_db import get_mind_rubrics; print(len(get_mind_rubrics()))"
# Output: 4933 ✅

pytest tests/ -v
# Output: 17 passed in 0.19s ✅
```

---

## Phase 1 — Synthetic Case Generation ⬜

**Status**: Not started
**Target**: Generate ~22,200 MIND clinical cases using LLaMA 3 8B

### Tasks

| Task | Status | File(s) |
|---|---|---|
| Case generator core | ⬜ Planned | `src/data/case_generator.py` |
| Prompt templates for generation | ⬜ Planned | `src/chatbot/prompts.py` (extend) |
| BIO auto-tagger | ⬜ Planned | `src/data/bio_tagger.py` |
| CLI generation script | ⬜ Planned | `scripts/generate_cases.py` |
| Data splitter | ⬜ Planned | `src/data/splitter.py` |
| Demo notebook | ⬜ Planned | `notebooks/02_case_generation_demo.ipynb` |
| Config finalization | ⬜ Planned | `configs/generation.yaml` (already drafted) |
| Context update | ⬜ Planned | `Context/PROGRESS.md`, `Context/DATA.md`, `Context/ARCHITECTURE.md`, `Context/GOTCHAS.md` |

### Exit Criteria

- `data/processed/mind_cases.jsonl` contains ≥ 22,000 cases
- `train.jsonl` / `val.jsonl` / `test.jsonl` with correct 80/10/10 splits
- 5 randomly sampled cases pass manual quality review
- Relevant `Context/` files updated and verified per `CONTEXT_RULES.md`

### Hardware

- College GPU server via SSH
- `nohup python scripts/generate_cases.py > generation.log 2>&1 &`

---

## Phase 2 — ChromaDB Rubric Index ⬜

**Status**: Not started (can run in parallel with Phase 1)
**Target**: Build dense vector index over all 74,513 rubrics

### Exit Criteria

- Query `"splitting headache from sun"` returns `HEAD > PAIN > Sun, from exposure to` in top-5

---

## Phase 3 — ClinicalBERT NER Training ⬜

**Status**: Not started (depends on Phase 1 data)
**Target**: Token-level F1 ≥ 88% on validation set

### Hardware

- Google Colab T4 free tier (~35–50 min training)

---

## Phase 4 — LLaMA 3 Post-Processor ⬜

**Status**: Not started (depends on Phase 3)

---

## Phase 5 — Pipeline & Remedy Ranking ⬜

**Status**: Not started (depends on Phases 3 + 4)
**Target**: Top-20 Rubric Recall ≥ 90%, MRR ≥ 0.65

---

## Phase 6 — Conversational Chatbot ⬜

**Status**: Not started

---

## Phase 7 — Streamlit Dashboard ⬜

**Status**: Not started

---

## Phase 8 — Polish, Docs & Defense ⬜

**Status**: Not started

---

## Changelog

| Date | Phase | Agent | Change |
|---|---|---|---|
| 2026-09-26 | 0 | Antigravity | Initial scaffolding complete. All directories, kent_db, configs, tests, stubs, EDA notebook, git init. |

---

_End of file._
