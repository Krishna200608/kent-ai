---
name: tdd
description: >
  Test-Driven Development (TDD) workflow for the kent-ai codebase.
  Use when writing new features, fixing bugs, or refactoring any module
  under src/. Guides the Red-Green-Refactor cycle with pytest, enforces
  test isolation, and ensures reproducibility per project conventions.
---

# TDD Skill — Kent-AI

## Purpose
Drive all new code through a **Red → Green → Refactor** cycle using `pytest`.
Every new function or class in `src/` must have a corresponding test in `tests/`.

---

## Mandatory Rules (from Context/CONVENTIONS.md)

1. **Random seeds**: Always set `np.random.seed(42)` and `torch.manual_seed(42)` in test fixtures that touch models.
2. **No real I/O in unit tests**: Mock `sqlite3`, ChromaDB clients, and file handles with `unittest.mock`.
3. **Test files mirror source**: `src/data/kent_db.py` → `tests/test_kent_db.py`.
4. **Fixture data**: Place small fixture JSON/CSV files in `tests/fixtures/`.

---

## Workflow

### Step 1 — Red (Write a Failing Test)
```python
# tests/test_<module>.py
import pytest

def test_<function>_returns_expected():
    # Arrange
    # Act
    # Assert
    assert result == expected   # This MUST fail before writing code
```
Run: `pytest tests/test_<module>.py -v` — confirm it **fails**.

### Step 2 — Green (Write Minimal Code)
- Write the **smallest** implementation that makes the test pass.
- Do not over-engineer; do not add untested behaviour.

Run: `pytest tests/test_<module>.py -v` — confirm it **passes**.

### Step 3 — Refactor
- Improve code quality (naming, docstrings, extraction) without changing behaviour.
- Re-run the full suite: `pytest tests/ -v --tb=short`.

---

## Kent-AI Specific Test Targets

| Module | Key Behaviours to Test |
|---|---|
| `src/data/kent_db.py` | Query returns list of rubric dicts; handles empty result |
| `src/models/ner_model.py` | BIO tag output shape matches input token count |
| `src/search/retriever.py` | Top-k results returned; ChromaDB client is mocked |
| `src/pipeline/generator.py` | Generated case JSON validates against schema |
| `src/chatbot/chatbot.py` | Response is non-empty string; no exceptions on valid input |

---

## Running the Suite

```bash
# Full suite
pytest tests/ -v --tb=short

# Single module
pytest tests/test_kent_db.py -v

# Coverage report
pytest tests/ --cov=src --cov-report=term-missing
```

---

## Definition of Done
- [ ] Test written **before** implementation code.
- [ ] All new tests pass (`pytest` exit code 0).
- [ ] Coverage on the changed module >= 80%.
- [ ] No `print()` statements left in test files.
- [ ] `Context/PROGRESS.md` updated with test status if a milestone is reached.
