"""Case Library & Saved Consultation Management Component (Phase 5 & UI Overhaul).

Provides clinical registry browsing, search, status filtering, multi-sort,
pagination, cards/compact-table toggle, bulk actions, and single-case operations (Rename, Duplicate, Export, Archive, Delete).
"""

from __future__ import annotations

from datetime import datetime
import logging
import math
from typing import Any, Dict, List, Optional
import streamlit as st

from src.dashboard.components.case_bulk_actions import render_bulk_action_bar
from src.dashboard.components.busy import busy_slot
from src.dashboard.components.icons import get_icon
from src.dashboard.components.totality_ring import totality_ring
from src.dashboard.pdf_exporter import generate_case_pdf
from src.dashboard.utils import esc
from src.data.case_store import (
    delete_case,
    generate_case_id,
    get_case,
    list_cases,
    purge_blank_cases,
    save_case,
    update_cases_status,
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


def _load_and_resume_case(cid: str) -> None:
    """Resume consultation from Case Library into Case Workspace."""
    loaded_case = get_case(cid)
    if not loaded_case:
        st.error(f"Unable to load case {cid}.")
        return

    st.session_state.current_case = loaded_case
    st.session_state.case_tray = {"rubrics": [], "remedies": []}

    # Hydrate tray rubrics from saved case
    if loaded_case.selected_rubric_ids:
        try:
            from src.data.kent_db import get_rubric_by_id
            for r_id in loaded_case.selected_rubric_ids:
                r_data = get_rubric_by_id(r_id)
                if r_data:
                    st.session_state.case_tray["rubrics"].append({
                        "rubric_id": r_data.get("id", r_id),
                        "id": r_data.get("id", r_id),
                        "path": r_data.get("path", f"Rubric #{r_id}"),
                        "remedy_count": r_data.get("remedy_count", 0),
                    })
        except Exception as err:
            logger.warning("Failed to hydrate tray on resume: %s", err)

    dm = st.session_state.dialogue_manager
    dm.reset()
    dm.resume_from_case(loaded_case)
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
    st.session_state.main_tabs = "Case Workspace"
    st.toast(f"Resumed consultation: {cid}")



def _on_click_new_case() -> None:
    """Callback to create a fresh case and switch to Case Workspace."""
    new_id = generate_case_id()
    fresh_case = ClinicalCase(case_id=new_id)
    save_case(fresh_case)
    st.session_state.current_case = fresh_case
    st.session_state.case_tray = {"rubrics": [], "remedies": []}
    dm = st.session_state.dialogue_manager
    dm.reset()
    dm.resume_from_case(fresh_case)
    st.session_state.current_report = None
    st.session_state.workspace_step = 1
    st.session_state.main_tabs = "Case Workspace"
    st.toast(f"Created new consultation: {new_id}")


def _on_click_load_demo() -> None:
    """Callback to load demonstration case and switch to Case Workspace."""
    from src.dashboard.components.demo_case import create_demo_case
    demo_case = create_demo_case()
    save_case(demo_case)
    st.session_state.current_case = demo_case
    st.session_state.case_tray = {"rubrics": [], "remedies": []}
    dm = st.session_state.dialogue_manager
    dm.reset()
    dm.resume_from_case(demo_case)
    st.session_state.current_report = None
    st.session_state.workspace_step = 1
    st.session_state.main_tabs = "Case Workspace"
    st.toast("Loaded demonstration clinical case.")

def render_case_library(current_case: ClinicalCase) -> None:
    """Render patient cases library with search, filtering, pagination, table view, and bulk actions."""
    all_cases = list_cases(limit=300)
    total_db_cases = len(all_cases)

    # 1. Header (clean, without legacy subtitle)
    st.html(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                {get_icon('clinical_notes', size=22, color='var(--accent, #10B981)')}
                <span style="margin: 0; font-size: 20px; font-weight: 800; color: var(--text, #E8EDF3);">Case library</span>
            </div>
            <div style="font-size: 12.5px; color: var(--text-faint, #8A98AE);">
                {total_db_cases} cases &bull; stored on this device
            </div>
        </div>
        """
    )

    # Detect blank drafts (0 dimensions, no chief complaint)
    blank_cases = [
        c for c in all_cases
        if c.get("dimensions_captured", 0) == 0 and not (c.get("chief_complaint") or "").strip()
    ]
    non_blank_cases = [c for c in all_cases if c not in blank_cases]
    blank_count = len(blank_cases)

    # 2. Main Search & "+ New Case" Toolbar Row
    col_search, col_demo, col_new = st.columns([3.5, 1.3, 1.2], vertical_alignment="bottom")
    with col_search:
        search_q = st.text_input(
            "Search Saved Consultations:",
            placeholder="Search by Patient Name, Case ID, Chief Complaint, or Symptoms...",
            key="case_lib_search",
            label_visibility="collapsed",
        )
    with col_demo:
        st.button(
            "Load Demo Case",
            key="btn_lib_load_demo",
            width="stretch",
            help="Load demonstration clinical consultation case",
            on_click=_on_click_load_demo,
        )
    with col_new:
        st.button(
            "+ New Case",
            key="btn_lib_new_case",
            type="primary",
            width="stretch",
            help="Start a fresh patient intake",
            on_click=_on_click_new_case,
        )

    # 3. Filter Controls Row: Status, Sort, View, Empty Drafts
    c_status, c_sort, c_view = st.columns([3, 2, 1.5], vertical_alignment="center")

    with c_status:
        status_filter = st.segmented_control(
            "Status:",
            options=["All", "Draft", "In review", "Analysed", "Archived"],
            default="All",
            key="case_lib_status_filter",
            label_visibility="collapsed",
        )

    with c_sort:
        sort_by = st.segmented_control(
            "Sort by:",
            options=["Updated", "Created", "Totality"],
            default="Updated",
            key="case_lib_sort_by",
            label_visibility="collapsed",
        )

    with c_view:
        view_mode = st.segmented_control(
            "View:",
            options=["Cards", "Table"],
            default="Cards",
            key="case_lib_view_mode",
            label_visibility="collapsed",
        )

    # Empty draft toggle & archive cleanup
    show_blanks = False
    if blank_count > 0:
        c_toggle, c_clean = st.columns([3, 1.5], vertical_alignment="center")
        with c_toggle:
            show_blanks = st.toggle(
                f"Show empty drafts ({blank_count})",
                value=False,
                key="toggle_show_blanks",
            )
        with c_clean:
            with st.popover(f"Clean up empty drafts ({blank_count})", help="Archive or purge cases with 0 dimensions"):
                st.markdown(f"**Clean up {blank_count} empty drafts?**")
                st.caption("Empty cases have 0 captured dimensions and no clinical complaint.")
                if st.button("Archive Empty Cases (Default)", type="primary", key="btn_archive_blanks", width="stretch"):
                    blank_cids = [c["case_id"] for c in blank_cases]
                    updated = update_cases_status(blank_cids, "ARCHIVED")
                    st.toast(f"Archived {updated} empty draft(s).")
                    st.rerun()
                if st.button("Permanently Purge", key="btn_purge_blanks_permanently", width="stretch"):
                    purged = purge_blank_cases()
                    st.toast(f"Purged {purged} empty draft(s).")
                    st.rerun()

    # Base list after empty filter
    cases = all_cases if show_blanks else non_blank_cases

    # Apply text search
    if search_q.strip():
        q = search_q.strip().lower()
        cases = [
            c for c in cases
            if q in c["patient_name"].lower()
            or q in c["case_id"].lower()
            or q in (c.get("chief_complaint") or "").lower()
        ]

    # Apply status filter
    if status_filter and status_filter != "All":
        sf = status_filter.lower().replace(" ", "_")
        filtered_by_status = []
        for c in cases:
            c_status_val = (c.get("status") or "").lower()
            dims = c.get("dimensions_captured", 0)
            has_report = bool(c.get("top_remedy") and c["top_remedy"] != "—")

            if sf == "archived" and c_status_val == "archived":
                filtered_by_status.append(c)
            elif sf == "analysed" and (has_report or c_status_val in ("analysed", "analyzed", "reported")):
                filtered_by_status.append(c)
            elif sf == "in_review" and not has_report and (dims >= 2 or c_status_val in ("in_review", "review")):
                filtered_by_status.append(c)
            elif sf == "draft" and not has_report and dims < 2 and c_status_val != "archived":
                filtered_by_status.append(c)
        cases = filtered_by_status

    # Apply sorting
    if sort_by == "Created":
        cases.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    elif sort_by == "Totality":
        cases.sort(key=lambda x: x.get("dimensions_captured", 0), reverse=True)
    else:
        cases.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

    if not cases:
        st.info("No cases match your filters. Click '+ New Case' to start a consultation.")
        return

    # 4. Multi-select Controls Toolbar
    visible_cids = [c["case_id"] for c in cases]
    selected_ids = [cid for cid in visible_cids if st.session_state.get(f"case_select_{cid}", False)]
    selected_count = len(selected_ids)

    col_sel_sum, col_sel_all, col_desel_all, col_sel_smart = st.columns(
        [3, 1.2, 1.2, 1.4],
        vertical_alignment="center",
    )

    with col_sel_sum:
        if selected_count > 0:
            st.html(
                f"<div style='font-size: 13px; color: var(--text-muted, #A3B0C2);'>"
                f"Showing <b>{len(cases)}</b> saved consultation(s) &bull; "
                f"<span style='color: var(--accent, #10B981); font-weight: 700; background: rgba(16, 185, 129, 0.12); padding: 2px 8px; border-radius: 4px;'>"
                f"{selected_count} selected</span></div>"
            )
        else:
            st.html(f"<div style='font-size: 13px; color: var(--text-muted, #A3B0C2);'>Showing <b>{len(cases)}</b> saved consultation(s):</div>")

    with col_sel_all:
        if st.button(
            f"Select All ({len(cases)})",
            key="btn_select_all_cases",
            width="stretch",
            help="Select all currently filtered cases",
        ):
            for c in cases:
                st.session_state[f"case_select_{c['case_id']}"] = True
            st.rerun()

    with col_desel_all:
        if st.button(
            "Deselect All",
            key="btn_deselect_all_cases",
            disabled=(selected_count == 0),
            width="stretch",
            help="Clear selection for all cases",
        ):
            for c in cases:
                st.session_state[f"case_select_{c['case_id']}"] = False
            st.rerun()

    with col_sel_smart:
        with st.popover("Quick Select", width="stretch", help="Smart selection presets"):
            st.markdown("##### Quick Selection Presets")
            if st.button("Select Analyzed", width="stretch", key="btn_sel_analyzed"):
                for c in cases:
                    has_rep = bool(c.get("top_remedy") and c["top_remedy"] != "—")
                    st.session_state[f"case_select_{c['case_id']}"] = has_rep
                st.rerun()
            if st.button("Select In Review", width="stretch", key="btn_sel_in_review"):
                for c in cases:
                    has_rep = bool(c.get("top_remedy") and c["top_remedy"] != "—")
                    dims = c.get("dimensions_captured", 0)
                    st.session_state[f"case_select_{c['case_id']}"] = (not has_rep and dims >= 2)
                st.rerun()
            if st.button("Select Drafts", width="stretch", key="btn_sel_drafts"):
                for c in cases:
                    has_rep = bool(c.get("top_remedy") and c["top_remedy"] != "—")
                    dims = c.get("dimensions_captured", 0)
                    st.session_state[f"case_select_{c['case_id']}"] = (not has_rep and dims < 2)
                st.rerun()

    if selected_count > 0:
        render_bulk_action_bar(selected_ids, current_case)

    # 5. Pagination
    per_page = 25 if view_mode == "Table" else 12
    total_pages = max(1, math.ceil(len(cases) / per_page))
    curr_page = int(st.session_state.get("case_lib_page", 1))
    curr_page = max(1, min(curr_page, total_pages))
    st.session_state.case_lib_page = curr_page

    start_idx = (curr_page - 1) * per_page
    end_idx = min(start_idx + per_page, len(cases))
    page_cases = cases[start_idx:end_idx]

    # Pagination header
    col_page_txt, col_prev, col_next = st.columns([4, 1, 1], vertical_alignment="center")
    with col_page_txt:
        st.caption(f"Showing {start_idx + 1}–{end_idx} of {len(cases)} cases (Page {curr_page} of {total_pages})")
    with col_prev:
        if st.button("‹ Prev", key="btn_page_prev", disabled=(curr_page <= 1), width="stretch"):
            st.session_state.case_lib_page = curr_page - 1
            st.rerun()
    with col_next:
        if st.button("Next ›", key="btn_page_next", disabled=(curr_page >= total_pages), width="stretch"):
            st.session_state.case_lib_page = curr_page + 1
            st.rerun()

    # 6. Render Table View or Cards View
    if view_mode == "Table":
        # Compact Table Header
        st.html(
            """
            <div style="display: grid; grid-template-columns: 36px 140px 1.5fr 110px 100px 1.2fr 110px 110px; gap: 8px; padding: 8px 12px; background: var(--surface-2, #182330); border: 1px solid var(--line, #243243); border-radius: 6px 6px 0 0; font-size: 11.5px; font-weight: 700; color: var(--text-muted, #A3B0C2);">
                <span></span>
                <span>Case ID</span>
                <span>Patient / Complaint</span>
                <span>Totality</span>
                <span>Status</span>
                <span>Leading Remedy</span>
                <span>Updated</span>
                <span>Actions</span>
            </div>
            """
        )
        for c_info in page_cases:
            cid = c_info["case_id"]
            is_active = (cid == current_case.case_id)
            dims_count = c_info.get("dimensions_captured", 0)
            has_report = bool(c_info.get("top_remedy") and c_info["top_remedy"] != "—")

            if has_report:
                status_label, status_cls = "Analysed", "analysed"
            elif dims_count >= 2:
                status_label, status_cls = "In review", "in-review"
            else:
                status_label, status_cls = "Draft", "draft"

            p_title = c_info.get("chief_complaint") or c_info["patient_name"] or "Untitled case"
            rel_time = format_relative_time(c_info["updated_at"])

            col_row = st.columns([0.35, 1.4, 2.5, 1.1, 1.0, 1.8, 1.2, 1.4], vertical_alignment="center")
            with col_row[0]:
                st.checkbox("Select", key=f"case_select_{cid}", label_visibility="collapsed")
            with col_row[1]:
                st.html(f"<code style='font-size: 11px;'>{esc(cid)}</code>")
            with col_row[2]:
                st.html(f"<div style='font-size: 12px; font-weight: 600; color: var(--text, #E8EDF3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' title='{esc(p_title)}'>{esc(p_title)}</div>")
            with col_row[3]:
                st.html(f"<span style='display: inline-flex; align-items: center; gap: 4px; font-size: 11px;'>{totality_ring(dims_count, size=16)} <b>{dims_count}/7</b></span>")
            with col_row[4]:
                st.html(f"<span class='sidebar-status-chip {status_cls}'>{status_label}</span>")
            with col_row[5]:
                rem_txt = c_info.get("top_remedy")
                lead_rem_html = f"<span style='font-size: 11.5px; color: var(--accent, #10B981); font-weight: 600;'>{esc(rem_txt)}</span>" if (rem_txt and rem_txt != "—") else "<span style='font-size: 11px; color: var(--text-faint, #8A98AE);'>Not analysed</span>"
                st.html(lead_rem_html)
            with col_row[6]:
                st.html(f"<span style='font-size: 11px; color: var(--text-faint, #8A98AE);' title='{esc(c_info['updated_at'])}'>{esc(rel_time)}</span>")
            with col_row[7]:
                if st.button("Open", key=f"tbl_open_{cid}", type="primary" if not is_active else "secondary", width="stretch"):
                    _load_and_resume_case(cid)

    else:
        # Cards View
        for c_info in page_cases:
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

            # Title fallback chain
            complaint_title = c_info.get("chief_complaint") or c_info.get("patient_name") or "Untitled case"
            rel_time = format_relative_time(c_info["updated_at"])

            with st.container(border=True):
                col_chk, col_info, col_actions = st.columns([0.35, 5, 2], vertical_alignment="center")

                with col_chk:
                    st.checkbox(
                        "Select",
                        key=f"case_select_{cid}",
                        label_visibility="collapsed",
                        help=f"Select case {cid} for bulk actions",
                    )

                with col_info:
                    demo_chip = f" &middot; {esc(c_info['demographics'])}" if c_info.get("demographics") else ""
                    top_rem = c_info.get("top_remedy")
                    lead_rem_html = (
                        f"Leading Remedy: <b>{esc(top_rem)}</b>"
                        if (top_rem and top_rem != "—")
                        else "<span style='color: var(--text-faint, #8A98AE);'>Not analysed yet</span>"
                    )

                    st.html(
                        f"""
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px; flex-wrap: wrap;">
                            <span style="font-weight: 800; font-size: 15.5px; color: var(--text, #E8EDF3);">{esc(complaint_title)}</span>
                            {status_chip}
                            {active_badge}
                        </div>
                        <div style="font-size: 12px; color: var(--text-muted, #A3B0C2); margin-bottom: 6px;">
                            <b>{esc(c_info['patient_name'])}</b>{demo_chip} &middot; <code>{esc(cid)}</code> &middot; Updated <span title="{esc(c_info['updated_at'])}">{esc(rel_time)}</span>
                        </div>
                        <div style="font-size: 11.5px; color: var(--text, #E8EDF3); display: flex; align-items: center; gap: 14px; flex-wrap: wrap;">
                            <span style="display: inline-flex; align-items: center; gap: 6px;">
                                {totality_ring(dims_count, size=18)} Totality: <b>{dims_count}/7</b> dimensions ({c_info.get('total_symptoms', 0)} symptoms)
                            </span>
                            <span>{lead_rem_html}</span>
                        </div>
                        """
                    )

                with col_actions:
                    c_resume, c_more = st.columns([3, 1], vertical_alignment="center")

                    with c_resume:
                        st.button(
                            "Resume" if not is_active else "In View",
                            key=f"btn_resume_{cid}",
                            type="primary" if not is_active else "secondary",
                            width="stretch",
                            disabled=is_active,
                            on_click=_load_and_resume_case,
                            args=(cid,),
                        )

                    with c_more:
                        pop = st.popover("•••", key=f"pop_{cid}", on_change="rerun")
                        with pop:
                            if pop.open:
                                st.markdown(f"##### Case `{esc(cid)}`")

                                # Duplicate action
                                if st.button("Duplicate Case", key=f"btn_dup_{cid}", width="stretch"):
                                    orig = get_case(cid)
                                    if orig:
                                        fresh_id = generate_case_id()
                                        dup_case = ClinicalCase.from_dict(orig.to_dict())
                                        dup_case.case_id = fresh_id
                                        dup_case.patient_name = f"{orig.patient_name} (Copy)"
                                        save_case(dup_case)
                                        st.toast(f"Created duplicate: {fresh_id}")
                                        st.rerun()

                                st.markdown("---")
                                st.markdown("**Exports:**")
                                # PDF Export
                                slot_pdf = st.empty()
                                if slot_pdf.button("Prepare PDF", key=f"btn_prep_pdf_{cid}", width="stretch"):
                                    with busy_slot(slot_pdf, "Compiling PDF...", key=f"btn_prep_pdf_{cid}", type="secondary"):
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
                                        on_click="ignore",
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
                                        on_click="ignore",
                                    )

                            st.markdown("---")
                            # Archive action
                            is_archived = (c_info.get("status") == "ARCHIVED")
                            if is_archived:
                                if st.button("Unarchive Case", key=f"btn_unarchive_{cid}", width="stretch"):
                                    update_cases_status([cid], "DRAFT")
                                    st.toast(f"Unarchived {cid}.")
                                    st.rerun()
                            else:
                                if st.button("Archive Case", key=f"btn_archive_{cid}", width="stretch"):
                                    update_cases_status([cid], "ARCHIVED")
                                    st.toast(f"Archived {cid}.")
                                    st.rerun()

                            # Delete action
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
