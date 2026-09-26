# Independent first-pass structure findings

Source inspected: kent_expanded_repertory.pdf, 1469 scanned pages, image-only, no embedded text or bookmarks. PDF page coordinates 1785 x 2478 in sampled pages. Page references below are one-based PDF pages.

## Contents and pagination

- PDF1 cover: Kent's Repertory of the Homoeopathic Materia Medica Expanded.
- PDF2 publication page (editions/reprints), PDF3 portrait, PDF4 blank.
- PDF5 publishers introduction; PDF6 preface to second edition; PDF7-9 P. Sivaraman preface explaining editorial conventions; PDF10-35 historical introductions, study guide, prior prefaces.
- PDF36 printed xxxviii: bibliography of numbered source additions. Superscripts in the repertory are citations, not grades. Numbered sources 1-24 plus 7a.
- PDF37 printed xxxix: alphabetical and sectionwise contents.
- PDF38 blank.
- PDF39-46 printed XLI-XLVIII: REMEDIES AND THEIR ABBREVIATIONS, A-Z dictionary in two columns of abbreviation/full-name pairs.
- PDF47-1469: repertory printed Arabic pages1-1423. Arithmetic mapping PDF = printed+46 confirmed at beginning, multiple boundaries, sample later pages, and final page. There are37 chapter sections; the contents groups five urinary sections under URINARY ORGANS.
- Exact TOC transcription and ranges are in sections.json. The8 shared boundary pages are in shared_page_boundaries.json. There is no assumption of disjoint page ranges: a shared page's top belongs the previous section and bottom belongs the next.

## Source-defined conventions (PDF7 printed ix; PDF8 printed x)

The editorial preface states that one, two or more leading dashes distinguish sub-rubrics and deeper rubrics. All sub-rubrics use bold Roman type. It describes first, second and third grades using bold CAPITALS, bold Italics with initial capital, and Roman type respectively. This numbering should be retained as source terminology. If a conventional numerical weighting uses upper-case=3, italic=2, regular=1, store that separately and document the conversion; do not silently equate first grade with numeric weight1.

Cross-references in brackets have three scopes: lowercase reference belongs to the same rubric in the same section; initial-capital reference belongs to another rubric in the same section; section name in bold capitals references another section. The text also supplies printed page numbers. References can have multiple targets (see PDF47 ACTIVITY -> Industrious56; Occupation amel69; Busy10).

Remedies are alphabetized by their abbreviations rather than full names (PDF8). The source uses a.m./p.m. and explicitly 12 midnight/12 noon. Do not confuse superscripts1-24/7a with remedy grades. Superscripts may modify a rubric label as well as a remedy.

## Hierarchy and reading order

Normal body reading order: left column from top to bottom, then right column, followed by next page. Maintain an active ancestry stack across columns and pages. A no-dash true root is generally a chapter child. Leading dash count records printed depth/repeated-prefix structure, but it is not proven to be a complete semantic-node grammar: a single line can contain a compact parent term plus qualifier. Remedy continuation lines are indented and attach to the same rubric; rubric descriptions themselves may wrap over several lines before the colon/remedies. A label may contain meaningful commas (e.g. sore, bruised, sensitive to pressure); do not split every comma into an artificial hierarchy level. Conversely, compact labels such as midnight, before may require an implicit midnight group if interpreted semantically. Preserve the source form and distinguish navigation hierarchy from semantically verified hierarchy.

Column-top bold carried headings repeat all or part of the active path with no leading dashes. They are not new root records. Both colon and semicolon endings occur. They may introduce continued remedy text or immediately resume deeper subrubrics. Carried headings can abbreviate the original rubric label. Use root/path context, location, and no inline remedy evidence; do not depend solely on exact equality or punctuation.

