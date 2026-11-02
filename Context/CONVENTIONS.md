# Kent-AI — Code Conventions

> Last updated: 2026-11-01 by Antigravity
> Phase: Complete through Phase 15 (Comprehensive Clinician UI/UX Overhaul, Phases 1–10; 168 Unit & Integration Tests Passing across 18 Test Modules, 0 Errors)

---

## 1. Python Version & Environment

| Item | Value |
|---|---|
| Required Python | ≥ 3.10 (project uses 3.12 on dev machine) |
| Virtual env | `.venv/` at project root (created via `py -3.12 -m venv .venv`) |
| Activate (Windows) | `.venv\Scripts\activate` |
| Package manager | `pip` (no Poetry, no uv for this project) |
| Project install | `pip install -e ".[dev]"` |

---

## 2. Import Style

### Standard Ordering

```python
# 1. __future__ imports (always first)
from __future__ import annotations

# 2. Standard library
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# 3. Third-party
import yaml

# 4. Project-internal (absolute imports only)
from src.config import load_config
from src.data.kent_db import get_sections, get_remedies
```

### Rules

- **Always use absolute imports** from `src.*`. Never use relative imports (no `from .kent_db import ...`).
- **Always include `from __future__ import annotations`** at the top of every module (enables PEP 604 `X | Y` syntax on Python 3.10).
- Imports in `__init__.py` files re-export public API names via `__all__`.
- **Loopback network calls**: When querying local daemon APIs (Ollama on `127.0.0.1:11434`), always build an explicit proxy bypass opener: `urllib.request.build_opener(urllib.request.ProxyHandler({}))` to avoid institutional proxy interception on Windows.

---

## 3. Type Annotations

- **All function signatures must have type hints** — parameters and return type.
- Use `Dict[str, Any]` from `typing` (not `dict[str, Any]`) for compatibility down to 3.10 (the `from __future__ import annotations` import handles the forward reference, but be consistent with existing code).
- Use `Optional[X]` or `X | None` for nullable parameters.
- Use `Union[str, Path]` for path-like parameters.

```python
# Good
def get_rubrics(
    section_id: int,
    parent_id: Optional[int] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    db_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
```

---

## 4. Docstrings

Use Google-style docstrings with `Args:`, `Returns:`, `Raises:` sections.

```python
def get_rubric_path(rubric_id: int, db_path: Optional[Union[str, Path]] = None) -> str:
    """Retrieve the full hierarchical path string for a given rubric.

    If the database row contains a pre-populated 'path' column, that is used;
    otherwise, the path is traversed recursively to the root.

    Args:
        rubric_id: Rubric primary key ID.
        db_path: Optional path to SQLite database.

    Returns:
        Path string in the format "SECTION > PARENT > CHILD".

    Raises:
        KeyError: If the rubric_id does not exist.
    """
```

### Rules

- Every public function and class MUST have a docstring.
- **Explain *why*, not just *what*** — especially for non-obvious design choices.
- Private helper functions need only a one-line docstring.

---

## 5. Module Organization

### Separation of Concerns

| Directory | Owns | Does NOT Touch |
|---|---|---|
| `src/data/` | SQLite, file I/O, data transforms | ML models, HTTP |
| `src/models/` | Model loading, inference, training | Database queries |
| `src/search/` | Embeddings, ChromaDB, ranking | Training loops |
| `src/chatbot/` | State machine, dialogue, prompts | Direct DB access |
| `src/pipeline/` | Orchestration of above modules | Implementation details of any one module |
| `src/dashboard/` | Streamlit UI rendering | Business logic (delegates to pipeline) |
| `scripts/` | CLI entry points only | Testable logic (imports from `src/`) |

### File Size

- No single file should exceed ~500 lines. If it does, extract a helper module.
- `__init__.py` files are for re-exports only — no business logic.

---

## 6. Configuration

- **All hyperparameters, model names, file paths, and magic numbers** live in `configs/*.yaml`.
- **Never hardcode** a model name, learning rate, batch size, or threshold in source code.
- Load configs via `src.config.load_config("model")` or the typed shortcuts.
- Config files use nested YAML keys (not flat), e.g., `model.name`, not `model_name`.

---

## 7. Database Access

- **Always use read-only connections**: `get_connection()` opens with `?mode=ro` URI and `PRAGMA query_only=ON`.
- **Always use the context manager**: `with get_connection() as conn:` — never store a long-lived connection.
- **Return `list[dict]`** from all query functions (via `sqlite3.Row` → `dict(row)`).
- **Parameterize all queries** — never use string formatting for SQL values.
- **Grade resolution**: Always use `COALESCE(rr.grade, rr.grade_candidate, 1)` when querying remedy grades.

