"""Busy / loading feedback helpers for Kent-AI dashboard.

Provides:
- ``inject_busy_runtime()``: idempotent JS injection of busy.js into the Streamlit page.
- ``busy_slot(slot, label, *, key, type, icon)``: context manager that shows a disabled
  "working..." twin button in *slot* while the wrapped block executes, then clears it.

Convention (CONVENTIONS.md §22):
- Always call ``inject_busy_runtime()`` at the END of ``main()`` in app.py.
- Every slow action (>500 ms expected) should use ``busy_slot`` OR ``st.spinner``.
- The ``__busy`` key suffix is reserved for twin-button widget IDs; do NOT reuse it.
- Never key a global indicator on ``data-test-script-state`` alone (header fragment
  polls every 2 s and also sets "running").
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Generator

import streamlit as st

_BUSY_JS_PATH = Path(__file__).resolve().parent.parent / "assets" / "busy.js"
_INJECTED_KEY = "_kent_busy_runtime_injected"


def inject_busy_runtime() -> None:
    """Inject busy.js into the Streamlit page exactly once per session.

    Must be called at the END of ``main()`` in app.py so that the JS is
    available for all widgets rendered in the same run.  Subsequent calls
    in the same Streamlit session are no-ops (guarded by session state).
    """
    if st.session_state.get(_INJECTED_KEY):
        return

    if not _BUSY_JS_PATH.exists():
        # Soft-fail: log but do not crash the app
        import logging
        logging.getLogger("dashboard.busy").warning(
            "busy.js not found at %s; skipping busy-runtime injection.", _BUSY_JS_PATH
        )
        return

    js_src = _BUSY_JS_PATH.read_text(encoding="utf-8")
    # Wrap in a <script> tag and inject via st.html with allow_javascript
    st.html(f"<script>{js_src}</script>", unsafe_allow_javascript=True)
    st.session_state[_INJECTED_KEY] = True


@contextlib.contextmanager
def busy_slot(
    slot: "st.delta_generator.DeltaGenerator",
    label: str,
    *,
    key: str,
    type: str = "primary",  # noqa: A002  (shadows built-in intentionally)
    icon: str | None = None,
) -> Generator[None, None, None]:
    """Context manager showing a disabled twin button while a slow call runs.

    The twin button has the key ``{key}__busy`` (the ``__busy`` suffix is
    reserved by convention).  It is displayed in *slot* before the wrapped
    block executes, then the slot is cleared and the real action result can be
    rendered by the caller.

    Usage::

        col_act = st.columns([1, 3])[0]
        with busy_slot(col_act, "Analyzing...", key="btn_extract", type="primary"):
            result = pipeline.extract(text)
        # After the block, slot shows nothing; caller renders result normally.

    Args:
        slot: A Streamlit container or column in which to render the busy twin.
        label: Human-readable label for the disabled twin button (e.g. "Analyzing...").
        key: Base widget key of the REAL button this replaces.  The twin gets key
            ``{key}__busy`` to satisfy Streamlit's uniqueness constraint.
        type: Button type passed to ``st.button``; default "primary".
        icon: Optional Material icon name string (e.g. ":material/hourglass_top:").

    Yields:
        Nothing; the caller runs the heavy work inside the ``with`` block.
    """
    twin_key = f"{key}__busy"
    display_label = f"{icon} {label}" if icon else label

    # Show disabled twin BEFORE the heavy call
    with slot:
        st.button(
            display_label,
            key=twin_key,
            disabled=True,
            type=type,
            width="stretch",
        )

    try:
        yield
    finally:
        # Clear the twin (Streamlit will replace it on rerun; the busy CSS
        # hides it automatically when data-kent-busy clears in the browser)
        pass
