# Kent-AI — UI/UX Overhaul Changelog & Decision Record

This document records architectural decisions, assumptions, backend changes, and phase deliverables for the Kent-AI UI/UX overhaul.

---

## Assumptions & Design Decisions

1. **Streamlit Navigation**:
   - Streamlit 1.64.0 is installed. `st.navigation` is available. For seamless multi-tab views that maintain workspace consultation state, `st.navigation` with top layout will be used in Phase 2 to isolate execution across pages and replace expensive full-app `st.tabs` reruns.
2. **Canonical Dimensions Single Source of Truth**:
   - Internal keys in database and models (`location`, `sensation`, `modality_agg`, `modality_amel`, `concomitant`, `temporal`, `mental`) remain unchanged for 100% backward compatibility with all ~81 saved cases and the SQLite schema.
   - The user-facing labels and order are mapped via `src/dashboard/constants.py`.
   - When scope = MIND, `Mental/Emotional` is ordered first and marked "paramount".
3. **Lazy Case Creation**:
   - Opening the workspace keeps an unsaved in-memory draft in `st.session_state.current_case` without inserting a blank row in SQLite.
   - Persistence occurs on first captured dimension, first chat turn, or explicit "Save" action.
4. **Design Tokens & Fonts**:
   - Design tokens live in `src/dashboard/styles.css` under `:root`.
   - Standard system font fallbacks (`"IBM Plex Sans", system-ui, sans-serif` and `"Source Serif 4", Georgia, serif`) ensure offline operation.

---

## Phase Execution Log

### Phase 0: Audit & Architecture Mapping (Complete)
- **Files Created**: `docs/UI_AUDIT_MAP.md`, `docs/UI_CHANGELOG.md`.
- **Audit Findings**: Identified 8 duplicated UI elements, Streamlit 1.64.0 capabilities, and session state dependencies across all 5 workspace areas.

---

### Phase 1: Bug Fixes, Design Tokens & Totality Ring (Complete)
- **Design Tokens**:
  - Embedded full token palette in `src/dashboard/styles.css` (`:root`): `--bg: #0B1117`, `--surface: #121A23`, `--surface-2: #182330`, `--line: #243243`, `--text: #E8EDF3`, `--text-muted: #A3B0C2`, `--text-faint: #8A98AE`, `--accent: #10B981`, `--accent-hover: #34D399`, `--accent-ink: #03160F`, `--accent-soft: rgba(16, 185, 129, 0.14)`.
  - Typography: UI `--font-ui` (IBM Plex Sans / system-ui), Repertory `--font-rubric` (Source Serif 4 / Georgia).
  - Global `:focus-visible` ring (2px `--accent`, 2px offset); removed default blue browser outline.
  - Primary button styling: `--accent` fill with `--accent-ink` text and hover/active/disabled states.
  - Tab styling: padding 10px 16px, 2px underline indicator in `--accent`, no box outline hugging text.
  - Hidden auto-anchor links (`[data-testid="stHeaderActionElements"]`).
  - Quick-reply chips / `st.pills` flex-wrap applied to prevent chip clipping.
- **Single Source of Truth (`src/dashboard/constants.py`)**:
  - Reconciled model name display as `"Llama 3 8B"` derived from `configs/chatbot.yaml` across top brand header, chat console badge, session options, and settings methodology.
  - Canonical 7 dimensions with MIND paramount ordering (`mental` first).
  - `format_rubric_path(path)`: replaces ` > ` with ` › `, repairs dropped OCR trailing dots on time abbreviations (e.g., `"11 a.m"` → `"11 a.m."`, `"4 a.m"` → `"4 a.m."`).
  - Master constants for `GRADE_WEIGHTS` (3: 3.0, 2: 2.0, 1: 1.0) and scope definitions (`4,933` / `74,513`).
- **Signature 7-Segment Totality Ring (`src/dashboard/components/totality_ring.py`)**:
  - Reusable SVG glyph rendering 7 circular arc segments, illuminated in `--accent` when captured.
  - Universal input support: integer count (0-7), key set/list, symptom dict, `ClinicalCase`, or `DialogueManager`.
  - Embedded in persistent case bar and case library cards.
