# Kent-AI — Gotchas & Known Quirks

> Last updated: 2026-11-06 by Antigravity
> Phase: Complete through Phase 22 (Master Repository Audit & Stabilization; 200 Unit, Integration & Smoke Tests Passing across 23 Test Modules, 0 Errors)

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

### 3.5 Python 3.12 Escape Sequence Enforcement

In Python 3.12+, unescaped backslashes in standard string literals (e.g., `\%`, `\g`, `\l` in Markdown/LaTeX reports) emit `SyntaxWarning: invalid escape sequence` and will become hard syntax errors in future Python releases.
- **Solution**: Always escape LaTeX math symbols with double backslashes (e.g. `$\\ge$`, `\\%`) or use raw strings (`rf"""..."""`).

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

### 6.6 Rare Variation Failures in LLaMA 3 Generation & Gap-Filling

In large-scale generation (>15,000 cases), ~0.05% of variations encounter one of three failure modes:
1. **JSON Syntax Malformation**: LLaMA 3 emits unescaped double quotes inside freeform narrative text or hits `max_tokens` mid-string, causing `json.JSONDecodeError` (`Expecting ',' delimiter`).
2. **Entity Schema Drift**: LLaMA 3 occasionally emits a list of plain strings (`"entities": ["anger", "distress"]`) instead of dictionaries, triggering `'str' object has no attribute 'get'` in `BIOTagger.align_entity_offsets()`.
3. **Transient Server Errors**: Intermittent Ollama daemon hiccups (`HTTP Error 500: Internal Server Error`).

