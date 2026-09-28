"""Google Stitch Design System & CSS theme injection for Streamlit (Phase 7)."""

from __future__ import annotations

from pathlib import Path
import streamlit as st

_CSS_PATH = Path(__file__).resolve().parent / "styles.css"


def inject_custom_css() -> None:
    """Inject custom Google Stitch clinical dark-mode CSS and typography into Streamlit DOM."""
    if _CSS_PATH.is_file():
        if hasattr(st, "html"):
            st.html(_CSS_PATH)
        else:
            css = _CSS_PATH.read_text(encoding="utf-8")
            st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)