- **Bug Fixes & Demographics Cleanup**:
  - Fixed demographic leaks in `case_store.py` and `case_bar.py`: eliminated `?` and bare `—`.
  - Fixed leading remedy in `case_library.py`: displays `"Not analysed yet"` instead of bare `"—"`.
  - Stepper navigation: removed intrusive ` [Locked]` text suffix.
  - Case bar z-index and overflow adjusted to prevent stepper tooltip clipping.
  - Lazy case creation: verified `case.is_blank` guard in `save_case` prevents blank case row creation.
- **Tests Added**:
  - `tests/test_ui_overhaul.py` (4 tests verifying constants, dimension ordering, rubric path formatting with OCR time dots, and totality ring SVG). All 14 dashboard and overhaul tests passing.

---

### Phase 2: Shell, Navigation, Case Bar, Stepper & Dialogs (Complete)
- **Top Bar (Single Row <=56px)**:
  - Replaced large header banner with a sleek single-row top bar in `src/dashboard/views/header.py`.
  - Brand wordmark "Kent-AI" + leaf icon. Subtitle moved to browser tab title (`st.set_page_config`).
  - Read-only scope chip (`MIND · 4,933` / `All · 74,513`).
  - Engine telemetry pill with popover for endpoint (`127.0.0.1:11434`), connection test, and retry.
- **Persistent Case Sub-Header & Stepper (`src/dashboard/components/case_bar.py`)**:
  - Case bar shows Case ID (mono), patient demographics (omitting empty `?`/`—`), live `totality_ring`, saved timestamp indicator, and "Patient info" button.
  - Multi-line 4-step Stepper buttons with title + sublabel:
    1. "1. Intake" · "Capture symptoms"
    2. "2. Review" · "Confirm and edit"
    3. "3. Analysis" · "Rank remedies"
    4. "4. Report" · "Export report"
  - Removed intrusive `[Locked]` text suffix.
- **Modal Dialogs (`src/dashboard/components/case_dialogs.py`)**:
  - `show_patient_info_dialog(case)`: single `@st.dialog` for editing demographics & chief complaint.
  - Removed duplicate "Optional: Patient details & chief complaint" expander in `step1_paste.py`.
  - `show_first_run_disclaimer_dialog()`: non-blocking first-run research notice dialog.
- **Sticky Bottom Action Bar (`src/dashboard/components/action_bar.py`)**:
  - Standardized bottom actions: `Back · Save draft · Continue to <next step>`.
- **Layout & Footer**:
  - Main container centered with `max-width: 1440px` and responsive side padding (24px / 16px).
  - Consolidated single 1-line muted disclaimer footer.
- **Tests Added**:
  - `test_phase2_case_dialogs_defined` and `test_phase2_action_bar_component` added to `tests/test_ui_overhaul.py`. All 11 smoke tests passing 100%.

---

### Phase 3: Slim Sidebar and Tray Persistence (Complete)
- **Sidebar Sizing & Layout (`src/dashboard/styles.css`)**:
  - Standardized width `clamp(280px, 20vw, 320px)` (~296px).
  - Enforced left-aligned text throughout (`text-align: left !important`).
- **Brand Row**:
  - 28px icon + "Kent-AI" wordmark; removed long title and subtitle.
- **Active Case Card (`src/dashboard/views/sidebar.py`)**:
  - Mono copyable Case ID, sanitized patient label (no `?`/`—`), live `totality_ring` SVG, status chip ("Draft", "In review", "Analysed", "Reported"), current step name, and "Go to Step X" button.
  - Empty state: "No Active Case" + primary "+ New Case" button.
- **Case Tray & Persistence**:
  - Heading with count badge (`Case Tray {n}`).
  - Grouped Rubrics and Remedies lists.
  - Rubric path in serif (`--font-rubric`) with `format_rubric_path` (` › ` breadcrumbs), full path tooltip, remedy count chip, and `✕` remove button.
  - Remedies with full name, abbreviation, and `✕` remove button.
  - Primary action: "Repertorize This Case" (repertorizes selected rubrics into Step 4 Report).
  - "Clear Tray" action (confirmation popover if >3 items).
  - Empty state: helpful guidance with "Open Rubric Explorer" button.
  - **Tray Persistence**: synced `tray["rubrics"]` with `current_case.selected_rubric_ids` across session initialization, library resume, and rubric tree selection.
- **Repertory Scope Control**:
  - `st.segmented_control` with "MIND focus" | "All chapters" and caption ("MIND: 4,933 rubrics · All: 74,513 rubrics").
  - Writes `st.session_state.scope` as single source of truth, syncs `case.scope_chapter`, and flags Explorer results stale on change.
