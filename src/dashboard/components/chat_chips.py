"""Clickable suggestion chip pills and instant quick-response actuation for clinical intake (Phase 4 & UI Overhaul)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional
import streamlit as st

from src.dashboard.components.icons import get_icon

if TYPE_CHECKING:
    from src.chatbot.dialogue_manager import DialogueManager


# Step-aware neutral suggestion templates (Phase 4 UI Overhaul & clinical fallback)
NEUTRAL_STEP_SUGGESTIONS: Dict[str, List[str]] = {
    "GREETING": [
        "I'd like to describe how I feel",
        "I have a physical complaint",
        "It's mostly emotional",
        "Severe recurring headache",
    ],
    "CHIEF_COMPLAINT": [
        "Severe throbbing headache",
        "Stomach pain & acid reflux",
        "Aching joints & stiffness",
        "Anxiety & trouble sleeping",
    ],
    "LOCATION": [
        "Forehead and temples",
        "Stomach & abdomen",
        "Chest and throat",
        "Lower back & joints",
    ],
    "SENSATION": [
        "Throbbing and pulsating",
        "Sharp stabbing pain",
        "Dull heavy ache",
        "Burning sensation",
    ],
    "MODALITY": [
        "Worse from warmth or heat",
        "Worse in cold or open air",
        "Better from resting quietly",
        "Better from gentle motion",
    ],
    "CONCOMITANT": [
        "Accompanied by nausea",
        "Dizziness and lightheadedness",
        "Chills and cold sweat",
        "No other symptoms",
    ],
    "TEMPORAL": [
        "Worse in the morning",
        "Worse in the evening or night",
        "Worse after midnight (2-3 AM)",
        "No particular time pattern",
    ],
    "MENTAL": [
        "I feel anxious or restless",
        "I feel irritable and impatient",
        "I prefer to be left alone",
        "My mood is relatively calm",
    ],
    "REVIEW": [
        "Yes, that covers all my symptoms!",
        "I'd like to clarify something",
        "Please proceed to repertorization",
        "Ready to view my remedies",
    ],
    "DONE": [
        "Proceed to Review",
        "Check my captured totality",
        "Start New Consultation",
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

    # 3. Fetch suggestions from dialogue manager (intent-first or LLaMA quick replies)
    suggestions = dm.get_current_suggestions()
    if not suggestions:
        curr_state = dm.state_machine.current_state.value if hasattr(dm.state_machine.current_state, "value") else str(dm.state_machine.current_state)
        suggestions = NEUTRAL_STEP_SUGGESTIONS.get(curr_state, [])

    if not suggestions:
        return None

    display_chips = list(suggestions[:5])

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

    hist_len = len(getattr(dm, "history", []))
    turn_cnt = getattr(dm.state_machine, "turn_count", 0)
    selected = st.pills(
        "Suggested Responses:",
        display_chips,
        key=f"pills_t{turn_cnt}_h{hist_len}_{'box' if in_container else 'dock'}",
        label_visibility="collapsed",
    )
    if selected:
        dm.current_suggestions = []  # Clear immediately so stale chips never linger
    return selected
