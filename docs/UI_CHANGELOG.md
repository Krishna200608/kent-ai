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