- **Engine Telemetry Row**:
  - Status dot + `MODEL_DISPLAY_NAME` + round-trip latency (`{latency}ms` / `Offline`).
  - Expander with endpoint, model, temperature, "Test Connection", and "Retry Connection" with terminal hint (`ollama serve`).
- **Sticky Footer**:
  - Direct links to Methodology and Totality Principles (no duplicated text).
  - Version `v{APP_VERSION} ({GIT_SHA})`.
  - One-line disclaimer with "Read full notice" triggering `show_first_run_disclaimer_dialog()`.
  - Removed duplicated "Dr. Kent's Totality Principles" expander and long justified disclaimer from sidebar.
- **Tests Added**:
  - `test_phase3_sidebar_exports_and_components`, `test_phase3_tray_persistence_sync`, `test_phase3_get_ollama_latency` added to `tests/test_ui_overhaul.py`.
  - All 19 dashboard, smoke, and overhaul tests passing 100%.

---

### Phase 4: Case Workspace, Snapshot Rail, and Chat Polish (Complete)
- **7:3 Two-Column Workspace Layout (`src/dashboard/views/step1_intake.py`)**:
  - Established clean 7:3 split: Left (70%) = intake workflow selector, dialogue console, paste notes, suggestions, input; Right (30%) = sticky **Case Snapshot** rail.
- **Sticky Case Snapshot Rail (`src/dashboard/components/case_snapshot.py`)**:
  - Replaced redundant Totality Strip, Active Case Summary, and What to Include dimension lists.
  - 7 canonical rows in prioritized order (`get_canonical_dimensions` respecting MIND priority).
  - Row states: empty (dashed), captured (accent soft), low-confidence review (amber warning), edited by clinician (blue).
  - Popover per captured row displaying source text provenance, extraction confidence %, and inline edit/update action.
  - Readiness line (`Ready: n/7 · Missing: ...`) with soft warnings when <3 dimensions are captured or when mental is missing in MIND scope.
  - Single primary "Continue to Review →" button gated on ≥1 dimension.
  - Bottom overflow ⋯ menu with Markdown export and "Start over" reset.
- **Dialogue Console Header & Controls (`src/dashboard/components/chat_header.py`)**:
  - Consolidated "Speaking as:" segmented control (`intake_style_control` with Patient / Practitioner options).
  - Interactive stage progress widget: stage label + count with thin progress track and hover flow tooltip.
  - Unified Export popover (Download .md, Download .txt, copyable block).
  - "Start over" popover confirmation stating message and dimension counts lost, with 30s undo snapshot support.
- **Chat Messages & Scroll Polish (`src/dashboard/components/chat_messages.py`, `chat_viewer.py`)**:
  - Transcript scroll container sized via `clamp(420px, 60vh, 640px)`.
  - Welcome blurb banner collapses after the first user message.
  - Compact message bubbles with 28px avatars, hover timestamps, and assistant question regeneration (`↺ Regenerate`).
- **Step-Aware Neutral Suggestions (`src/dashboard/components/chat_chips.py`)**:
  - Replaced static symptom chips with config-driven neutral suggestions (`NEUTRAL_STEP_SUGGESTIONS`) keyed by intake state.
  - Automatically hidden when Speaking as = Practitioner or when `show_suggested_replies` toggle is off.
- **Paste Notes Polish (`src/dashboard/views/step1_paste.py`)**:
  - Word count counter directly below narrative textarea.
  - Verified local privacy notice: "Stored on this device; nothing leaves this machine."
  - Extraction wrapped in `st.status` with multi-stage progress (Encoding → Extracting → Arbitrating → Complete).
  - Collapsible clinical documentation tips expander.
- **Tests Added**:
  - `test_phase4_case_snapshot_component` and `test_phase4_step_aware_neutral_suggestions` in `tests/test_ui_overhaul.py`.
  - All 11 smoke tests and 21 unit tests passing 100%.

---

### Phase 5: Case Library, Registry Table, Pagination & Archiving (Complete)
- **Header & Device Storage**:
  - Replaced legacy subtitle with clean header: "Case library" and caption "{n} cases · stored on this device".