**Solution**:
- The main pipeline isolates individual variation errors without crashing, continuing progress.
- Post-generation, run [`scripts/backfill_missing_cases.py`](file:///home/narya/kent-ai/scripts/backfill_missing_cases.py) to audit the corpus, detect any missing `(rubric_id, case_idx)` tuples, generate them with 3-attempt retry backoff, and automatically re-partition the dataset splits.

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

## 8. Runtime & Dashboard Deprecation Gotchas

### 8.1 Streamlit 1.64 `use_container_width` Deprecation
In Streamlit 1.64+, passing `use_container_width=True` to `st.button`, `st.popover`, `st.download_button`, `st.dataframe`, and `st.plotly_chart` emits a runtime deprecation warning:
`Please replace 'use_container_width' with 'width'... use width='stretch'`.
- **Root Cause**: Streamlit modernized its layout engine with a unified `width: "content" | "stretch" | int` parameter.
- **Verified Workaround**: Always use `width="stretch"` across all buttons, popovers, download widgets, dataframes, and charts in `src/dashboard/`.

### 8.2 SeqEval `UndefinedMetricWarning` on Empty Entity Classes
When computing evaluation metrics on datasets or mock batches where certain entity classes have zero predicted samples, `seqeval.metrics` emits:
`UndefinedMetricWarning: Precision is ill-defined and being set to 0.0 due to no predicted samples. Use zero_division parameter to control this behavior.`
- **Root Cause**: Division by zero when precision denominator ($TP + FP = 0$) is encountered for rare classes.
- **Verified Workaround**: Always pass `zero_division=0` to `seqeval.metrics.f1_score`, `precision_score`, `recall_score`, and `classification_report` in `scripts/evaluate.py` and `src/models/trainer.py`.

### 8.3 Streamlit Hot Reload & Module Dependency Desynchronization
Streamlit's internal runner keeps `sys.modules` alive across browser re-runs. If child modules (e.g. `chat_viewer.py`) are dynamically reloaded via `importlib.reload()` before their parent dependencies (`dialogue_manager.py`), child modules can bind to stale class definitions, triggering `AttributeError: type object 'DialogueManager' has no attribute '...'`.
- **Root Cause**: Non-topological module reload order in `src/dashboard/app.py`.
- **Verified Workaround**: Reload dependencies in strict topological order (`src.config` $\rightarrow$ `src.chatbot.prompts` $\rightarrow$ `src.chatbot.state_machine` $\rightarrow$ `src.chatbot.dialogue_manager` $\rightarrow$ `src.dashboard.styles` $\rightarrow$ `src.dashboard.components.*`). Additionally, provide defensive `getattr()` fallback helpers in child components.

### 8.4 Sidebar Collapse Right-Side Void & Viewport Width
When collapsing the sidebar in Streamlit, an empty black void appeared on the right side of the screen; the main content container remained capped as if the sidebar were still occupying horizontal space.
- **Root Cause**: Direct CSS had an unconditional `min-width: 280px !important;` rule on `section[data-testid="stSidebar"]`. When collapsed, Streamlit sets `aria-expanded="false"`, but the CSS forced the element to retain a 280px minimum width layout footprint, squeezing `.stMain` into `calc(100vw - 280px)`.
- **Verified Workaround**: In `src/dashboard/styles.css`, scope `min-width: 280px !important;` strictly to `section[data-testid="stSidebar"][aria-expanded="true"]`. For `[aria-expanded="false"]`, enforce `min-width: 0 !important; width: 0 !important; margin: 0 !important; padding: 0 !important; transform: translateX(-100%) !important;` and allow `.stMain` and `[data-testid="stMainBlockContainer"]` to expand to `width: 100% !important; max-width: 100% !important;`.

### 8.5 Streamlit Page Scroll Locking (`overflow: hidden`)
The consultation dashboard unexpectedly became unscrollable past ~900px, cutting off the Totality Matrix, Review step, and Repertorization report tables.
- **Root Cause**: An over-aggressive CSS rule placed `overflow: hidden !important;` on `.stMain` and `[data-testid="stAppViewContainer"]` to prevent double scrollbars.
- **Verified Workaround**: Set `overflow-y: auto !important; overflow-x: hidden !important;` with smooth scrolling behavior on `.stMain`. Scroll confinement should only be applied to internal sub-containers (e.g. the 450px chat scroll area).

### 8.6 `QUICK_REPLIES:` Control Tag Leaking into Streaming Chat
LLaMA 3 occasionally produced assistant responses containing raw control text: `QUICK_REPLIES: Worst after exercise, Better when sitting`, while the suggested response pills remained stale.
- **Root Cause**: `visible_only` and `_parse_and_strip_quick_replies` in `dialogue_manager.py` strictly expected bracketed JSON arrays (e.g. `[QUICK_REPLIES: ["..."]]`). When LLaMA 3 emitted plain comma-separated text or unbracketed lines, `visible_only` failed to detect the control boundary, streaming raw text into the UI, and the parser discarded the suggestions.
- **Verified Workaround**:
  1. In `visible_only`, implement regex lookahead and prefix boundary buffering to detect and halt immediately on `QUICK_REPLIES`, `SLOT_UPDATE`, or bracket markers across chunk boundaries.
  2. In `_parse_and_strip_quick_replies`, parse bracketed JSON, plain comma-separated strings, and markdown bullet lists into clean patient chips.
  3. In `clean_message_text` and `_safe_clean_bot_text`, strip any unbracketed `QUICK_REPLIES:.*$` and `SLOT_UPDATE:.*$` from current and historic turns.

### 8.7 Streamlit Submodule Caching in `sys.modules`
Editing submodules under `src/dashboard/components/` or `src/chatbot/` did not take effect in an active Streamlit server session, leaving old bytecode running in memory until the server process was terminated.
- **Root Cause**: Streamlit's file watcher re-executes `app.py` on save, but standard Python `import` returns cached modules from `sys.modules`.
- **Verified Workaround**: In `src/dashboard/app.py`, wrap submodules with explicit `importlib.reload()`:
  ```python
  import src.chatbot.dialogue_manager as _dm_mod
  importlib.reload(_dm_mod)
  import src.dashboard.components.chat_viewer as _cv_mod
  importlib.reload(_cv_mod)
  ```

### 8.8 Immediate Rendering of Thinking Skeleton Before Synchronous LLM Calls
The assistant chat bubble appeared completely blank with no loading indicator while Kent-AI was generating a response.
- **Root Cause**: `dm.prepare_turn()` executed heavy multi-second slot extraction (Tier 3 LLM calls) synchronously *before* entering `with scroll_area:` and mounting the assistant message container.
- **Verified Workaround**: Mount `thinking_box.markdown(skeleton_html)` inside `with st.chat_message("assistant"):` *prior* to running `dm.prepare_turn()` and `dm.stream_reply()`. The shimmering bars animate during the entire reflection window and clear the exact millisecond the first visible chunk is yielded.

### 8.9 Streamlit Widget State Mutation in Callbacks Only
Attempting to update an `st.text_area` widget value via `st.session_state["paste_text"] = new_val` during the main script pass fails with `StreamlitAPIException` or is silently overwritten by the widget's previous frontend state.
- **Root Cause**: Streamlit locks widget keys during script execution. Once a widget has been instantiated, direct script assignment to its session_state key cannot override the frontend widget instance.
- **Verified Workaround**: Mutate widget state strictly inside an `on_change` callback (e.g. `_on_example_pill_change` on `st.pills`). Callbacks run before widget instantiation, allowing clean pre-render state mutation.

### 8.10 Streamlit Forms (`st.form`) & Keyboard Submission
Using an un-nested `st.text_area` triggers full-page reruns on every blur event, causing laggy typing in long narratives.
- **Root Cause**: Individual Streamlit inputs without a form boundary communicate back to the server on every value change.
- **Verified Workaround**: Wrap narrative intake inside `with st.form("paste_intake"):` and `st.form_submit_button("Extract & review")`. This enables standard Ctrl/Cmd+Enter keyboard submission and defers all execution until explicit form submission.

### 8.11 Idempotent SQLite Column Migration Pattern
Adding new columns like `extraction_meta_json TEXT` to `clinical_cases` in SQLite without dropping or recreating tables.
- **Root Cause**: SQLite `CREATE TABLE IF NOT EXISTS` ignores schema evolution when the table already exists.
- **Verified Workaround**: Query `PRAGMA table_info(clinical_cases)` in `init_case_db(db_path)` to inspect existing column names, and execute `ALTER TABLE clinical_cases ADD COLUMN extraction_meta_json TEXT` conditionally. Fallback gracefully in `get_case` with `json.loads(row["extraction_meta_json"] or "{}")`.

### 8.12 `st.segmented_control` with `key` and `default`
Passing both `default=...` and specifying a `key` whose value already exists in `st.session_state` logs a Streamlit warning: `The widget with key "intake_mode_select" was created with a default value but also had its value set via the Session State API.`
- **Root Cause**: Streamlit elements disallow specifying an initial `default` argument if the key is already populated in session state.
- **Verified Workaround**: Ensure `st.session_state[key]` is set if missing or invalid, and omit the `default` parameter entirely from `st.segmented_control`.

### 8.13 `ClinicalCase.is_blank` vs. Seeded Initial Assistant Greeting
When starting or resuming a consultation, `DialogueManager` seeds an assistant greeting (`dm.history = [greeting]`). If `c.transcript` is populated from this alone, `case.is_blank` returns `False`, breaking draft management and AppTest smoke assertions.
- **Root Cause**: `is_blank` checked `bool(self.transcript and self.transcript.strip())`.
- **Verified Workaround**: Check `has_user_turns = any(t.get("role") == "user" for t in self.dialogue_history)`. If no patient/practitioner turns exist yet, the consultation remains blank and `c.transcript` is empty.

### 8.14 Separation of UI Actions from Genuine Chat Replies
In the `DONE` state, displaying UI navigation commands (like `"Proceed to Review →"`) in suggestion chips leaked them into user messages if clicked, requiring substring routing hacks like `"proceed to review" in input.lower()`.
- **Root Cause**: Mixing UI workflow buttons with conversational suggestions.
- **Verified Workaround**: Provide typed terminal action options via `dm.get_action_options()` (`continue_review`, `add_detail`, `start_new`), rendered as real Streamlit buttons in the docked action bar. Suggestion chips in `DONE` state strictly contain genuine conversational replies (`"Everything looks accurate"`, etc.).

### 8.15 Real-Time Daemon Polling via `@st.fragment(run_every=...)` & Bare Test Context
When rendering dynamic hardware/daemon status indicators (e.g. Ollama online/offline badge) that must auto-update without page reloads, using `@st.fragment(run_every="2s")` allows isolated WebSocket polling every 2 seconds without disrupting chat inputs or stepper navigation.
- **Gotcha 1 (Sticky Failure State)**: If a chat turn fails while Ollama is offline, `dm.last_call_failed = True` persists even when Ollama is started in another terminal. The polling fragment must explicitly reset `dm.last_call_failed = False` whenever `check_ollama_online()` returns `True`.
- **Gotcha 2 (Cache Duration)**: Caching ping functions with long TTLs (e.g. 10s) delays badge responsiveness. Reduce TTL to 2s to align with polling intervals.
- **Gotcha 3 (Testing Fragment Functions in Unit Tests)**: Streamlit's `@st.fragment` decorator returns `None` immediately if `get_script_run_ctx() is None` (bare pytest execution without an active script runner). When writing unit tests for a fragment function outside `AppTest`, invoke `getattr(func, "__wrapped__", func)(*args)` to execute the underlying logic directly.

### 8.16 Streamlit `st.columns()` Integer Count Requirement in Test Mocks
When writing tests that mock Streamlit layout containers via `st.columns = lambda n: ...`, passing keyword arguments like `vertical_alignment="center"` or variable column proportion lists causes `TypeError: lambda() got an unexpected keyword argument` in the test runner.
- **Root Cause**: Simplistic test mocks only accept a single integer count argument (`n: int`).
- **Verified Workaround**: Inside component rendering functions (e.g. `render_rubric_card`), invoke `st.columns(n)` using plain integer counts without extra kwargs unless guarded or standardized across test harness fixtures.

### 8.17 ASCII-Only Character Requirement for `st.toast` Notifications
Calling `st.toast("Ollama Online · 12ms")` triggers assertion failure in `test_source_guards_no_emoji_in_toasts_and_no_x_buttons` during CI/CD audit passes.
- **Root Cause**: The AST guard enforces that all `st.toast(...)` strings contain strictly ASCII characters (`ord(c) < 128`), treating Unicode interpuncts (`·`), arrows (`→`), and non-breaking spaces as potential emoji or unrendered symbol defects.
- **Verified Workaround**: Strictly use ASCII hyphens (`-`) or ASCII arrows (`->`) in all toast messages (e.g. `st.toast("Ollama Online - 12ms")`).

### 8.18 PyMuPDF / Fitz Deprecation Migration
Referencing `import fitz` emits a `FutureWarning: The fitz API is deprecated and will be removed in future. Use import pymupdf instead.`
- **Root Cause**: Upstream PyMuPDF 1.24+ deprecated the legacy C-extension `fitz` module namespace in favor of standard `pymupdf`.
- **Verified Workaround**: Replace `import fitz` with `import pymupdf as fitz` or `import pymupdf` across all PDF exporters and verification tests.

### 8.19 Trailing Dot Formatting in Kentian Remedy Abbreviations
Querying remedy keynotes by abbreviation in modal dialogs (`show_remedy_dialog`) fails to resolve certain remedies when passing raw unpunctuated names (e.g. searching for `"Lach"` fails because the database stores `"Lach."`).
- **Root Cause**: Kent's Repertory stores abbreviation strings with trailing periods (e.g. `Acon.`, `Lach.`, `Bell.`, `Sulph.`), but clinical text and user inputs frequently omit the dot.
- **Verified Workaround**: In `get_remedy_by_abbreviation` and `show_remedy_dialog`, execute a multi-candidate match query checking: 1) exact abbreviation, 2) abbreviation with dot appended, 3) abbreviation with dot stripped, and 4) `LOWER(normalized) = LOWER(?)`.

