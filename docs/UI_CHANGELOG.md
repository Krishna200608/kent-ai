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

