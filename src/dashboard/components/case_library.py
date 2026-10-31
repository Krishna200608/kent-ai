"""Case Library & Saved Consultation Management Component (Phase 1 & 7).

Allows clinicians to save, search, resume, delete, and export patient consultations.
"""

from __future__ import annotations

import logging
import streamlit as st

from src.dashboard.components.icons import get_icon
from src.dashboard.pdf_exporter import generate_case_pdf
from src.dashboard.utils import esc
from src.data.case_store import (
    delete_case,
    generate_case_id,
    get_case,
    list_cases,
    purge_blank_cases,
    save_case,
)
from src.models.case import ClinicalCase
from src.pipeline.orchestrator import PatientReport

logger = logging.getLogger("case_library")


def render_case_library(current_case: ClinicalCase) -> None:
    """Render patient cases library with search, resume, and export actions."""
    st.html(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                {get_icon('clinical_notes', size=24, color='#10B981')}
                <h3 style="margin: 0; font-size: 20px;">Patient Case Library</h3>
            </div>
            <div style="font-size: 13px; color: #9CA3AF;">
                Persistent SQLite Consultation Storage
            </div>
        </div>
        """
    )

    all_cases = list_cases(limit=100)
    blank_count = sum(
        1 for c in all_cases
        if c.get("dimensions_captured", 0) == 0 and not (c.get("chief_complaint") or "").strip()
    )

    if blank_count > 0:
        col_search, col_clean, col_new = st.columns([3, 1.4, 1.2], vertical_alignment="bottom")
    else:
        col_search, col_new = st.columns([4, 1.2], vertical_alignment="bottom")
        col_clean = None

    with col_search:
        search_q = st.text_input(
            "Search Saved Consultations:",
            placeholder="Search by Patient Name, Case ID, or Chief Complaint...",
            key="case_lib_search",
        )

    if col_clean is not None:
        with col_clean:
            if st.button(
                f"Clean up {blank_count} empty draft{'s' if blank_count > 1 else ''}",
                type="secondary",
                width="stretch",
                help="Purge cases with 0 captured dimensions and no chief complaint",
            ):
                purged = purge_blank_cases()
                st.toast(f"Purged {purged} empty draft(s).")
                st.rerun()

    with col_new:
        if st.button("+ New Case", type="primary", width="stretch", help="Start a new patient intake"):
            new_id = generate_case_id()
            fresh_case = ClinicalCase(case_id=new_id)
            st.session_state.current_case = fresh_case
            dm = st.session_state.dialogue_manager
            dm.reset()
            dm.load_from_case(fresh_case)
            dm.get_greeting()
            st.session_state.current_report = None
            st.session_state.workspace_step = 1
            st.session_state.active_nav_tab = "Case Workspace"
            st.toast(f"Created new consultation: {new_id}")
            st.rerun()

    cases = all_cases
    if search_q.strip():
        q = search_q.strip().lower()
        cases = [
            c for c in cases
            if q in c["patient_name"].lower() or q in c["case_id"].lower() or q in (c.get("chief_complaint") or "").lower()
        ]

    if not cases:
        st.info("No saved cases found. Click '+ New Case' to start a consultation.")
        return

    st.markdown(f"Showing **{len(cases)}** saved consultation(s):")

    for c_info in cases:
        cid = c_info["case_id"]
        is_active = (cid == current_case.case_id)
        active_badge = f"<span class='status-pill' style='color:#10B981; border-color:#10B981; margin-left:8px;'>ACTIVE</span>" if is_active else ""

        with st.container(border=True):
            col_info, col_actions = st.columns([5, 2], vertical_alignment="center")

            with col_info:
                st.html(
                    f"""
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                        <span style="font-weight: 800; font-size: 15px; color: #FFFFFF;">{esc(c_info['patient_name'])}</span>
                        <span style="font-size: 12px; color: #9CA3AF;">({esc(c_info['demographics'])})</span>
                        <code style="font-size: 11px; color: #10B981; background: rgba(16, 185, 129, 0.1); padding: 2px 6px; border-radius: 4px;">{esc(cid)}</code>
                        {active_badge}
                    </div>
                    <div style="font-size: 12.5px; color: #D1D5DB; margin-bottom: 6px;">
                        <b>Chief Complaint:</b> {esc(c_info['chief_complaint'] or 'Not specified')}
                    </div>
                    <div style="font-size: 11.5px; color: #9CA3AF; display: flex; gap: 14px; flex-wrap: wrap;">
                        <span>Totality: <b>{c_info['dimensions_captured']}/7</b> dimensions ({c_info['total_symptoms']} symptoms)</span>
                        <span>Leading Remedy: <b>{esc(c_info['top_remedy'])}</b></span>
                        <span>Updated: {esc(c_info['updated_at'][:16].replace('T', ' '))}</span>
                    </div>
                    """
                )

            with col_actions:
                c_load, c_dl, c_del = st.columns([2, 1, 1])

                with c_load:
                    if st.button("Resume" if not is_active else "In View", key=f"btn_resume_{cid}", type="primary" if not is_active else "secondary", width="stretch"):
                        loaded_case = get_case(cid)
                        if loaded_case:
                            st.session_state.current_case = loaded_case
                            dm = st.session_state.dialogue_manager
                            dm.load_from_case(loaded_case)
                            st.session_state.current_report = None
                            if loaded_case.report_data:
                                # Wrap report data back into PatientReport
                                try:
                                    st.session_state.current_report = PatientReport(
                                        patient_id=loaded_case.report_data.get("patient_id", loaded_case.case_id),
                                        transcript=loaded_case.report_data.get("transcript", ""),
                                        dimensions=loaded_case.report_data.get("dimensions", {}),
                                        matched_rubrics=loaded_case.report_data.get("matched_rubrics", []),
                                        ranked_remedies=loaded_case.report_data.get("ranked_remedies", []),
                                        search_queries=loaded_case.report_data.get("search_queries", []),
                                        entities=loaded_case.report_data.get("entities", []),
                                    )
                                except Exception as err:
                                    logger.warning("Failed to restore PatientReport for case %s: %s", cid, err)
                            st.session_state.workspace_step = 4 if loaded_case.report_data else (2 if loaded_case.filled_dimensions_count >= 1 else 1)
                            st.session_state.active_nav_tab = "Case Workspace"
                            st.toast(f"Resumed consultation: {cid}")
                            st.rerun()

                with c_dl:
                    with st.popover("Export", help="Export PDF or JSON"):
                        loaded = get_case(cid)
                        if loaded:
                            pdf_data = generate_case_pdf(loaded)
                            st.download_button(
                                "Download PDF",
                                data=pdf_data,
                                file_name=f"{cid}_consultation.pdf",
                                mime="application/pdf",
                                width="stretch",
                                key=f"dl_pdf_{cid}",
                            )
                            st.download_button(
                                "Download JSON",
                                data=loaded.to_json(),
                                file_name=f"{cid}_case.json",
                                mime="application/json",
                                width="stretch",
                                key=f"dl_json_{cid}",
                            )

                with c_del:
                    if st.button("Delete", key=f"btn_del_{cid}", help="Delete saved case from SQLite"):
                        delete_case(cid)
                        st.toast(f"Deleted {cid}.")
                        st.rerun()