### 8.20 Fragment Runs Flip `data-test-script-state="running"` (Header Polling Gotcha)
When using `@st.fragment(run_every="2s")` to poll Ollama status in the top bar, Streamlit updates the root attribute `data-test-script-state="running"` every 2 seconds.
- **Root Cause**: Fragment runs execute in the same script runner context and toggle DOM script state attributes during re-execution. Keying global busy overlays or progress bars on `data-test-script-state="running"` alone causes periodic flashing even when the app is completely idle.
- **Verified Workaround**: Guard global loading indicators using user interaction tracking in `busy.js`. Record `lastInput = performance.now()` on `pointerdown` and `keydown` (Enter/Tab/Space), and only activate the global indicator if the script state transition occurred within a short window (`1500ms`) of a real user action.

### 8.21 Orphan Tooltips Following Dynamic Streamlit DOM Pruning
When buttons, icons, or popover triggers with `help="..."` are re-rendered or removed during Streamlit reruns, React may prune the trigger element while leaving the floating tooltip (`[data-testid="stTooltipContent"]`) mounted in the portal DOM.
- **Root Cause**: Tooltip portals are rendered outside the element container. When the trigger is unmounted during state transitions, the tooltip element can become orphaned and permanently stuck on screen.
- **Verified Workaround**: Never attach `help="..."` to icon-only buttons or popover triggers (`•••`, `✎`). Use explicit labels or keyboard-accessible `data-tip` patterns. In `busy.js`, run a periodic sweep (`sweepTooltips()`) checking whether the tooltip host has a corresponding `aria-describedby` trigger in the document; if not, apply `data-kent-orphan="true"` (`display: none !important`).

