# Kent-AI — Gotchas & Known Quirks

> Last updated: 2026-09-26 by Antigravity (Phase 0 scaffolding agent)
> Phase: 0 (complete)

---

## 1. Database Gotchas

### 1.1 Remedy Grades Are Mostly NULL

The `grade` column in `rubric_remedies` is `NULL` for **all 507,179 rows** — no human-reviewed grades exist yet. The `grade_candidate` column (auto-detected from OCR typography analysis) is populated for 458,354 rows but is `NULL` for 48,825 rows.

**Impact**: The DAL resolves grades via `COALESCE(grade, grade_candidate, 1)`, meaning ~48,825 remedies silently default to Grade 1. This is a known approximation. Do not assume grade values are authoritative.

### 1.2 Unresolved Remedies

Some `rubric_remedies` rows have `remedy_id = NULL` — the OCR raw token could not be matched to a known remedy in the `remedies` dictionary. These entries still have `normalized` and `raw_token` populated but `abbreviation` and `full_name` will be `NULL`.

**Impact**: When iterating remedies, always guard for `None` on `abbreviation` and `full_name`. The `normalized` or `raw_token` field is the fallback identifier.

Example unresolved tokens: `alum-p'§`, `atrot!`, `Bar-§`, `CANN-L`, `lac-h` — many are OCR artifacts or abbreviations not in the 8-page remedy dictionary.

### 1.3 OCR Superscripts vs. Grades

Kent's Expanded Edition uses superscript numbers (1–24, 7a) as **bibliography citations**, NOT remedy grades. The editorial preface explicitly warns against confusing them. The extraction pipeline attempted to separate these, but ambiguity remains in `raw_token` values.

### 1.4 FTS5 Content Sync