Examples:
- PDF47 left ends ABSORBED, buried in thought and its one-dash children. Right starts ABSORBED, buried in thought; then more one-dash children. This is one rubric tree.
- PDF142 left ends MORNING with part of its remedy list. Right starts MORNING: then remedy continuation before one-dash children. These remedies belong to that same MORNING node.
- PDF249 first column PAIN, shooting, forehead has nesting of at least5 leading dashes, including laterality/direction/time.
- PDF250 first column carried PAIN, shooting, temples; describes an active path at depth2. Further down, one-dash sore, bruised, sensitive to pressure starts another PAIN child. Its remedies continue in column2 under shortened PAIN, sore, bruised: before depth2 modifiers.
- PDF1100 starts PAIN, upper arm: plus continued remedies, and right begins PAIN, upper arm; plus depth2 modifiers.
- PDF1469 final section GENERALITIES ends WOUNDS children and WRAPPING up amel.

Shared chapter-boundary pages:331,476,681,708,713,726,760,808. Correct order is top-left, top-right, bottom-left, bottom-right. Large centered chapter heading separates zones. Running headers may already name the new section while upper text still belongs the old one (TEETH PDF476; STOOL PDF681; PROSTATE GLAND PDF713). Header alone is therefore insufficient to classify the whole page. See shared_page_boundaries.json for manual whitespace y cuts.

## Extraction recommendations

1. Preserve a lossless raw OCR layer (page, column/zone, word/line, bounding box, confidence, text), plus source coordinates. Keep all OCR wording alongside any normalized label.
2. Detect scan exterior edges and central column divider per page. It varies: PDF47 divider around56% page width, PDF50 around52%. Naive equal-half clipping cuts text on shifted scans. Neighbor-page bleed on left/right must be excluded.
3. Recover leading dashes from pixels, not solely OCR text; long thin rules are dropped or merged. Use dash length/run counts and label x position, with per-column calibration, and preserve confidence.
4. Build rubric parent pointers and deterministic source-order IDs. Preserve full path, normalized searchable path, children ordering, rubric remedy membership, cross-reference raw text and targets, and citation source numbers.
5. Export SQLite for indexed/random/tree queries, JSONL for streaming interchange, and a small local browser for expandable tree plus full-text/remedy lookup. Each node should link back to source page and bounding area for verification.
6. Grade typography must be flagged uncertain where scan/OCR case/style is ambiguous; a missing grade should be null/unknown, never defaulted as certain. Uppercase/titlecase/lowercase tokens plus style/visual inspection can support classification. Keep raw token spelling and style evidence.
7. Normalize remedy abbreviations against the8-page dictionary but retain unresolved tokens; punctuation/hyphenation can distinguish remedies, and OCR may append bibliography superscripts to abbreviation text.
8. Cross-reference resolution should preserve unresolved/ambiguous references with candidates, not invent targets. Printed page constraints narrow matching; same-rubric/same-chapter scope should be kept.
9. Use the mixed/broken-layout cases above as focused parser validation examples, not merely first-page checks. Tree depth jumps, unexpected roots at column tops, malformed remedies and references are useful review flags.

All review images and scripts are scratch work under this directory. No source file was modified.

## Important post-pass hierarchy qualification

An independent parser audit found PDF51 (printed5): under ANXIETY > night, the depth2 label is `midnight, before`. The right-column carry says `ANXIETY, night, midnight;` and the first child is depth3 `after`. A mechanical row stack yields `midnight, before > after`, which should NOT be asserted as a semantically correct relationship. The printed notation sometimes incorporates repeated/implicit phrase context or compact qualifications, and may have editorial inconsistencies. The preface's exact wording is: "To avoid misalignment of sub- and sub-sub rubrics I have used dashes before them (—) one, two or more as the case is. Thus there is a slight difference in the format from the original work." It does not specify a formal one-dash-per-semantic-node grammar.

For trustworthy extraction, retain printed depth, raw label, and carried heading independently; flag compact-label versus carried-path conflicts for review. A semantic expansion may create an implicit midnight grouping with before/after qualifiers, but requires care: prior same-depth children can inherit the before qualifier. A raw source navigation tree is still useful if explicitly provisional. Do not silently claim every mechanical parent pointer is semantically verified.