### 8.22 Form Submit Buttons Use `kind="primaryFormSubmit"` Selector
Form submission buttons rendered via `st.form_submit_button(type="primary")` do NOT match CSS rules targeting `button[kind="primary"]`.
- **Root Cause**: Streamlit assigns `kind="primaryFormSubmit"` to form submission buttons. Generic `button[kind="primary"]` selectors fail to style submit buttons, causing contrast and color inconsistencies (e.g. illegible black text on default white buttons).
- **Verified Workaround**: Target buttons using `button[data-testid^="stBaseButton-primary"]` and `button[data-testid^="stBaseButton-secondary"]` across all stylesheets. This matches both standard and form-submit button variants reliably.

### 8.23 Lazy Tabs and the `main_tabs` Callback Rule
Attempting to change active tabs programmatically by writing `st.session_state.main_tabs = "Case Workspace"` inside the main script body after `st.tabs` has already rendered fails to switch tabs or raises a Streamlit key mutation error.
- **Root Cause**: Streamlit widget values cannot be modified during the same execution run after the widget has already been instantiated.
- **Verified Workaround**: Place navigation state mutations strictly inside button `on_click` callbacks (e.g. `st.button("Resume", on_click=_load_and_resume_case, args=(cid,))`). Streamlit executes widget callbacks before the script runs, allowing `st.session_state.main_tabs = "Case Workspace"` to be set before `st.tabs(..., key="main_tabs")` is evaluated.

