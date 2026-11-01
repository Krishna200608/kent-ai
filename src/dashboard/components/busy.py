"""Busy-state feedback helpers (click feedback runtime and label-swap helper)."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional

import streamlit as st

_JS_PATH = Path(__file__).resolve().parent.parent / "assets" / "busy.js"


def inject_busy_runtime() -> None:
    """Inject the click-feedback runtime (idempotent in the browser via a window flag)."""
    if _JS_PATH.is_file():
        st.html(f"<script>{_JS_PATH.read_text(encoding='utf-8')}</script>", unsafe_allow_javascript=True)


@contextmanager
def busy_slot(
    slot: Any,
    label: str,
    *,
    key: str,
    type: str = "secondary",
    icon: Optional[str] = None,
) -> Iterator[None]:
    """Replace a clicked button with a disabled 'working' twin while a slow call runs.

    Why: gives a real label change ("Analyzing rubrics...") and server-side double-submit
    protection. The twin key ends with '__busy' so styles.css can show a spinner on it.
    """
    slot.button(label, key=f"{key}__busy", type=type, disabled=True, width="stretch", icon=icon)
    try:
        yield
    finally:
        slot.empty()
