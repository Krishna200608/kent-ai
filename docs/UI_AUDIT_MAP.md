# Kent-AI — UI/UX Audit Map (Phase 0)

> Generated: 2026-11-01 | Environment: Streamlit 1.64.0, Python 3.12, SQLite, ChromaDB

---

## 1. Screen & Component Inventory

| Screen / Area | Primary File / Function | Key `st.session_state` Keys | CSS Hooks & Selectors | Database Tables |
|---|---|---|---|---|
| **App Shell & Top Bar** | `app.py` (`main`), `views/header.py` (`render_header`) | `repertory_scope`, `current_case`, `dialogue_manager` | `.brand-header`, `.brand-pills`, `.status-pill` | `cases.sqlite` (`clinical_cases`) |
| **Sidebar & Case Tray** | `views/sidebar.py` (`render_sidebar`, `render_sidebar_case_tray`) | `repertory_scope`, `inference_engine`, `case_tray`, `show_dev_details` | `[data-testid="stSidebar"]`, `.step-counter-badge` | Read-only DAL queries |
| **Case Bar & Stepper** | `components/case_bar.py` (`render_case_bar`) | `workspace_step`, `current_case`, `current_report` | `.persistent-case-bar`, `[data-testid="stPopover"]` | `clinical_cases` |
| **Step 1: Guided Chat** | `views/step1_intake.py`, `components/chat_viewer.py` | `dialogue_manager`, `chat_is_streaming`, `confirm_chat_reset` | `.stGlassCard`, `[data-testid="stChatMessage"]`, `.status-dot` | `clinical_cases` |
| **Step 1: Paste Notes** | `views/step1_paste.py`, `components/extraction_preview.py` | `paste_text`, `paste_preview`, `example_pill_select` | `[data-testid="stForm"]`, `.intake-pill` | `clinical_cases` |
| **Step 2: Review** | `views/step2_review.py` (`render_step2_review`) | `current_case`, `workspace_step` | `.stGlassCard`, `[data-testid="stExpander"]` | `clinical_cases` |
| **Step 3: Analysis** | `views/step3_analysis.py`, `components/totality_grid.py` | `current_report`, `current_case`, `ranking_sort_mode` | `.totality-matrix-table`, `.grid-header` | `clinical_cases`, `rubric_remedies` |
| **Step 4: Report** | `views/step4_report.py`, `pdf_exporter.py` | `current_report`, `current_case` | `.report-hero-card`, `.badge-*`, `.stPlotlyChart` | `clinical_cases` |
| **Case Library** | `components/case_library.py`, `case_bulk_actions.py` | `case_lib_search`, `case_select_*`, `toggle_show_blanks` | `.stGlassCard`, `[data-testid="stContainer"]` | `clinical_cases` (all rows) |
| **Rubric Explorer** | `views/explorer.py`, `components/rubric_tree.py` | `repertory_scope`, `case_tray` | `.rubric-card`, `.breadcrumb-trail` | `rubrics`, `rubric_remedies`, `sections` |
| **Materia Medica** | `views/materia_medica.py`, `components/remedy_comparison.py` | `rem_filter_text`, `case_tray` | `[data-testid="stExpander"]`, `.status-pill` | `remedies`, `rubric_remedies` |
| **Settings & Methodology** | `views/settings.py` (`render_settings_view`) | Static methodology documentation | `[data-testid="stContainer"]` | None |

---

## 2. Navigation Architecture
- **Streamlit Version**: `1.64.0` (supports `st.navigation`, `st.fragment`, `st.dialog`, `st.segmented_control`, `st.popover`, `st.status`, `st.container(key=...)`).
- **Current Tab Navigation**: Implemented via top-level `st.tabs(["Case Workspace", "Case Library", "Rubric Explorer", "Materia Medica", "Settings & Methodology"])` in `app.py`. Note: `st.tabs` executes all 5 tab function bodies on every rerun.
- **Workflow Stepper**: 4 consultation stages inside `Case Workspace` driven by `st.session_state.workspace_step` (1: Intake, 2: Review, 3: Analysis, 4: Report).

---

## 3. Dispersed & Duplicated Chrome Elements (To Consolidate)

| Element | Current Locations | Target Single Source of Truth |
|---|---|---|
| **Repertory Scope** | Sidebar radio, top header pill, explorer section dropdown | Sidebar segmented control (writes `session_state.repertory_scope`); top bar chip mirrors it |
| **Engine Status** | Top header pill, chat header badge, sidebar engine expander | Top bar engine pill (popover with details/retry); unified polling in `ollama_status.py` |
| **Research Disclaimer** | `app.py` bottom banner, sidebar bottom text, `settings.py` §3, report view | Unified 1-line muted footer + first-run modal + full text in Methodology page |
| **App Branding** | Top header banner, sidebar header box, page title | Slim ≤56px top bar + sidebar brand row; subtitle moved to About |
| **Totality (n/7) Indicator** | Case bar text pill, totality strip HUD, library cards | Canonical 7-segment SVG `totality_ring(captured_keys, size)` |
| **7-Dimension List** | `dimensions.py`, `symptom_strip.py`, `intake_guide.py`, `step4_report.py` | `src/dashboard/constants.py` canonical dictionary + right-rail Case Snapshot |
| **Patient Demographics** | `case_bar.py` popover, `step1_paste.py` expander | Single `st.dialog` opened from Case Bar ("Patient info") |
| **Dr. Kent's Totality Principles** | Sidebar expander quote, `settings.py` §1 | Retained solely in Methodology; sidebar links to anchor |

---

## 4. Case Status Taxonomy
- **Supported in SQLite / DAL**: `"draft"`, `"in_review"`, `"analyzed"`, `"archived"`.
- **Derived UI State Rules**:
  - `DRAFT`: 0-1 dimensions captured, un-analyzed.
  - `IN REVIEW`: ≥2 dimensions captured, un-analyzed.
  - `ANALYZED`: Ranked remedies and repertorization report generated.
  - `ARCHIVED`: User-archived or completed case.
