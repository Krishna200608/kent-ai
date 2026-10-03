---
name: domain-modeling
description: >
  Domain modeling and entity relationship design skill for kent-ai.
  Use when defining new data structures, extending the Kent's Repertory
  domain model, designing schemas for generated clinical cases, or
  mapping domain concepts to code entities. Grounds all models in the
  actual homeopathic repertory database schema and the verified BIO label
  system from Context/DATA.md.
---

# Domain Modeling Skill — Kent-AI

## Domain Overview

Kent-AI operates in the intersection of two domains:

1. **Homeopathic Repertory Domain** — Kent's Repertory: a hierarchical
   index of 74,513 rubrics (symptoms) mapped to remedies with degree scores.
2. **Clinical NLP Domain** — clinical case narratives with named entity spans
   annotated using a 15-class BIO label system.

Any new data model must be grounded in the actual database schema (`Context/DATA.md`)
and the verified `SyntheticCase` schema (`Context/DATA.md §Synthetic Case Schema`).

---

## Core Domain Entities (from Context/DATA.md)

### Rubric (SQLite `rubrics` table — 74,513 rows)

```python
# Actual DB columns — do not invent fields
rubric = {
    "id": int,            # Primary key
    "parent_id": int,     # NULL for root rubrics
    "section_id": int,    # References sections.id (1=MIND, 3=HEAD, ...)
    "depth": int,         # 0=root, up to 7
    "label": str,         # Short display label, e.g., "morning"
    "path": str,          # Full ancestry, e.g., "MIND > ABSENT-MINDED > morning"
    "text": str,          # Extended description (may be NULL)
    "order_index": int,
    "hierarchy_status": str,
}
```

### Remedy (SQLite `remedies` table — 679 rows)

```python
remedy = {
    "id": int,
    "abbreviation": str,  # e.g., "Acon.", "Nat-m." — may be NULL for unresolved OCR
    "normalized": str,    # Lowercase key, e.g., "acon", "nat-m"
    "full_name": str,     # e.g., "Aconitum napellus" — may be NULL for unresolved
}
```

### Remedy Grade (from `rubric_remedies` table — 507,179 rows)

Kent's Repertory uses a **3-grade typographic system** (not 4):

| Grade | Typography | Meaning |
|---|---|---|
| 3 | BOLD CAPITALS | Highest prominence — verified in provings and clinical practice |
| 2 | Bold Italics | Moderately verified |
| 1 | Roman (plain text) | Clinical observation only |

> **Important**: The `grade` column (human-reviewed) is NULL for ALL 507,179 rows.
> Only `grade_candidate` (auto-detected OCR) is populated for 458,354 rows.
> The DAL always resolves via `COALESCE(grade, grade_candidate, 1)` — default is 1, not 0.
> Never assume grades are authoritative.

Always guard for `None` on `abbreviation` and `full_name` when iterating rubric remedies
(GOTCHAS.md §1.2 — unresolved OCR tokens).

---

## BIO Label Space (15 classes — from Context/DATA.md)

The project uses **exactly these 15 BIO classes**. Do not add, rename, or invent others.

| Category | Description | BIO Tags |
|---|---|---|
| `LOC` | Anatomical location / organ | `B-LOC`, `I-LOC` |
| `SEN` | Sensation description | `B-SEN`, `I-SEN` |
| `MOD_AGG` | Aggravation (worse from) | `B-MOD_AGG`, `I-MOD_AGG` |
| `MOD_AMEL` | Amelioration (better from) | `B-MOD_AMEL`, `I-MOD_AMEL` |
| `CONC` | Concomitant symptom | `B-CONC`, `I-CONC` |
| `TEMP` | Temporal modality | `B-TEMP`, `I-TEMP` |
| `MENT` | Mental / Emotional state | `B-MENT`, `I-MENT` |
| Outside any span | — | `O` |

**Forbidden labels** (do NOT use): `B-SYM`, `I-SYM`, `B-MOD`, `I-MOD`, `B-REM`, `I-REM`, `B-DUR`, `I-DUR`.

---

## SyntheticCase Schema (from Context/DATA.md)

Each line in `data/processed/mind_cases.jsonl` (and `train.jsonl`, `val.jsonl`, `test.jsonl`):

