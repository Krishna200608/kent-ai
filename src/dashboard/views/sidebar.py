"""Sidebar telemetry and consultation controls."""

from __future__ import annotations

import uuid
import streamlit as st

from src.dashboard.components.icons import get_icon
from src.dashboard.constants import format_rubric_path
from src.dashboard.dimensions import pluralize
from src.dashboard.session import ENGINE_OPTIONS, get_pipeline
from src.models.case import ClinicalCase
from src.pipeline.orchestrator import PatientReport


def render_sidebar_case_tray():
    """Render persistent Current Case tray in sidebar."""
    tray = st.session_state.get("case_tray", {"rubrics": [], "remedies": []})
    rubrics = tray.get("rubrics", [])
    remedies = tray.get("remedies", [])
    total_items = len(rubrics) + len(remedies)

    st.markdown("---")
    st.html(
        f"""
        <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;'>
            <div style='display: flex; align-items: center; gap: 6px;'>
                {get_icon('briefcase', size=16, color='#10B981')}
                <span style='font-size: 14px; font-weight: 700; color: #F9FAFB;'>Current Case Tray</span>
            </div>
            <span class='step-counter-badge'>{pluralize(total_items, "item", "items")}</span>
        </div>
        """
    )

    if total_items == 0:
        st.markdown(
            '<div style="font-size: 12px; color: #8492A6; margin-bottom: 8px;">'
            'No items collected yet. Click <b>+ Add to case</b> on rubrics or remedies in Explorer or Materia Medica.'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # List rubrics
    if rubrics:
        st.markdown(f"**Selected Rubrics ({pluralize(len(rubrics), 'rubric', 'rubrics')}):**")
        for idx, r in enumerate(rubrics):
            col_r_txt, col_r_del = st.columns([5, 1])
            with col_r_txt:
                raw_name = r.get("path") or r.get("name", "Rubric")
                r_name = format_rubric_path(raw_name)
                if len(r_name) > 34:
                    r_name = "..." + r_name[-31:]
                st.markdown(f"<span style='font-size: 11.5px; color: #E5E7EB;'>&bull; {r_name}</span>", unsafe_allow_html=True)
            with col_r_del:
                if st.button("✕", key=f"del_tray_r_{idx}", help="Remove rubric from case"):
                    tray["rubrics"].pop(idx)
                    st.rerun()

    # List remedies
    if remedies:
        st.markdown(f"**Selected Remedies ({pluralize(len(remedies), 'remedy', 'remedies')}):**")
        for idx, rem in enumerate(remedies):
            col_rem_txt, col_rem_del = st.columns([5, 1])
            with col_rem_txt:
                rem_name = rem.get('full_name') or rem.get('abbreviation')
                rem_abbr = rem.get('abbreviation') or ''
                st.markdown(f"<span style='font-size: 11.5px; color: #34D399;'>&bull; {rem_name} ({rem_abbr})</span>", unsafe_allow_html=True)
            with col_rem_del:
                if st.button("✕", key=f"del_tray_rem_{idx}", help="Remove remedy from case"):
                    tray["remedies"].pop(idx)
                    st.rerun()

    col_btn1, col_btn2 = st.columns([3, 2])
    with col_btn1:
        if rubrics and st.button("Repertorize This Case", type="primary", width="stretch", key="tray_repertorize_btn"):
            pipeline = st.session_state.pipeline
            ranked = pipeline.ranker.rank(rubrics, top_n=10)
            report = PatientReport(
                patient_id=f"TRAY-{uuid.uuid4().hex[:6].upper()}",
                transcript=f"Totality compiled from {pluralize(len(rubrics), 'manually selected rubric', 'manually selected rubrics')} in Case Tray.",
                dimensions={"case_rubrics": [r.get("path") or r.get("name") for r in rubrics]},
                matched_rubrics=rubrics,
                ranked_remedies=ranked,
                search_queries=[r.get("path", "") for r in rubrics],
            )
            st.session_state.current_report = report
            st.session_state.workspace_step = 4
            st.toast("Case repertorized! Displayed in Step 4 Report.")
            st.rerun()
    with col_btn2:
        if st.button("Clear Tray", key="clear_all_tray", width="stretch"):
            st.session_state.case_tray = {"rubrics": [], "remedies": []}
            st.rerun()


def render_sidebar():
    """Render clinical sidebar telemetry and consultation controls."""
    with st.sidebar:
        st.html(
            f"""
            <div style='text-align: center; margin-bottom: 16px; padding: 4px 8px;'>
                <div style='margin-bottom: 8px; display: inline-flex; justify-content: center; align-items: center; width: 50px; height: 50px; border-radius: 14px; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3);'>
                    {get_icon('local_florist', size=28, color='#10B981')}
                </div>
                <div style='font-size: 16px; font-weight: 800; color: #10B981; line-height: 1.25;'>Kent-AI Clinical Decision Support</div>
                <div style='font-size: 11px; color: #9CA3AF; margin-top: 2px;'>Classical Decision Support</div>
            </div>
            """
        )

        case: ClinicalCase | None = st.session_state.get("current_case")

        st.html(
            f"""
            <div style='display: flex; align-items: center; gap: 6px; margin: 10px 0 6px 0;'>
                {get_icon('tune', size=16, color='#10B981')}
                <span style='font-size: 13px; font-weight: 700; color: #F9FAFB;'>Repertory Scope Selection</span>
            </div>
            """
        )
        scope_options = [
            "MIND Chapter Focus (4,933 rubrics)",
            "All 37 Chapters (74,513 rubrics)",
        ]
        new_scope = st.radio(
            "Repertory Scope Control",
            scope_options,
            key="repertory_scope",
            label_visibility="collapsed",
            help="Single source of truth for intake analysis and repertorization across all workspaces.",
        )

        if case:
            case.scope_chapter = "MIND" if "MIND" in new_scope else "ALL"

        with st.expander("Inference Engine & Settings", expanded=False):
            curr_engine = st.session_state.get("inference_engine", ENGINE_OPTIONS[0])
            default_eng_idx = 0
            for i, opt in enumerate(ENGINE_OPTIONS):
                if opt == curr_engine:
                    default_eng_idx = i
                    break

            selected_engine = st.radio(
                "Inference Engine",
                ENGINE_OPTIONS,
                index=default_eng_idx,
                key="engine_radio_select",
                label_visibility="collapsed",
                help="Select underlying NLP architecture for token extraction and symptom classification.",
            )
            if selected_engine != st.session_state.get("inference_engine"):
                st.session_state.inference_engine = selected_engine
                st.session_state.pipeline = get_pipeline(selected_engine)
                if "dialogue_manager" in st.session_state and hasattr(st.session_state.dialogue_manager, "orchestrator"):
                    st.session_state.dialogue_manager.orchestrator = st.session_state.pipeline
                st.rerun()

            st.toggle(
                "Developer telemetry",
                key="show_dev_details",
                help="Toggle low-level system latency, rubric IDs, and model details.",
            )

        render_sidebar_case_tray()

        st.markdown("---")
        with st.expander("Dr. Kent's Totality Principles", expanded=False):
            st.markdown(
                '<div style="font-size: 12px; color: #D1D5DB; line-height: 1.5; font-style: italic;">'
                '“The mental symptoms are the most important, for they express the very man himself. '
                'Next in importance are the physical generals, especially those related to time, temperature, and weather.”'
                '<div style="font-weight: 700; color: #10B981; margin-top: 4px; font-style: normal;">— Dr. J. T. Kent</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        st.html(
            """
            <div style='font-size: 11px; color: #8492A6; text-align: justify; margin-top: 14px;'>
                <b>Investigational Tool:</b> Kent-AI is an academic clinical decision-support and repertorization research system. It does not replace qualified homeopathic or medical evaluation.
            </div>
            """
        )
