---
name: frontend-design
description: >
  Streamlit UI design and improvement skill for the kent-ai dashboard.
  Use when adding new pages, improving existing components, fixing layout
  issues, or enhancing the visual quality of the Streamlit interface in
  src/dashboard/. Covers layout, theming, component selection, and
  accessibility.
---

# Frontend Design Skill — Kent-AI (Streamlit)

## Scope
All UI work lives in `src/dashboard/`. Do NOT mix UI logic with
business logic — the dashboard layer imports from `src/chatbot/`
and `src/search/` only (per `Context/ARCHITECTURE.md`).

---

## Streamlit Design Principles

### 1. Page Structure
Every Streamlit page file should follow this template:
```python
"""
Module: src/dashboard/<page_name>.py
Purpose: <one-line description>
"""
import streamlit as st
from src.chatbot import <...>   # or src.search

# ── Page config (set once, at the top) ─────────────────────────────
st.set_page_config(
    page_title="Kent AI — <Page Name>",
    page_icon="🏥",
    layout="wide",
)

# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Navigation")
    # ...

# ── Main content ─────────────────────────────────────────────────────
st.title("<Page Title>")
# ...
```

### 2. Theming
Use the `.streamlit/config.toml` for all colour/font settings.
Do NOT hardcode hex colours in Python — use `st.markdown` with CSS variables sparingly.

```toml
# .streamlit/config.toml
[theme]
primaryColor = "#4A90D9"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#1C2333"
textColor = "#FAFAFA"
font = "sans serif"
```

### 3. Component Hierarchy
| Purpose | Component |
|---|---|
| Status indicators | `st.metric()` |
| Structured output | `st.dataframe()` or `st.table()` |
| Long text / notes | `st.text_area()` |
| Progress | `st.progress()` + `st.spinner()` |
| Alerts | `st.success()`, `st.warning()`, `st.error()` |
| Charts | `st.plotly_chart()` (prefer over `st.bar_chart` for control) |

### 4. Performance
- Use `@st.cache_data` for functions that load data from SQLite or disk.
- Use `@st.cache_resource` for model objects (NER model, ChromaDB client).
- Never load a model inside a Streamlit callback — cache it at module level.

```python
@st.cache_resource
def load_ner_model():
    from src.models.ner_model import NERModel
    return NERModel()
```

### 5. Accessibility
- Every interactive widget must have a unique, descriptive `key=` parameter.
- Use `st.columns()` for responsive layout instead of fixed pixel widths.
- Ensure colour contrast meets WCAG AA (4.5:1 ratio for text).

---

## Dashboard Pages (Current)

| File | Purpose |
|---|---|
| `src/dashboard/main.py` | Entry point, navigation |
| `src/dashboard/case_viewer.py` | Display generated cases |
| `src/dashboard/rubric_search.py` | Rubric retrieval interface |
| `src/dashboard/chatbot_ui.py` | Chat interface |
| `src/dashboard/metrics.py` | Pipeline metrics and progress |

---

## Running Locally
```bash
streamlit run src/dashboard/main.py
```

## Checklist Before Committing UI Changes
- [ ] `@st.cache_resource` used for model/DB objects.
- [ ] No business logic in dashboard files — delegated to `src/chatbot/` or `src/search/`.
- [ ] All widgets have unique `key=` parameters.
- [ ] Page tested at both 1280px and 800px viewport widths.
- [ ] No hardcoded colour values in Python code.
