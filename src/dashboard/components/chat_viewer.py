"""Chat viewer component for interactive clinical intake (Phase 2, 7 & 14).

Orchestrates multi-turn clinical conversation, 7-dimension totality strip,
accessible chat message list, suggested response chips, and review handover.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional
import urllib.request
import streamlit as st

from src.chatbot.dialogue_manager import DialogueManager
from src.dashboard.components.chat_actions import render_chat_action_bar
from src.dashboard.components.chat_chips import render_quick_reply_chips
from src.dashboard.components.chat_header import (
    format_chat_transcript_md,
    get_current_step_label,
    render_chat_header,
)
from src.dashboard.components.chat_messages import render_chat_messages
from src.dashboard.components.icons import get_icon
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
ASSISTANT_AVATAR = str(_ASSISTANT_SVG.resolve()) if _ASSISTANT_SVG.is_file() else "assistant"
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


@st.cache_data(ttl=10, show_spinner=False)
def check_ollama_online(api_base: str = "http://127.0.0.1:11434") -> bool:
    """Direct HTTP ping to check if local Ollama daemon is active and responding.

    Checks 127.0.0.1 (IPv4) first to bypass Windows IPv6 resolution latency.
    Bypasses system proxies for local addresses. Cached for 10s to eliminate latency.
    """
    if os.environ.get("KENT_MOCK_PIPELINE", "0") == "1":
        return False

    candidates = ["http://127.0.0.1:11434", api_base, "http://localhost:11434"]
    seen = set()
    unique_candidates = [c for c in candidates if c and not (c in seen or seen.add(c))]
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for base in unique_candidates:
        try:
            url = f"{base.rstrip('/')}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with opener.open(req, timeout=1.5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            continue
    return False


ollama_online = check_ollama_online


def render_chat_interface(dm: DialogueManager) -> None:
    """Render full-width multi-turn conversation, 7-dimension HUD, and docked review bar."""
    active_case = st.session_state.get("current_case")

    filled_count = sum(
        1 for dim in KENT_DIMENSIONS_ORDERED
        if (dim.key in dm.state_machine.filled_slots) or bool(dm.extracted_slots.get(dim.key))
    )

    # 1. Symptom Totality Strip
    hud_html = f"""
    <div class="stGlassCard" style="margin-bottom: 12px; padding: 14px 18px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                {get_icon('track_changes', color='#10B981', size=18)}
                <span style="font-weight: 700; font-size: 15px; color: #F9FAFB;">Symptom Totality Strip</span>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 13px; font-weight: 700; color: #10B981;">{filled_count} of 7 Dimensions Captured</span>
            </div>
        </div>
        {render_slot_badges_html(dm.extracted_slots, dm=dm)}
    </div>
    """
    st.markdown(hud_html, unsafe_allow_html=True)

    # 2. Dialogue Console Header
    is_llm_online = check_ollama_online(getattr(dm, "api_base", "http://127.0.0.1:11434"))
    if is_llm_online and hasattr(dm, "api_base"):
        dm.api_base = "http://127.0.0.1:11434"

    render_chat_header(dm, active_case, is_llm_online)

    # Ensure at least the greeting is present so there is never an empty conversation
    if not dm.history:
        dm.get_greeting()

    is_streaming = st.session_state.get("chat_is_streaming", False)

    # 3. Main Chat Container with scrollable message area
    with st.container(border=True):
        scroll_area = st.container(height=450)
        with scroll_area:
            render_chat_messages(dm, active_case, ASSISTANT_AVATAR, USER_AVATAR)

        # Suggested responses docked right above input inside chat panel
        selected_chip = render_quick_reply_chips(dm, in_container=False)

        # Dynamic placeholder based on mode
        is_practitioner = getattr(dm, "intake_mode", "patient") == "practitioner"
        input_placeholder = (
            "Enter clinical findings, patient quotes, or observations (e.g. 'Rt temple pain, worse 3pm, anxious')..."
            if is_practitioner
            else "Tell Kent-AI how you are feeling (e.g. 'I feel anxious and restless in the evening, worse when alone')..."
        )

        user_prompt = st.chat_input(input_placeholder, disabled=is_streaming)

    # 4. Docked Action Bar under chat panel
    render_chat_action_bar(dm, active_case)

    # 5. Process turn input (from chip or user input)
    input_to_process = selected_chip or user_prompt
    if input_to_process:
        raw = []
        with scroll_area:
            speaker_label = "Practitioner" if is_practitioner else "You"
            with st.chat_message("user", avatar=USER_AVATAR):
                st.html(
                    f"<div style='font-size: 11.5px; font-weight: 700; color: #94A3B8; margin-bottom: 4px; letter-spacing: 0.02em;'>"
                    f"{esc(speaker_label)}"
                    f"</div>"
                )
                st.markdown(input_to_process)

            with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
                st.html(
                    "<div style='font-size: 11.5px; font-weight: 700; color: #10B981; margin-bottom: 4px; letter-spacing: 0.02em;'>"
                    "Kent-AI"
                    "</div>"
                )
                thinking_box = st.empty()
                thinking_box.markdown(
                    f"""
                    <div class="skeleton-thinking-bubble">
                        <div style="font-size: 11.5px; color: #10B981; font-weight: 700; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;">
                            <span class="status-dot"></span> {get_icon('sparkles', size=13, color='#10B981')} Kent-AI is reflecting...
                        </div>
                        <div class="skeleton-shimmer-line line-1"></div>
                        <div class="skeleton-shimmer-line line-2"></div>
                        <div class="skeleton-shimmer-line line-3"></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

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
                    st.write_stream(_stream_with_thinking(dm.visible_only(dm.stream_reply(prompt), raw)))
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