### 8.24 Python Property `AttributeError` Forwarding to `__getattr__`
When evaluating a `@property` (such as `case.section_id`), if any code inside the property getter raises an `AttributeError` (e.g. calling `self.scope_chapter.upper()` when `scope_chapter` is an integer `1`), Python's property descriptor intercepts the `AttributeError`, assumes the property itself does not exist, and falls back to invoking `__getattr__("section_id")`.
- **Root Cause**: `self.scope_chapter` was set as an integer `1` (in `create_demo_case()` or `settings.py`) or stored as string `'1'`, causing `1.upper()` to throw `AttributeError: 'int' object has no attribute 'upper'`. Python caught this and forwarded to `__getattr__("section_id")`, producing the misleading error `AttributeError: 'ClinicalCase' object has no attribute 'section_id'`.
- **Verified Workaround**: Inside `@property def section_id(self)`, use safe type checks (`isinstance(scope, int)`, `scope_str.isdigit()`, `getattr(self, "scope_chapter", "MIND")`). Normalize `scope_chapter` across `demo_case.py`, `settings.py`, and `case_store.py` to canonical string values (`"MIND"` or `"ALL"`), and provide default fallbacks in `__getattr__` for backward-compatible models.

### 8.25 Chat Suggestion Chips Shadowing, Substring Collisions, and Widget Keys
In multi-turn guided clinical intake, suggestion chip pills (`st.pills`) can become completely desynchronized from the bot's question due to three subtle architectural flaws:
- **UI-Layer Dict Shadowing**: If `render_quick_reply_chips` queries a static state template dictionary `NEUTRAL_STEP_SUGGESTIONS.get(curr_state)` before calling `dm.get_current_suggestions()`, and that dictionary covers all FSM states, `dm.get_current_suggestions()` is never reached. This silently throws away custom-tailored LLaMA `QUICK_REPLIES` and prompt-classified options on every turn. Always make `dm.get_current_suggestions()` the primary source.
- **Substring Collision in Intent Classification**: Checking bare substring patterns like `"what brings"` in Chief Complaint will match questions like `"And what brings you relief?"` (a modality inquiry). Always use multi-word boundaries (e.g. `"what brings you in"`, `"what brings you to"`) to prevent cross-dimension hijacking.
- **Streamlit Widget Key Collision on Skips**: If a user selects "Skip" or "None of these", `dm.prepare_turn` skips the slot, but if `turn_count` is not incremented, `st.pills` retains the exact same widget key across reruns (`pills_turn_{turn_count}`). Streamlit preserves the previous widget selection or triggers duplicate click events. Always incorporate both turn count and message history length (`f"pills_t{turn_cnt}_h{hist_len}_{dock}"`) into dynamic widget keys.

