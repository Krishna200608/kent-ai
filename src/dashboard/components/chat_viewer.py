"""Chat viewer component for interactive clinical intake (Phase 7)."""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict, List, Optional

from src.chatbot.dialogue_manager import DialogueManager
from src.dashboard.components.icons import get_icon


KENT_DIMENSIONS = [
    ("Location", "Location", "location", "badge-loc", "LOC"),
    ("Sensation", "Sensation", "sensation", "badge-sen", "SEN"),
    ("Worse from", "Worse from", "modality_agg", "badge-agg", "MOD_AGG"),
    ("Better from", "Better from", "modality_amel", "badge-amel", "MOD_AMEL"),
    ("Concomitants", "Concomitants", "concomitant", "badge-conc", "CONC"),
    ("Temperature", "Temperature", "temporal", "badge-temp", "TEMP"),
    ("Mental", "Mental", "mental", "badge-ment", "MENT"),
]


def get_current_step_label(dm: DialogueManager) -> str:
    """Return compact Step X of 9 label."""
    stages = dm.state_machine.get_clinical_stage_flow()
    current_state = dm.state_machine.current_state

    current_idx = 0
    current_label = "Intake"
    for idx, (st_enum, label) in enumerate(stages):
        if st_enum == current_state:
            current_idx = idx
            current_label = label
            break

    return f"Step {current_idx + 1} of {len(stages)}: {current_label}"


def render_slot_badges_html(slots: Dict[str, List[str]], dm: Optional[DialogueManager] = None) -> str:
    """Render the 7-segment Live Symptom Dimension HUD in plain language with empty/filled states."""
    segments_html = []

    for disp_name, label, key, badge_class, code in KENT_DIMENSIONS:
        items = slots.get(key, [])
        is_filled = bool(items) or (dm is not None and (key in dm.state_machine.filled_slots or dm.detected_dimensions.get(key, False)))
        if is_filled:
            snippet = items[0] if items else "Recorded"
            if len(snippet) > 18:
                snippet = snippet[:16] + ".."
            title_text = f"{label} ({code}): {', '.join(items) if items else 'Recorded'}"
            segments_html.append(
                f'<div class="hud-segment hud-segment-filled {badge_class}" title="{title_text}" data-code="{code}">'
                f'<div class="hud-dim-title">● {disp_name}</div>'
                f'<div class="hud-dim-sub">{snippet}</div>'
                f'</div>'
            )
        else:
            segments_html.append(
                f'<div class="hud-segment hud-segment-unfilled" title="{label} ({code}): Not asked yet" data-code="{code}">'
                f'<div class="hud-dim-title">{disp_name}</div>'
                f'<div class="hud-dim-sub">Not asked yet</div>'
                f'</div>'
            )

    grid_markup = f'<div class="hud-segments-grid">{"".join(segments_html)}</div>'

    extracted_chips = []
    for disp_name, label, key, badge_class, code in KENT_DIMENSIONS:
        for item in slots.get(key, []):
            extracted_chips.append(
                f'<span class="badge {badge_class}" title="Dimension: {label} ({code}) | Value: {item}">'
                f'<b>{disp_name}:</b> {item} '
                f'</span>'
            )

    chips_markup = ""
    if extracted_chips:
        chips_markup = f'<div style="margin-top: 10px; display: flex; flex-wrap: wrap; gap: 6px;">{"".join(extracted_chips)}</div>'

    return grid_markup + chips_markup


def render_slot_badges(slots: Dict[str, List[str]]) -> None:
    """Render slot badges into Streamlit DOM."""
    st.markdown(render_slot_badges_html(slots), unsafe_allow_html=True)


def render_quick_reply_chips(dm: DialogueManager, in_container: bool = False) -> Optional[str]:
    """Render dynamic instant answer chips tailored to Kent-AI's active question."""
    current_suggestions = dm.get_current_suggestions()
    if not current_suggestions:
        return None

    title_margin = "10px 0 6px 2px" if in_container else "12px 0 6px 2px"
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin: {title_margin};">
            <span style="font-size: 13px; font-weight: 600; color: #10B981; display: flex; align-items: center; gap: 6px;">
                {get_icon('touch_app', size=16, color='#10B981')} Suggested Responses:
            </span>
            <span style="font-size: 11px; color: #9CA3AF;">Click to reply instantly</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected = None
    # Fluid 2-column wrapping layout so suggestions don't get squished or truncated
    cols = st.columns(2)
    for idx, suggestion in enumerate(current_suggestions):
        with cols[idx % 2]:
            if st.button(
                suggestion,
                key=f"chip_turn_{dm.state_machine.turn_count}_{idx}_{'box' if in_container else 'dock'}",
                use_container_width=True,
            ):
                selected = suggestion
    return selected


