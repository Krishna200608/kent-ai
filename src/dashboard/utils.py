"""Clinical Dashboard Utilities (Phase 7)."""

from __future__ import annotations

import html
from typing import Any


def esc(x: Any) -> str:
    """HTML escape helper for safe template interpolation."""
    return html.escape(str(x or ""), quote=True)
