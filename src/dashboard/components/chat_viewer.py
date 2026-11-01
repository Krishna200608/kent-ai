"""Chat viewer component for interactive clinical intake (Phase 2 & 7)."""

from __future__ import annotations

from datetime import datetime
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.request
import streamlit as st

logger = logging.getLogger("chat_viewer")

from src.chatbot.dialogue_manager import DialogueManager
from src.data.case_store import save_case
from src.dashboard.components.icons import get_icon
from src.dashboard.utils import esc, safe_rerun_fragment
from src.dashboard.dimensions import (
    DIMENSION_MAP,
    KENT_DIMENSIONS_ORDERED,
    pluralize,
)
from src.dashboard.components.symptom_strip import (
    render_slot_badges,
    render_slot_badges_html,
)
from src.dashboard.components.chat_chips import render_quick_reply_chips

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


def _safe_clean_bot_text(text: str) -> str:
    """Safely sanitize bot message text using DialogueManager cleaner or fallback."""
    clean_fn = getattr(DialogueManager, "clean_message_text", None)
    if clean_fn:
        return clean_fn(text)
    import re
    text = re.sub(r"\[?\s*QUICK_REPLIES\s*:\s*\[.*?\]\s*\]?", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\[?\s*SLOT_UPDATE\s*:\s*\{[^{}]*\}\s*\]?", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"(?:\[\s*)?QUICK_REPLIES\s*:.*$", "", text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    text = re.sub(r"(?:\[\s*)?SLOT_UPDATE\s*:.*$", "", text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    return text.strip().rstrip("[\n\r\t `:,-({")


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


def get_current_step_label(dm: DialogueManager) -> str:
    """Return compact Step X of 10 label."""
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


def format_chat_transcript(dm: DialogueManager) -> str:
    """Format full multi-turn consultation transcript with metadata for debugging/analysis."""
    lines = []
    lines.append("# Kent-AI Clinical Consultation Transcript")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"- **Exported At**: {now_str}")
    lines.append(f"- **Current Stage**: {get_current_step_label(dm)}")

    # Active extracted dimensions
    dims_recorded = []
    for dim in KENT_DIMENSIONS_ORDERED:
        items = dm.extracted_slots.get(dim.key, [])
        if items:
            dims_recorded.append(f"  - **{dim.label}**: {', '.join(items)}")

    lines.append(f"- **Totality Coverage**: {len(dims_recorded)}/7 dimensions")
    if dims_recorded:
        lines.extend(dims_recorded)
    else:
        lines.append("  - *No symptom dimensions recorded yet.*")

    lines.append("\n---\n")

    if not dm.history:
        lines.append("*(No conversation turns recorded yet.)*")
    else:
        is_practitioner = getattr(dm, "intake_mode", "patient") == "practitioner"
        for idx, turn in enumerate(dm.history, 1):
            role = turn.get("role", "unknown")
            content = turn.get("content", "").strip()
            speaker = "Kent-AI (Assistant)" if role == "assistant" else ("Practitioner (Clinician)" if is_practitioner else "Patient (User)")
            clean_content = _safe_clean_bot_text(content) if role == "assistant" else content
            lines.append(f"### Turn {idx}: [{speaker}]\n{clean_content}\n")

    lines.append("---\n*Generated by Kent-AI Clinical Assistant for session debugging and prompt analysis.*")
    return "\n".join(lines)


def render_chat_interface(dm: DialogueManager) -> None:
    """Render multi-turn conversation, 7-segment live HUD, and review transitions."""
    filled_count = sum(
        1 for dim in KENT_DIMENSIONS_ORDERED
        if (dim.key in dm.state_machine.filled_slots) or bool(dm.extracted_slots.get(dim.key))
    )

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

    if filled_count >= 1:
        c_rev1, c_rev2 = st.columns([4, 2], vertical_alignment="center")
        with c_rev1:
            missing = [d.label for d in KENT_DIMENSIONS_ORDERED if not dm.extracted_slots.get(d.key)]
            if missing:
                st.caption(f"Unrecorded dimensions: {', '.join(missing[:3])} (can be added now or in Review)")
            else:
                st.caption("All 7 clinical symptom dimensions captured!")
        with c_rev2:
            if st.button("Proceed to Review \u2192", type="primary", width="stretch", key="intake_to_review_btn"):
                if hasattr(st.session_state, "current_case") and st.session_state.current_case:
                    active_case = st.session_state.current_case
                    dm.sync_to_case(active_case)
                    if not getattr(active_case, "clinical_summary", "") and active_case.is_ready_for_repertorization:
                        try:
                            from src.pipeline.case_summarizer import CaseSummarizer
                            active_case.clinical_summary = CaseSummarizer().generate_summary(active_case)
                        except Exception as e:
                            logger.info("Auto-summary generation on review handover: %s", e)
                    save_case(active_case)
                st.session_state.workspace_step = 2
                st.rerun()

    # Manage / Edit captured symptoms if any exist
    any_captured = any(bool(items) for items in dm.extracted_slots.values())
    if any_captured:
        with st.expander("Manage Captured Symptoms (Edit / Remove)", expanded=False):
            st.markdown("<div style='font-size: 12px; color: #9CA3AF; margin-bottom: 8px;'>Clinicians can review or delete extracted clinical tokens:</div>", unsafe_allow_html=True)
            for dim in KENT_DIMENSIONS_ORDERED:
                items = dm.extracted_slots.get(dim.key, [])
                if items:
                    for idx, item in enumerate(list(items)):
                        c_tok, c_act = st.columns([5, 1])
                        with c_tok:
                            st.markdown(f"<span class='badge {dim.badge_class}'><b>{dim.label}:</b> {item}</span>", unsafe_allow_html=True)
                        with c_act:
                            if st.button("x", key=f"hud_del_{dim.key}_{idx}_{item}", help=f"Remove {item}"):
                                dm.extracted_slots[dim.key].remove(item)
                                if not dm.extracted_slots[dim.key] and dim.key in dm.state_machine.filled_slots:
                                    dm.state_machine.filled_slots.remove(dim.key)
                                active_case = st.session_state.get("current_case")
                                if active_case:
                                    dm.sync_to_case(active_case)
                                    save_case(active_case)
                                safe_rerun_fragment()

    # Console Subheader with live LLM engine status indicator
    is_llm_online = check_ollama_online(getattr(dm, "api_base", "http://127.0.0.1:11434"))
    if is_llm_online and hasattr(dm, "api_base"):
        dm.api_base = "http://127.0.0.1:11434"
    if is_llm_online:
        engine_badge_html = """
        <span style="font-size: 12px; color: #10B981; display: inline-flex; align-items: center; gap: 5px; font-weight: 600;" tabindex="0" aria-label="LLaMA 3:8B is online on 127.0.0.1:11434 and providing dynamic empathetic clinical reasoning." data-tip="LLaMA 3:8B is online on 127.0.0.1:11434 and providing dynamic empathetic clinical reasoning." title="LLaMA 3:8B is online on 127.0.0.1:11434 and providing dynamic empathetic clinical reasoning.">
            <span class="status-dot"></span> LLaMA 3:8B Online
        </span>
        """
    else:
        engine_badge_html = """
        <span style="font-size: 12px; color: #F59E0B; display: inline-flex; align-items: center; gap: 5px; font-weight: 600;" tabindex="0" aria-label="Ollama daemon is offline on 127.0.0.1:11434. Running on deterministic FSM templates. Run 'ollama serve' in your terminal to activate LLaMA 3." data-tip="Ollama daemon is offline on 127.0.0.1:11434. Running on deterministic FSM templates. Run 'ollama serve' in your terminal to activate LLaMA 3." title="Ollama daemon is offline on 127.0.0.1:11434. Running on deterministic FSM templates. Run 'ollama serve' in your terminal to activate LLaMA 3.">
            <span class="status-dot-amber"></span> Offline Fallback (ollama serve)
        </span>
        """

    col_hdr_left, col_hdr_right = st.columns([5, 6])
    is_practitioner = getattr(dm, "intake_mode", "patient") == "practitioner"
    mode_badge_html = (
        '<span class="badge" style="background: rgba(16, 185, 129, 0.16); border: 1px solid rgba(16, 185, 129, 0.45); color: #34D399; font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 4px;">Practitioner-Led</span>'
        if is_practitioner
        else '<span class="badge" style="background: rgba(59, 130, 246, 0.16); border: 1px solid rgba(59, 130, 246, 0.45); color: #93C5FD; font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 4px;">Patient Self-Intake</span>'
    )

    with col_hdr_left:
        st.html(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; padding-top: 4px; flex-wrap: wrap;">
                <span style="font-size: 14.5px; font-weight: 700; color: #F3F4F6; display: flex; align-items: center; gap: 6px;">
                    {get_icon('forum', size=18, color='#10B981')} Clinical Dialogue Console
                </span>
                <span class="step-counter-badge">{get_current_step_label(dm)}</span>
                {mode_badge_html}
            </div>
            """
        )
    with col_hdr_right:
        c_mode, c_copy, c_status = st.columns([1.5, 1, 1], vertical_alignment="center")
        with c_mode:
            curr_mode = getattr(dm, "intake_mode", "patient").capitalize()
            selected_style = st.segmented_control(
                "Intake Style",
                options=["Patient", "Practitioner"],
                default="Patient" if curr_mode == "Patient" else "Practitioner",
                key="intake_style_control",
                label_visibility="collapsed",
                help="Patient self-intake (conversational) vs Practitioner-led (rapid clinical entry)",
            )
            if selected_style:
                target_mode = selected_style.lower()
                if target_mode != getattr(dm, "intake_mode", "patient"):
                    if hasattr(dm, "set_intake_mode"):
                        dm.set_intake_mode(target_mode)
                    else:
                        dm.intake_mode = target_mode
                    st.toast(
                        f"Switched to {selected_style} Intake Mode",
                        icon="🩺" if target_mode == "practitioner" else "👤",
                    )
                    safe_rerun_fragment()
        with c_copy:
            with st.popover("Copy Chat", width="stretch", help="Copy complete conversation history and extracted symptom dimensions for debugging/analysis"):
                st.markdown("##### Consultation Transcript")
                st.caption("Click the copy icon in the top right of the code box below to copy all chat, or download as a text file.")
                transcript_text = format_chat_transcript(dm)
                st.download_button(
                    label="Download (.txt)",
                    data=transcript_text,
                    file_name=f"kent_ai_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    width="stretch",
                    key="chat_console_download_txt",
                )
                st.code(transcript_text, language="markdown")
        with c_status:
            st.html(
                f"""
                <div style="display: flex; justify-content: flex-end; align-items: center; height: 100%; padding-top: 4px;">
                    {engine_badge_html.strip()}
                </div>
                """
            )

    if getattr(dm, "last_call_failed", False):
        col_warn, col_retry = st.columns([5, 1])
        with col_warn:
            st.warning("The language model is offline or timed out. Questions are now scripted.")
        with col_retry:
            if st.button("Retry", key="btn_retry_llm_conn"):
                dm.last_call_failed = False
                check_ollama_online.clear()
                safe_rerun_fragment()

    # Chat panel with internal scroll area and pinned chat input
    with st.container(border=True):
        scroll_area = st.container(height=450)
        with scroll_area:
            # Active empty state: reachable on initial consultation launch when a new case
            # is initialized and case.dialogue_history is empty ([]), before user enters first utterance.
            if not dm.history:
                empty_title = (
                    "Kent-AI Clinical Workstation (Practitioner-Led)"
                    if is_practitioner
                    else "Kent-AI Clinical Companion Active"
                )
                empty_desc = (
                    "Enter shorthand clinical notes, modalities, or direct patient observations. Kent-AI continuously extracts 7-dimension totality and maps rubrics in real time."
                    if is_practitioner
                    else "Speak naturally about your physical symptoms, modalities, triggers, and emotional state. Kent-AI guides dynamic clinical intake to discover matching repertory rubrics."
                )
                st.html(
                    f"""
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; color: #9CA3AF; padding: 36px 20px; text-align: center;">
                        <div style="width: 52px; height: 52px; border-radius: 14px; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3); display: flex; align-items: center; justify-content: center; margin-bottom: 12px; box-shadow: 0 4px 16px rgba(16, 185, 129, 0.15);">
                            {get_icon('sparkles', size=26, color='#10B981')}
                        </div>
                        <div style="font-weight: 700; font-size: 16px; color: #F9FAFB; letter-spacing: -0.01em;">{empty_title}</div>
                        <div style="font-size: 13.5px; color: #9CA3AF; max-width: 460px; margin-top: 6px; line-height: 1.55;">
                            {empty_desc}
                        </div>
                    </div>
                    """
                )
            else:
                for idx, msg in enumerate(dm.history):
                    role = msg["role"]
                    c_text = msg["content"]
                    if role == "assistant":
                        c_text = _safe_clean_bot_text(c_text)
                        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
                            st.html(
                                f"<div style='font-size: 11.5px; font-weight: 700; color: #10B981; margin-bottom: 4px; letter-spacing: 0.02em;'>"
                                f"Kent-AI"
                                f"</div>"
                            )
                            st.markdown(c_text)
                    else:
                        speaker_label = "Practitioner" if is_practitioner else "You"
                        with st.chat_message("user", avatar=USER_AVATAR):
                            st.html(
                                f"<div style='font-size: 11.5px; font-weight: 700; color: #94A3B8; margin-bottom: 4px; letter-spacing: 0.02em;'>"
                                f"{speaker_label}"
                                f"</div>"
                            )
                            st.markdown(c_text)

        # Suggested responses docked right above input inside chat panel
        selected_chip = render_quick_reply_chips(dm, in_container=False)

        # Pinned chat input inside the chat panel with dynamic role placeholder
        input_placeholder = (
            "Enter clinical findings, patient quotes, or observations (e.g. 'Rt temple pain, worse 3pm, anxious')..."
            if is_practitioner
            else "Tell Kent-AI how you are feeling (e.g. 'I feel anxious and restless in the evening, worse when alone')..."
        )
        user_prompt = st.chat_input(input_placeholder)

    input_to_process = selected_chip or user_prompt
    if input_to_process:
        # If user selected or requested 'Proceed to Review', navigate directly to Step 2
        if "proceed to review" in input_to_process.lower():
            active_case = st.session_state.get("current_case")
            if active_case:
                dm.sync_to_case(active_case)
                if not getattr(active_case, "clinical_summary", "") and active_case.is_ready_for_repertorization:
                    try:
                        from src.pipeline.case_summarizer import CaseSummarizer
                        active_case.clinical_summary = CaseSummarizer().generate_summary(active_case)
                    except Exception as e:
                        logger.info("Auto-summary on review chip: %s", e)
                save_case(active_case)
            st.session_state.workspace_step = 2
            st.rerun()

        raw = []
        with scroll_area:
            with st.chat_message("user", avatar=USER_AVATAR):
                st.html(
                    f"<div style='font-size: 11.5px; font-weight: 700; color: #94A3B8; margin-bottom: 4px; letter-spacing: 0.02em;'>"
                    f"You"
                    f"</div>"
                )
                st.markdown(input_to_process)
            with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
                st.html(
                    f"<div style='font-size: 11.5px; font-weight: 700; color: #10B981; margin-bottom: 4px; letter-spacing: 0.02em;'>"
                    f"Kent-AI"
                    f"</div>"
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

                try:
                    st.write_stream(_stream_with_thinking(dm.visible_only(dm.stream_reply(prompt), raw)))
                except Exception as err:
                    logger.warning("Error streaming assistant reply: %s", err)
                    dm.last_call_failed = True
                finally:
                    thinking_box.empty()

        if getattr(dm, "last_call_failed", False) or not raw:
            fallback_text = dm._mock_response_for_state()
            raw = [fallback_text]
            st.toast("Language model connection offline or timed out.", icon="⚠️")

        dm.finalize_turn("".join(raw))

        # Persist case updates on dialogue turns
        active_case = st.session_state.get("current_case")
        if active_case:
            dm.sync_to_case(active_case)
            save_case(active_case)

        safe_rerun_fragment()
