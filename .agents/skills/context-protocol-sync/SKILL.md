---
name: context-protocol-sync
description: Automates and enforces the Context Update Protocol Matrix across all Context/ files (PROGRESS.md, ARCHITECTURE.md, DATA.md, GOTCHAS.md, CONVENTIONS.md, PROJECT.md).
triggers:
  - "sync-context"
  - "context sync"
  - "commit prepped"
  - "task complete"
  - "milestone complete"
  - "update context"
author: "kent-ai-team"
version: "1.0.0"
---

# Context Protocol Sync Skill

## Overview

In `kent-ai`, the `Context/` directory represents **the single source of truth** for all autonomous engineering agents and human contributors. Any code modification, dataset generation, architecture refactor, or bug discovery must be synchronized with the corresponding context files before a task can be marked complete or committed to version control.

This skill operationalizes the Context Update Protocol Matrix defined in `project_foundation.md` and `Context/CONTEXT_RULES.md`.

---

## Context Update Protocol Matrix

| Trigger Event | Target Context File | Required Update Action |
|---|---|---|
| Phase / Milestone finishes or progresses | `Context/PROGRESS.md` | Update status badges, checklist checkboxes (`[x]`), verified metrics, and add a dated entry to `## Changelog`. |
| New module added or stub transitioned to functional | `Context/ARCHITECTURE.md` | Update repository tree marker from `Stub` to `★ CORE` or add new module path and doc summary. |
| Dataset artifacts (`*.jsonl`) or embeddings generated | `Context/DATA.md` | Record exact row counts, file byte sizes, 80/10/10 split counts, schema details, or ChromaDB collection metrics. |
| Bug, exception, NULL edge case, or timeout discovered | `Context/GOTCHAS.md` | Append an entry with `Symptom`, `Root Cause`, and `Verified Workaround`. |
| New library, CLI pattern, or coding convention introduced | `Context/CONVENTIONS.md` | Document imports, typing rules, or environmental requirements. |
| Major scope shift, milestone redefined, or team change | `Context/PROJECT.md` | Update executive summary, milestones, and context file index. |

---

## Verification & Execution Routine

When this skill is triggered, execute the following 6-step protocol sequentially:

### Step 1: Inspect Repository State & File Diffs

Run git status and inspect modified or untracked files:

```powershell
# Check modified and untracked files
git status --porcelain

# Inspect list of files changed relative to HEAD
git diff --name-only HEAD
```

Identify what categories of files have changed:
- Files in `src/`: Code logic changed or stubs implemented.
- Files in `data/processed/` or `data/embeddings/`: Data artifacts produced.
- Files in `configs/`: System hyperparameter or configuration changed.
- Tests in `tests/`: New tests added or passing counts altered.

---

### Step 2: Milestone & Phase Progress Audit (`Context/PROGRESS.md`)

If any deliverable or milestone was advanced:
1. Verify unit tests passing count:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/ -v
   ```
2. Update the phase status header in `Context/PROGRESS.md` (e.g. `🔄 In Progress` $\to$ `✅ Complete`).
3. Check off completed deliverable items (`- [x]` or table `✅ Done`).
4. Ensure the `Last updated:` date header in `Context/PROGRESS.md` is updated to current ISO date (`YYYY-MM-DD`).
5. Append an audit entry to `## Changelog` at the bottom of `Context/PROGRESS.md`:
   ```markdown
   | YYYY-MM-DD | <Phase #> | Antigravity | <Concise summary of changes and passing test counts> |
   ```

---

### Step 3: Architecture & Module Tree Audit (`Context/ARCHITECTURE.md`)

If any file in `src/` was created, renamed, or graduated from stub to functional:
1. Inspect the module tree in `Context/ARCHITECTURE.md` § `## Repository Tree`.
2. Ensure new files are listed with their exact relative paths.
3. Graduate status markers from `Stub: ...` to `★ CORE: ... — implemented`.
4. If new data flows or pipeline stages were introduced, verify the ASCII pipeline diagram under § `## Data Flow`.
5. Update `Last updated:` date header.

