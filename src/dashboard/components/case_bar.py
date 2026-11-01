"""Persistent Case Bar and Consultation Stepper Header (Phase 2 & UI Overhaul).

Displays active Case ID, patient demographics, totality progress ring,
and unified 4-step stepper navigation with state-aware gating.
"""

from __future__ import annotations

from datetime import datetime
import streamlit as st

from src.dashboard.components.busy import busy_slot
from src.dashboard.components.case_dialogs import show_patient_info_dialog
from src.dashboard.components.icons import get_icon
from src.dashboard.components.totality_ring import totality_ring
from src.dashboard.utils import esc
from src.data.case_store import save_case
from src.models.case import ClinicalCase


def render_case_bar(case: ClinicalCase) -> None:
    """Render persistent case summary and unified 4-step stepper."""
    filled_dims = case.filled_dimensions_count
    rubrics_count = len(case.selected_rubric_ids)
    current_step = st.session_state.get("workspace_step", 1)

    has_report = case.report_data is not None or st.session_state.get("current_report") is not None
    ready_for_analysis = case.is_ready_for_repertorization

    # Demographics formatting without leaking '?' or bare '—'
    demo_parts = []
    if case.patient_age:
        demo_parts.append(f"{case.patient_age}y")
    if case.patient_sex and case.patient_sex != "Unspecified":
        demo_parts.append(case.patient_sex)
    demo_html = f" &middot; {esc(' '.join(demo_parts))}" if demo_parts else ""

    last_saved = st.session_state.get(f"last_saved_time_{case.case_id}")
    saved_indicator = (
        f'<span style="font-size: 11.5px; color: var(--text-faint, #8A98AE);">Saved {last_saved}</span>'
        if last_saved
        else '<span style="font-size: 11.5px; color: var(--warn, #F5B94A);">Draft (Unsaved)</span>'
    )

    # Row 1: Sticky Case Context Banner
    col_case_meta, col_case_actions = st.columns([7, 3], vertical_alignment="center")

    with col_case_meta:
        st.html(
            f"""
            <div class="persistent-case-bar" style="margin-bottom: 0; padding: 8px 14px;">
                <div class="case-bar-left">
                    <div class="case-id-badge">
                        {get_icon('clinical_notes', size=16, color='#10B981')}
                        <span style="font-weight: 700; font-family: monospace; letter-spacing: 0.02em;">{esc(case.case_id)}</span>
                    </div>
                    <div class="case-demographics">
                        <b>{esc(case.patient_name)}</b>{demo_html}
                    </div>
                    <div style="margin-left: 4px;">
                        {saved_indicator}
                    </div>
                    <div class="case-totality-pill" tabindex="0" aria-label="{filled_dims} of 7 totality dimensions recorded" title="{filled_dims} of 7 totality dimensions recorded" style="display: inline-flex; align-items: center; gap: 6px;">
                        {totality_ring(case, size=18)}
                        <span>Totality: <b>{filled_dims}/7</b></span>
                    </div>
                    {f'<div class="case-rubrics-pill">{rubrics_count} Rubrics</div>' if rubrics_count else ''}
                </div>
            </div>
            """
        )

    with col_case_actions:
        c_pt, c_save = st.columns([1, 1], vertical_alignment="center")
        with c_pt:
            if st.button("Patient info", key="case_bar_pt_dlg_btn", width="stretch", help="Edit patient demographics and complaint"):
                show_patient_info_dialog(case)

        with c_save:
            slot_save = st.empty()
            if slot_save.button("Save", type="secondary", width="stretch", help=f"Save case {case.case_id} to local SQLite database", key="case_bar_save_btn", shortcut="Ctrl+S"):
                with busy_slot(slot_save, "Saving...", key="case_bar_save_btn", type="secondary"):
                    save_case(case)
                    now_str = datetime.now().strftime("%H:%M")
                    st.session_state[f"last_saved_time_{case.case_id}"] = now_str
                    st.session_state[f"case_bar_saved_flash_{case.case_id}"] = True
                    st.toast("Saved")
                    st.rerun()
            if st.session_state.pop(f"case_bar_saved_flash_{case.case_id}", False):
                st.caption("✓ Saved")

    # Row 2: Unified Interactive Stepper (4 steps with titles, sublabels, and gating)
    STEPS = [
        (
            1,
            "1. Intake",
            "Capture symptoms",
            True,
            "Step 1: Patient Clinical Intake dialogue and text extraction",
        ),
        (
            2,
            "2. Review",
            "Confirm and edit",
            True,
            "Step 2: Clinical review and 7-dimension validation",
        ),
        (
            3,
            "3. Analysis",
            "Rank remedies",
            ready_for_analysis,
            "Step 3: Repertorization analysis and rubric curation" if ready_for_analysis else "Capture at least 1 symptom dimension to unlock Analysis",
        ),
        (
            4,
            "4. Report",
            "Export report",
            has_report,
            "Step 4: Comprehensive clinical decision-support report" if has_report else "Run repertorization analysis to generate report",
        ),
    ]

    with st.container(key="stepper_nav"):
        st_cols = st.columns(4)
        for idx, (step_num, title, sublabel, is_enabled, tooltip) in enumerate(STEPS):
            with st_cols[idx]:
                is_active = (current_step == step_num)
                btn_type = "primary" if is_active else "secondary"
                # Multi-line label showing Title and Sublabel
                button_text = f"{title}\n{sublabel}"
                if st.button(
                    button_text,
                    type=btn_type,
                    disabled=not is_enabled,
                    width="stretch",
                    key=f"stepper_btn_{step_num}",
                    help=tooltip,
                ):
                    st.session_state.workspace_step = step_num
                    st.rerun()

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
