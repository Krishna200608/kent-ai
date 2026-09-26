# Kent-AI — Data Context

> Last updated: 2026-09-26 by Antigravity (Phase 0 scaffolding agent)
> Phase: 0 (complete)

---

## Primary Data Source

| Property | Value |
|---|---|
| File | `data/raw/repertory.sqlite` (and `data/raw/kent_public_edition/repertory.sqlite`) |
| Size | 112 MB (118,095,872 bytes) |
| Format | SQLite 3 with FTS5 virtual tables |
| Access | Read-only via `src.data.kent_db.get_connection()` |
| Schema DDL | `data/raw/kent_public_edition/schema.sql` |
| Upstream Bundle | `data/raw/kent_public_edition/` |

---

## Database Schema

### Core Tables

#### `sections` — 37 rows
Anatomical/symptom chapter divisions of Kent's Repertory.

```sql
CREATE TABLE sections(
    id             INTEGER PRIMARY KEY,
    name           TEXT,        -- e.g., "MIND", "HEAD", "EXTREMITIES"
    printed_start  INTEGER,     -- First printed page number
    printed_end    INTEGER,     -- Last printed page number
    pdf_start      INTEGER,     -- First PDF page (printed + 46)
    pdf_end        INTEGER,     -- Last PDF page
    group_name     TEXT         -- Grouping label (e.g., "URINARY ORGANS")
);
```

#### `rubrics` — 74,513 rows
Individual symptom descriptors organized as a tree.

```sql
CREATE TABLE rubrics(
    id               INTEGER PRIMARY KEY,
    parent_id        INTEGER REFERENCES rubrics(id),  -- NULL = root rubric
    section_id       INTEGER REFERENCES sections(id),
    depth            INTEGER,   -- 0 = root, 1 = child, 2 = grandchild, ...
    label            TEXT,      -- Short display label, e.g., "morning"
    path             TEXT,      -- Full ancestry, e.g., "MIND > ABSENT-MINDED > morning"
    text             TEXT,      -- Extended description (if any)
    start_pdf_page   INTEGER,
    end_pdf_page     INTEGER,
    start_line_id    INTEGER,
    order_index      INTEGER,   -- Sibling sort order
    flags_json       TEXT,
    hierarchy_status TEXT
);
```

#### `remedies` — 679 rows
Master dictionary of homeopathic remedy abbreviations.

```sql
CREATE TABLE remedies(
    id              INTEGER PRIMARY KEY,
    abbreviation    TEXT,       -- e.g., "Acon.", "Nat-m."
    normalized      TEXT,       -- Lowercase key, e.g., "acon", "nat-m"
    full_name       TEXT,       -- e.g., "Aconitum napellus"
    source_pdf_page INTEGER
);
```

#### `rubric_remedies` — 507,179 rows
Many-to-many join linking rubrics to remedies with grade data.

```sql
CREATE TABLE rubric_remedies(
    id                          INTEGER PRIMARY KEY,
    rubric_id                   INTEGER REFERENCES rubrics(id),
    ordinal                     INTEGER,   -- Position within rubric's remedy list
    raw_token                   TEXT,      -- Exact OCR text (may include artifacts)
    remedy_id                   INTEGER REFERENCES remedies(id),  -- NULL if unresolved
    normalized                  TEXT,      -- Cleaned abbreviation
    grade                       INTEGER,   -- Reviewed grade (1/2/3), usually NULL
    grade_candidate             INTEGER,   -- Auto-detected grade (1/2/3 or NULL)
    grade_basis                 TEXT,      -- "bold_caps" | "italic" | "roman" | "unresolved"
    source_refs_json            TEXT,
    confidence                  REAL,
    pdf_page                    INTEGER,
    source_line_id              INTEGER,
    source_provenance_status    TEXT
);
```

> **Grade resolution in kent_db.py**: `COALESCE(grade, grade_candidate, 1)`.
> The `grade` column (human-reviewed) is currently NULL for all 507,179 rows.
> The `grade_candidate` column (auto-detected) is populated for 458,354 rows.
> 48,825 rows have both NULL → default to grade 1.

### Auxiliary Tables