---

## 8. Testing

- Test framework: **pytest** (configured in `pyproject.toml`).
- Test files live in `tests/` and are named `test_<module>.py`.
- Test suite status: **168 passing tests across 18 test files** (100% pass rate in ~116s, 0 errors, 0 warnings).
- Use **class-based grouping** (`class TestKentDBReader:`) for related tests.
- ChromaDB test fixtures must use unique ephemeral collection names (`f"test_rubrics_{uuid.uuid4().hex[:8]}"`) to prevent inter-test state contamination.
- Tests run against the **real database** (no mocks for the SQLite layer) — this is intentional for correctness verification.
- Run: `.venv\Scripts\pytest.exe tests/ -v`

---

## 9. Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Modules | `snake_case.py` | `kent_db.py`, `case_generator.py` |
| Functions | `snake_case` | `get_mind_rubrics()`, `search_rubrics()` |
| Classes | `PascalCase` | `KentDB`, `SymptomNER`, `CaseGenerator` |
| Constants | `UPPER_SNAKE_CASE` | `CASE_GENERATION_PROMPT` |
| Config keys | `snake_case` in YAML | `learning_rate`, `max_seq_length` |
| Test functions | `test_<what_is_tested>` | `test_get_mind_rubrics_count` |
| Test classes | `Test<Module>` | `TestKentDBReader`, `TestConfigSystem` |

---

## 10. Error Handling

- Use specific exception types: `FileNotFoundError`, `KeyError`, `ValueError`.
- Never use bare `except:` or `except Exception:` without re-raising or logging.
- Database lookup functions return `None` for missing records (do not raise).
- Path resolution functions (`get_db_path`, `get_rubric_path`) raise on failure.

---

## 11. Git