### 8.26 Fresh Consultation Startup & `advance_to_next_gap` Premature Jump
When opening a new case or starting fresh, the chat header progress bar prematurely jumped to **`Location 3/10`** (30% progress) while the assistant was still outputting the initial greeting message.
- **Root Cause**: `DialogueManager.resume_from_case(case)` unconditionally executed `self.state_machine.advance_to_next_gap()`. On fresh cases with zero captured dimensions (`Totality: 0/7`) and empty history, `_get_next_unfilled_slot()` scanned `SLOT_ORDER = [LOCATION, SENSATION, ...]` and selected `LOCATION` as the first missing gap, advancing `current_state` to `LOCATION` before the patient had said a single word.
- **Verified Workaround**: Guard `advance_to_next_gap()` by inspecting whether the case actually contains captured dimensions or dialogue history:
  ```python
  has_existing_data = any(self.extracted_slots.values()) or bool(self.history)
  if has_existing_data:
      self.state_machine.advance_to_next_gap()
  else:
      self.state_machine.current_state = IntakeState.GREETING
  ```
  Fresh cases start at `IntakeState.GREETING` (`Greeting 1/10`), advancing to `Complaint 2/10` and `Location 3/10` only as conversation unfolds. Similarly, `undo_last_turn()` restores `IntakeState.GREETING` when all turns are rolled back.

### 8.27 Streamlit `st.segmented_control` Option Disabling & Scope Locking
Streamlit's `st.segmented_control` does not support disabling individual options within a list (e.g. disabling "All chapters" while keeping "MIND focus" selectable).
- **Root Cause**: The underlying React component renders options as an atomic set; options cannot receive individual disabled attributes or tooltips.
- **Verified Workaround**: Replace the interactive widget with dedicated semantic CSS containers (`.scope-selector-container`, `.scope-pill-active`, `.scope-pill-disabled`, `.scope-tag-coming-soon`). The active pill renders with emerald accent styling, while the disabled pill renders with a dashed border, muted colors, a lock icon, `cursor: not-allowed`, and an accessible tooltip explaining that All 37 Chapters is scheduled for the v2.0 milestone. Ensure session state and case attributes (`case.scope_chapter = "MIND"`) are strictly enforced.

---

## 9. Multi-Model GPU Training & HuggingFace Gotchas

### 9.1 DeBERTa-v3 with PyTorch AMP FP16 Gradient Unscaling Error
When fine-tuning DeBERTa-v3 (`microsoft/deberta-v3-base`) using HuggingFace `Trainer` with `fp16=True`, PyTorch AMP throws:
`ValueError: Attempting to unscale FP16 gradients.`
- **Root Cause**: DeBERTa-v2/v3 models use disentangled attention with custom embedding sharing and operations in FP32 where gradients are already unscaled or incompatibly scaled for native PyTorch `GradScaler`.
- **Verified Workaround**: On NVIDIA Ampere, Ada Lovelace, or Hopper GPUs (e.g. RTX 5000 Ada), use Bfloat16 (`bf16=True, fp16=False`). Bfloat16 uses 8 exponent bits (same dynamic range as FP32) and does not require a loss scaler, completely avoiding gradient unscaling errors. In `src/models/trainer.py`, detect `"deberta"` and activate `bf16=True`.

### 9.2 HuggingFace `hf-xet` Campus Network Transfer Throttling
Recent versions of `huggingface_hub` install `hf-xet` which replaces standard HTTP range requests with a Content Addressable Storage (CAS) client opening dozens of concurrent chunk connections. On university/institutional networks with deep packet inspection or rate-limiting firewalls, this causes transfers to crawl at 30–50 KB/s.
- **Root Cause**: Concurrent CAS chunk connection throttling.
- **Verified Workaround**: Set `export HF_HUB_DISABLE_XET=1` in your shell environment and scripts. Standard direct streaming via HTTPS immediately downloads weights at full line speed (>65 MB/s).

---

_End of file._
