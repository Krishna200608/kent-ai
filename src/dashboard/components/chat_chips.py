"""Clickable suggestion chip pills and instant quick-response actuation for clinical intake (Phase 4 & UI Overhaul)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional
import streamlit as st

from src.dashboard.components.icons import get_icon

if TYPE_CHECKING:
    from src.chatbot.dialogue_manager import DialogueManager


# Step-aware neutral suggestion templates (Phase 4 UI Overhaul)
NEUTRAL_STEP_SUGGESTIONS: Dict[str, List[str]] = {
    "GREETING": [
        "I'd like to describe how I feel",
        "I have a physical complaint",
        "It's mostly emotional",
    ],
    "CHIEF_COMPLAINT": [
        "It started recently",
        "It has been ongoing for a while",
        "It comes and goes in episodes",
    ],
    "LOCATION": [
        "It affects a specific area",
        "It spreads across multiple places",
        "It feels deep inside",
    ],
    "SENSATION": [
        "It is sharp or intense",
        "It feels dull and aching",
        "It feels throbbing or pulsing",
        "It is a burning or tingling sensation",
    ],
    "MODALITY": [
        "Worse from warmth or heat",
        "Worse in cold or open air",
        "Better from resting quietly",
        "Better from gentle motion",
    ],
    "CONCOMITANT": [
        "I feel tired or nauseous with it",
        "There are no other symptoms",
        "It comes with sweating or chills",
    ],
    "TEMPORAL": [
        "Worse in the morning",
        "Worse in the evening or night",
        "Worse at a specific time of day",
        "No particular time pattern",
    ],
    "MENTAL": [
        "I feel anxious or restless",
        "I feel irritable and impatient",
        "I prefer to be left alone",
        "My mood is unaffected",
    ],
    "REVIEW": [
        "Everything looks accurate",
        "I'd like to clarify something",
        "No further symptoms to add",
    ],
    "DONE": [
        "Proceed to Review",
        "Check my captured totality",
    ],
}


def render_quick_reply_chips(dm: DialogueManager, in_container: bool = False) -> Optional[str]:
    """Render dynamic instant answer chips tailored to Kent-AI's active question using st.pills.

    Hides suggestions when:
    - User is in Practitioner mode (Speaking as = Practitioner)
    - Settings toggle 'Show suggested replies' is disabled
    """
    # 1. Hide if disabled in settings
    if not st.session_state.get("show_suggested_replies", True):
        return None

    # 2. Hide when Speaking as = Practitioner
    is_practitioner = getattr(dm, "intake_mode", "patient") == "practitioner"
    if is_practitioner:
        return None

    # 3. Determine current state and fetch neutral suggestions
    curr_state = dm.state_machine.current_state.value if hasattr(dm.state_machine.current_state, "value") else str(dm.state_machine.current_state)
    suggestions = NEUTRAL_STEP_SUGGESTIONS.get(curr_state)
    if not suggestions:
        suggestions = dm.get_current_suggestions()

    if not suggestions:
        return None

    display_chips = list(suggestions[:4])

    title_margin = "6px 0 4px 2px" if in_container else "8px 0 4px 2px"
    st.html(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin: {title_margin};">
            <span style="font-size: 12px; font-weight: 600; color: var(--accent, #10B981); display: flex; align-items: center; gap: 5px;">
                {get_icon('sparkles', size=14, color='var(--accent, #10B981)')} Suggested Responses
            </span>
            <span style="font-size: 11px; color: var(--text-faint, #8A98AE);">Click to reply instantly</span>
        </div>
        """
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