- Commit messages follow: `<type>: <description>` (e.g., `feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
- Large binary files (`.sqlite`, `.gz`, model weights) are `.gitignored`.
- The `.venv/` directory is never committed.

---

## 12. Streamlit 1.64 Layout & Widget Conventions

- **Container Width**: Never use `use_container_width=True` on Streamlit widgets. Streamlit 1.64 deprecates this parameter. Always specify `width="stretch"` on `st.button`, `st.popover`, `st.download_button`, `st.dataframe`, and `st.plotly_chart`.
- **Module Reload Hierarchy**: When re-importing application components in `app.py`, reload dependencies in strict topological order (`config` $\rightarrow$ `prompts` $\rightarrow$ `state_machine` $\rightarrow$ `dialogue_manager` $\rightarrow$ `styles` $\rightarrow$ `components.*`).
- **Sanitization Helpers**: All client components must provide defensive `getattr()` or regex sanitizers when rendering LLM responses.

---

## 13. SeqEval & Classification Metric Conventions

- Always pass `zero_division=0` to all `seqeval.metrics` calls (`f1_score`, `precision_score`, `recall_score`, `classification_report`). This ensures deterministic 0.0 scores instead of emitting runtime `UndefinedMetricWarning` on small or mock test splits.

---

## 14. Multi-Model CLI Training Conventions

- All token classification training scripts must expose `--model-name` to accept arbitrary HuggingFace backbone identifiers (e.g., `microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext`, `michiyasunaga/BioLinkBERT-base`, `microsoft/deberta-v3-base`).
- Default model identifier must point to `emilyalsentzer/Bio_ClinicalBERT` for backwards compatibility.

---

## 15. Streamlit CSS & Viewport Conventions

- **Sidebar Scoping**: Never apply static `min-width` rules to `section[data-testid="stSidebar"]` unconditionally. Always scope via `section[data-testid="stSidebar"][aria-expanded="true"]` to avoid phantom layout footprints when collapsed.
- **Scroll Integrity**: Never lock the main page viewport with `overflow: hidden !important;` on `.stMain` or `[data-testid="stAppViewContainer"]`. Always maintain `overflow-y: auto !important; overflow-x: hidden !important;` and confine scrolling to designated sub-containers (e.g. `st.container(height=450)`).
- **Fragment Reruns**: Use `safe_rerun_fragment()` from `src.dashboard.utils` when re-evaluating isolated UI components (`st.fragment`), with graceful fallback to `st.rerun()`.

---

## 16. ReportLab PDF Generation Conventions

- **Deferred Generation**: Never generate PDF binaries during standard dashboard script re-runs. Always defer generation inside popovers or download callbacks to preserve interface responsiveness.
- **Document Flow**: Build clinical consultation PDFs using ReportLab Flowables (`SimpleDocTemplate`, `Paragraph`, `Table`, `Spacer`, `HRFlowable`). Set explicit column widths (`colWidths`) and wrap table cell strings in `Paragraph` to enable text wrapping.

---

## 17. LLM Chat Streaming & Control Syntax Filtering

- **Chunk Lookahead Buffering**: Generators feeding `st.write_stream` must buffer potential control markers (`QUICK_REPLIES`, `SLOT_UPDATE`, code fences) across chunk boundaries to prevent control tags from leaking into visible chat messages.
- **Dual Format Support**: Quick reply parsers must seamlessly support both bracketed JSON arrays (`QUICK_REPLIES: ["..."]`) and plain comma/newline-separated lists.
- **Immediate Feedback**: Always render visual thinking indicators (`.skeleton-thinking-bubble`) inside the assistant message container before initiating synchronous extraction or inference calls.

---

## 18. Streamlit Form & Narrative Intake Conventions

- **Form Boundary**: Wrap clinical narrative intake in `with st.form("paste_intake"):` and `st.form_submit_button("Extract & review")`. This enables standard Ctrl/Cmd+Enter keyboard submission and avoids expensive server reruns on every keystroke.
- **Widget State in Callbacks**: Never assign to widget keys in the main script pass (`st.session_state["paste_text"] = ...`). Always update widget state via an `on_change` callback (e.g. `_on_example_pill_change` on `st.pills`).

---

## 19. HTML Escaping (`esc()`) Security Enforcement

- **Mandatory Sanitization**: Every string variable interpolated into HTML (`f"<div>{esc(var)}</div>"`) MUST pass through `src.dashboard.utils.esc()`.
- **Zero Unescaped Interpolation**: Never render raw patient text or LLM output with `unsafe_allow_html=True` without escaping.
- **Span Bounds Clamping**: When rendering highlight `<mark>` spans, always clamp character offsets (`max(0, start)`, `min(len(text), end)`), resolve overlapping spans deterministically, and escape both highlighted and intervening text.

---

## 20. Accessible Tooltip & Color Independence Conventions

- **Interactive Tooltips**: Tooltips must never rely solely on native browser mouse hover `title=`. Always pair with `tabindex="0" aria-label="..." data-tip="..." title="..."` so tooltips work via keyboard focus, screen readers, and CSS hover/focus-visible.
- **Color Independence**: Never use color as the sole indicator of state (e.g., green for ready, grey for locked). Always pair color with explicit text labels (e.g., `[Locked]`, `(Recommended)`, `Captured` / `Not captured`) or an accessible icon.
- **Contrast Ratios**: All foreground text must achieve at least WCAG AA contrast against its background (≥ 4.5:1 for normal text, ≥ 3:1 for large text and UI components). Primary buttons use `#0A0F1D` text on `#10B981` (6.83:1).

---

## 21. Dialogue Manager & Chat Component Conventions

- **Modular UI Structure**: Chat components must remain modular and under ~500 lines (`chat_header.py`, `chat_messages.py`, `chat_actions.py`, and `chat_viewer.py` orchestrator under 250 lines).
- **Separation of UI Actions and Conversational Replies**: Do not place workflow navigation buttons into suggestion chips. Terminal actions belong in `dm.get_action_options()`, rendered as typed Streamlit buttons. Suggestion chips in `DONE` state strictly contain genuine conversational replies.
- **Per-Turn Diff Tracking**: User turns record `turn_id` and `captured: {dim_key: [tokens]}` diffs. Undo operations (`undo_capture`, `undo_last_turn`) revert slots and dimensions atomically.
- **Accessibility Live Regions**: Mount accessible live regions (`<div role="status" aria-live="polite" class="sr-only">`) announcing assistant turns to screen readers.
- **Touch Target Dimensions**: Suggestion pills and interactive chips must achieve at least 40px minimum touch height (`min-height: 40px !important`, `padding: 8px 14px !important`).
- **Emoji-Free Policy**: Never include emojis in UI labels, notification toasts (`st.toast`), or button texts.

---

## 22. UI/UX Design System, Design Tokens & Ground-Truth Single Source

- **Single Source of Truth (`constants.py`)**: All canonical dimension definitions (`get_canonical_dimensions`), grade weights (`GRADE_WEIGHTS`), model display names (`MODEL_DISPLAY_NAME`), and evaluation benchmarks (`EVALUATION_METRICS`) MUST be imported from `src/dashboard/constants.py`. Never hardcode duplicate dictionaries or weights in views.
- **Design Tokens in CSS**: All visual styling must use CSS variables defined in `:root` inside `src/dashboard/styles.css` (`--bg: #0B1117`, `--surface: #121A23`, `--surface-2: #182330`, `--line: #243243`, `--text: #E8EDF3`, `--text-muted: #A3B0C2`, `--accent: #10B981`). Target stable hooks (`.st-key-*`, `data-testid`), never dynamic Streamlit hash classes.
- **Signature Totality Ring**: Use the reusable 7-segment SVG glyph component from `src/dashboard/totality_ring.py` for all totality completeness indicators.
- **Microcopy Discipline**: Microcopy must be sentence case, verb-first ("Continue to review", "Start over", "Open", "Export"), without conversational filler. Never leak unformatted `?` or bare `—` placeholders in clinical metadata.
- **ASCII-Only Notification Constraint**: Strings passed to `st.toast()` MUST be strictly ASCII (`ord(c) < 128`). Use standard hyphens `-` instead of Unicode interpuncts `·` or arrows `→`.
- **PyMuPDF Forward Compatibility**: Always use `import pymupdf as fitz` or `import pymupdf` to maintain forward compatibility and avoid deprecation warnings.

---

## 23. Busy Feedback, Loading Performance & Navigation Conventions

- **`busy.js` Contract**: User clicks immediately show button-level loading feedback within ~120ms (`data-kent-busy="true"`). The global loading indicator (`html[data-kent-busy="true"]`) is strictly gated on user interactions and never keyed solely on `data-test-script-state` (to avoid flashing during periodic fragment runs). Minimum visibility time of 450ms is enforced to prevent visual flicker.
- **`busy_slot` Context Manager**: Wrap long-running operations (>500ms) with `busy_slot(slot, label, key=..., type=...)`. The twin button reserves the key suffix `__busy` (`f"{key}__busy"`) which receives the `.st-key-*__busy` CSS spinner while disabled.
- **Never Key Global Indicator on Script-State Alone**: Header telemetry polls every 2 seconds via `@st.fragment(run_every="2s")`. This flips `data-test-script-state` to `running`. The JS runtime must track `lastInput` gesture timestamps within a 1500ms window before activating global progress bars.
- **Download Buttons (`on_click="ignore"`)**: All `st.download_button` calls MUST include `on_click="ignore"` to prevent clicking a download button from triggering a full app rerun or stuck spinner.
- **Lazy Tabs and the `main_tabs` Callback Rule**: All top-level tabs use `tabs = dict(zip(TAB_LABELS, st.tabs(TAB_LABELS, key="main_tabs", on_change="rerun")))` with `with tabs[name]: if tabs[name].open:`. Inter-tab navigation (e.g. from Resume or New Case) MUST occur inside widget `on_click` callbacks setting `st.session_state.main_tabs = "Case Workspace"`, because widget keys cannot be mutated during the same run after instantiation.
- **Search-on-Submit & On-Demand Exports**: Never run unbounded vector searches or N+1 SQLite queries on initial page render. Rubric search only executes on form submission (Enter or button); exports are prepared on demand with cached byte buffers.

---

## 24. Repertory Scope Discipline (Chapter 1: MIND Focus vs All Chapters)

- **MIND Scope as Single Active Source**: The current validated NLP extraction and ChromaDB dense retrieval pipeline operates on Chapter 1: MIND (`4,933` rubrics). `st.session_state.scope = SCOPE_MIND` (`"MIND focus"`) and `case.scope_chapter = "MIND"` must be enforced across all views.
- **"All Chapters" Coming Soon Treatment**: Do not provide active or switchable toggles to All 37 Chapters in user-facing UI until v2.0. Instead, render an active "MIND Focus" pill alongside a disabled, dashed-border "All 37 Chapters (Coming Soon in v2.0)" badge with a lock icon (`:material/lock:`) and an explanatory tooltip.
- **Backend Model Compatibility**: The backend database, models, and ranker must remain backward-compatible with both integer section IDs (`1`), string names (`"MIND"`), and `None` (for all chapters), ensuring test suite stability and seamless transition when full 37-chapter indexing launches in v2.0.

---

## 25. Clinical Intake FSM Startup & Resumption Conventions

- **Fresh Case Dialogue Invariant**: Fresh consultations (zero captured dimensions, empty dialogue history) MUST start at `IntakeState.GREETING` (`Greeting 1/10`), matching the assistant's initial welcome prompt.
- **Conditional `advance_to_next_gap`**: Never call `self.state_machine.advance_to_next_gap()` unconditionally in `resume_from_case()`. Only advance to the first unfilled gap when the case contains existing symptoms or conversation turns (`has_existing_data = any(self.extracted_slots.values()) or bool(self.history)`).
- **Undo Restoration**: When rolling back turns via `undo_last_turn()`, if the rollback returns the conversation to the initial turn with zero extracted slots, restore `self.state_machine.current_state = IntakeState.GREETING`.

---

_End of file._
