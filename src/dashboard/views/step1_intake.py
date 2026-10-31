"""Step 1 Patient Clinical Intake view (Chatbot bedside dialogue and narrative text intake)."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.chatbot.dialogue_manager import DialogueManager, get_min_dimensions_to_unlock
from src.dashboard.components.chat_viewer import format_chat_transcript, render_chat_interface
from src.dashboard.components.icons import get_icon
from src.dashboard.dimensions import KENT_DIMENSIONS_ORDERED
from src.dashboard.utils import safe_rerun_fragment
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
    """Render Step 1: Patient Clinical Intake (bedside chat or narrative paste)."""
    st.markdown("#### Step 1: Patient Clinical Intake")
    intake_mode = st.radio(
        "Intake Modality:",
        ["Bedside Dialogue (Chatbot)", "Paste Clinical Narrative (Text)"],
        horizontal=True,
        key="intake_mode_select",
    )

    if intake_mode == "Bedside Dialogue (Chatbot)":
        render_bedside_dialogue_panel(dm, current_case)
    else:
        # Paste Clinical Narrative mode
        with st.container(border=True):
            example_cases = {
                "Select a clinical vignette (or enter free text below)...": "",
                "Case 1: Severe anxiety in morning, worse alone (MIND)": "Doctor, I feel terribly anxious and depressed every morning, worse when alone. My thoughts race with fear and dread. I have no fever and no nausea.",
                "Case 2: Absent-minded & forgetful on waking (MIND)": "Patient complains of extreme absent-mindedness and difficulty concentrating, especially in the morning after waking up, with trembling hands and restless pacing.",
                "Case 3: Fear of dark & crowds with weeping (MIND)": "Patient reports overwhelming fear in the dark and in crowded places. Weeps easily upon any emotional upset, feels completely forsaken and abandoned, relieved by fresh open air.",
                "Case 4: Extreme irritability & impatience with anger (MIND)": "Patient is exceedingly irritable, cannot bear contradiction or noise, full of wrath and quick to anger over trifles, intensely restless at night.",
            }

            selected_example = st.selectbox("Pre-load Clinical Vignette:", list(example_cases.keys()))
            default_text = example_cases.get(selected_example, "")

            user_case_text = st.text_area(
                "Patient Clinical Narrative:",
                value=default_text,
                placeholder="Describe patient symptoms in free text...",
                height=140,
            )

            col_p_run, col_p_info = st.columns([2, 4], vertical_alignment="center")
            with col_p_run:
                if st.button("Extract Symptoms & Proceed →", type="primary", disabled=not bool(user_case_text.strip()), width="stretch"):
                    with st.spinner("Extracting 7 clinical dimensions..."):
                        raw_rep = pipeline.process_transcript(transcript=user_case_text, section_id=1 if "MIND" in current_case.scope_chapter else None)
                        # Load extracted dimensions into current_case directly
                        for dkey, vals in raw_rep.dimensions.items():
                            norm_key = dkey.lower()
                            if norm_key in current_case.dimensions:
                                for v in vals:
                                    current_case.add_symptom(norm_key, v)
                        current_case.chief_complaint = user_case_text[:120] + ("..." if len(user_case_text) > 120 else "")
                        save_case(current_case)
                        dm.load_from_case(current_case)
                        st.session_state.workspace_step = 2
                        st.rerun()

            with col_p_info:
                st.caption("Extracts Location, Sensation, Modalities, Concomitants, Temporal, and Mental generals directly into Clinical Review.")