```json
{
  "case_id": "case_4_1_a1b2c3",
  "rubric_id": 4,
  "rubric_path": "MIND > ABSENT-MINDED",
  "narrative": "Doctor, I feel terribly absent-minded every morning...",
  "entities": [
    { "text": "absent-minded", "label": "MENT", "start": 23, "end": 36 },
    { "text": "every morning", "label": "TEMP", "start": 37, "end": 50 }
  ],
  "tokens": ["Doctor", ",", "I", "feel", "terribly", "absent", "-", "minded", "every", "morning", "."],
  "bio_tags": ["O", "O", "O", "O", "O", "B-MENT", "I-MENT", "I-MENT", "B-TEMP", "I-TEMP", "O"],
  "metadata": {
    "model": "llama3:8b",
    "backend": "ollama",
    "rubric_id": 4,
    "top_remedies": ["Cann-i.", "Lach.", "Nux-v."],
    "case_idx": 1
  }
}
```

Do NOT invent a `ClinicalCase` with different fields. Use this schema.

---

## SymptomProfile (from `src/models/resolver.py`)

The 7-dimension resolver output dataclass.

> **Important**: The Python field names use descriptive snake_case, **not** the
> uppercase BIO domain codes. Do NOT write `profile.LOC`, `profile.SEN`, etc. —
> these are not valid Python attributes.

```python
@dataclass
class SymptomProfile:
    chief_complaint: str = ""
    location:       List[str] = field(default_factory=list)  # LOC dimension
    sensation:      List[str] = field(default_factory=list)  # SEN dimension
    modality_agg:   List[str] = field(default_factory=list)  # MOD_AGG dimension
    modality_amel:  List[str] = field(default_factory=list)  # MOD_AMEL dimension
    concomitant:    List[str] = field(default_factory=list)  # CONC dimension
    temporal:       List[str] = field(default_factory=list)  # TEMP dimension
    mental:         List[str] = field(default_factory=list)  # MENT dimension
    negated:        List[str] = field(default_factory=list)
    raw_entities:   List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]: ...
    def get_search_queries(self) -> List[str]: ...
    # get_search_queries() synthesizes composite ChromaDB query strings
    # e.g. "forehead throbbing worse from sun", "anxiety in morning"
```

### Domain Code → Python Field Mapping

| Domain Code | Python Field | Example values |
|---|---|---|
| `LOC` | `location` | `["right side of head"]` |
| `SEN` | `sensation` | `["throbbing", "burning"]` |
| `MOD_AGG` | `modality_agg` | `["worse in morning"]` |
| `MOD_AMEL` | `modality_amel` | `["better by pressure"]` |
| `CONC` | `concomitant` | `["with nausea"]` |
| `TEMP` | `temporal` | `["at midnight"]` |
| `MENT` | `mental` | `["anxiety", "irritable"]` |

Additional fields (not BIO dimensions):

| Field | Type | Purpose |
|---|---|---|
| `chief_complaint` | `str` | First-sentence summary of the complaint |
| `negated` | `List[str]` | Symptom strings explicitly denied by the patient |
| `raw_entities` | `List[Dict]` | Original entity dicts from NER (`text`, `label`, `start`, `end`) |

---

## Modeling Workflow

### Step 1 — Inspect Existing Entities
Before defining any new entity, check:
- `Context/DATA.md` — database schema and key constants
- `src/data/kent_db.py` — what the DAL already returns
- `src/models/resolver.py` — existing `SymptomProfile`
- `src/pipeline/report_generator.py` — output report schema

### Step 2 — Define New Entities
Only define a new entity if it genuinely does not exist in the above sources.
Use a Python `@dataclass` for new structured types.

### Step 3 — Validate Against Real Data
If the entity is persisted or serialised, validate instances against the
`SyntheticCase` JSON schema in tests.

### Step 4 — Document
Add any new entity to `Context/ARCHITECTURE.md` (Key Module API Summary section).

---

## Key Constants (verified from live database — Context/DATA.md)

| Constant | Value |
|---|---|
| Total sections | 37 |
| Total rubrics | 74,513 |
| MIND rubrics (section_id=1) | 4,933 |
| Total remedies | 679 |
| Grade classes | 3 (1, 2, 3) |
| BIO label classes | 15 |
| ChromaDB embedding dim | 384 |
| ChromaDB distance metric | Cosine (sim = 1 − distance) |
