---
name: code-review
description: >
  Structured code review checklist for the kent-ai codebase.
  Use when reviewing a pull request, auditing a newly written module,
  or self-reviewing before committing. Covers correctness, security,
  style (PEP-8 / project conventions), modularity, test coverage, and
  domain-specific clinical NLP concerns.
---

# Code Review Skill — Kent-AI

## Review Philosophy
A review is not a style war. Flag only issues that affect **correctness,
security, maintainability, or performance**. Praise good patterns explicitly.

---

## Review Checklist

### 1. Correctness
- [ ] Does the function do what its docstring says?
- [ ] Are edge cases handled? (empty list, None, zero-length string)
- [ ] Do SQLite queries use `COALESCE(grade, grade_candidate, 1)` for remedy grades? (CONVENTIONS.md §7)
- [ ] Do ChromaDB cosine distance results get converted to similarity (`1 - d`)? (GOTCHAS.md §7.1)
- [ ] Does BIO tagging produce the correct 15-class label space? (`O` + 7×{`B-`, `I-`} for `LOC`, `SEN`, `MOD_AGG`, `MOD_AMEL`, `CONC`, `TEMP`, `MENT`)
- [ ] Do generated case JSONs include all required fields from the `SyntheticCase` schema (`case_id`, `rubric_id`, `rubric_path`, `narrative`, `entities`, `tokens`, `bio_tags`, `metadata`)?

### 2. Security & Data Integrity
- [ ] No API keys or credentials hardcoded; all config in `configs/*.yaml`.
- [ ] SQLite queries use parameterised statements — never f-string or format() for SQL values (CONVENTIONS.md §7).
- [ ] Database opened read-only: `get_connection()` with `PRAGMA query_only=ON`.

### 3. Style & Readability (per Context/CONVENTIONS.md)
- [ ] `from __future__ import annotations` is the first import in every module.
- [ ] Import order: stdlib → third-party → `src.*` (absolute only — no relative imports).
- [ ] All public functions and classes have Google-style docstrings (Args, Returns, Raises).
- [ ] Function signatures have complete type hints (parameters + return type).
- [ ] Uses `Optional[X]`, `Union[X, Y]`, `Dict[str, Any]` from `typing` (not bare `dict[...]`).
- [ ] Constants are `UPPER_SNAKE_CASE`; classes are `PascalCase`; functions/modules are `snake_case`.
- [ ] No single file exceeds ~500 lines (CONVENTIONS.md §5).

### 4. Modularity & Layer Separation (per Context/ARCHITECTURE.md)
- [ ] Code lives in the correct `src/` subdirectory (see layer table below).
- [ ] No circular imports — `src/data/` does not import from `src/models/`, etc.
- [ ] All thresholds, model names, file paths in `configs/*.yaml` — not hardcoded.
- [ ] Configs loaded via `src.config.load_config()` — not via raw `open()`.

**Layer Ownership:**

| Layer | Owns | Must NOT Import From |
|---|---|---|
| `src/data/` | SQLite, file I/O, data transforms | `src/models/`, HTTP |
| `src/models/` | Model loading, inference | Database queries |
| `src/search/` | Embeddings, ChromaDB, ranking | Training loops |
| `src/chatbot/` | State machine, dialogue, prompts | Direct DB access |
| `src/pipeline/` | Orchestration | Implementation details of any one module |
| `src/dashboard/` | Streamlit UI rendering | Business logic (delegates to `src/pipeline/`) |

### 5. Tests (per Context/CONVENTIONS.md §8)
- [ ] Every new public function has at least one corresponding test.
- [ ] Tests for `src/data/kent_db.py` use the **real SQLite database** — this is intentional, do NOT require mocks here.
- [ ] Tests for ChromaDB (`src/search/vector_store.py`) use `chromadb.EphemeralClient()` with a unique `uuid.uuid4().hex[:8]` collection name.
- [ ] Tests for Ollama-backed modules (case generator, resolver, dialogue manager) mock the REST call.
- [ ] Test functions named `test_<what_is_tested>`; grouped in `class Test<Module>`.

### 6. Performance (ML/NLP specific)
- [ ] `RubricEmbedder` uses lazy model loading (`_get_model()`) — model not loaded on import.
- [ ] ChromaDB `collection.upsert()` called in batches of ≤500 documents (GOTCHAS.md §7.3).
- [ ] No model `.forward()` / embedding called in a Python loop over many items — use batching.
- [ ] Large tensors are not serialised as plain text in logs (use `.shape` for inspection).

### 7. Domain Correctness (Clinical NLP / Homeopathic)
- [ ] BIO labels use only the 15-class system: `O`, `B-LOC`, `I-LOC`, `B-SEN`, `I-SEN`, `B-MOD_AGG`, `I-MOD_AGG`, `B-MOD_AMEL`, `I-MOD_AMEL`, `B-CONC`, `I-CONC`, `B-TEMP`, `I-TEMP`, `B-MENT`, `I-MENT`.
- [ ] Special tokens (`[CLS]`, `[SEP]`, `[PAD]`) labeled with `-100`, not `"O"` (GOTCHAS.md §6.4).
- [ ] Hyphenated terms like `absent-minded` split by `r"\w+|[^\w\s]"` → 3 tokens with correct BIO continuation (GOTCHAS.md §6.2).
- [ ] `SymptomProfile` resolver output contains all 7 dimensions: `LOC`, `SEN`, `MOD_AGG`, `MOD_AMEL`, `CONC`, `TEMP`, `MENT`.

---

## Feedback Format

```
[SEVERITY] File: src/<module>.py  Line: <N>
Issue   : <short description>
Why     : <why this matters>
Suggest : <concrete fix>
```

Severity levels: `BLOCKER` | `MAJOR` | `MINOR` | `NIT`

---

## After Review
- If all BLOCKER and MAJOR items are resolved → **Approve**.
- Update `Context/PROGRESS.md` if the reviewed change closes a phase milestone.
