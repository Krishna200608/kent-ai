# Kent repertory: searchable digital edition

This package digitizes the supplied **Kent's Repertory of the Homoeopathic Materia Medica, Expanded**. The principal data file is `repertory.sqlite`: a portable SQLite database with parent–child rubric relationships, full-text search, remedy occurrences, cross-references, and source-page provenance.

## Open it

On Windows, double-click **START_VIEWER.bat**. It opens a local browser. Python 3.10 or newer is the only viewer dependency; no packages or accounts are required.

Choose a section and expand its rubrics, search for words in a full rubric path, or look up a remedy. A rubric detail shows its own remedies and its children. **Source PDF** opens the original scanned page. The scanned PDF is not included. Supply your own copy with the --source option below to enable scan links. Without it, all data browsing and page transcription search still work.

Run terminal commands from this package's folder. To launch manually:

```powershell
python viewer.py
```

To connect your source PDF:

```powershell
python viewer.py --source "C:\path\to\kent_expanded_repertory.pdf"
```

The browser and database work locally. The viewer binds only to `127.0.0.1` and opens the database read-only. Keep its terminal window open while reading; press Ctrl+C in that window to stop the viewer.

## What the hierarchy means

The book has 37 sections. The contents also groups Bladder, Kidneys, Prostate Gland, Urethra, and Urine under **Urinary Organs**. A rubric without a leading dash is a section's root rubric. Each added printed dash increases its depth by one. Commas within a rubric label do not create extra levels.

For example:

```text
MIND
  ABSORBED, buried in thought
    morning
    evening
```

`rubrics.parent_id` identifies the immediate inferred parent. `rubrics.path` provides a readable path for searching. `order_index` preserves source order. A rubric's remedy list is its own printed list; remedies are not automatically inherited from parents or children.

Some compact printed labels imply a grouping that is not printed as a separate rubric. When a carried heading and the following qualifier provide specific evidence, an empty context node is marked `inferred_context` and flagged for review. Other ambiguous relationships retain their printed depth and a review flag. No remedies are invented for context nodes.

Repertory printed pages 1–1423 correspond to PDF pages 47–1469. Eight pages contain the end of one section and the start of another; their reading order and section assignments are handled by region. Details are in `STRUCTURE.md`.

## Files

| File | Purpose |
| --- | --- |
| `repertory.sqlite` | Main indexed database; recommended for applications and analysis |
| `tree.json` | Compact nested hierarchy, including the Urinary Organs group |
| `rubrics.jsonl.gz` | Streaming rubric records with relationships, remedy occurrences, references, and provenance |
| `pages.jsonl.gz` | Every PDF page's searchable transcription and metadata, including manual cover/publication-page text |
| `raw_ocr.jsonl.gz` | Original machine OCR lines, words, confidence, coordinates, and rotation mappings |
| `remedies.json` | Database remedy directory export |
| `remedy_aliases.json` | Alias lookup map with remedy IDs, status, and notes |
| `remedy_directory.json` | Visually reviewed directory transcription, raw readings, aliases, and source notes |
| `book_ocr.txt` | Entire book's OCR text with explicit page separators |
| `book_text.txt` | Searchable page text, including manual cover/publication-page transcriptions |
| `manifest.json`, `quality_report.json` | Coverage, extraction methods, checks, and limitations |
| `export_manifest.json` | Interchange export counts, page coverage, sizes, and SHA-256 hashes |
| `review_queue.jsonl.gz` | Detected issues with rubric paths and source-page references |
| `schema.sql`, `EXPORT_FORMAT.md` | Database and interchange format documentation |
| `viewer.py`, `query.py`, `START_VIEWER.bat` | Local browser and JSON command-line access |

`.jsonl.gz` files contain one JSON object per line, compressed with gzip. Python reads them directly with `gzip.open(path, 'rt', encoding='utf-8')`.

## Accuracy and review status

This is a **machine OCR edition with an inferred rubric hierarchy**, not a fully proofread transcription. The complete source is scanned; it has no embedded text. OCR can confuse small remedy abbreviations, punctuation, case, superscript citations, and hierarchy dashes. The database preserves raw text and source links rather than silently discarding unfamiliar readings. The review queue flags detectable structural and text problems; absence of a flag does not establish correctness.

The remedy directory, bibliography, cover, and publication page received separate visual review. Unreadable publication details remain marked `[illegible]`. Body remedy matches use lowercase abbreviations, remove surrounding punctuation and apparent citation suffixes, and preserve internal hyphens. Printed aliases are recognized; an inferred correction to a directory typo remains separate in `remedy_aliases`. Unmatched readings remain in `rubric_remedies` with `remedy_id = NULL`.

**Grades:** the preface calls bold CAPITALS the first grade, bold initial-capital italics the second, and Roman type the third. `grade_candidate` follows that source terminology using OCR case only: **1 capitals, 2 initial capital, 3 lowercase**. It does not establish the actual font style. `grade` remains NULL unless separately verified. These numbers are not conventional repertorization weights and should not be treated as confirmed scoring values.

**Superscripts:** numbers above rubrics or remedies cite the book's bibliography; they are not grades. `source_refs_json` contains unverified numeric OCR candidates. The raw word images' locations and original pages are the evidence for checking them.

**Cross-references:** raw reference text is retained. A parsed destination page is an OCR-derived candidate; ambiguous expressions remain unresolved. Cross-reference targets are not replaced with guessed rubric IDs.

## Query from Python

```python
import sqlite3

db = sqlite3.connect('repertory.sqlite')
db.row_factory = sqlite3.Row

# Search complete rubric paths and their own text.
rows = db.execute('''
    SELECT r.id, r.path, r.start_pdf_page
    FROM rubric_search f JOIN rubrics r ON r.id = f.rowid
    WHERE rubric_search MATCH ? LIMIT 25
''', ('"anxiety" AND "night"',)).fetchall()

# Retrieve immediate children using a returned rubric ID.
children = db.execute('''
    SELECT id, label, path FROM rubrics
    WHERE parent_id = ? ORDER BY order_index
''', (rows[0]['id'],)).fetchall() if rows else []

# Find occurrences of a normalized remedy abbreviation.
occurrences = db.execute('''
    SELECT r.path, rr.raw_token, rr.grade_candidate, rr.pdf_page
    FROM rubric_remedies rr JOIN rubrics r ON r.id = rr.rubric_id
    WHERE rr.normalized = ? ORDER BY r.order_index
''', ('sulph',)).fetchall()
```

Command-line examples (JSON output):

```powershell
python query.py stats
python query.py sections
python query.py children --section 1
python query.py node 16
python query.py children --parent 16
python query.py search "anxiety night"
python query.py search "preface" --scope pages
python query.py remedy "sulph" --exact
python query.py page 51
```

Inspect `quality_report.json` before relying on individual transcriptions. Each source page remains accessible for correction or a subsequent proofreading pass.

## Public release

The repository is https://github.com/su4532/kent-repertory-explorer. This copy omits personal filesystem paths and local verification logs. Its SQLite database has been compacted after sanitation. The original source PDF is not distributed. Source publication notices remain in the transcriptions; see the repository NOTICE.