---

### Step 4: Dataset Artifacts & Embeddings Audit (`Context/DATA.md`)

If datasets (`*.jsonl`) or embeddings were generated or modified:
1. Obtain exact line counts and file sizes:
   ```powershell
   .venv\Scripts\python.exe -c "
   from pathlib import Path
   import json
   for p in sorted(Path('data/processed').glob('*.jsonl')):
       lines = sum(1 for _ in open(p, 'r', encoding='utf-8'))
       print(f'{p.name}: {lines:,} lines ({p.stat().st_size:,} bytes)')
   "
   ```
2. Obtain ChromaDB index count if `data/embeddings/` is updated:
   ```powershell
   .venv\Scripts\python.exe -c "
   from src.search.vector_store import RubricVectorStore
   store = RubricVectorStore()
   print('ChromaDB collection count:', store.count())
   "
   ```
3. Update `Context/DATA.md` tables with exact verified numbers (never vague qualifiers like "several" or "many").
4. If data splits were generated, confirm the 80/10/10 ratio:
   - Train: ~80%
   - Val: ~10%
   - Test: ~10%
5. Update `Last updated:` date header.

---

### Step 5: Incident & Edge-Case Audit (`Context/GOTCHAS.md`)

If any unexpected behavior occurred during execution (e.g., Windows CP1252 encoding crashes, NULL remedy grades, missing libraries, subword token alignment drift, ChromaDB memory spikes):
1. Format a new gotcha entry using the standard template:
   ```markdown
   ### <Section>.<ID> <Brief Descriptive Title>

   **Symptom**:
   <Exact error message, exception type, or observed failure>

   **Root Cause**:
   <Underlying explanation of why the failure occurred>

   **Verified Workaround**:
   <Concrete code fix, command override, or architectural guard implemented>
   ```
2. Place the entry under the appropriate category (`## 1. Database Gotchas`, `## 2. Hierarchy Gotchas`, `## 3. Python / Environment Gotchas`, etc.).
3. Update `Last updated:` date header.

---

### Step 6: Conventions & Dependencies Audit (`Context/CONVENTIONS.md`)

If new packages, flags, or patterns were introduced:
1. Ensure new packages are documented in `pyproject.toml` and noted in `Context/CONVENTIONS.md`.
2. Check that all new Python files adhere to conventions:
   - `from __future__ import annotations` as first non-docstring import.
   - Absolute imports only (`from src. ...`).
   - Explicit type hints on all functions (`Dict[str, Any]`, `Optional[T]`).
   - Google-style docstrings with `Args:`, `Returns:`, `Raises:`.
3. Update `Last updated:` date header.

---

## Safety Gate & Quality Checklist

Before closing any user task or pushing commits, run this automated gate:

```powershell
# Verify all context files have valid headers and no lingering unverified placeholders
.venv\Scripts\python.exe -c "
from pathlib import Path
import re

context_dir = Path('Context')
required_files = ['PROGRESS.md', 'ARCHITECTURE.md', 'DATA.md', 'GOTCHAS.md', 'CONVENTIONS.md', 'PROJECT.md', 'CONTEXT_RULES.md']

missing = [f for f in required_files if not (context_dir / f).is_file()]
if missing:
    print(f'[FAIL] Missing context files: {missing}')
    exit(1)

for f in required_files:
    content = (context_dir / f).read_text(encoding='utf-8')
    if 'Last updated:' not in content:
        print(f'[FAIL] {f} missing Last updated header')
        exit(1)

print('[PASS] All Context files verified and compliant.')
"
```

> [!CAUTION]
> **SAFETY GATE FAILURE**: If any functional module or data artifact has been modified, but the corresponding `Context/` file has NOT been updated, **HALT** immediately and issue an alert:
> `Alert: Context Protocol Synchronization Incomplete. Update Context/<file>.md before marking task complete.`
