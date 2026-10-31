"""Clickable suggestion chip pills and instant quick-response actuation for clinical intake."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import streamlit as st

from src.dashboard.components.icons import get_icon

if TYPE_CHECKING:
    from src.chatbot.dialogue_manager import DialogueManager


def render_quick_reply_chips(dm: DialogueManager, in_container: bool = False) -> Optional[str]:
    """Render dynamic instant answer chips tailored to Kent-AI's active question using st.pills."""
    current_suggestions = dm.get_current_suggestions()
    if not current_suggestions:
        return None

    display_chips = list(current_suggestions[:4])
    if "None of these / other" not in display_chips and len(display_chips) < 4:
        display_chips.append("None of these / other")

    title_margin = "8px 0 4px 2px" if in_container else "10px 0 4px 2px"
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin: {title_margin};">
            <span style="font-size: 12.5px; font-weight: 600; color: #10B981; display: flex; align-items: center; gap: 6px;">
                {get_icon('sparkles', size=15, color='#10B981')} Suggested Responses:
            </span>
            <span style="font-size: 11px; color: #9CA3AF;">Click to reply instantly</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected = st.pills(
        "Suggested Responses:",
        display_chips,
        key=f"pills_turn_{dm.state_machine.turn_count}_{'box' if in_container else 'dock'}",
        label_visibility="collapsed",
    )
    if selected:
        dm.current_suggestions = []  # Clear immediately so stale chips never linger
    return selected
