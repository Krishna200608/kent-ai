"""Step 1 Patient Clinical Intake view (router for Guided conversation, Paste notes, and Manual entry)."""

from __future__ import annotations

from typing import Any
import streamlit as st

from src.chatbot.dialogue_manager import DialogueManager, get_min_dimensions_to_unlock
from src.dashboard.components.chat_viewer import format_chat_transcript, render_chat_interface
from src.dashboard.components.icons import get_icon
from src.dashboard.dimensions import KENT_DIMENSIONS_ORDERED
from src.dashboard.utils import safe_rerun_fragment
from src.dashboard.views.step1_paste import render_step1_paste_view
from src.data.case_store import save_case
from src.models.case import ClinicalCase


@st.fragment
def render_bedside_dialogue_panel(dm: DialogueManager, current_case: ClinicalCase) -> None:
    """Render Bedside Dialogue chat and intake controls in an isolated fragment."""
    col_chat, col_ctrl = st.columns([3, 1])
    with col_ctrl:
        with st.container(border=True):
            st.html(
                f"""
                <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 12px;'>
                    {get_icon('tune', size=18, color='#10B981')}
                    <span style='font-size: 15px; font-weight: 700; color: #F9FAFB;'>Intake Controls</span>
                </div>
                """
            )

            st.markdown("<div style='font-size: 13px; font-weight: 700; color: #D1D5DB; margin-bottom: 6px;'>Active Case Summary:</div>", unsafe_allow_html=True)
            filled_items = []
            for dim in KENT_DIMENSIONS_ORDERED:
                vals = current_case.dimensions.get(dim.key, [])
                if vals:
                    filled_items.append((dim.label, ", ".join(vals), dim.badge_class, dim.tooltip))

            if filled_items:
                for d_label, d_val, b_cls, d_tip in filled_items:
                    st.markdown(f"<div style='font-size: 12px; margin-bottom: 4px;' title='{d_tip}'><span class='badge {b_cls}' style='font-size:11px; padding:2px 6px;'>{d_label}</span> <span style='color:#F9FAFB;'>{d_val}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='font-size: 12px; color: #8492A6; margin-bottom: 8px; font-style: italic;'>No symptoms captured yet. Converse in the dialogue console to extract dimensions.</div>", unsafe_allow_html=True)

            st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)

            collected_count = current_case.filled_dimensions_count
            min_dims = get_min_dimensions_to_unlock()
            can_proceed = current_case.is_ready_for_repertorization or (collected_count >= min_dims)

            if can_proceed:
                if st.button("Proceed to Clinical Review →", type="primary", width="stretch", key="btn_proceed_review"):
                    dm.sync_to_case(current_case)
                    save_case(current_case)
                    st.session_state.workspace_step = 2
                    st.rerun(scope="app")
            else:
                st.button("Proceed to Clinical Review →", type="primary", disabled=True, width="stretch", help=f"Capture at least {min_dims} symptom dimension to unlock.", key="btn_proceed_review_disabled")
                st.markdown(f"<div style='font-size: 11.5px; color: #9CA3AF; margin-top: 4px;'>Requires at least {min_dims} dimension &mdash; currently {collected_count}/7.</div>", unsafe_allow_html=True)

            st.markdown("---")

            with st.popover("Export Consultation Transcript", width="stretch"):
                st.markdown("##### Consultation Transcript")
                transcript_text = format_chat_transcript(dm)
                st.download_button(
                    label="Download Chat (.txt)",
                    data=transcript_text,
                    file_name=f"{current_case.case_id}_consultation.txt",
                    mime="text/plain",
                    width="stretch",
                    key="sidebar_ctrl_download_txt",
                )
                st.code(transcript_text, language="markdown")

            st.markdown("---")

            if st.session_state.get("confirm_intake_reset", False):
                st.warning("Clear all intake symptoms?")
                col_cf1, col_cf2 = st.columns(2)
                with col_cf1:
                    if st.button("Yes, Clear", type="primary", width="stretch", key="confirm_reset_yes"):
                        dm.reset()
                        dm.get_greeting()
                        current_case.dimensions = {k: [] for k in current_case.dimensions}
                        save_case(current_case)
                        st.session_state.current_report = None
                        st.session_state.confirm_intake_reset = False
                        st.toast("Consultation reset.")
                        safe_rerun_fragment()
                with col_cf2:
                    if st.button("Cancel", width="stretch", key="confirm_reset_no"):
                        st.session_state.confirm_intake_reset = False
                        safe_rerun_fragment()
            else:
                if st.button("Reset Consultation", type="secondary", width="stretch", key="btn_reset_consult"):
                    st.session_state.confirm_intake_reset = True
                    safe_rerun_fragment()

    with col_chat:
        render_chat_interface(dm)


def render_step1_intake(dm: DialogueManager, current_case: ClinicalCase, pipeline: Any) -> None:
    """Render Step 1: Patient Clinical Intake (router for Guided conversation, Paste notes, and Manual entry)."""
    st.markdown("#### Step 1: Patient Clinical Intake")

    # Options and one-line captions
    mode_options = ["Guided conversation", "Paste notes", "Enter manually"]
    mode_captions = {
        "Guided conversation": "patient present, about 5-8 min",
        "Paste notes": "from existing notes, about 30 s",
        "Enter manually": "jumps to Step 2 to enter rubrics directly",
    }

    # Normalize existing session state if transitioning from legacy radio values
    curr_selection = st.session_state.get("intake_mode_select")
    if curr_selection not in mode_options:
        if curr_selection == "Paste Clinical Narrative (Text)":
            curr_selection = "Paste notes"
        else:
            curr_selection = "Guided conversation"
        st.session_state.intake_mode_select = curr_selection

    selected_mode = st.segmented_control(
        "Select clinical intake workflow:",
        mode_options,
        default=curr_selection,
        key="intake_mode_select",
        label_visibility="collapsed",
    )

    if not selected_mode:
        selected_mode = "Guided conversation"

    caption_text = mode_captions.get(selected_mode, "")
    st.caption(f"Workflow: {selected_mode} — {caption_text}")
    st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

    if selected_mode == "Enter manually":
        # Jump directly to Step 2 (Review) without requiring a pre-saved case
        st.session_state.workspace_step = 2
        st.rerun(scope="app")
    elif selected_mode == "Paste notes":
        render_step1_paste_view(current_case, dm, pipeline)
    else:
        render_bedside_dialogue_panel(dm, current_case)
