---
name: kent-repertory-inspector
description: Query, validate, and debug Kent's Repertory SQLite database (data/raw/repertory.sqlite) using src/data/kent_db.py data access logic.
triggers:
  - "kent db"
  - "repertory.sqlite"
  - "rubric"
  - "check remedies"
  - "validate mind rubrics"
author: "kent-ai-team"
version: "1.0.0"
---

# Kent Repertory Inspector Skill

## Overview

Kent's Repertory is the foundational clinical corpus of `kent-ai`. It is stored as an immutable SQLite database at `data/raw/repertory.sqlite` (112 MB) containing:
- **37 Sections** (MIND, HEAD, EYE, VISION, THROAT, STOMACH, ABDOMEN, EXTREMITIES, etc.)
- **74,513 Rubrics** (hierarchical clinical symptom tree up to depth 7)
- **679 Remedies** in the master dictionary
- **507,179 Rubric-Remedy Associations** with typography grades

This skill provides an automated inspection, validation, and debugging interface powered by the auxiliary CLI script:
`.agent/skills/kent-repertory-inspector/scripts/query_db.py` and the data access layer `src/data/kent_db.py`.

---

## Command Reference & Usage

Always invoke the inspector script using the project virtual environment Python binary:

```powershell
.venv\Scripts\python.exe .agent/skills/kent-repertory-inspector/scripts/query_db.py [FLAGS]
```

### Supported Flags

| Flag | Purpose | Expected Output / Assertion |
|---|---|---|
| `--stats` | Print complete database statistics (sections, rubrics, remedies, top chapters). | Verifies DB integrity, file size (112.6 MB), and table row counts. |
| `--verify-mind` | Verify that Section 1 (MIND) contains exactly 4,933 rubrics. | Returns `[PASS] OK` if count is exactly 4,933; exits with code 1 if mismatched. |
| `--rubric-id <ID>` | Resolve full hierarchical path and non-null remedy list for a rubric. | Outputs path string (e.g. `HEAD > PAIN > Sun...`) and table of remedies sorted by grade. |
| `--check-null-grades` | Audit `rubric_remedies` for NULL reviewed grades and candidate typography. | Outputs nullity ratios, candidate distribution, and effective resolved grades. |
| `--search "<TEXT>"` | Query rubrics by path and label keywords. | Returns top matching rubrics across sections or within a filtered chapter. |
| `--section-id <ID>` | Filter search to a specific section (e.g., 1 for MIND, 3 for HEAD). | Combined with `--search` to narrow scope. |
| `--db-path <PATH>` | Explicit path override if inspecting an alternate bundle. | Defaults to auto-resolving `data/raw/repertory.sqlite`. |

---

## Operational Workflows

### 1. Database Health Check & Schema Verification
When entering a phase or validating test failures:
```powershell
.venv\Scripts\python.exe .agent/skills/kent-repertory-inspector/scripts/query_db.py --stats
```
Expected output:
- Total Sections: **37**
- Total Rubrics: **74,513**
- MIND Rubrics: **4,933**
- Total Remedies: **679**
- Rubric-Remedy Links: **507,179**

### 2. MIND Section Baseline Gate (Phase 0 / Phase 1)
To ensure the target dataset for synthetic case generation is completely intact:
```powershell
.venv\Scripts\python.exe .agent/skills/kent-repertory-inspector/scripts/query_db.py --verify-mind
```
Safety Check:
- Exits with returncode `0` on success.
- If returncode is non-zero, fail current task and alert user.

### 3. Rubric & Remedy Drill-Down
To inspect the remedies, typography grades, and path of any rubric:
```powershell
# Example: Rubric 4 (ABSENT-MINDED)
.venv\Scripts\python.exe .agent/skills/kent-repertory-inspector/scripts/query_db.py --rubric-id 4

# Example: Rubric 8516 (HEAD > PAIN > TEMPLES > sun, exposure to)
.venv\Scripts\python.exe .agent/skills/kent-repertory-inspector/scripts/query_db.py --rubric-id 8516
```
The output displays:
- Canonical hierarchical path: `SECTION > PARENT > CHILD`
- Table of remedies with normalized names, abbreviations, full Latin names, and grades.

### 4. Remedy Grade Quality Audit
To audit the database for NULL values and OCR candidate typography:
```powershell
.venv\Scripts\python.exe .agent/skills/kent-repertory-inspector/scripts/query_db.py --check-null-grades
```

---

## Remedy Grade Resolution Rules

When interpreting remedies from `rubric_remedies`, adhere strictly to the project DAL logic defined in `src/data/kent_db.py` and `Context/GOTCHAS.md` §1.1:

$$\text{Effective Grade} = \text{COALESCE}(\text{grade}, \text{grade\_candidate}, 1)$$

| Grade | Classical Kentian Typography | Clinical Significance | Count in DB | % of Total |
|---|---|---|---|---|
| **Grade 3** | Bold / ALL CAPS | Keynote, highest clinical prominence and verified curative response | 313,519 | 61.82% |
| **Grade 2** | Italics | Frequently verified symptom | 113,336 | 22.35% |
| **Grade 1** | Roman / Plain text | Observed during homeopathic provings or clinical reports | 80,324 | 15.84% |

> [!WARNING]
> The `grade` column (human-reviewed) is currently NULL for all 507,179 rows. 
> The `grade_candidate` column (auto-detected from OCR) is populated for 458,354 rows.
> Exactly 48,825 rows have both NULL and automatically default to Grade 1.

---

## Formatting Agent Responses

When reporting rubric or remedy inspection results to the user:
1. Always format output using standard GitHub Markdown tables.
2. Present remedies grouped or sorted by descending Grade (Grade 3 $\to$ Grade 2 $\to$ Grade 1).
3. If a remedy is unresolved (`remedy_id = NULL`), explicitly denote it as `(unresolved OCR token: <token>)`.
4. Provide the exact rubric ID and path in monospace backticks.
