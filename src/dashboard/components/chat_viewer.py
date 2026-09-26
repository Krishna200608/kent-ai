"""Chat viewer component for interactive clinical intake (Phase 7)."""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict, List

from src.chatbot.dialogue_manager import DialogueManager


def render_slot_badges(slots: Dict[str, List[str]]) -> None:
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
        st.markdown("<p style='color: #6B7280; font-size: 13px; margin: 0;'><i>Listening for symptoms (Location, Sensation, Modalities, Time, Mind)...</i></p>", unsafe_allow_html=True)
    else:
        st.markdown("".join(badge_html), unsafe_allow_html=True)


def render_chat_interface(dm: DialogueManager) -> None:
    """Render multi-turn conversation and slot tracking."""
    # Top slot tracking card
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(
                "<h4 style='margin:0 0 8px 0;'><span class='material-symbols-outlined' style='vertical-align:middle; color:#10B981; margin-right:6px;'>track_changes</span> Live Symptom Dimension HUD</h4>",
                unsafe_allow_html=True,
            )
            render_slot_badges(dm.extracted_slots)
        with col2:
            state_name = dm.state_machine.current_state.value
            filled = len(dm.state_machine.filled_slots)
            st.markdown(
                f"""
                <div style='text-align: right;'>
                    <div style='font-size: 11px; color: #9CA3AF; text-transform: uppercase;'>Current Stage</div>
                    <div style='font-weight: 700; color: #10B981; font-size: 15px;'>{state_name}</div>
                    <div style='font-size: 12px; color: #06B6D4; margin-top: 2px;'>Totality: {filled}/7 dimensions</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.progress(min(1.0, max(0.0, filled / 7.0)))

    # Chat history display container
    for msg in dm.history:
        role = msg["role"]
        content = msg["content"]
        if role == "assistant":
            with st.chat_message("assistant", avatar=":material/local_florist:"):
                st.markdown(content)
        else:
            with st.chat_message("user", avatar=":material/person:"):
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

    st.markdown("<div style='font-size: 12px; color: #9CA3AF; margin: 10px 0 4px 2px;'>Quick clinical suggestions:</div>", unsafe_allow_html=True)
    chip_cols = st.columns(len(current_suggestions))
    selected_chip = None
    for idx, suggestion in enumerate(current_suggestions):
        with chip_cols[idx]:
            if st.button(suggestion, icon=":material/chat_bubble:", key=f"chip_{idx}_{dm.state_machine.current_state.name}", use_container_width=True):
                selected_chip = suggestion

    # Chat input
    user_prompt = st.chat_input("Tell Kent-AI how you are feeling (e.g. 'My head hurts when in the sun')...")
    
    input_to_process = selected_chip or user_prompt
    if input_to_process:
        with st.chat_message("user", avatar=":material/person:"):
            st.markdown(input_to_process)

        with st.spinner("Kent-AI is reflecting..."):
            bot_reply = dm.process_turn(input_to_process)

        with st.chat_message("assistant", avatar=":material/local_florist:"):
            st.markdown(bot_reply)
        st.rerun()

