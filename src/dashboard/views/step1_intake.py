"""Step 1 Patient Clinical Intake view (router for Guided conversation, Paste notes, and Manual entry)."""

from __future__ import annotations

from typing import Any
import streamlit as st

from src.chatbot.dialogue_manager import DialogueManager
from src.dashboard.components.case_snapshot import render_case_snapshot
from src.dashboard.components.chat_viewer import render_chat_interface
from src.dashboard.views.step1_paste import render_step1_paste_view
from src.models.case import ClinicalCase


@st.fragment
def render_bedside_dialogue_panel(dm: DialogueManager, current_case: ClinicalCase) -> None:
    """Render Bedside Dialogue chat interface in an isolated fragment."""
    render_chat_interface(dm)


def render_step1_intake(dm: DialogueManager, current_case: ClinicalCase, pipeline: Any) -> None:
    """Render Step 1: Patient Clinical Intake with 7:3 two-column layout and sticky Case snapshot."""
    col_main, col_rail = st.columns([7, 3], gap="large")

    with col_rail:
        render_case_snapshot(current_case, dm)

    with col_main:
        st.markdown("#### Step 1: Patient Clinical Intake")

        # Intake modality switcher
        mode_options = ["Guided conversation", "Paste notes", "Enter manually"]
        mode_captions = {
            "Guided conversation": "patient present, about 5-8 min",
            "Paste notes": "from existing notes, about 30 s",
            "Enter manually": "jumps to Step 2 to enter rubrics directly",
        }

        # Normalize existing session state if transitioning from legacy radio values
        if "intake_mode_select" not in st.session_state or st.session_state.intake_mode_select not in mode_options:
            curr_val = st.session_state.get("intake_mode_select")
            if curr_val == "Paste Clinical Narrative (Text)":
                st.session_state.intake_mode_select = "Paste notes"
            else:
                st.session_state.intake_mode_select = "Guided conversation"

        selected_mode = st.segmented_control(
            "Select clinical intake workflow:",
            mode_options,
            key="intake_mode_select",
            label_visibility="collapsed",
        )

        if not selected_mode:
            selected_mode = "Guided conversation"

        caption_text = mode_captions.get(selected_mode, "")
        st.caption(f"Workflow: {selected_mode} — {caption_text}")
        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

        if selected_mode == "Enter manually":
            st.session_state.workspace_step = 2
            st.rerun(scope="app")
        elif selected_mode == "Paste notes":
            render_step1_paste_view(current_case, dm, pipeline)
        else:
            render_bedside_dialogue_panel(dm, current_case)
