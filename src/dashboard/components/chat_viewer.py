"""Chat viewer component for interactive clinical intake (Phase 4 & UI Overhaul).

Orchestrates multi-turn clinical conversation, accessible chat messages,
step-aware suggested response chips, streaming token delivery, and case synchronization.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
import streamlit as st

from src.chatbot.dialogue_manager import DialogueManager
from src.chatbot.state_machine import IntakeState
from src.dashboard.components.chat_chips import render_quick_reply_chips
from src.dashboard.components.chat_header import (
    format_chat_transcript_md,
    get_current_step_label,
    render_chat_header,
)
from src.dashboard.components.chat_messages import render_chat_messages
from src.dashboard.components.icons import get_icon
from src.dashboard.components.ollama_status import check_ollama_online, ollama_online
from src.dashboard.components.symptom_strip import (
    render_slot_badges,
    render_slot_badges_html,
)
from src.dashboard.dimensions import KENT_DIMENSIONS_ORDERED
from src.dashboard.utils import esc, safe_rerun_fragment
from src.data.case_store import save_case

logger = logging.getLogger("chat_viewer")

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
_ASSISTANT_SVG = _ASSETS_DIR / "assistant_avatar.svg"
_USER_SVG = _ASSETS_DIR / "user_avatar.svg"
ASSISTANT_AVATAR = (
    str(_ASSISTANT_SVG.resolve()) if _ASSISTANT_SVG.is_file() else "assistant"
)
USER_AVATAR = str(_USER_SVG.resolve()) if _USER_SVG.is_file() else "user"

# Re-exports for 100% backward compatibility
__all__ = [
    "check_ollama_online",
    "ollama_online",
    "get_current_step_label",
    "render_slot_badges_html",
    "render_slot_badges",
    "render_quick_reply_chips",
    "format_chat_transcript",
    "render_chat_interface",
    "ASSISTANT_AVATAR",
    "USER_AVATAR",
]

format_chat_transcript = format_chat_transcript_md


def render_chat_interface(dm: DialogueManager) -> None:
    """Render full-width multi-turn conversation and input within left workspace column."""
    active_case = st.session_state.get("current_case")

    # 1. Dialogue Console Header Row
    is_llm_online = check_ollama_online(
        getattr(dm, "api_base", "http://127.0.0.1:11434")
    )
    if is_llm_online and hasattr(dm, "api_base"):
        dm.api_base = "http://127.0.0.1:11434"

    render_chat_header(dm, active_case, is_llm_online)

    # Ensure at least the greeting is present so there is never an empty conversation
    if not dm.history:
        dm.get_greeting()

    is_streaming = st.session_state.get("chat_is_streaming", False)

    # 2. Main Chat Container with scrollable message area
    with st.container(border=True):
        scroll_area = st.container(height=480)
        with scroll_area:
            render_chat_messages(dm, active_case, ASSISTANT_AVATAR, USER_AVATAR)

        # Suggested responses docked right above input inside chat panel
        selected_chip = render_quick_reply_chips(dm, in_container=False)

        # Terminal DONE state action buttons if consultation completed
        if dm.state_machine.current_state == IntakeState.DONE:
            actions = dm.get_action_options()
            if actions:
                st.markdown(
                    "<div style='margin: 8px 0;'></div>", unsafe_allow_html=True
                )
                cols = st.columns(len(actions))
                for idx, act in enumerate(actions):
                    act_id = act.get("id")
                    act_label = act.get("label", "")
                    act_type = (
                        "primary" if act.get("type") == "primary" else "secondary"
                    )
                    with cols[idx]:
                        if st.button(
                            act_label,
                            type=act_type,
                            width="stretch",
                            key=f"btn_done_act_{act_id}",
                        ):
                            if act_id == "continue_review":
                                st.session_state.workspace_step = 2
                                st.rerun(scope="app")
                            elif act_id == "add_detail":
                                dm.state_machine.current_state = (
                                    IntakeState.CLARIFICATION
                                )
                                dm.prepare_turn("I would like to add another detail.")
                                if active_case:
                                    dm.sync_to_case(active_case)
                                    save_case(active_case)
                                safe_rerun_fragment()
                            elif act_id == "start_new":
                                dm.reset()
                                dm.get_greeting()
                                if active_case:
                                    active_case.dimensions = {
                                        k: [] for k in active_case.dimensions
                                    }
                                    active_case.dialogue_history = []
                                    active_case.extraction_meta = {
                                        "intake_mode": dm.intake_mode
                                    }
                                    dm.sync_to_case(active_case)
                                    save_case(active_case)
                                st.toast("Started new consultation.")
                                safe_rerun_fragment()

        # Dynamic placeholder based on mode
        is_practitioner = getattr(dm, "intake_mode", "patient") == "practitioner"
        input_placeholder = (
            "Enter clinical findings, patient quotes, or observations (e.g. 'Rt temple pain, worse 3pm, anxious')..."
            if is_practitioner
            else "Tell Kent-AI how you are feeling (e.g. 'I feel anxious and restless in the evening, worse when alone')..."
        )

        user_prompt = st.chat_input(input_placeholder, disabled=is_streaming)

    # 3. Process turn input (from chip or user input)
    input_to_process = selected_chip or user_prompt
    if input_to_process:
        raw = []
        with scroll_area:
            speaker_label = "Practitioner" if is_practitioner else "You"
            with st.chat_message("user", avatar=USER_AVATAR):
                st.html(
                    f"<div class='chat-msg-header' style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;'>"
                    f"<span style='font-size: 11.5px; font-weight: 700; color: var(--text-muted, #A3B0C2); letter-spacing: 0.02em;'>"
                    f"{esc(speaker_label)}"
                    f"</span>"
                    f"</div>"
                )
                st.markdown(input_to_process)

            with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
                st.html(
                    "<div class='chat-msg-header' style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;'>"
                    "<span style='font-size: 11.5px; font-weight: 700; color: var(--accent, #10B981); letter-spacing: 0.02em;'>"
                    "Kent-AI"
                    "</span>"
                    "</div>"
                )
                thinking_box = st.empty()
                thinking_box.html(f"""
                    <div class="skeleton-thinking-bubble">
                        <div style="font-size: 11.5px; color: var(--accent, #10B981); font-weight: 700; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;">
                            <span class="status-dot"></span> {get_icon('sparkles', size=13, color='var(--accent, #10B981)')} Kent-AI is reflecting...
                        </div>
                        <div class="skeleton-shimmer-line line-1"></div>
                        <div class="skeleton-shimmer-line line-2"></div>
                        <div class="skeleton-shimmer-line line-3"></div>
                    </div>
                    """)

                prompt = dm.prepare_turn(input_to_process)

                def _stream_with_thinking(stream_gen):
                    cleared = False
                    try:
                        for chunk in stream_gen:
                            if not cleared:
                                thinking_box.empty()
                                cleared = True
                            yield chunk
                    finally:
                        if not cleared:
                            thinking_box.empty()

                st.session_state.chat_is_streaming = True
                try:
                    st.write_stream(
                        _stream_with_thinking(
                            dm.visible_only(dm.stream_reply(prompt), raw)
                        )
                    )
                except Exception as err:
                    logger.warning("Error streaming assistant reply: %s", err)
                    dm.last_call_failed = True
                finally:
                    st.session_state.chat_is_streaming = False
                    thinking_box.empty()

        if getattr(dm, "last_call_failed", False) or not raw:
            fallback_text = dm._mock_response_for_state()
            raw = [fallback_text]
            st.toast("Language model connection offline or timed out.")

        dm.finalize_turn("".join(raw))

        if active_case:
            dm.sync_to_case(active_case)
            save_case(active_case)

        safe_rerun_fragment()
