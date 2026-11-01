"""Reusable 7-segment Totality Ring SVG component (Phase 1 & UI Overhaul).

Renders a signature circular 7-segment glyph representing the 7 canonical
homeopathic symptom dimensions, lit up when captured.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Set, Union
from src.dashboard.constants import CANONICAL_DIMENSIONS_ORDERED, INTERNAL_TO_CANONICAL


# Precalculated arc paths for 7 segments on 36x36 viewBox (center 18,18, radius 13.5, 6deg gap)
_CX = 18.0
_CY = 18.0
_RADIUS = 13.5
_GAP_DEG = 6.0
_STEP_DEG = 360.0 / 7.0
_ARC_DEG = _STEP_DEG - _GAP_DEG

_RING_PATHS: List[str] = []
for _i in range(7):
    _start_deg = -90.0 + _i * _STEP_DEG + (_GAP_DEG / 2.0)
    _end_deg = _start_deg + _ARC_DEG
    _x1 = _CX + _RADIUS * math.cos(math.radians(_start_deg))
    _y1 = _CY + _RADIUS * math.sin(math.radians(_start_deg))
    _x2 = _CX + _RADIUS * math.cos(math.radians(_end_deg))
    _y2 = _CY + _RADIUS * math.sin(math.radians(_end_deg))
    _RING_PATHS.append(f"M {_x1:.2f} {_y1:.2f} A {_RADIUS:.2f} {_RADIUS:.2f} 0 0 1 {_x2:.2f} {_y2:.2f}")


def _extract_captured_flags(captured: Any) -> tuple[List[bool], int]:
    """Extract 7-boolean list of captured dimensions and total count."""
    flags = [False] * 7
    dim_keys = [d.key for d in CANONICAL_DIMENSIONS_ORDERED]

    if isinstance(captured, int):
        count = max(0, min(7, captured))
        for i in range(count):
            flags[i] = True
        return flags, count

    if captured is None:
        return flags, 0

    # Support ClinicalCase object directly
    if hasattr(captured, "dimensions"):
        dims = getattr(captured, "dimensions", {})
        if isinstance(dims, dict):
            captured = dims
    elif hasattr(captured, "symptoms"):
        symptoms = getattr(captured, "symptoms", {})
        if isinstance(symptoms, dict):
            captured = symptoms

    # Support DialogueManager object directly
    if hasattr(captured, "extracted_slots"):
        slots = getattr(captured, "extracted_slots", {})
        filled = set(getattr(getattr(captured, "state_machine", None), "filled_slots", set()))
        captured_set = set()
        for k, v in slots.items():
            if bool(v):
                captured_set.add(k)
        captured_set.update(filled)
        captured = captured_set

    # If it's a dict
    if isinstance(captured, dict):
        for idx, dim in enumerate(CANONICAL_DIMENSIONS_ORDERED):
            # Check canonical key or internal key
            val = captured.get(dim.key) or captured.get(dim.internal_key)
            if bool(val):
                flags[idx] = True

    # If it's a set or list
    elif isinstance(captured, (set, list, tuple)):
        # Normalize items
        norm_items = set()
        for item in captured:
            k = str(item).strip()
            canonical_k = INTERNAL_TO_CANONICAL.get(k, k)
            norm_items.add(canonical_k)
        for idx, dim in enumerate(CANONICAL_DIMENSIONS_ORDERED):
            if dim.key in norm_items or dim.internal_key in norm_items:
                flags[idx] = True

    count = sum(1 for f in flags if f)
    return flags, count


def totality_ring(
    captured: Any,
    size: int = 28,
    show_count: bool = False,
    class_name: str = "",
) -> str:
    """Generate SVG markup for 7-segment totality ring.

    Args:
        captured: Int count (0-7), sequence/set of dimension keys, dict of symptoms,
                  ClinicalCase, or DialogueManager instance.
        size: Width and height of the SVG glyph in pixels.
        show_count: If True or if size >= 36, render captured count number in the center.
        class_name: Optional CSS class to append to the svg tag.

    Returns:
        Self-contained HTML SVG string.
    """
    flags, count = _extract_captured_flags(captured)

    # Render segments
    segments_svg = []
    for idx, (path_d, is_lit) in enumerate(zip(_RING_PATHS, flags)):
        dim = CANONICAL_DIMENSIONS_ORDERED[idx]
        stroke_color = "var(--accent, #10B981)" if is_lit else "var(--line, #243243)"
        stroke_width = "3.2" if is_lit else "2.4"
        title_text = f"{dim.label}: {'Captured' if is_lit else 'Not recorded'}"
        seg = (
            f'<path d="{path_d}" fill="none" stroke="{stroke_color}" '
            f'stroke-width="{stroke_width}" stroke-linecap="round">'
            f'<title>{title_text}</title></path>'
        )
        segments_svg.append(seg)

    # Center count text if requested
    center_text = ""
    if show_count or size >= 36:
        font_sz = max(9, int(size * 0.32))
        center_text = (
            f'<text x="18" y="21.5" text-anchor="middle" font-family="var(--font-ui, system-ui)" '
            f'font-size="{font_sz}" font-weight="700" fill="var(--text, #E8EDF3)">{count}</text>'
        )

    title_all = f"{count} of 7 totality dimensions captured"
    cls_attr = f' class="totality-ring {class_name}"' if class_name else ' class="totality-ring"'

    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 36 36"{cls_attr} '
        f'role="img" aria-label="{title_all}" style="vertical-align: middle; flex-shrink: 0;">'
        f'<title>{title_all}</title>'
        f'{"".join(segments_svg)}'
        f'{center_text}'
        f'</svg>'
    )


render_totality_ring = totality_ring

__all__ = ["totality_ring", "render_totality_ring"]