def render_chat_interface(dm: DialogueManager) -> None:
    """Render multi-turn conversation, compact step indicator, and 7-segment live HUD."""
    filled_count = sum(
        1 for _, _, k, _, _ in KENT_DIMENSIONS
        if (k in dm.state_machine.filled_slots) or bool(dm.extracted_slots.get(k))
    )
    step_badge = get_current_step_label(dm)

    hud_html = f"""
    <div class="stGlassCard" style="margin-bottom: 12px; padding: 14px 18px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                {get_icon('track_changes', color='#10B981', size=18)}
                <span style="font-weight: 700; font-size: 15px; color: #F9FAFB;">Live Symptom Dimensions</span>
                <span class="step-counter-badge">{step_badge}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 13px; font-weight: 700; color: #10B981;">Totality: {filled_count}/7</span>
            </div>
        </div>
        {render_slot_badges_html(dm.extracted_slots, dm=dm)}
    </div>
    """
    st.markdown(hud_html, unsafe_allow_html=True)

    # Manage / Edit captured symptoms if any exist
    any_captured = any(bool(items) for items in dm.extracted_slots.values())
    if any_captured:
        with st.expander("Manage Captured Symptoms (Edit / Remove)", expanded=False):
            st.markdown("<div style='font-size: 12px; color: #9CA3AF; margin-bottom: 8px;'>Clinicians can review or delete extracted clinical tokens:</div>", unsafe_allow_html=True)
            for disp_name, label, key, badge_class, _ in KENT_DIMENSIONS:
                items = dm.extracted_slots.get(key, [])
                if items:
                    for idx, item in enumerate(list(items)):
                        c_tok, c_act = st.columns([5, 1])
                        with c_tok:
                            st.markdown(f"<span class='badge {badge_class}'><b>{disp_name}:</b> {item}</span>", unsafe_allow_html=True)
                        with c_act:
                            if st.button("✕", key=f"hud_del_{key}_{idx}_{item}", help=f"Remove {item}"):
                                dm.extracted_slots[key].remove(item)
                                if not dm.extracted_slots[key] and key in dm.state_machine.filled_slots:
                                    dm.state_machine.filled_slots.remove(key)
                                st.rerun()

    # Console Subheader (without clutter note)
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin: 12px 0 8px 2px;">
            <span style="font-size: 14px; font-weight: 600; color: #D1D5DB; display: flex; align-items: center; gap: 6px;">
                {get_icon('forum', size=16, color='#10B981')} Clinical Dialogue Console
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Dynamic scrollable chat box container (sizes to content with max-height 520px)
    chat_container = st.container(border=True)
    selected_chip: Optional[str] = None

    with chat_container:
        if not dm.history:
            st.markdown(
                f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; color: #9CA3AF; padding: 24px 20px; text-align: center;">
                    <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3); display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                        {get_icon('chat', size=24, color='#10B981')}
                    </div>
                    <div style="font-weight: 700; font-size: 15px; color: #F9FAFB;">Consultation Active (MIND Chapter Focus)</div>
                    <div style="font-size: 13px; color: #9CA3AF; max-width: 440px; margin-top: 4px; line-height: 1.5;">
                        Speak naturally with Kent-AI about how you feel. The intake engine focuses on mental & emotional generals alongside somatic modalities.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for msg in dm.history:
                role = msg["role"]
                content = msg["content"]
                if role == "assistant":
                    with st.chat_message("assistant", avatar="🌿"):
                        st.markdown(content)
                else:
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(content)

            # While container is near-empty (0-1 messages), render suggestions inside container!
            if len(dm.history) <= 1:
                selected_chip = render_quick_reply_chips(dm, in_container=True)

    # When multiple messages accumulate (>1), render suggestions docked above the chat input
    if len(dm.history) > 1:
        docked_chip = render_quick_reply_chips(dm, in_container=False)
        if docked_chip:
            selected_chip = docked_chip

    # Chat input with MIND-oriented placeholder
    user_prompt = st.chat_input("Tell Kent-AI how you are feeling (e.g. 'I feel anxious and restless in the evening, worse when alone')...")

    input_to_process = selected_chip or user_prompt
    if input_to_process:
        with chat_container:
            with st.chat_message("user", avatar="👤"):
                st.markdown(input_to_process)
            with st.chat_message("assistant", avatar="🌿"):
                thinking_box = st.empty()
                thinking_box.markdown(
                    """
                    <div class="skeleton-thinking-bubble">
                        <div style="font-size: 11px; color: #10B981; font-weight: 700; display: flex; align-items: center; gap: 6px;">
                            <span class="status-dot"></span> Kent-AI is reflecting...
                        </div>
                        <div class="skeleton-shimmer-line line-1"></div>
                        <div class="skeleton-shimmer-line line-2"></div>
                        <div class="skeleton-shimmer-line line-3"></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                bot_reply = dm.process_turn(input_to_process)
                thinking_box.markdown(bot_reply)
        st.rerun()

