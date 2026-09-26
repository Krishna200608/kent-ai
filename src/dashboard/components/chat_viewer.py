"""Chat viewer component for interactive clinical intake (Phase 7)."""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict, List

from src.chatbot.dialogue_manager import DialogueManager
from src.dashboard.components.icons import get_icon


def render_slot_badges_html(slots: Dict[str, List[str]]) -> str:
    """Render color-coded Google Stitch pill badges for extracted dimensions."""
    badge_html = []
    
    dim_config = [
        ("LOC", slots.get("location", []), "badge-loc"),
        ("SEN", slots.get("sensation", []), "badge-sen"),
        ("AGG", slots.get("modality_agg", []), "badge-agg"),
        ("AMEL", slots.get("modality_amel", []), "badge-amel"),
        ("CONC", slots.get("concomitant", []), "badge-conc"),
        ("TEMP", slots.get("temporal", []), "badge-temp"),
        ("MENT", slots.get("mental", []), "badge-ment"),
    ]

    has_any = False
    for label, items, css_class in dim_config:
        for item in items:
            has_any = True
            badge_html.append(f'<span class="badge {css_class}"><b>{label}:</b> {item}</span>')

    if not has_any:
        return "<p style='color: #6B7280; font-size: 13px; margin: 0;'><i>Listening for symptoms (Location, Sensation, Modalities, Time, Mind)...</i></p>"
    return "".join(badge_html)


def render_slot_badges(slots: Dict[str, List[str]]) -> None:
    """Render slot badges into Streamlit DOM."""
    st.markdown(render_slot_badges_html(slots), unsafe_allow_html=True)


def render_chat_interface(dm: DialogueManager) -> None:
    """Render multi-turn conversation and slot tracking."""
    state_name = dm.state_machine.current_state.value
    filled = len(dm.state_machine.filled_slots)

    hud_html = f"""
    <div class="stGlassCard" style="margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                {get_icon('track_changes', color='#10B981', size=20)}
                <span style="font-weight: 700; font-size: 15px; color: #F9FAFB;">Live Symptom Dimension HUD</span>
            </div>
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 11px; color: #9CA3AF; text-transform: uppercase;">Stage: <b style="color: #10B981;">{state_name}</b></span>
                <span style="font-size: 11px; color: #06B6D4;">Totality: <b>{filled}/7</b></span>
            </div>
        </div>
        <div>
            {render_slot_badges_html(dm.extracted_slots)}
        </div>
    </div>
    """
    st.markdown(hud_html, unsafe_allow_html=True)
    st.progress(min(1.0, max(0.0, filled / 7.0)))

    # Chat history display container
    for msg in dm.history:
        role = msg["role"]
        content = msg["content"]
        if role == "assistant":
            with st.chat_message("assistant", avatar="assistant"):
                st.markdown(content)
        else:
            with st.chat_message("user", avatar="user"):
                st.markdown(content)

    # Dynamic contextual suggestion chips based on active stage
    suggestion_map = {
        "GREETING": ["My head hurts severely", "I have stomach burning", "Feeling anxious and exhausted"],
        "LOCATION": ["Forehead and temples", "Stomach & epigastrium", "Right side of chest", "Lower back & lumbar"],
        "SENSATION": ["Throbbing, pulsating sensation", "Sharp stabbing pains", "Burning like hot coal", "Dull heavy pressure"],
        "MODALITY_AGG": ["Worse in the heat & sun", "Worse from cold draft & open air", "Worse from any movement", "Worse after eating meals"],
        "MODALITY_AMEL": ["Better with cold water compresses", "Better lying down in a dark room", "Better with gentle walking", "Better with warm drinks"],
        "TEMPORAL": ["Worse in morning on waking", "Worse in the evening at twilight", "Worse after midnight (2-3 AM)", "Constant all day"],
        "MENTAL": ["Very restless and anxious", "Irritable and impatient", "Depressed and want to be alone", "No change in mood"],
        "REVIEW": ["Yes, that covers all my symptoms!", "Please analyze and repertorize", "I also noticed nausea with the headache"],
    }
    current_suggestions = suggestion_map.get(dm.state_machine.current_state.name, ["That's all my symptoms", "I feel better now"])

    st.markdown("<div style='font-size: 12px; color: #9CA3AF; margin: 12px 0 6px 2px;'>Quick clinical suggestions:</div>", unsafe_allow_html=True)
    chip_cols = st.columns(len(current_suggestions))
    selected_chip = None
    for idx, suggestion in enumerate(current_suggestions):
        with chip_cols[idx]:
            if st.button(suggestion, key=f"chip_{idx}_{dm.state_machine.current_state.name}", use_container_width=True):
                selected_chip = suggestion

    # Chat input
    user_prompt = st.chat_input("Tell Kent-AI how you are feeling (e.g. 'My head hurts when in the sun')...")
    
    input_to_process = selected_chip or user_prompt
    if input_to_process:
        with st.chat_message("user", avatar="user"):
            st.markdown(input_to_process)

        with st.spinner("Kent-AI is reflecting..."):
            bot_reply = dm.process_turn(input_to_process)

        with st.chat_message("assistant", avatar="assistant"):
            st.markdown(bot_reply)
        st.rerun()
