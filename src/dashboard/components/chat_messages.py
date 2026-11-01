"""Chat message rendering with compact bubbles, hover timestamps, and per-turn undo controls (Phase 4 & UI Overhaul)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
import streamlit as st

from src.dashboard.components.icons import get_icon
from src.dashboard.utils import esc, safe_rerun_fragment
from src.data.case_store import save_case

if TYPE_CHECKING:
    from src.chatbot.dialogue_manager import DialogueManager
    from src.models.case import ClinicalCase


def render_chat_messages(
    dm: DialogueManager,
    active_case: ClinicalCase | None,
    assistant_avatar: str,
    user_avatar: str,
) -> None:
    """Render conversation history with compact bubbles, collapsible welcome blurb, and hover timestamps."""
    is_practitioner = getattr(dm, "intake_mode", "patient") == "practitioner"
    total_turns = len(dm.history)

    # 1. Welcome blurb collapses after the first user message
    if total_turns <= 1:
        st.html(
            f"""
            <div class="chat-welcome-banner">
                <div class="chat-welcome-icon">{get_icon('sparkles', size=18, color='var(--accent, #10B981)')}</div>
                <div>
                    <div class="chat-welcome-title">Kent-AI Clinical Companion Active</div>
                    <div class="chat-welcome-sub">Speak naturally about physical symptoms, modalities, triggers, and emotional state. Kent-AI guides dynamic clinical intake to discover matching repertory rubrics.</div>
                </div>
            </div>
            """
        )

    latest_assistant_text = ""

    for idx, msg in enumerate(dm.history):
        role = msg.get("role", "user")
        c_text = msg.get("content", "").strip()
        clean_text = dm.clean_message_text(c_text) if role == "assistant" else c_text
        time_hint = msg.get("time") or datetime.now().strftime("%H:%M")

        if role == "assistant":
            latest_assistant_text = clean_text
            origin = msg.get("origin", "llm")
            origin_badge = ""
            if origin == "scripted":
                origin_badge = (
                    '<span class="badge" style="background: rgba(245, 158, 11, 0.12); '
                    'border: 1px solid rgba(245, 158, 11, 0.35); color: #FBBF24; '
                    'font-size: 10px; font-weight: 600; padding: 1px 5px; margin-left: 6px; border-radius: 3px;">'
                    'Scripted</span>'
                )

            with st.chat_message("assistant", avatar=assistant_avatar):
                st.html(
                    f"<div class='chat-msg-header' style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;'>"
                    f"<span style='font-size: 11.5px; font-weight: 700; color: var(--accent, #10B981); letter-spacing: 0.02em;'>"
                    f"Kent-AI {origin_badge}"
                    f"</span>"
                    f"<span style='font-size: 10.5px; color: var(--text-faint, #8A98AE);' title='Received at {time_hint}'>{time_hint}</span>"
                    f"</div>"
                )
                st.markdown(clean_text)

                # Under the latest assistant message: goal description and turn actions
                if idx == total_turns - 1:
                    current_goal = dm.state_machine.get_current_goal_description()
                    with st.expander("Why am I asking this?", expanded=False):
                        st.markdown(
                            f"<div style='font-size: 12.5px; color: var(--text-muted, #A3B0C2); line-height: 1.5;'>{esc(current_goal)}</div>",
                            unsafe_allow_html=True,
                        )

                    if total_turns >= 2:
                        c_undo, c_regen = st.columns([1, 1], vertical_alignment="center")
                        with c_undo:
                            if st.button("Undo last answer", key="btn_undo_last_answer", help="Revert the last response and captured symptoms", width="stretch"):
                                dm.undo_last_turn()
                                if active_case:
                                    dm.sync_to_case(active_case)
                                    save_case(active_case)
                                st.toast("Reverted last turn.")
                                safe_rerun_fragment()
                        with c_regen:
                            if st.button("↺ Regenerate", key="btn_regen_last_answer", help="Regenerate question", width="stretch"):
                                dm.history.pop()
                                st.toast("Regenerating question...")
                                safe_rerun_fragment()

        else:
            speaker_label = "Practitioner" if is_practitioner else "You"
            with st.chat_message("user", avatar=user_avatar):
                st.html(
                    f"<div class='chat-msg-header' style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;'>"
                    f"<span style='font-size: 11.5px; font-weight: 700; color: var(--text-muted, #A3B0C2); letter-spacing: 0.02em;'>"
                    f"{esc(speaker_label)}"
                    f"</span>"
                    f"<span style='font-size: 10.5px; color: var(--text-faint, #8A98AE);' title='Sent at {time_hint}'>{time_hint}</span>"
                    f"</div>"
                )
                st.markdown(clean_text)

                # Render captured symptom chips with undo buttons
                captured = msg.get("captured", {})
                turn_id = msg.get("turn_id", f"turn_{idx}")
                if isinstance(captured, dict) and any(captured.values()):
                    st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)
                    for dim_key, items in captured.items():
                        dim_title = dim_key.replace("_", " ").title()
                        for it_idx, item in enumerate(items):
                            c_chip, c_del = st.columns([4, 1.2], vertical_alignment="center")
                            with c_chip:
                                st.markdown(
                                    f"<span class='badge' style='background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); color: #34D399; font-size: 11px; padding: 2px 7px; border-radius: 4px;'>"
                                    f"<b>{esc(dim_title)}:</b> {esc(item)}</span>",
                                    unsafe_allow_html=True,
                                )
                            with c_del:
                                remove_key = f"btn_undo_cap_{turn_id}_{dim_key}_{it_idx}"
                                if st.button(
                                    f"Remove {item}",
                                    key=remove_key,
                                    help=f"Remove {item} from {dim_title}",
                                ):
                                    dm.undo_capture(turn_id, dim_key, item)
                                    if active_case:
                                        dm.sync_to_case(active_case)
                                        save_case(active_case)
                                    st.toast(f"Removed '{item}'.")
                                    safe_rerun_fragment()

    # Screen reader live region
    if latest_assistant_text:
        st.html(
            f'<div role="status" aria-live="polite" class="sr-only">{esc(latest_assistant_text)}</div>'
        )
