"""Persistent Case Bar and Consultation Stepper Header (Phase 1 & 7).

Displays active Case ID, patient demographics, totality progress, and stepper navigation.
Keeps clinicians anchored in their clinical workflow without cognitive overload.
"""

from __future__ import annotations

import streamlit as st

from src.dashboard.components.icons import get_icon
from src.data.case_store import save_case
from src.models.case import ClinicalCase


def render_case_bar(case: ClinicalCase) -> None:
    """Render persistent case summary and 4-step consultation stepper at top of workspace."""
    filled_dims = case.filled_dimensions_count
    rubrics_count = len(case.selected_rubric_ids)
    step = st.session_state.get("workspace_step", 1)

    st.html(
        f"""
        <div class="persistent-case-bar">
            <div class="case-bar-left">
                <div class="case-id-badge">
                    {get_icon('clinical_notes', size=16, color='#10B981')}
                    <span style="font-weight: 700; letter-spacing: 0.02em;">{case.case_id}</span>
                </div>
                <div class="case-demographics">
                    <b>{case.patient_name}</b> &middot; {case.patient_age or '—'} {case.patient_sex or ''}
                </div>
                <div class="case-totality-pill" title="{filled_dims} of 7 Kentian symptom dimensions recorded">
                    <span class="status-dot"></span> Totality: <b>{filled_dims}/7</b>
                </div>
                {f'<div class="case-rubrics-pill">{rubrics_count} Rubrics</div>' if rubrics_count else ''}
            </div>
            <div class="case-bar-right">
                <div class="stepper-indicator">
                    <span class="step-chip {'step-active' if step == 1 else 'step-done' if step > 1 else ''}">1. Intake</span>
                    <span class="stepper-arrow">&rarr;</span>
                    <span class="step-chip {'step-active' if step == 2 else 'step-done' if step > 2 else ''}">2. Review</span>
                    <span class="stepper-arrow">&rarr;</span>
                    <span class="step-chip {'step-active' if step == 3 else 'step-done' if step > 3 else ''}">3. Analysis</span>
                    <span class="stepper-arrow">&rarr;</span>
                    <span class="step-chip {'step-active' if step == 4 else 'step-done' if step > 4 else ''}">4. Report</span>
                </div>
            </div>
        </div>
        """
    )

    # Secondary action bar for stepper navigation and case metadata editing
    col_step_nav, col_patient_edit, col_save = st.columns([6, 3, 2], vertical_alignment="center")

    with col_step_nav:
        st_cols = st.columns(4)
        with st_cols[0]:
            if st.button("1. Intake", type="primary" if step == 1 else "secondary", width="stretch", key="step_btn_1"):
                st.session_state.workspace_step = 1
                st.rerun()
        with st_cols[1]:
            if st.button("2. Review", type="primary" if step == 2 else "secondary", width="stretch", key="step_btn_2"):
                st.session_state.workspace_step = 2
                st.rerun()
        with st_cols[2]:
            disabled_3 = not case.is_ready_for_repertorization
            if st.button("3. Analysis", type="primary" if step == 3 else "secondary", disabled=disabled_3, width="stretch", key="step_btn_3", help="Unlocked when at least 1 symptom dimension is captured"):
                st.session_state.workspace_step = 3
                st.rerun()
        with st_cols[3]:
            has_report = case.report_data is not None or st.session_state.get("current_report") is not None
            if st.button("4. Report", type="primary" if step == 4 else "secondary", disabled=not has_report, width="stretch", key="step_btn_4", help="View repertorization report"):
                st.session_state.workspace_step = 4
                st.rerun()

    with col_patient_edit:
        with st.popover(f"Patient Info: {case.patient_name}", width="stretch"):
            st.markdown("##### Patient Demographics")
            new_name = st.text_input("Patient Name / Ref:", value=case.patient_name, key="edit_pt_name")
            c_age, c_sex = st.columns(2)
            with c_age:
                new_age = st.number_input("Age:", min_value=0, max_value=120, value=case.patient_age or 35, key="edit_pt_age")
            with c_sex:
                sex_opts = ["Unspecified", "Female", "Male", "Other"]
                curr_idx = sex_opts.index(case.patient_sex) if case.patient_sex in sex_opts else 0
                new_sex = st.selectbox("Sex:", sex_opts, index=curr_idx, key="edit_pt_sex")
            new_chief = st.text_area("Chief Complaint Summary:", value=case.chief_complaint, key="edit_pt_chief")

            if st.button("Save Demographics", type="primary", width="stretch"):
                case.patient_name = new_name.strip() or "Anonymous Patient"
                case.patient_age = int(new_age) if new_age else None
                case.patient_sex = new_sex if new_sex != "Unspecified" else None
                case.chief_complaint = new_chief.strip()
                save_case(case)
                st.toast("Patient demographics updated.")
                st.rerun()

    with col_save:
        if st.button("Save Case", type="secondary", width="stretch", help="Save current consultation state to local SQLite database"):
            save_case(case)
            st.toast(f"Case {case.case_id} saved to library.")
