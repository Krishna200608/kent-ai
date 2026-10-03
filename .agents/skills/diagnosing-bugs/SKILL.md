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
# Place in: tests/debug/repro_<issue>.py
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

Check existing log files first:
- `logs/pilot_generation.log` — for case generation issues
- `logs/chromadb_index.log` — for retrieval issues
- Any traceback in the terminal output

---

## Step 3 — Verify Against Docs / Schema

Before concluding a fix, verify your assumption:

| Issue Type | Verification Source |
|---|---|
| ChromaDB query mismatch | `Context/GOTCHAS.md` + ChromaDB docs |
| BIO tag shape error | `src/models/ner_model.py` docstring |
| SQLite schema mismatch | Run `kent-repertory-inspector` skill |
| JSON schema failure | `src/pipeline/schema.py` or `data/schemas/` |
| Metric regression | Run `eval-metric-parser` skill |

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

## Kent-AI Known Gotchas (from Context/GOTCHAS.md)

- ChromaDB `persist_directory` must exist before instantiation.
- LLaMA 3 generation can time out on CPU — always set `timeout` param.
- `kent_db.py` returns raw SQLite rows; always convert to `dict` before downstream use.
- BIO token count must exactly match the tokeniser output length — off-by-one is the most common NER bug.
