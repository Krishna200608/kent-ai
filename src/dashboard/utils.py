"""Clinical Dashboard Utilities (Phase 7)."""

from __future__ import annotations

import html
from typing import Any


def esc(x: Any) -> str:
    """HTML escape helper for safe template interpolation."""
    return html.escape(str(x or ""), quote=True)


def safe_rerun_fragment() -> None:
    """Safely trigger a fragment rerun with fallback to standard rerun.

    Prevents StreamlitInvalidLayoutContextError when called outside an active fragment rerun,
    such as during programmatic testing with AppTest or non-fragment execution paths.
    """
    import streamlit as st

    try:
        st.rerun(scope="fragment")
    except Exception:
        st.rerun()