- **Toolbar & Search**:
  - Debounced search filtering across patient name, Case ID, chief complaint, and captured symptoms.
  - Status filter via `st.segmented_control` (`All`, `Draft`, `In review`, `Analysed`, `Archived`).
  - Sort selection: Last updated (default), Date created, Totality score (high to low).
  - View mode toggle: `Cards` vs `Table`.
  - Primary "+ New Case" button initializing fresh in-memory case and navigating directly to Intake.
- **Empty Drafts Handling**:
  - Automatically hides empty drafts (0 dimensions, no complaint) by default behind a collapsible "Show empty drafts (n)" toggle.
  - "Clean up empty drafts" popover: default action is **Archive** (`update_cases_status(cids, "ARCHIVED")`), preserving clinical data while decluttering views, with a permanent purge option.
- **Pagination**:
  - 12 cases per page for Cards, 25 cases per page for Table.
  - Navigation indicator: "Showing X–Y of Z cases (Page A of B)" with Prev/Next buttons.
- **Title Fallback Chain**:
  - Robust title fallback: chief complaint → patient name → "Untitled case".
  - Metadata row with clean demographics: age/gender omitted when unrecorded (no leaked `?` or `—`), Case ID in mono badge, and relative update time.
- **Table View (Clinical Registry Grid)**:
  - Dense tabular view with columns: Selection checkbox, Case ID, Patient / Chief Complaint, Totality Ring & Count, Status chip, Leading Remedy, Updated timestamp, Actions.
- **Individual & Bulk Case Actions**:
  - Open / Resume button: restores case, tray rubrics, dialogue state machine, and routes to appropriate step (Report if analyzed, Review if ≥1 dimension, else Intake).
  - Multi-select checkboxes with sticky bulk action bar (`render_bulk_action_bar`): bulk Export JSON/Markdown, bulk Archive, and bulk Delete.
  - Overflow ⋯ menu per case: Duplicate Case (creates copy with new ID), Prepare/Download PDF, Download JSON, Archive/Unarchive, and Delete with confirmation guard.
- **Tests Added**:
  - `test_phase5_case_library_exports_and_helpers` in `tests/test_ui_overhaul.py`.
  - Full smoke test suite (`test_app_smoke.py`), overhaul suite, and dashboard suite all passing 100%.

---

### Phase 6: Rubric Explorer, Remedy Grouping & Materia Medica Dialog (Complete)
- **Single-Row Search Form (`src/dashboard/views/explorer.py`)**:
  - Wrapped in `st.form(key="rubric_search_form")` for Enter key submission.
  - Query input with clearable field and clinical placeholder (`"e.g. fear of dark, anxiety in the evening"`).
  - Search mode via `st.segmented_control`: `Meaning` (BioLinkBERT vector similarity) | `Exact` (direct SQLite keyword match) | `Hybrid` (blended lexical + semantic score), with descriptive tooltips.
  - Result count via `st.segmented_control`: `10` / `15` / `25` / `50` (replaces slider).
  - Compact primary "Search" button.
- **Scope Caption & Conditional Section Filter**:
  - Scope caption: `"Searching MIND · 4,933 rubrics"` when in MIND scope; `"Searching All chapters · 74,513 rubrics"` when in All chapters scope.
  - Section/Chapter selector dropdown rendered only when scope is set to All chapters.
- **Advanced Filters Expander**:
  - Minimum similarity slider (0.0 to 1.0, default 0.35).
  - Remedy count range slider (1 to 300).
  - Multi-sort: Relevance (Similarity), Remedy count (High to Low), Remedy count (Low to High - Specific), Alphabetical (A–Z).
- **Hybrid Search Engine (`hybrid_rubric_search`)**:
  - Blends dense vector search scores (0.65 weight) with exact FTS5/LIKE keyword token overlap and reciprocal rank (0.35 weight).
  - Fixed SQLite FTS and fallback LIKE query in `src/data/kent_db.py` to calculate `(SELECT COUNT(*) FROM rubric_remedies WHERE rubric_id = d.id) AS remedy_count`.
- **Collapsed Result Card (`src/dashboard/components/rubric_tree.py`)**:
  - Multi-select checkbox.
  - Breadcrumbs formatted in `--font-rubric` (`"Source Serif 4"`) with ` › ` separators, muted ancestors, bold leaf, and query keyword `<mark>` highlighting.
  - Specificity badge via `get_rubric_specificity(remedy_count)`: `Specific` (≤20 remedies), `Broad` (≥80 remedies), or `Moderate`.
  - Thin similarity bar + % with tooltip: `"Semantic similarity to your query, not clinical relevance"`.
  - Instant `+ Add` button toggling to `✓ Added` when already present in `case_tray`, with `st.toast` and persistence in `current_case.selected_rubric_ids`.
