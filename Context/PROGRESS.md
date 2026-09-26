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

## Phase 1 — Synthetic Case Generation 🔄

**Status**: Pipeline Implemented & Verified ✅ (Ready for production batch run on GPU)
**Date**: 2026-09-26
**Agent**: Antigravity (Gemini 3.8 Flash)
**Target**: Generate ~22,200 MIND clinical cases using LLaMA 3 8B with crash-safe checkpointing

### Tasks

| Task | Status | File(s) |
|---|---|---|
| Case generator core | ✅ Done | `src/data/case_generator.py` (Ollama REST + deterministic mock mode) |
| Prompt templates for generation | ✅ Done | `src/chatbot/prompts.py` (7-dim clinical prompts + few-shot examples) |
| BIO auto-tagger | ✅ Done | `src/data/bio_tagger.py` (exact tokenization, offset drift repair, subword align) |
| CLI generation script | ✅ Done | `scripts/generate_cases.py` (atomic checkpoints, signal handling, `--split`) |
| Data splitter | ✅ Done | `src/data/splitter.py` (80/10/10 stratified deficit-balancing algorithm) |
| Demo notebook | ✅ Done | `notebooks/02_case_generation_demo.ipynb` (interactive walkthrough) |
| Config finalization | ✅ Done | `configs/generation.yaml` |
| Context update | ✅ Done | `Context/PROGRESS.md`, `Context/DATA.md`, `Context/ARCHITECTURE.md`, `Context/GOTCHAS.md` |

### Verification & Testing

```bash
pytest tests/test_bio_tagger.py tests/test_case_generator.py tests/test_splitter.py -v
# Output: 13 passed in 0.08s ✅

python scripts/generate_cases.py --mock --limit 20 --cases-per-rubric 4 --split
# Output: 80 cases generated in 0.16s, splits created (64 train / 8 val / 8 test) ✅

python scripts/generate_cases.py --mock --limit 20 --cases-per-rubric 4 --resume
# Output: Resumed from checkpoint: 20 rubrics already completed ✅
```

### Production GPU Launch Instructions

```bash
# On College GPU Server:
ollama run llama3:8b
nohup python scripts/generate_cases.py --split > generation.log 2>&1 &
tail -f generation.log
```

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
