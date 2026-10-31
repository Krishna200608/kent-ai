"""7-Segment Live Symptom Dimension Totality Strip HTML & Streamlit renderer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional
import streamlit as st

from src.dashboard.dimensions import KENT_DIMENSIONS_ORDERED
from src.dashboard.utils import esc

if TYPE_CHECKING:
    from src.chatbot.dialogue_manager import DialogueManager


def render_slot_badges_html(slots: Dict[str, List[str]], dm: Optional[DialogueManager] = None) -> str:
    """Render single, high-contrast 7-segment Live Symptom Dimension Strip."""
    segments_html = []

    for dim in KENT_DIMENSIONS_ORDERED:
        items = slots.get(dim.key, [])
        is_filled = bool(items) or (dm is not None and (dim.key in dm.state_machine.filled_slots or dm.detected_dimensions.get(dim.key, False)))
        if is_filled:
            val_str = ", ".join(esc(it) for it in items) if items else "Recorded"
            title_text = esc(f"{dim.label} ({dim.code}): {dim.captures}\nCaptured: {', '.join(items)}")
            segments_html.append(
                f'<div class="hud-segment hud-segment-filled {dim.badge_class}" title="{title_text}" data-code="{dim.code}">'
                f'<div class="hud-dim-title"><span class="status-dot" style="width:6px;height:6px;display:inline-block;margin-right:4px;"></span>{esc(dim.label)}</div>'
                f'<div class="hud-dim-sub" style="white-space: normal; line-height: 1.25;">{val_str}</div>'
                f'</div>'
            )
        else:
            rec_tag = " <span style='font-size:9px; color:#F59E0B;'>(Recommended)</span>" if dim.key in ("modality_amel", "temporal") else ""
            title_text = esc(f"{dim.label} ({dim.code}): {dim.captures}\nStatus: Not recorded yet")
            segments_html.append(
                f'<div class="hud-segment hud-segment-unfilled" title="{title_text}" data-code="{dim.code}">'
                f'<div class="hud-dim-title">{esc(dim.label)}{rec_tag}</div>'
                f'<div class="hud-dim-sub" style="color: #9CA3AF;">Not recorded yet</div>'
                f'</div>'
            )

    return f'<div class="hud-segments-grid">{ "".join(segments_html) }</div>'


def render_slot_badges(slots: Dict[str, List[str]]) -> None:
    """Render slot badges into Streamlit DOM."""
    st.markdown(render_slot_badges_html(slots), unsafe_allow_html=True)
