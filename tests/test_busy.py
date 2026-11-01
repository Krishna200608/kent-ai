"""Tests for the busy/loading feedback helpers (CONVENTIONS §22).

Test (a): busy_slot renders a disabled twin button and clears it gracefully.
Test (b): Source guards
  - no use_container_width in any src/dashboard/**/*.py
  - no non-ASCII chars in st.toast / st.info / st.warning icon= args (allow :material/...:)
  - styles.css has NO button[kind= selectors
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "src" / "dashboard"
STYLES_CSS = DASHBOARD_DIR / "styles.css"


def _collect_py_files(base: Path) -> list[Path]:
    """Return all .py files under *base* recursively."""
    return list(base.rglob("*.py"))


# ---------------------------------------------------------------------------
# (a) busy_slot import & interface sanity
# ---------------------------------------------------------------------------


def test_busy_module_importable() -> None:
    """busy.py must import without error."""
    from src.dashboard.components.busy import busy_slot, inject_busy_runtime  # noqa: F401

    assert callable(busy_slot)
    assert callable(inject_busy_runtime)


def test_busy_slot_renders_twin_and_clears() -> None:
    """busy_slot shows a disabled '__busy' twin during the call and clears it after."""
    from src.dashboard.components.busy import busy_slot

    mock_slot = MagicMock()
    with busy_slot(mock_slot, "Analyzing rubrics...", key="btn_rep", type="primary"):
        mock_slot.button.assert_called_once_with(
            "Analyzing rubrics...",
            key="btn_rep__busy",
            type="primary",
            disabled=True,
            width="stretch",
            icon=None,
        )
        assert mock_slot.empty.call_count == 0

    mock_slot.empty.assert_called_once()


def test_inject_busy_runtime_calls_html(monkeypatch: pytest.MonkeyPatch) -> None:
    """inject_busy_runtime injects script tag with unsafe_allow_javascript=True."""
    import streamlit as st

    from src.dashboard.components.busy import inject_busy_runtime

    mock_html = MagicMock()
    monkeypatch.setattr(st, "html", mock_html)

    inject_busy_runtime()
    mock_html.assert_called_once()
    args, kwargs = mock_html.call_args
    assert "<script>" in args[0]
    assert "window.__kentBusy" in args[0]
    assert kwargs.get("unsafe_allow_javascript") is True


# ---------------------------------------------------------------------------
# (b) Source guards
# ---------------------------------------------------------------------------


def test_no_use_container_width_in_dashboard() -> None:
    """No src/dashboard/**/*.py file may call use_container_width=True."""
    violations: list[str] = []
    for f in _collect_py_files(DASHBOARD_DIR):
        src = f.read_text(encoding="utf-8", errors="replace")
        if "use_container_width" in src:
            violations.append(str(f.relative_to(DASHBOARD_DIR.parent.parent)))
    assert not violations, (
        "use_container_width found in dashboard files (use width='stretch' instead):\n"
        + "\n".join(violations)
    )


def test_no_button_kind_selectors_in_css() -> None:
    """styles.css must not contain button[kind= attribute selectors."""
    if not STYLES_CSS.exists():
        pytest.skip("styles.css not found")
    css = STYLES_CSS.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(r'button\[kind\s*=', css)
    assert not matches, (
        f"Found {len(matches)} obsolete button[kind= selector(s) in styles.css. "
        "Replace with button[data-testid^='stBaseButton-*'] per GOTCHAS §8.21."
    )


def test_no_emoji_in_toast_args() -> None:
    """st.toast / st.info / st.warning calls must use ASCII-only strings.

    We parse the AST of every dashboard Python file and check that all
    string literals passed as the first positional arg (or icon= kwarg)
    to those functions contain only printable ASCII characters (ord < 128).
    """
    NON_ASCII = re.compile(r"[^\x00-\x7F]")
    TARGETS = {"toast", "info", "warning", "error", "success"}
    violations: list[str] = []

    for path in _collect_py_files(DASHBOARD_DIR):
        src_text = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(src_text, filename=str(path))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr in TARGETS):
                continue

            for arg in node.args[:1]:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if NON_ASCII.search(arg.value):
                        violations.append(
                            f"{path.name}:{node.lineno}: non-ASCII in st.{func.attr}({arg.value!r})"
                        )

            for kw in node.keywords:
                if kw.arg == "icon" and isinstance(kw.value, ast.Constant):
                    val = kw.value.value
                    if isinstance(val, str) and NON_ASCII.search(val):
                        violations.append(
                            f"{path.name}:{node.lineno}: non-ASCII icon= in st.{func.attr}(icon={val!r})"
                        )

    assert not violations, (
        "Non-ASCII / emoji found in st.toast/info/warning calls "
        "(use ASCII text or :material/icon_name: string literals):\n"
        + "\n".join(violations)
    )
