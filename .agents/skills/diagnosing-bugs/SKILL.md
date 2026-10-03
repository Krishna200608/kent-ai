---
name: diagnosing-bugs
description: >
  Structured bug diagnosis ladder for the kent-ai pipeline.
  Use when a test fails, an exception is thrown, a metric regresses,
  or any component of the NLP/retrieval/generation pipeline produces
  unexpected output. Enforces a strict Isolate → Instrument → Verify
  → Escalate sequence before touching production code.
---

# Diagnosing Bugs Skill — Kent-AI

## Core Rule
**Never randomly change code hoping it fixes the issue.**
Follow the 4-step ladder below. Escalate to the user after 3 failed attempts.

---

## Step 1 — Isolate

Reproduce the bug with the **smallest possible input**.

```python
# Scratch script — do NOT commit
# Place in: tests/ temporarily, delete after diagnosis
import logging
logging.basicConfig(level=logging.DEBUG)

# Minimal call that triggers the bug
from src.<module> import <function>
result = <function>(<minimal_input>)
print(result)
```

Questions to answer before moving on:
- Does the bug reproduce consistently?
- Which module/function is the entry point of failure?
- Is it a data issue, logic issue, or dependency issue?

---

## Step 2 — Instrument

Add targeted logging. **Do not use `print()`** — use the standard `logging` module.

```python
import logging
logger = logging.getLogger(__name__)

# Inside the suspicious function:
logger.debug("Input received: %s", repr(input_value))
logger.debug("Intermediate state: %s", repr(intermediate))
```

Check existing outputs first:
- Terminal traceback and stdout from `pytest` or script runs
- `logs/generation.log` — if the bug is in case generation
- ChromaDB query return values (use `logger.debug` on `.query()` results)

---

## Step 3 — Verify Against Actual Code & Docs

Before concluding a fix, verify your assumption against the actual repository.

| Issue Type | Verification Source |
|---|---|
| SQLite query returns wrong shape | `src/data/kent_db.py` + `Context/DATA.md` (schema, grade COALESCE) |
| BIO offset mismatch | `src/data/bio_tagger.py` — check `align_entity_offsets()` 4-tier ladder |
| ChromaDB cosine distance confusion | `Context/GOTCHAS.md` §7.1 (distance ∈ [0,2]; sim = 1 − d) |
| ChromaDB cross-test contamination | `Context/GOTCHAS.md` §7.4 (EphemeralClient collection isolation) |
| Case JSON schema failure | `Context/DATA.md` §Synthetic Case Schema + `src/data/case_generator.py` |
| NER token count mismatch | `Context/GOTCHAS.md` §6.2 (hyphenated terms split to 3 tokens) |
| LLaMA 3 offset drift | `Context/GOTCHAS.md` §6.1 (±15 char window search in `bio_tagger.py`) |
| LLM variation collapse | `Context/GOTCHAS.md` §6.5 (dynamic seed = seed + case_idx × 137) |
| Config key missing | `configs/model.yaml`, `configs/generation.yaml`, etc. (loaded via `src.config.load_config()`) |
| Resolver 7-dim extraction wrong | `src/models/resolver.py` — check `SymptomProfile` dataclass fields |
| Ranker grade weighting wrong | `src/search/ranker.py` — grades 1/2/3 only (COALESCE default = 1) |
| State machine stuck in wrong state | `src/chatbot/state_machine.py` — `IntakeState` enum transitions |
| Dialogue slot not updated | `src/chatbot/dialogue_manager.py` — slot tracker logic |

---

## Step 4 — Escalate (After 3 Failures)

Stop. Do NOT make a 4th change. Report:

```
Bug Report
----------
Component : <module/function>
Repro steps: <exact command or code>
Expected  : <what should happen>
Actual    : <what actually happens>
Logs      : <paste relevant log lines>
Attempts  :
  1. <what was tried> → <result>
  2. <what was tried> → <result>
  3. <what was tried> → <result>
Hypothesis: <current best guess>
```

---

## Actual Kent-AI Module Map

```
src/data/kent_db.py          — SQLite DAL (real DB in tests — no mocks)
src/data/bio_tagger.py       — BIO token tagger with offset drift repair
src/data/case_generator.py   — LLaMA 3 synthetic case pipeline (Ollama REST + Mock)
src/data/splitter.py         — 80/10/10 stratified deficit splitter

src/models/symptom_ner.py    — Bio_ClinicalBERT NER wrapper (Phase 3 stub)
src/models/resolver.py       — LLaMA post-processor & negation resolver
src/models/trainer.py        — Training loop (Phase 3 stub)

src/search/embedder.py       — sentence-transformers embedder (lazy load)
src/search/vector_store.py   — ChromaDB wrapper with HNSW cosine index
src/search/ranker.py         — Remedy intersection & grade ranker

src/chatbot/state_machine.py   — FSM with IntakeState enum
src/chatbot/dialogue_manager.py — Multi-turn dialogue manager
src/chatbot/prompts.py         — Prompt templates

src/pipeline/orchestrator.py    — End-to-end transcript → report orchestrator
src/pipeline/report_generator.py — JSON + Markdown report generator

src/dashboard/app.py            — Streamlit 4-workspace clinical portal
src/dashboard/styles.py         — CSS injection
src/dashboard/styles.css        — Google Stitch CSS theme
src/dashboard/dimensions.py     — DIMENSION_MAP single source of truth
src/dashboard/components/chat_viewer.py  — Multi-turn chat HUD
src/dashboard/components/rubric_tree.py  — Rubric cards with remedy inspector
src/dashboard/components/icons.py        — Icon helpers
```
