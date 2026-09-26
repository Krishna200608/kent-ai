# 📚 API Reference — Kent-AI Internal Modules

---

## 1. `src.data.kent_db`

### `get_connection(db_path=None)`
Context-managed read-only connection to `repertory.sqlite` with `PRAGMA query_only=ON`.

### `get_sections(db_path=None) -> list[dict]`
Retrieves all 37 repertory sections with printed/PDF page ranges and rubric counts.

### `get_mind_rubrics(limit=None, offset=0, db_path=None) -> list[dict]`
Retrieves rubrics in Section 1 (MIND), returning 4,933 records.

### `get_rubrics(section_id, parent_id=None, limit=None, offset=0, db_path=None) -> list[dict]`
Fetches rubrics for a specific section, optionally filtered by `parent_id`.

### `get_rubric_path(rubric_id, db_path=None) -> str`
Resolves hierarchical string path (e.g. `MIND > ABANDONED > feels he is`).

### `get_remedies(rubric_id, db_path=None) -> list[dict]`
Fetches all remedies associated with a rubric, including `grade` (3, 2, or 1), `abbreviation`, and `full_name`.

### `search_rubrics(query, section_id=None, limit=40, offset=0, db_path=None) -> list[dict]`
Searches rubrics using SQLite FTS5 prefix match with automatic LIKE fallback.

---

## 2. `src.config`

### `load_config(config_name: str) -> dict`
Loads specified YAML configuration from `configs/`.

### `get_project_root() -> Path`
Resolves repository root path dynamically.
