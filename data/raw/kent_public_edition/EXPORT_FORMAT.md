# Portable export format

All files use UTF-8 and preserve OCR-derived text. IDs are integers shared with
`repertory.sqlite`; `null` means absent or unresolved. Page numbers starting at 1
refer to PDF pages. Printed page labels are separate strings and may be null.
The SQLite database is the primary dataset; these are convenient derivative views.

- **rubrics.jsonl.gz**: gzip-compressed JSON Lines, one rubric per line, ordered
  by rubric ID. Includes the SQLite rubric fields (with `flags_json` decoded into
  `flags`), `parent_id`, ordered `child_ids`, remedy membership records,
  cross-references, recorded rubric issues, and provenance. `provenance.line_ids`
  links to source OCR lines in the database. `order_index` preserves book order.
- **pages.jsonl.gz**: one page per line in PDF order; page type, section ID,
  OCR confidence, text, flags, and `section_regions` (section ID, name, and
  `whole`/`top`/`bottom` region). OCR bounding boxes and word geometry are omitted.
  Pages 1–2 contain flagged manual transcriptions; their original machine OCR
  remains in `raw_ocr.jsonl.gz`.
  A shared page's `section_id` is not sufficient to assign every line on that page;
  use each rubric's section ID and the source scan.
- **tree.json**: compact nested navigation tree. Root `children` contains sections
  or groups; groups contain sections, sections contain root rubrics, and rubrics
  contain subrubrics. Each child has a `type` of `group`, `section`, or `rubric`.
  No bulk rubric text or remedy arrays are repeated in this tree.
- **remedies.json**: remedy directory as an array with ID, abbreviation,
  normalized lookup key, full name, and source PDF page.
- **remedy_aliases.json**: object keyed by lookup alias, with `remedy_id`,
  `status`, and `note` preserved from the alias directory. This is empty when
  an older database has no alias table; an alias is not a reviewed OCR correction.
- **export_manifest.json**: export counts, completeness flag, grading policy,
  file sizes, and SHA-256 hashes. `coverage_complete` checks page count only; it
  does not assert that OCR, hierarchy, remedy identification, or grades are correct.

Remedy occurrences retain `raw_token`, `normalized`, nullable `remedy_id`,
`grade`, `grade_candidate`, `grade_basis`, `confidence`, and source page.
`source_line_id` and `source_provenance_status` preserve line-level provenance;
consult the status before treating a line assignment as exact.
`source_refs_json` is decoded into `source_refs`. Joined `abbreviation` and
`full_name` are null when a token did not match the extracted remedy directory.
Candidates and unresolved tokens must not be treated as verified remedy grades.
The source ordinal, when inferred, is 1 = capitals, 2 = initial-capital/italic
candidate, 3 = lowercase/Roman candidate; these are not numeric treatment scores.

Cross-references preserve their raw text and resolution status. A null
`target_rubric_id` means the reference was not resolved to a rubric.

Read an export in Python without external packages:

```python
import gzip, json

with gzip.open("rubrics.jsonl.gz", "rt", encoding="utf-8") as source:
    for rubric in map(json.loads, source):
        if rubric["section_id"] == 1:
            print(rubric["id"], rubric["path"], rubric["child_ids"])

with open("tree.json", encoding="utf-8") as source:
    hierarchy = json.load(source)
```

For direct random access or search, use SQLite, `query.py`, or the local reader.
JSON Lines is intended for streaming/import; the tree is intended for navigation.