| Table | Rows | Purpose |
|---|---|---|
| `pages` | 1,469 | PDF page metadata, OCR text, confidence |
| `lines` | 137,062 | Individual OCR lines with bounding boxes |
| `cross_references` | 1,923 | "See also" links between rubrics |
| `issues` | 7,510 | Data quality flags (parsing ambiguities) |
| `bibliography` | ~25 | Numbered source citations |
| `remedy_aliases` | varies | Alternative remedy spellings |
| `page_sections` | varies | Many-to-many page↔section (shared boundary pages) |
| `metadata` | varies | Key-value project metadata |

### Virtual Tables & Views

```sql
-- Full-text search indexes (FTS5, prefix-capable)
CREATE VIRTUAL TABLE rubric_search USING fts5(path, text, content='rubrics', content_rowid='id');
CREATE VIRTUAL TABLE page_search   USING fts5(text, content='pages', content_rowid='pdf_page');

-- Convenience views
CREATE VIEW rubric_tree  AS SELECT r.*, s.name AS section_name, p.label AS parent_label ...;
CREATE VIEW review_queue AS SELECT * FROM issues ORDER BY severity, pdf_page;
```

---

## Key Constants

These numbers are verified against the live database and used as assertions in tests.

| Constant | Value | Verification Query |
|---|---|---|
| Total sections | 37 | `SELECT COUNT(*) FROM sections` |
| Total rubrics | 74,513 | `SELECT COUNT(*) FROM rubrics` |
| MIND rubrics (section_id=1) | 4,933 | `SELECT COUNT(*) FROM rubrics WHERE section_id=1` |
| Total remedies | 679 | `SELECT COUNT(*) FROM remedies` |
| Total rubric↔remedy links | 507,179 | `SELECT COUNT(*) FROM rubric_remedies` |
| Largest section (EXTREMITIES) | 17,179 | `SELECT COUNT(*) FROM rubrics WHERE section_id=31` |
| Max rubric depth | 7 | `SELECT MAX(depth) FROM rubrics` |
| PDF page offset | +46 | `pdf_page = printed_page + 46` (confirmed at boundaries) |

---

## Section Breakdown (All 37 Sections)

| ID | Name | Rubrics |
|---|---|---|
| 1 | MIND | 4,933 |
| 2 | VERTIGO | 477 |
| 3 | HEAD | 7,240 |
| 4 | EYE | 1,998 |
| 5 | VISION | 954 |
| 6 | EAR | 2,189 |
| 7 | HEARING | 188 |
| 8 | NOSE | 1,680 |
| 9 | FACE | 2,266 |
| 10 | MOUTH | 1,668 |
| 11 | TEETH | 798 |
| 12 | THROAT | 980 |
| 13 | THROAT-EXTERNAL | 325 |
| 14 | STOMACH | 3,132 |
| 15 | ABDOMEN | 4,095 |
| 16 | RECTUM | 1,415 |
| 17 | STOOL | 283 |
| 18 | BLADDER | 778 |
| 19 | KIDNEYS | 256 |
| 20 | PROSTATE GLAND | 93 |
| 21 | URETHRA | 599 |
| 22 | URINE | 428 |
| 23 | GENITALIA-MALE | 1,130 |
| 24 | GENITALIA-FEMALE | 1,461 |
| 25 | LARYNX AND TRACHEA | 731 |
| 26 | RESPIRATION | 842 |
| 27 | COUGH | 1,555 |
| 28 | EXPECTORATION | 363 |
| 29 | CHEST | 3,830 |
| 30 | BACK | 4,115 |
| 31 | EXTREMITIES | 17,179 |
| 32 | SLEEP | 1,144 |
| 33 | CHILL | 764 |
| 34 | FEVER | 583 |
| 35 | PERSPIRATION | 404 |
| 36 | SKIN | 1,301 |
| 37 | GENERALITIES | 2,336 |

---

## Rubric Depth Distribution

| Depth | Count | Meaning |
|---|---|---|
| 0 | 5,073 | Root rubrics (direct section children) |
| 1 | 22,132 | First-level qualifiers |
| 2 | 25,531 | Second-level qualifiers (largest group) |
| 3 | 15,753 | Third-level |
| 4 | 5,170 | Fourth-level |
| 5 | 783 | Fifth-level |
| 6 | 68 | Sixth-level |
| 7 | 3 | Maximum depth (7 levels deep) |

---

## Remedy Grade System

Kent's Repertory uses a typographic grading system for remedy prominence:

| Grade | Typography | Meaning | `grade_candidate` Count |
|---|---|---|---|
| 3 | **BOLD CAPITALS** | Highest prominence — verified in provings and clinical practice | 313,519 |
| 2 | *Bold Italics* | Moderately verified — confirmed by multiple provers | 113,336 |
| 1 | Roman (plain text) | Clinical observation — occasionally noted | 31,499 |
| NULL | — | Auto-detection failed; `kent_db.py` defaults to 1 | 48,825 |

> **Important**: The `grade` column (human-reviewed) is NULL for every row.
> Only `grade_candidate` (auto-detected from OCR typography) is populated.
> The DAL uses `COALESCE(grade, grade_candidate, 1)` to resolve.

---

## Processed Data Artifacts (Phase 1)

| File | Status | Format | Description |
|---|---|---|---|
| `data/processed/mind_cases.jsonl` | Active | JSONL | Synthetic clinical cases with tokens and BIO tags |
| `data/processed/generation_checkpoint.json` | Active | JSON | Atomic crash-safe checkpoint (completed IDs, counts, timestamps) |
| `data/processed/train.jsonl` | Active | JSONL | 80% stratified training partition |
| `data/processed/val.jsonl` | Active | JSONL | 10% stratified validation partition |
| `data/processed/test.jsonl` | Active | JSONL | 10% stratified test partition |
| `data/embeddings/kent_rubrics/` | Phase 2 | ChromaDB | Dense HNSW index of all 74,513 rubrics |
| `data/models/clinicalbert_homeoNER/` | Phase 3 | HuggingFace | Fine-tuned Bio_ClinicalBERT checkpoint |

---

## Synthetic Case Schema (`SyntheticCase`)

Each line in `mind_cases.jsonl`, `train.jsonl`, `val.jsonl`, and `test.jsonl` is a JSON object with:

```json
{
  "case_id": "case_4_1_a1b2c3",
  "rubric_id": 4,
  "rubric_path": "MIND > ABSENT-MINDED",
  "narrative": "Doctor, I feel terribly absent-minded every morning. My thoughts wander constantly...",
  "entities": [
    {
      "text": "absent-minded",
      "label": "MENT",
      "start": 23,
      "end": 36
    },
    {
      "text": "every morning",
      "label": "TEMP",
      "start": 37,
      "end": 50
    }
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

### Entity Categories & BIO Label Space (15 tags)

| Category | Description | Examples | BIO Tags |
|---|---|---|---|
| `LOC` | Anatomical location / organ | forehead, temples, chest, stomach | `B-LOC`, `I-LOC` |
| `SEN` | Sensation description | throbbing, burning, stitching, dull ache | `B-SEN`, `I-SEN` |
| `MOD_AGG` | Aggravation (worse from) | worse from noise, worse in warm room | `B-MOD_AGG`, `I-MOD_AGG` |
| `MOD_AMEL` | Amelioration (better from) | better lying down, improved by cold air | `B-MOD_AMEL`, `I-MOD_AMEL` |
| `CONC` | Concomitant symptom | with nausea, trembling hands | `B-CONC`, `I-CONC` |
| `TEMP` | Temporal modality | morning, at night, 3 AM, twilight | `B-TEMP`, `I-TEMP` |
| `MENT` | Mental / Emotional state | anxiety, weeping, fear of death, rage | `B-MENT`, `I-MENT` |
| `O` | Outside any entity span | punctuation, stop words, non-symptoms | `O` |

---

## ChromaDB Rubric Vector Store (`data/embeddings/kent_rubrics/`)

Dense vector index constructed in Phase 2 for semantic retrieval over Kent's Repertory rubrics.

| Property | Value |
|---|---|
| Collection Name | `kent_rubrics` |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector Dimension | 384 (unit L2-normalized) |
| Distance Metric | Cosine similarity (`metadata: {"hnsw:space": "cosine"}`) |
| Document Content | Full hierarchical rubric path (e.g. `MIND > ABSENT-MINDED > morning`) |

### Document Metadata Schema

```json
{
  "rubric_id": 4,
  "section_id": 1,
  "section_name": "MIND",
  "depth": 1,
  "path": "MIND > ABSENT-MINDED > morning",
  "label": "morning",
  "remedy_count": 8
}
```

---

_End of file._

