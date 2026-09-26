# Kent-AI — Code Conventions

> Last updated: 2026-09-26 by Antigravity (Phase 0 scaffolding agent)
> Phase: 0 (complete)

---

## 1. Python Version & Environment

| Item | Value |
|---|---|
| Required Python | ≥ 3.10 (project uses 3.12 on dev machine) |
| Virtual env | `.venv/` at project root (created via `py -3.12 -m venv .venv`) |
| Activate (Windows) | `.venv\Scripts\activate` |
| Package manager | `pip` (no Poetry, no uv for this project) |
| Project install | `pip install -e ".[dev]"` |

---

## 2. Import Style

### Standard Ordering

```python
# 1. __future__ imports (always first)
from __future__ import annotations

# 2. Standard library
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# 3. Third-party
import yaml

# 4. Project-internal (absolute imports only)
from src.config import load_config
from src.data.kent_db import get_sections, get_remedies
```

### Rules

- **Always use absolute imports** from `src.*`. Never use relative imports (no `from .kent_db import ...`).
- **Always include `from __future__ import annotations`** at the top of every module (enables PEP 604 `X | Y` syntax on Python 3.10).
- Imports in `__init__.py` files re-export public API names via `__all__`.

---

## 3. Type Annotations

- **All function signatures must have type hints** — parameters and return type.
- Use `Dict[str, Any]` from `typing` (not `dict[str, Any]`) for compatibility down to 3.10 (the `from __future__ import annotations` import handles the forward reference, but be consistent with existing code).
- Use `Optional[X]` or `X | None` for nullable parameters.
- Use `Union[str, Path]` for path-like parameters.

```python
# Good
def get_rubrics(
    section_id: int,
    parent_id: Optional[int] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    db_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
```

---

## 4. Docstrings

Use Google-style docstrings with `Args:`, `Returns:`, `Raises:` sections.

```python
def get_rubric_path(rubric_id: int, db_path: Optional[Union[str, Path]] = None) -> str:
    """Retrieve the full hierarchical path string for a given rubric.

    If the database row contains a pre-populated 'path' column, that is used;
    otherwise, the path is traversed recursively to the root.

    Args:
        rubric_id: Rubric primary key ID.
        db_path: Optional path to SQLite database.

    Returns:
        Path string in the format "SECTION > PARENT > CHILD".

    Raises:
        KeyError: If the rubric_id does not exist.
    """
```

### Rules

- Every public function and class MUST have a docstring.
- **Explain *why*, not just *what*** — especially for non-obvious design choices.
- Private helper functions need only a one-line docstring.

---

## 5. Module Organization

### Separation of Concerns

| Directory | Owns | Does NOT Touch |
|---|---|---|
| `src/data/` | SQLite, file I/O, data transforms | ML models, HTTP |
| `src/models/` | Model loading, inference, training | Database queries |
| `src/search/` | Embeddings, ChromaDB, ranking | Training loops |
| `src/chatbot/` | State machine, dialogue, prompts | Direct DB access |
| `src/pipeline/` | Orchestration of above modules | Implementation details of any one module |
| `src/dashboard/` | Streamlit UI rendering | Business logic (delegates to pipeline) |
| `scripts/` | CLI entry points only | Testable logic (imports from `src/`) |

### File Size

- No single file should exceed ~500 lines. If it does, extract a helper module.
- `__init__.py` files are for re-exports only — no business logic.

---

## 6. Configuration

- **All hyperparameters, model names, file paths, and magic numbers** live in `configs/*.yaml`.
- **Never hardcode** a model name, learning rate, batch size, or threshold in source code.
- Load configs via `src.config.load_config("model")` or the typed shortcuts.
- Config files use nested YAML keys (not flat), e.g., `model.name`, not `model_name`.

---

## 7. Database Access

- **Always use read-only connections**: `get_connection()` opens with `?mode=ro` URI and `PRAGMA query_only=ON`.
- **Always use the context manager**: `with get_connection() as conn:` — never store a long-lived connection.
- **Return `list[dict]`** from all query functions (via `sqlite3.Row` → `dict(row)`).
- **Parameterize all queries** — never use string formatting for SQL values.
- **Grade resolution**: Always use `COALESCE(rr.grade, rr.grade_candidate, 1)` when querying remedy grades.

---

## 8. Testing

- Test framework: **pytest** (configured in `pyproject.toml`).
- Test files live in `tests/` and are named `test_<module>.py`.
- Use **class-based grouping** (`class TestKentDBReader:`) for related tests.
- **Stub tests** for unimplemented modules contain a single `assert True` placeholder.
- Tests run against the **real database** (no mocks for the SQLite layer) — this is intentional for correctness verification.
- Run: `.venv\Scripts\pytest.exe tests/ -v`

---

## 9. Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Modules | `snake_case.py` | `kent_db.py`, `case_generator.py` |
| Functions | `snake_case` | `get_mind_rubrics()`, `search_rubrics()` |
| Classes | `PascalCase` | `KentDB`, `SymptomNER`, `CaseGenerator` |
| Constants | `UPPER_SNAKE_CASE` | `CASE_GENERATION_PROMPT` |
| Config keys | `snake_case` in YAML | `learning_rate`, `max_seq_length` |
| Test functions | `test_<what_is_tested>` | `test_get_mind_rubrics_count` |
| Test classes | `Test<Module>` | `TestKentDBReader`, `TestConfigSystem` |

---

## 10. Error Handling

- Use specific exception types: `FileNotFoundError`, `KeyError`, `ValueError`.
- Never use bare `except:` or `except Exception:` without re-raising or logging.
- Database lookup functions return `None` for missing records (do not raise).
- Path resolution functions (`get_db_path`, `get_rubric_path`) raise on failure.

---

## 11. Git

- Commit messages follow: `<type>: <description>` (e.g., `feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
- Large binary files (`.sqlite`, `.gz`, model weights) are `.gitignored`.
- The `.venv/` directory is never committed.

---

_End of file._
