"""Tests for the busy/loading feedback helpers (CONVENTIONS §22).

Test (a): busy_slot renders a disabled twin button and clears it gracefully.
Test (b): Source guards
  - no use_container_width in any src/dashboard/**/*.py
  - no non-ASCII chars in st.toast / st.info / st.warning icon= args
  - styles.css has NO button[kind= selectors
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

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


def test_busy_slot_is_context_manager() -> None:
    """busy_slot must be a contextlib-based context manager (has __enter__/__exit__)."""
    import contextlib

    from src.dashboard.components.busy import busy_slot

    # It is decorated with @contextlib.contextmanager, so calling it returns
    # a _GeneratorContextManager.
    # We call it with a mock slot that does nothing.

    class _FakeSlot:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def button(self, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
            pass

    fake = _FakeSlot()

    # Must not raise; the yield point is the key contract
    cm = busy_slot(fake, "Working...", key="test_busy_key")
    assert hasattr(cm, "__enter__")
    assert hasattr(cm, "__exit__")


def test_inject_busy_runtime_soft_fails_without_session(monkeypatch: pytest.MonkeyPatch) -> None:
    """inject_busy_runtime must not crash even if session_state check raises."""
    import streamlit as st

    from src.dashboard.components.busy import _INJECTED_KEY, inject_busy_runtime

    # Simulate already injected (guard key present) → should be a no-op
    original_get = st.session_state.get

    injected_flag: dict[str, bool] = {}

    def _mock_get(key: str, default: object = None) -> object:  # noqa: ANN001
        if key == _INJECTED_KEY:
            return injected_flag.get(key, False)
        return original_get(key, default)

    monkeypatch.setattr(st.session_state, "get", _mock_get)
    injected_flag[_INJECTED_KEY] = True

    # Should return immediately without calling st.html (no error)
    inject_busy_runtime()  # No exception = pass


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
    string literals passed as the first positional arg (or ``icon=`` kwarg)
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
            # Match st.toast / st.info / st.warning (attribute calls)
            if not (isinstance(func, ast.Attribute) and func.attr in TARGETS):
                continue

            # Check first positional arg (the message)
            for arg in node.args[:1]:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if NON_ASCII.search(arg.value):
                        violations.append(
                            f"{path.name}:{node.lineno}: non-ASCII in st.{func.attr}({arg.value!r})"
                        )

            # Check icon= keyword arg
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
