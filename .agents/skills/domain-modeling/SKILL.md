---
name: domain-modeling
description: >
  Domain modeling and entity relationship design skill for kent-ai.
  Use when defining new data structures, extending the Kent's Repertory
  domain model, designing schemas for generated clinical cases, or
  mapping domain concepts to code entities. Grounds all models in the
  homeopathic repertory and clinical NLP domain.
---

# Domain Modeling Skill — Kent-AI

## Domain Overview

Kent-AI operates in the intersection of two domains:

1. **Homeopathic Repertory Domain** — Kent's Repertory: a hierarchical
   index of symptoms (rubrics) mapped to remedies with degree scores (1–4).
2. **Clinical NLP Domain** — clinical case narratives containing
   named entities (symptoms, body parts, modalities, remedies).

Any new data model must be grounded in both domains.

---

## Core Domain Entities

```
Rubric
├── id: int (SQLite PK)
├── chapter: str          # e.g., "MIND", "HEAD"
├── section: str          # sub-chapter
├── rubric_text: str      # the symptom description
└── remedies: List[RemedyScore]

RemedyScore
├── remedy_name: str      # e.g., "Sulphur"
└── degree: int           # 1 (minor) to 4 (major)

ClinicalCase
├── case_id: str          # UUID
├── case_text: str        # free-text narrative
├── bio_tokens: List[BIOToken]
├── dimensions: CaseDimensions
└── retrieved_rubrics: List[RubricMatch]

BIOToken
├── token: str
├── label: str            # "B-SYM", "I-SYM", "B-MOD", "O", etc.
└── confidence: float

CaseDimensions          # 7 required dimensions
├── chief_complaint: str
├── onset_duration: str
├── location: str
├── modalities: str       # worse/better factors
├── concomitants: str
├── mental_generals: str
└── physical_generals: str

RubricMatch
├── rubric: Rubric
└── score: float          # cosine similarity from ChromaDB
```

---

## Modeling Workflow

### Step 1 — Identify Entities and Relationships
List all nouns in the feature description. Each noun is a candidate entity.
Draw the relationship: 1:1, 1:N, N:M.

### Step 2 — Map to Existing Code
Check if an entity already exists:
- SQLite schema → `data/raw/repertory.sqlite` (use `kent-repertory-inspector`)
- Python dataclass/dict → `src/data/`, `src/pipeline/`
- JSON schema → `data/schemas/`

### Step 3 — Define the Schema

For any new entity that is persisted or serialised, write a JSON Schema:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "<EntityName>",
  "type": "object",
  "required": ["field1", "field2"],
  "properties": {
    "field1": { "type": "string", "description": "..." },
    "field2": { "type": "integer", "minimum": 1, "maximum": 4 }
  }
}
```

Save to: `data/schemas/<entity_name>.schema.json`

### Step 4 — Write a Python Dataclass

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class <EntityName>:
    """
    <One-line description of the entity>.
    
    Attributes:
        field1: <description>
        field2: <description>
    """
    field1: str
    field2: int
```

Place in the appropriate `src/` module per the architecture.

### Step 5 — Validate
- Validate all generated instances against the JSON schema in tests.
- Ensure `ClinicalCase.dimensions` covers all 7 required dimensions.

---

## Modeling Rules

- All `case_id` values are UUIDs — use `uuid.uuid4()`.
- `degree` scores are always integers in [1, 4].
- BIO labels follow the scheme: `B-<TYPE>`, `I-<TYPE>`, `O`
  where `<TYPE>` ∈ {`SYM`, `LOC`, `MOD`, `REM`, `DUR`}.
- `CaseDimensions` must always have all 7 fields populated (no None).
- Any new entity must have a corresponding entry in `Context/ARCHITECTURE.md`.
