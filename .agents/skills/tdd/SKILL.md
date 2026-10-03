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
Every new public function or class in `src/` must have a corresponding test in `tests/`.

---

## Mandatory Rules (from Context/CONVENTIONS.md)

1. **Test framework**: `pytest` — configured in `pyproject.toml`.
2. **Test file location**: `tests/test_<module>.py`, mirroring `src/`.
3. **Class-based grouping**: Use `class Test<Module>:` for related tests (e.g., `class TestKentDBReader:`).
4. **SQLite tests use the real database** — this is intentional per project convention (see Context/CONVENTIONS.md §8). Do NOT mock the SQLite layer for `src/data/kent_db.py` tests. This is a deliberate correctness verification strategy.
5. **ChromaDB tests use `EphemeralClient`** with a unique collection name per test fixture (e.g., `collection_name=f"test_rubrics_{uuid.uuid4().hex[:8]}"`) to prevent cross-test contamination (GOTCHAS.md §7.4).
6. **Stub tests**: Unimplemented modules have a single `assert True` placeholder. Replace with real tests as the module is implemented.
7. **Random seeds for ML tests**: Set `np.random.seed(42)` and `torch.manual_seed(42)` in fixtures that instantiate models.

---

## Workflow

### Step 1 — Red (Write a Failing Test)
```python
# tests/test_<module>.py
import pytest

class Test<Module>:
    def test_<function>_returns_expected(self):
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
- Re-run the full suite: `.venv\Scripts\pytest.exe tests/ -v`.

---

## Kent-AI Test Targets

| Test File | Module Under Test | Testing Strategy |
|---|---|---|
| `tests/test_kent_db.py` | `src/data/kent_db.py` | Real SQLite DB (13 passing tests, no mocks) |
| `tests/test_bio_tagger.py` | `src/data/bio_tagger.py` | Isolated string inputs, no DB |
| `tests/test_case_generator.py` | `src/data/case_generator.py` | Mock Ollama REST calls |
| `tests/test_splitter.py` | `src/data/splitter.py` | Deterministic input lists |
| `tests/test_symptom_ner.py` | `src/models/symptom_ner.py` | Stub; replace when Phase 3 starts |
| `tests/test_resolver.py` | `src/models/resolver.py` | Mocked Ollama, rule-based fallback |
| `tests/test_vector_store.py` | `src/search/vector_store.py` | EphemeralClient + unique collection names |
| `tests/test_ranker.py` | `src/search/ranker.py` | Fixture rubric/remedy data |
| `tests/test_pipeline.py` | `src/pipeline/orchestrator.py` | Integration: mock LLM + real ChromaDB |
| `tests/test_state_machine.py` | `src/chatbot/state_machine.py` | FSM state transitions |
| `tests/test_dialogue_manager.py` | `src/chatbot/dialogue_manager.py` | Slot tracking, mock LLM |
| `tests/test_dashboard.py` | `src/dashboard/app.py` | Component rendering, export logic |

---

## Running the Suite

```bash
# Activate the virtual environment first (Windows)
.venv\Scripts\activate

# Full suite
.venv\Scripts\pytest.exe tests/ -v

# Single test file
.venv\Scripts\pytest.exe tests/test_kent_db.py -v

# With short traceback for debugging
.venv\Scripts\pytest.exe tests/ -v --tb=short
```

---

## Definition of Done
- [ ] Test written **before** implementation code (Red step confirmed).
- [ ] All new tests pass (`pytest` exit code 0).
- [ ] Existing 60+ passing tests remain unaffected.
- [ ] No `print()` statements left in test files (use `logging`).
- [ ] `Context/PROGRESS.md` updated if a phase milestone is reached.