The `rubric_search` and `page_search` FTS5 virtual tables are `content=` tables (they reference the source table's rowid). If you ever bulk-modify `rubrics` or `pages` (which you should not — this is read-only data), the FTS indexes will be stale. The database is treated as immutable.

---

## 2. Hierarchy Gotchas

### 2.1 Compact Labels Are Not Always Semantic Hierarchy

Kent's printed rubric labels like `midnight, before` are compact notations, not necessarily parent-child relationships. A mechanical parser yields `midnight, before > after`, but this does NOT mean "after" is semantically a child of "midnight, before." The `hierarchy_status` column flags uncertain cases.

See `kent_public_edition/STRUCTURE.md` §"Important post-pass hierarchy qualification" for the full discussion.

### 2.2 Shared Boundary Pages

Eight PDF pages (331, 476, 681, 708, 713, 726, 760, 808) contain rubrics from two different sections. The `page_sections` table handles this many-to-many relationship. Do not assume one page belongs to one section.

### 2.3 Carried Column Headings

At column tops, the printed book repeats the active rubric path as a "carried heading" without leading dashes. These are NOT new rubrics — they are continuations. The parser has already handled this, but if you ever write new parsing code, be aware of this pattern.

---

## 3. Python / Environment Gotchas

### 3.1 Windows `python` Alias

On the dev machine, `python` is the Windows Store alias (fails with "Python was not found"). Use `py -3.12` or the venv's `.venv\Scripts\python.exe` directly.

### 3.2 Line Endings

Git warns about LF → CRLF conversion on Windows. The repo defaults to LF. If you create files programmatically, write them with `\n` not `\r\n`.

### 3.3 Path with Spaces

The project lives at `d:\Research Project\kent-ai` — note the space in "Research Project". Always quote paths in shell commands. Python `Path` handles this natively.

### 3.4 Hardlink vs. Symlink

`data/raw/repertory.sqlite` and `data/raw/kent_public_edition/repertory.sqlite` are hardlinked. Both paths refer to the same inode. The upstream public edition bundle is permanently organized under `data/raw/kent_public_edition/`. There is also a directory junction at `d:\Research Project\Kent` → `d:\Research Project\kent-ai`.

---

## 4. Data Shape Gotchas

### 4.1 `get_mind_rubrics()` Returns ALL Section 1 Rubrics (Not Just Roots)

The function returns all 4,933 rubrics in section_id=1, across all depths (0–5). To get only root-level MIND rubrics, use `get_rubrics(section_id=1, parent_id=-1)`.

### 4.2 Rubric `path` Column vs. Reconstructed Path

Every rubric has a pre-populated `path` column (e.g., `"MIND > ABSENT-MINDED > morning"`). The `get_rubric_path()` function prefers this column and only falls back to recursive traversal if it's empty. The pre-populated path is authoritative.

### 4.3 Section Name Is Part of the Path

The `path` column includes the section name as the first component: `"MIND > FEAR > dark"`, not just `"FEAR > dark"`. This is intentional — it makes paths globally unique across sections.

---

## 5. Test Gotchas

### 5.1 Tests Use the Real Database

Unit tests in `test_kent_db.py` query the actual `repertory.sqlite` file. They are NOT mocked. If the database file is missing or moved, all 13 DB tests will fail with `FileNotFoundError`.

### 5.2 Specific Rubric IDs Are Hardcoded in Tests

Tests reference rubric IDs 1, 2, and 4 by their expected labels (`ABANDONED`, `feels he is`, `ABSENT-MINDED`). These IDs are stable in the digitized edition but would break if the database were regenerated with different IDs.

---

## 6. Case Generation & BIO Tagging Gotchas

### 6.1 LLM Character Offset Drift in JSON Mode

LLMs (including LLaMA 3 8B) frequently return character start/end offsets that are off by 1–3 characters due to leading whitespace, quotes, or tokenization boundaries.
- **Problem**: `narrative[start:end]` does not exactly match `entity["text"]`.
- **Solution**: `BIOTagger.align_entity_offsets()` implements a 4-tier verification ladder:
  1. Exact check at `narrative[start:end]`
  2. Local window search within ±15 characters of `start`
  3. Global exact substring search
  4. Global case-insensitive search
  Always run raw entity outputs through `align_entity_offsets()` before downstream tokenization.

### 6.2 Hyphenated Clinical Terms (e.g. `absent-minded`)

Regex tokenizers that match `\w+` will split hyphenated terms into separate tokens (`['absent', 'minded']`).
- **Convention**: Our standard tokenization regex `r"\w+|[^\w\s]"` splits into `['absent', '-', 'minded']`.
- **BIO implication**: If the whole span `"absent-minded"` is labeled `MENT`, the tokens become `B-MENT`, `I-MENT`, `I-MENT`. This matches BERT/ClinicalBERT WordPiece subword tokenization expectations.

### 6.3 Stratified Splitting on Small Rubric Groups (k=4)

When splitting 4 cases per rubric with an 80/10/10 target:
- Simple per-rubric integer rounding (`round(4 * 0.8) = 3`, `round(4 * 0.1) = 0`) forces either 0 cases into val/test or skews splits to 50/25/25.
- **Solution**: `src.data.splitter.split_cases()` uses global deficit balancing: base quota of $\lfloor k \times 0.8 \rfloor$ goes to Train to guarantee representation, and remaining cases are assigned to the split with the largest remaining deficit relative to global 80/10/10 targets.

### 6.4 Special Tokens in ClinicalBERT Need `-100` Masking

When converting token BIO tags to HuggingFace tokenizer subwords:
- Special tokens (`[CLS]`, `[SEP]`, `[PAD]`) have `offset_mapping == (0, 0)`.
- **Requirement**: They MUST be labeled `-100` (PyTorch `CrossEntropyLoss` ignore index), never `"O"` or `0`, otherwise the model learns to predict entity tags for sentence boundary tokens. Use `BIOTagger.align_with_subwords(..., ignore_index=-100)`.

### 6.5 Autoregressive Prompt Cache & Variation Collapse in LLaMA 3

When generating multiple case variations (e.g., 4 variations) for the same rubric:
- **Problem**: With a static RNG seed (`seed: 42`) and generic prompt, Ollama hits KV-cache / greedy sampling paths, repeating near-identical patient stories (~72.2% pairwise Jaccard overlap).
- **Solution**: 
  1. Condition the user prompt with explicit clinical archetypes (`VARIATION_STYLES`: somatizing, conversational, introverted, acute crisis).
  2. Inject dynamic entropy seeding: `dynamic_seed = self.seed + (case_idx * 137)`.
  This dropped lexical overlap to **13.1%** (86.9% lexical diversity) with 100% BIO slice alignment.

---

## 7. ChromaDB & Vector Store Gotchas

### 7.1 ChromaDB Cosine Distance vs. Similarity
ChromaDB's HNSW index with `"hnsw:space": "cosine"` returns *cosine distance* $d \in [0, 2]$, where $d = 1 - \cos(\theta)$.
- **Gotcha**: A score of `0.0` is an exact match (distance 0), while `1.0` is orthogonal.
- **Conversion**: Always convert distance to similarity using $\text{sim} = \max(0.0, \min(1.0, 1.0 - d))$ before presenting scores or filtering by threshold.

### 7.2 Heavy PyTorch / Transformer Import Penalty
Importing `sentence_transformers` or `torch` takes 1.5–3.0 seconds on Windows and loads heavy native DLLs.
- **Rule**: `RubricEmbedder` uses lazy loading — the model is only loaded when `_get_model()` is called, not on module import. CLI and unit tests should keep mock mode options for rapid verification without cold-start latency.

### 7.3 ChromaDB Batch Size Limits
ChromaDB SQLite backend will fail with "too many SQL variables" if upserting thousands of documents at once.
- **Rule**: Always chunk documents and embeddings into batches (e.g. `batch_size=500`) when calling `collection.upsert()`.

### 7.4 EphemeralClient Collection Isolation in Pytest
`chromadb.EphemeralClient()` creates an in-process in-memory store. If multiple test fixtures or files use the default collection name (`kent_rubrics`), documents added in one test file will persist into subsequent tests within the same pytest session.
- **Rule**: Test fixtures must supply an isolated, unique collection name using `uuid.uuid4().hex[:8]` (e.g. `collection_name=f"test_rubrics_{uuid.uuid4().hex[:8]}"`).

---

_End of file._
