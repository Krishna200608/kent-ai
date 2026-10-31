"""Case Library & Saved Consultation Management Component (Phase 1 & 7).

Allows clinicians to save, search, resume, delete, and export patient consultations.
"""

from __future__ import annotations

from datetime import datetime
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


def format_relative_time(iso_str: str) -> str:
    """Format ISO timestamp as relative time string."""
    try:
        if "T" in iso_str:
            dt = datetime.fromisoformat(iso_str)
        else:
            dt = datetime.strptime(iso_str, "%Y-%m-%d %H:%M:%S")
        diff = datetime.now() - dt
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        elif seconds < 172800:
            return "yesterday"
        else:
            return f"{seconds // 86400}d ago"
    except Exception:
        return iso_str[:16].replace("T", " ")


def render_case_library(current_case: ClinicalCase) -> None:
    """Render patient cases library with search, resume, status chips, and export actions."""
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
    blank_cases = [
        c for c in all_cases
        if c.get("dimensions_captured", 0) == 0 and not (c.get("chief_complaint") or "").strip()
    ]
    non_blank_cases = [c for c in all_cases if c not in blank_cases]
    blank_count = len(blank_cases)

    col_search, col_new = st.columns([4, 1.2], vertical_alignment="bottom")

    with col_search:
        search_q = st.text_input(
            "Search Saved Consultations:",
            placeholder="Search by Patient Name, Case ID, or Chief Complaint...",
            key="case_lib_search",
        )

    with col_new:
        if st.button("+ New Case", type="primary", width="stretch", help="Start a new patient intake"):
            new_id = generate_case_id()
            fresh_case = ClinicalCase(case_id=new_id)
            st.session_state.current_case = fresh_case
            dm = st.session_state.dialogue_manager
            dm.reset()
            dm.load_from_case(fresh_case)
            st.session_state.current_report = None
            st.session_state.workspace_step = 1
            st.session_state.active_nav_tab = "Case Workspace"
            st.toast(f"Created new consultation: {new_id}")
            st.rerun()

    # Empty draft management controls
    show_blanks = False
    if blank_count > 0:
        c_toggle, c_purge = st.columns([3, 1], vertical_alignment="center")
        with c_toggle:
            show_blanks = st.toggle(
                f"Show empty drafts ({blank_count})",
                value=False,
                key="toggle_show_blanks",
            )
        with c_purge:
            if st.button(
                f"Clean up {blank_count} empty draft{'s' if blank_count > 1 else ''}",
                type="secondary",
                width="stretch",
                key="btn_purge_blanks",
                help="Permanently delete cases with 0 captured dimensions and no chief complaint",
            ):
                purged = purge_blank_cases()
                st.toast(f"Purged {purged} empty draft(s).")
                st.rerun()

    cases = all_cases if show_blanks else non_blank_cases

    if search_q.strip():
        q = search_q.strip().lower()
        cases = [
            c for c in cases
            if q in c["patient_name"].lower()
            or q in c["case_id"].lower()
            or q in (c.get("chief_complaint") or "").lower()
        ]

    if not cases:
        st.info("No saved cases found. Click '+ New Case' to start a consultation.")
        return

    st.markdown(f"Showing **{len(cases)}** saved consultation(s):")

    for c_info in cases:
        cid = c_info["case_id"]
        is_active = (cid == current_case.case_id)
        active_badge = (
            "<span class='status-pill' style='color:#10B981; border-color:#10B981; margin-left:8px; font-size:11px;'>ACTIVE</span>"
            if is_active
            else ""
        )

        has_report = bool(c_info.get("top_remedy") and c_info["top_remedy"] != "—")
        dims_count = c_info.get("dimensions_captured", 0)

        if has_report:
            status_chip = "<span class='status-pill' style='color:#10B981; border-color:rgba(16,185,129,0.4); font-size:11px;'>ANALYZED</span>"
        elif dims_count >= 2:
            status_chip = "<span class='status-pill' style='color:#38BDF8; border-color:rgba(56,189,248,0.4); font-size:11px;'>IN REVIEW</span>"
        else:
            status_chip = "<span class='status-pill' style='color:#9CA3AF; border-color:rgba(156,163,175,0.4); font-size:11px;'>DRAFT</span>"

        complaint_title = c_info.get("chief_complaint") or f"Consultation for {c_info['patient_name']}"
        rel_time = format_relative_time(c_info["updated_at"])

        with st.container(border=True):
            col_info, col_actions = st.columns([5, 2], vertical_alignment="center")

            with col_info:
                st.html(
                    f"""
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px; flex-wrap: wrap;">
                        <span style="font-weight: 800; font-size: 15.5px; color: #FFFFFF;">{esc(complaint_title)}</span>
                        {status_chip}
                        {active_badge}
                    </div>
                    <div style="font-size: 12px; color: #9CA3AF; margin-bottom: 6px;">
                        <b>{esc(c_info['patient_name'])}</b> &middot; {esc(c_info['demographics'])} &middot; <code>{esc(cid)}</code> &middot; Updated {esc(rel_time)}
                    </div>
                    <div style="font-size: 11.5px; color: #D1D5DB; display: flex; gap: 14px; flex-wrap: wrap;">
                        <span>Totality: <b>{dims_count}/7</b> dimensions ({c_info.get('total_symptoms', 0)} symptoms)</span>
                        <span>Leading Remedy: <b>{esc(c_info.get('top_remedy', '—'))}</b></span>
                    </div>
                    """
                )

            with col_actions:
                c_resume, c_more = st.columns([3, 1], vertical_alignment="center")

                with c_resume:
                    if st.button(
                        "Resume" if not is_active else "In View",
                        key=f"btn_resume_{cid}",
                        type="primary" if not is_active else "secondary",
                        width="stretch",
                    ):
                        loaded_case = get_case(cid)
                        if loaded_case:
                            st.session_state.current_case = loaded_case
                            dm = st.session_state.dialogue_manager
                            dm.reset()
                            dm.load_from_case(loaded_case)
                            st.session_state.current_report = None
                            if loaded_case.report_data:
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
                            st.session_state.workspace_step = (
                                4 if loaded_case.report_data
                                else (2 if loaded_case.filled_dimensions_count >= 1 else 1)
                            )
                            st.session_state.active_nav_tab = "Case Workspace"
                            st.toast(f"Resumed consultation: {cid}")
                            st.rerun()

                with c_more:
                    with st.popover("•••", help="Case options and exports"):
                        st.markdown(f"##### Case `{esc(cid)}`")
                        
                        # Generate PDF on-demand (deferred)
                        if st.button("Prepare PDF Export", key=f"btn_prep_pdf_{cid}", width="stretch"):
                            loaded_for_pdf = get_case(cid)
                            if loaded_for_pdf:
                                st.session_state[f"pdf_bytes_{cid}"] = generate_case_pdf(loaded_for_pdf)

                        if f"pdf_bytes_{cid}" in st.session_state:
                            st.download_button(
                                "Download PDF",
                                data=st.session_state[f"pdf_bytes_{cid}"],
                                file_name=f"{cid}_clinical_report.pdf",
                                mime="application/pdf",
                                width="stretch",
                                key=f"dl_pdf_{cid}",
                            )

                        loaded_for_json = get_case(cid)
                        if loaded_for_json:
                            st.download_button(
                                "Download JSON",
                                data=loaded_for_json.to_json(),
                                file_name=f"{cid}_case.json",
                                mime="application/json",
                                width="stretch",
                                key=f"dl_json_{cid}",
                            )

                        st.markdown("---")
                        confirm_del = st.checkbox("Confirm deletion", key=f"chk_del_{cid}")
                        if st.button(
                            "Delete Case",
                            key=f"btn_del_{cid}",
                            type="primary" if confirm_del else "secondary",
                            disabled=not confirm_del,
                            width="stretch",
                            help="Permanently delete this case from the database",
                        ):
                            delete_case(cid)
                            st.toast(f"Deleted {cid}.")
                            st.rerun()
