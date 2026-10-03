---
name: code-review
description: >
  Structured code review checklist for the kent-ai codebase.
  Use when reviewing a pull request, auditing a newly written module,
  or self-reviewing before committing. Covers correctness, security,
  style (PEP-8), modularity, test coverage, and domain-specific
  clinical NLP concerns.
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
- [ ] Are BIO tag counts validated against tokeniser output length?
- [ ] Does the JSON output conform to the case schema in `data/schemas/`?

### 2. Security & Data Integrity
- [ ] No raw patient data (even synthetic) logged to stdout.
- [ ] No API keys or credentials hardcoded; use `config/` or env vars.
- [ ] SQLite queries use parameterised statements (no f-string injection).

### 3. Style & Readability (PEP-8)
- [ ] Line length ≤ 99 characters.
- [ ] All public functions have type hints and a docstring explaining **why**, not just **what**.
- [ ] No mutable default arguments (`def f(x=[])`).
- [ ] Imports: stdlib → third-party → local, separated by blank lines.

### 4. Modularity
- [ ] Function does one thing. If it's > 40 lines, ask: can it be split?
- [ ] No logic duplicated across modules — extract to a shared utility.
- [ ] New code lives in the correct `src/` subdirectory per `Context/ARCHITECTURE.md`.

### 5. Tests
- [ ] Every new public function has at least one corresponding test.
- [ ] Tests do not hit the real SQLite DB or real ChromaDB — mocked.
- [ ] Fixtures use `np.random.seed(42)` / `torch.manual_seed(42)`.

### 6. Performance (ML/NLP specific)
- [ ] No `model.forward()` called inside a Python loop over many items — use batching.
- [ ] Large tensors are not serialised as plain text in logs.
- [ ] ChromaDB queries specify `n_results` to avoid fetching entire collection.

### 7. Domain Correctness (Clinical NLP)
- [ ] Generated cases cover the required 7 clinical dimensions.
- [ ] Rubric retrieval returns ≥ top-20 relevant rubrics for test queries.
- [ ] BIO tokens for clinical entities are correctly labelled (B-, I-, O).

---

## Feedback Format

Use the following structure for each issue found:

```
[SEVERITY] File: src/module.py  Line: 42
Issue   : <short description>
Why     : <why this matters>
Suggest : <concrete fix>
```

Severity levels: `BLOCKER` | `MAJOR` | `MINOR` | `NIT`

---

## After Review
- If all BLOCKER and MAJOR items are resolved → **Approve**.
- Update `Context/PROGRESS.md` if the reviewed change closes a milestone item.
