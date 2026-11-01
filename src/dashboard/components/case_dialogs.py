"""Modal dialogs for Kent-AI clinical consultation (Phase 2 & UI Overhaul).

Provides:
- Patient Information dialog (demographics, chief complaint)
- First-run Clinical Research Disclaimer acknowledgement dialog
"""

from __future__ import annotations

import streamlit as st

from src.dashboard.components.icons import get_icon
from src.dashboard.utils import esc
from src.data.case_store import save_case
from src.models.case import ClinicalCase


@st.dialog("Patient Information")
def show_patient_info_dialog(case: ClinicalCase) -> None:
    """Modal dialog for editing patient demographics and chief complaint."""
    st.markdown(
        f"""
        <div style="font-size: 13px; color: var(--text-muted, #A3B0C2); margin-bottom: 12px;">
            Update consultation demographics for <b>{esc(case.case_id)}</b>. Data is stored locally on this machine.
        </div>
        """,
        unsafe_allow_html=True,
    )

    new_name = st.text_input(
        "Patient Name / Clinical ID:",
        value=case.patient_name,
        key="dlg_pt_name",
        help="Patient identifier or pseudonym for consultation records",
    )

    c_age, c_sex = st.columns(2)
    with c_age:
        new_age = st.number_input(
            "Age (years):",
            min_value=0,
            max_value=120,
            value=case.patient_age or 35,
            key="dlg_pt_age",
        )
    with c_sex:
        sex_opts = ["Unspecified", "Female", "Male", "Other"]
        curr_idx = sex_opts.index(case.patient_sex) if case.patient_sex in sex_opts else 0
        new_sex = st.selectbox("Biological Sex:", sex_opts, index=curr_idx, key="dlg_pt_sex")

    new_chief = st.text_area(
        "Chief Complaint / Reason for Encounter:",
        value=case.chief_complaint,
        placeholder="Primary presenting symptom, onset, and chief suffering...",
        key="dlg_pt_chief",
        height=100,
    )

    c_save, c_cancel = st.columns([1.2, 1])
    with c_save:
        if st.button("Save Demographics", type="primary", width="stretch", key="dlg_btn_save"):
            case.patient_name = new_name.strip() or "Anonymous Patient"
            case.patient_age = int(new_age) if new_age else None
            case.patient_sex = new_sex if new_sex != "Unspecified" else None
            case.chief_complaint = new_chief.strip()
            save_case(case)
            st.toast("Patient demographics updated.")
            st.rerun()
    with c_cancel:
        if st.button("Cancel", width="stretch", key="dlg_btn_cancel"):
            st.rerun()


@st.dialog("Clinical Decision Support Notice")
def show_first_run_disclaimer_dialog() -> None:
    """Non-blocking first-run acknowledgement dialog for clinical research tool."""
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            {get_icon('verified', size=24, color='#10B981')}
            <span style="font-size: 16px; font-weight: 700; color: var(--text, #E8EDF3);">
                Investigational Clinical Decision Support
            </span>
        </div>
        <div style="font-size: 13.5px; color: var(--text, #E8EDF3); line-height: 1.6; margin-bottom: 16px;">
            Kent-AI is an investigational software platform for classical homeopathic repertorization
            synthesizing Dr. J. T. Kent's 74,513 rubrics with biomedical language models.
            <ul style="margin: 8px 0 12px 18px; padding: 0; color: var(--text-muted, #A3B0C2);">
                <li>It does <b>not</b> provide autonomous diagnoses or prescriptions.</li>
                <li>All repertory indications must be validated by a certified practitioner.</li>
                <li>All case data remains encrypted/stored locally on this machine.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("I Acknowledge & Understand", type="primary", width="stretch", key="dlg_ack_disclaimer"):
        st.session_state["has_acknowledged_disclaimer"] = True
        st.toast("Acknowledgement recorded.")
        st.rerun()
