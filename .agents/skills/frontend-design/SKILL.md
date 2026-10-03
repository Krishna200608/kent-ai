---
name: frontend-design
description: >
  Streamlit UI design and improvement skill for the kent-ai dashboard.
  Use when adding new pages, improving existing components, fixing layout
  issues, or enhancing the visual quality of the Streamlit interface.
  Grounded in the actual implementation in src/dashboard/.
---

# Frontend Design Skill — Kent-AI (Streamlit)

## Scope
All UI work lives in `src/dashboard/`. The dashboard layer may import from
`src/pipeline/` and `src/chatbot/` — it must NOT reach into `src/data/` or
`src/models/` directly (per `Context/ARCHITECTURE.md`).

---

## Actual Dashboard File Structure

```
src/dashboard/
├── app.py              # ★ Main Streamlit entrypoint — 4-workspace clinical portal
├── styles.py           # CSS injection (Google Stitch theme via st.markdown)
├── styles.css          # Google Stitch CSS (midnight canvas #0A0F1D, 27KB)
├── dimensions.py       # DIMENSION_MAP — single source of truth for 7 clinical dims
└── components/
    ├── chat_viewer.py  # Multi-turn chat HUD with live slot pills
    ├── rubric_tree.py  # Rubric cards with expandable 3-grade remedy inspector
    └── icons.py        # Icon helpers
```

Do NOT create new page files like `case_viewer.py`, `rubric_search.py`, or
`metrics.py` — the 4-workspace layout lives entirely in `app.py`.

---

## Design System (Google Stitch Standard)

The project uses a custom **Google Stitch** CSS design system injected via `src/dashboard/styles.py`.

Key design tokens (from `src/dashboard/styles.css`):
- **Background**: Midnight canvas `#0A0F1D`
- **Cards**: Glassmorphism with backdrop-filter
- **Status indicators**: Pulse-glow animations
- **Custom scrollbar**: Emerald-themed (fixed-height 450–520px chat container)
- **Dimension badges**: 7-colour system for LOC/SEN/MOD_AGG/MOD_AMEL/CONC/TEMP/MENT

Do NOT add inline hex colours to Python files — all styling goes through `styles.css` or `styles.py`.

---

## The 7 Clinical Dimensions (from `src/dashboard/dimensions.py`)

`DIMENSION_MAP` is the **single source of truth** for dimension metadata.
Always import from `src.dashboard.dimensions` — never redeclare dimension names inline.

The 7 dimensions: `LOC`, `SEN`, `MOD_AGG`, `MOD_AMEL`, `CONC`, `TEMP`, `MENT`.

---

## Streamlit Implementation Rules

### 1. Caching
```python
from src.pipeline.orchestrator import PipelineOrchestrator

@st.cache_resource
def load_orchestrator():
    """Load the pipeline orchestrator once — heavy Ollama + ChromaDB init."""
    return PipelineOrchestrator()
```
- `@st.cache_resource` for objects (orchestrator, ChromaDB client, embedder).
- `@st.cache_data` for pure data functions (rubric lists, section metadata).
- Never load heavy resources inside a Streamlit callback or widget handler.

### 2. Widget Keys
Every interactive widget must have a unique, descriptive `key=` parameter.
Duplicate keys across re-renders cause Streamlit state bugs.

### 3. Pluralization
Use the `pluralize` helper from `src/dashboard/dimensions.py` to avoid
`"(1 remedies)"` strings (this bug was fixed in UI/UX Pass 2).

### 4. Match Tier Thresholds (from `src/dashboard/components/rubric_tree.py`)
Do not change the calibrated cosine similarity thresholds without updating both the component and the CSS badge classes:
- **Strong**: ≥ 0.68
- **Good**: 0.58–0.679
- **Fair**: 0.52–0.579
- **Weak**: < 0.52

### 5. Layout
- Max content width: 1200px.
- Use `st.tabs()` for the 4 workspaces (Live Intake Chat, Instant Repertorization Engine, 74k Rubric Explorer, Materia Medica Index).
- Use `st.columns()` for responsive layout — no fixed pixel widths in Python.

---

## Running the Dashboard Locally

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Start Streamlit
streamlit run src/dashboard/app.py

# Headless (for server)
streamlit run src/dashboard/app.py --server.headless true --server.port 8503
```

---

## Checklist Before Committing UI Changes
- [ ] No business logic in dashboard files — all delegated to `src/pipeline/` or `src/chatbot/`.
- [ ] `@st.cache_resource` used for all heavy objects.
- [ ] All widgets have unique `key=` parameters.
- [ ] `DIMENSION_MAP` from `src.dashboard.dimensions` — not redeclared inline.
- [ ] No inline hex colour values in Python — only in `styles.css`.
- [ ] `pluralize` used wherever count + noun is displayed.
- [ ] Dashboard tested by running headless and checking HTTP 200 OK.
- [ ] `tests/test_dashboard.py` passes after changes.
