"""Persistent Case Bar and Consultation Stepper Header (Phase 1 & 7).

Displays active Case ID, patient demographics, totality progress, and unified stepper navigation.
Keeps clinicians anchored in their clinical workflow without cognitive overload.
"""

from __future__ import annotations

import streamlit as st

from src.dashboard.components.icons import get_icon
from src.dashboard.utils import esc
from src.data.case_store import save_case
from src.models.case import ClinicalCase


def render_case_bar(case: ClinicalCase) -> None:
    """Render persistent case summary, demographics popover, and unified 4-step stepper."""
    filled_dims = case.filled_dimensions_count
    rubrics_count = len(case.selected_rubric_ids)
    current_step = st.session_state.get("workspace_step", 1)

    has_report = case.report_data is not None or st.session_state.get("current_report") is not None
    ready_for_repertorization = case.is_ready_for_repertorization

    # Row 1: Case context banner + Quick Actions (Patient Info popover, Save Case button)
    col_case_meta, col_case_actions = st.columns([7, 3], vertical_alignment="center")

    with col_case_meta:
        st.html(
            f"""
            <div class="persistent-case-bar" style="margin-bottom: 0; padding: 10px 14px;">
                <div class="case-bar-left">
                    <div class="case-id-badge">
                        {get_icon('clinical_notes', size=16, color='#10B981')}
                        <span style="font-weight: 700; letter-spacing: 0.02em;">{esc(case.case_id)}</span>
                    </div>
                    <div class="case-demographics">
                        <b>{esc(case.patient_name)}</b> &middot; {esc(case.patient_age or '—')} {esc(case.patient_sex or '')}
                    </div>
                    <div class="case-totality-pill" title="{filled_dims} of 7 Kentian symptom dimensions recorded">
                        <span class="status-dot"></span> Totality: <b>{filled_dims}/7</b>
                    </div>
                    {f'<div class="case-rubrics-pill">{rubrics_count} Rubrics</div>' if rubrics_count else ''}
                </div>
            </div>
            """
        )

    with col_case_actions:
        c_pt, c_save = st.columns([1, 1], vertical_alignment="center")
        with c_pt:
            with st.popover(f"Patient Info", width="stretch", help="Edit patient name, age, sex, and complaint"):
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

        with c_save:
            if st.button("Save", type="secondary", width="stretch", help=f"Save case {case.case_id} to local SQLite database", key="case_bar_save_btn"):
                save_case(case)
                st.toast(f"Case {case.case_id} saved to library.")

    # Row 2: Unified Interactive Stepper (Single source of navigation)
    STEPS = [
        (1, "1. Intake", True, "Step 1: Patient Clinical Intake dialogue and text extraction"),
        (2, "2. Review", True, "Step 2: Clinical review and 7-dimension validation"),
        (3, "3. Analysis", ready_for_repertorization, "Step 3: Repertorization analysis and rubric curation" if ready_for_repertorization else "Capture at least 1 symptom dimension to unlock analysis"),
        (4, "4. Report", has_report, "Step 4: Comprehensive clinical decision-support report" if has_report else "Run repertorization analysis to generate report"),
    ]

    st_cols = st.columns(4)
    for idx, (step_num, step_label, is_enabled, tooltip) in enumerate(STEPS):
        with st_cols[idx]:
            is_active = (current_step == step_num)
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                step_label,
                type=btn_type,
                disabled=not is_enabled,
                width="stretch",
                key=f"stepper_btn_{step_num}",
                help=tooltip,
            ):
                st.session_state.workspace_step = step_num
                st.rerun()

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