- **Expanded Row & Grade Grouping**:
  - Shows only remedies without repeating path, match %, or remedy count.
  - Grouped by non-empty grades only (hides empty grades entirely).
  - Grade headers: ③ Bold · Confirmed, ② Italic · Qualified, ① Roman · Observed.
  - Interactive remedy chips displaying abbreviation with full Latin name in tooltip.
  - Clicking a remedy chip opens the new Materia Medica modal dialog.
- **Materia Medica Modal Dialog (`src/dashboard/components/case_dialogs.py`)**:
  - `show_remedy_dialog(remedy_id_or_abbr, db)`: displays remedy name, abbreviation badge, cataloged rubrics count, MIND rubrics count, and top Grade 3 confirmed keynotes with one-click `+ Add` to tray.
- **Sticky Multi-Select Action Bar**:
  - When ≥1 rubric is checked, renders sticky bottom action bar: `"Add {n} to Case Tray"`.
- **Tests Added**:
  - `test_phase6_rubric_specificity_and_hybrid_search` and `test_phase6_remedy_dialog_and_explorer_callable` in `tests/test_ui_overhaul.py`.
  - Full smoke test suite (`test_app_smoke.py`), overhaul suite (14 tests), and dashboard suite (10 tests) all passing 100%.

---

### Phase 7: Split Methodology & Settings Pages (Complete)
- **Navigation Split (`src/dashboard/app.py`, `src/dashboard/views/__init__.py`)**:
  - Split legacy combined "Settings & Methodology" tab into two dedicated, top-level tabs: `Methodology` and `Settings`.
- **Methodology Page (`src/dashboard/views/methodology.py`)**:
  - Section 1: Dr. J. T. Kent's Totality Principles with hierarchical symptom breakdown (Mental Generals paramount, Physical Generals, Particular Symptoms) and Totality Scoring Formula with grade weights (3.0×, 2.0×, 1.0×) and specificity weighting derived directly from `GRADE_WEIGHTS` in `constants.py`.
  - Section 2: The 7 Totality Dimensions in canonical order from `get_canonical_dimensions()`.
  - Section 3: NLP Architecture & Encoders: BioLinkBERT-Base (110M), PubMedBERT (110M), 4-Encoder Ensemble, and local LLaMA 3 8B arbitration.
  - Section 4: Verified Evaluation Benchmarks: `EVALUATION_METRICS` (Token BIO F1 88.4%, Recall@20 91.2%, MRR 0.68) with plain-language clinician explanations.
  - Section 5: Investigational Clinical Decision-Support Notice (§3 in full).
- **Settings Page (`src/dashboard/views/settings.py`)**:
  - Inference Engine: Ollama endpoint status, configured LLM model (`MODEL_DISPLAY_NAME`), and "Test Connection" button with round-trip latency (`get_ollama_latency()`).
  - Consultation Defaults: Repertory scope selector (MIND focus vs All chapters), display density (Comfortable vs Compact), autosave toggle, and step-aware suggested replies toggle.
  - Data Management & Backups: One-click "Export All Cases to JSON" timestamped backup, "Import Consultations" JSON uploader, and safe database purge protected by typed confirmation (`"DELETE ALL"`).
  - About & Version Telemetry: Application version `v{APP_VERSION}`, git short SHA `{GIT_SHA}`, and on-device privacy guarantee.
- **Tests Added**:
  - `test_phase7_split_methodology_and_settings` in `tests/test_ui_overhaul.py`.
  - Full smoke test suite (`test_app_smoke.py`), overhaul suite (15 tests), and dashboard suite (10 tests) all passing 100%.

---

### Phase 8: Review, Analysis, Report Refinements & Materia Medica Polish (Complete)
- **Step 2 Review (`src/dashboard/views/step2_review.py`)**:
  - Organized symptom cards dynamically via `get_canonical_dimensions(scope)` (Mental & Emotional Generals paramount in MIND scope).
  - Accessible symptom removal buttons (`Remove` button per symptom replacing bare buttons).
  - Clean inline symptom addition inputs per dimension.
  - Retained Physician Brief / Clinical Summary with local LLM regeneration and manual edit modal expander.
- **Step 3 Analysis (`src/dashboard/views/step3_analysis.py`)**:
  - Classical Repertorization Matrix with interactive mute and eliminatory toggles.
  - Comparative Candidate Remedy Ranking Table: score breakdown (weighted score, rubric coverage ratio, grade contributions).
  - Expandable "Why this remedy" list detailing every covered rubric, Kentian grade (③ Bold, ② Italic, ① Roman), semantic similarity, and exact point contribution.
  - Comparative clinical note explicitly advising against single-candidate automated prescriptions.
  - One-click Materia Medica modal dialog inspection button (`show_remedy_dialog`) for every candidate remedy.
- **Step 4 Report (`src/dashboard/views/step4_report.py`)**:
  - Paper-style printable report layout with `@media print` styling in `src/dashboard/styles.css`.
  - Header case metadata: sanitized demographics (omitting empty `?`/`—`), Scope, model name (`MODEL_DISPLAY_NAME`), and version `v{APP_VERSION}`.
  - Section 1: Validated 7-Dimension Clinical Totality findings.
  - Section 2: Comparative Candidate Analysis (top candidates with score advantage margin over runner-up).
  - Section 3: Remedy Totality Ranking Chart and breakdown table.
  - Section 4: Classical Repertorization Matrix.
  - Section 5: Matched Repertory Rubrics with full expanders.
  - Section 6: Full Investigational Clinical Decision-Support Notice.
  - Multi-format exports: on-demand compiled PDF, Markdown, and print layout.
- **Materia Medica View (`src/dashboard/views/materia_medica.py`)**:
  - Remedy cards styled with design tokens, abbreviation badges, cataloged count, and MIND count.
  - Keynotes rendered in `--font-rubric` with `format_rubric_path` and Grade 3 badges.
  - "Inspect Details" button opening the Materia Medica modal dialog.
- **Tests Added**:
  - `test_phase8_step_views_and_materia_medica_exports` in `tests/test_ui_overhaul.py`.
  - Full smoke test suite (`test_app_smoke.py`), overhaul suite (16 tests), and dashboard suite (10 tests) all passing 100%.

---

### Phase 9: Caching, Performance & Demonstration Case Mode (Complete)
- **Service Caching**:
  - Maintained singletons for `get_db()` and `get_pipeline()` wrapped in `@st.cache_resource`.
  - Fast Ollama ping latency cached via `@st.cache_data(ttl=2)` in `src/dashboard/components/ollama_status.py`.
- **Realistic Demonstration Case Generator (`src/dashboard/components/demo_case.py`)**:
  - `create_demo_case()`: produces a realistic MIND consultation case (`DEMO-MIND-001`) with 6/7 totality dimensions, chief complaint, clinical summary, and extraction metadata.
  - Allows clinicians and researchers to test Review, Analysis, Totality Matrix, and Reports immediately without waiting for local LLM generation.
- **Demo Mode Triggers**:
  - Added "Load Demo Case" in `case_snapshot.py` action popover.
  - Added "Load Demo Case" button to the `case_library.py` toolbar.
- **Tests Added**:
  - `test_phase9_demo_case_creation` in `tests/test_ui_overhaul.py`.
  - Full smoke test suite (`test_app_smoke.py`), overhaul suite (17 tests), and dashboard suite (10 tests) all passing 100%.

---

### Phase 10: Final QA, Verification & Acceptance Audit (Complete)
- **Regression Suite Verification**:
  - `tests/test_app_smoke.py`: 11/11 tests green (53.33s).
  - `tests/test_ui_overhaul.py`: 17/17 tests green (8.18s).
  - `tests/test_dashboard.py`: 10/10 tests green (42.66s).
  - Total: 38/38 passing unit and integration tests across the dashboard suite.
- **UI Hygiene & Accessibility Audit**:
  - Zero emojis in toasts, buttons, or HTML content (verified by `test_source_guards_no_emoji_in_toasts_and_no_x_buttons`).
  - Strict HTML escaping: all user and LLM interpolated strings pass through `src.dashboard.utils.esc()`.
  - Design tokens used exclusively via `:root` CSS variables; zero hard-coded brand colors or duplicate inline styles.
  - Contrast compliance: text on surfaces meets or exceeds WCAG AA (≥4.5:1 ratio).
  - All existing ~81 saved consultations in SQLite load seamlessly with complete backward compatibility.







