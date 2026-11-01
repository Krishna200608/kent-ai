"""Sidebar telemetry, active case tracking, and consultation tray controls (Phase 3 & UI Overhaul)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import uuid
import streamlit as st

from src.dashboard.components.case_dialogs import show_first_run_disclaimer_dialog
from src.dashboard.components.busy import busy_slot
from src.dashboard.components.icons import get_icon
from src.dashboard.components.ollama_status import check_ollama_online, get_ollama_latency
from src.dashboard.components.totality_ring import render_totality_ring
from src.dashboard.constants import (
    APP_VERSION,
    GIT_SHA,
    MODEL_DISPLAY_NAME,
    SCOPE_ALL,
    SCOPE_ALL_COUNT,
    SCOPE_DEFINITIONS,
    SCOPE_MIND,
    SCOPE_MIND_COUNT,
    format_rubric_path,
)
from src.dashboard.dimensions import pluralize
from src.dashboard.utils import esc
from src.data.case_store import save_case
from src.models.case import ClinicalCase
from src.pipeline.orchestrator import PatientReport


def _sync_tray_to_case(case: Optional[ClinicalCase]) -> None:
    """Synchronize current tray rubric IDs to the active ClinicalCase and persist to SQLite."""
    if not case:
        return
    tray = st.session_state.get("case_tray", {"rubrics": [], "remedies": []})
    rubrics = tray.get("rubrics", [])
    new_ids: List[int] = []
    for r in rubrics:
        rid = r.get("rubric_id") if "rubric_id" in r else r.get("id")
        if rid is not None:
            try:
                int_id = int(rid)
                if int_id not in new_ids:
                    new_ids.append(int_id)
            except (ValueError, TypeError):
                continue
    case.selected_rubric_ids = new_ids
    if not case.is_blank or new_ids:
        try:
            save_case(case)
        except Exception:
            pass


def render_sidebar_active_case_card(case: Optional[ClinicalCase]) -> None:
    """Render compact active case card with copyable ID, status chip, totality ring, and step jump."""
    if not case or case.is_blank:
        st.html(
            """
            <div class="sidebar-case-card empty">
                <div class="sidebar-case-patient" style="color: var(--text-muted, #A3B0C2);">No Active Case</div>
                <div class="sidebar-case-step">Start a consultation to capture symptoms.</div>
            </div>
            """
        )
        if st.button("+ New Case", key="sidebar_empty_new_case_btn", type="primary", width="stretch"):
            fresh_case = ClinicalCase()
            st.session_state.current_case = fresh_case
            st.session_state.workspace_step = 1
            st.session_state.current_report = None
            st.session_state.case_tray = {"rubrics": [], "remedies": []}
            if "dialogue_manager" in st.session_state:
                st.session_state.dialogue_manager.reset()
            st.rerun()
        return

    # Derive patient display label
    p_name = case.patient_name.strip() if case.patient_name else "Anonymous Patient"
    demo_parts: List[str] = []
    if case.patient_age:
        demo_parts.append(f"{case.patient_age}y")
    if case.patient_sex:
        demo_parts.append(str(case.patient_sex))
    p_label = f"{p_name} · {' '.join(demo_parts)}" if demo_parts else p_name

    # Derive consultation step and status
    curr_step = int(st.session_state.get("workspace_step", 1))
    step_titles = {1: "Intake", 2: "Review", 3: "Analysis", 4: "Report"}
    curr_step_name = step_titles.get(curr_step, "Intake")

    if case.report_data:
        status_text = "Reported" if curr_step == 4 else "Analysed"
        status_class = "analysed"
    elif case.filled_dimensions_count >= 1:
        status_text = "In review"
        status_class = "in-review"
    else:
        status_text = "Draft"
        status_class = "draft"

    ring_svg = render_totality_ring(case, size=30)

    st.html(
        f"""
        <div class="sidebar-case-card">
            <div class="sidebar-case-header">
                <span class="sidebar-case-id" title="Clinical Case Identifier">{esc(case.case_id)}</span>
                <span class="sidebar-status-chip {status_class}">{status_text}</span>
            </div>
            <div class="sidebar-case-body">
                <div class="sidebar-case-info">
                    <div class="sidebar-case-patient" title="{esc(p_label)}">{esc(p_label)}</div>
                    <div class="sidebar-case-step">Step {curr_step}: {curr_step_name}</div>
                </div>
                <div class="sidebar-case-ring" title="Symptom Totality Coverage">
                    {ring_svg}
                </div>
            </div>
        </div>
        """
    )

    if st.button(
        f"Go to Step {curr_step}: {curr_step_name}",
        key="sidebar_goto_step_btn",
        width="stretch",
    ):
        st.session_state.workspace_step = curr_step
        st.session_state.main_tabs = "Case Workspace"
        st.rerun()


def render_sidebar_case_tray() -> None:
    """Render persistent case tray in sidebar with grouped rubrics and remedies."""
    tray = st.session_state.get("case_tray", {"rubrics": [], "remedies": []})
    rubrics = tray.get("rubrics", [])
    remedies = tray.get("remedies", [])
    total_items = len(rubrics) + len(remedies)
    current_case: Optional[ClinicalCase] = st.session_state.get("current_case")

    st.html(
        f"""
        <div class="sidebar-tray-header">
            <div class="sidebar-tray-title">
                {get_icon('briefcase', size=16, color='var(--accent, #10B981)')}
                <span>Case Tray</span>
            </div>
            <span class="step-counter-badge">{total_items}</span>
        </div>
        """
    )

    if total_items == 0:
        st.html(
            """
            <div class="sidebar-tray-empty-text">
                No items collected yet. Click <b>+ Add to case</b> on rubrics or remedies in Explorer or Materia Medica.
            </div>
            """
        )
        if st.button("Open Rubric Explorer", key="sidebar_tray_open_explorer", width="stretch"):
            st.session_state.main_tabs = "Rubric Explorer"
            st.toast("Navigate to the Rubric Explorer tab to search rubrics.")
            st.rerun()
        return

    # Rubrics section
    if rubrics:
        st.markdown(f"**Selected Rubrics ({len(rubrics)}):**")
        for idx, r in enumerate(rubrics):
            raw_path = r.get("path") or r.get("name", "Rubric")
            formatted_path = format_rubric_path(raw_path)
            short_path = formatted_path
            if len(short_path) > 30:
                short_path = "..." + short_path[-27:]

            rem_count = r.get("remedy_count")
            rem_badge = f"<span class='tray-remedy-chip'>{rem_count} rem</span>" if rem_count else ""

            col_txt, col_del = st.columns([5, 1])
            with col_txt:
                st.html(
                    f"<div class='tray-rubric-text' title='{esc(formatted_path)}'>&bull; {esc(short_path)} {rem_badge}</div>"
                )
            with col_del:
                if st.button("✕", key=f"del_tray_r_{idx}", help=f"Remove '{esc(formatted_path)}' from tray"):
                    tray["rubrics"].pop(idx)
                    _sync_tray_to_case(current_case)
                    st.rerun()

    # Remedies section
    if remedies:
        st.markdown(f"**Selected Remedies ({len(remedies)}):**")
        for idx, rem in enumerate(remedies):
            rem_name = rem.get("full_name") or rem.get("abbreviation", "Remedy")
            rem_abbr = rem.get("abbreviation") or ""
            col_rem_txt, col_rem_del = st.columns([5, 1])
            with col_rem_txt:
                st.html(
                    f"<div class='tray-rubric-text' style='color: var(--accent, #10B981);' title='{esc(rem_name)}'>&bull; {esc(rem_name)} ({esc(rem_abbr)})</div>"
                )
            with col_rem_del:
                if st.button("✕", key=f"del_tray_rem_{idx}", help=f"Remove '{esc(rem_name)}' from tray"):
                    tray["remedies"].pop(idx)
                    st.rerun()

    # Primary Tray Actions
    if rubrics:
        slot_tray_rep = st.empty()
        if slot_tray_rep.button("Repertorize This Case", type="primary", width="stretch", key="tray_repertorize_btn"):
            with busy_slot(slot_tray_rep, "Repertorizing...", key="tray_repertorize_btn", type="primary"):
                with st.spinner("Repertorizing tray rubrics...", show_time=True):
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
                    st.session_state.main_tabs = "Case Workspace"
                    st.toast("Case repertorized! Displayed in Step 4 Report.")
                    st.rerun()

    # Clear Tray Control
    if total_items > 3:
        with st.popover("Clear Tray", help="Remove all items from current case tray"):
            st.markdown(f"Clear all **{total_items}** items from tray?")
            if st.button("Confirm Clear", key="confirm_clear_tray_popover", type="primary", width="stretch"):
                st.session_state.case_tray = {"rubrics": [], "remedies": []}
                _sync_tray_to_case(current_case)
                st.rerun()
    else:
        if st.button("Clear Tray", key="clear_all_tray_btn", width="stretch"):
            st.session_state.case_tray = {"rubrics": [], "remedies": []}
            _sync_tray_to_case(current_case)
            st.rerun()


def render_sidebar_scope_control(case: Optional[ClinicalCase]) -> None:
    """Render single source of truth repertory scope segmented control."""
    st.html(
        f"""
        <div class="sidebar-section-header">
            {get_icon('tune', size=16, color='var(--accent, #10B981)')}
            <span>Repertory Scope</span>
        </div>
        """
    )

    current_scope = st.session_state.get("scope", SCOPE_MIND)
    options = [SCOPE_MIND, SCOPE_ALL]
    default_val = current_scope if current_scope in options else SCOPE_MIND

    scope_selection = st.segmented_control(
        "Repertory Scope Control",
        options=options,
        default=default_val,
        key="sidebar_repertory_scope_seg",
        label_visibility="collapsed",
        help="Single source of truth: MIND chapter focus (4,933) vs All 37 chapters (74,513).",
    )

    if scope_selection and scope_selection != current_scope:
        st.session_state.scope = scope_selection
        st.session_state.repertory_scope = SCOPE_DEFINITIONS.get(scope_selection, {}).get("full_label", scope_selection)
        st.session_state.explorer_results_stale = True
        if case:
            case.scope_chapter = "MIND" if scope_selection == SCOPE_MIND else "ALL"
            try:
                save_case(case)
            except Exception:
                pass
        st.rerun()

    st.html(
        f"""
        <div class="sidebar-scope-caption">
            MIND: {SCOPE_MIND_COUNT:,} rubrics &bull; All: {SCOPE_ALL_COUNT:,} rubrics
        </div>
        """
    )


def render_sidebar_engine_row() -> None:
    """Render compact engine status indicator with expandable telemetry and diagnostics."""
    dm = st.session_state.get("dialogue_manager")
    api_base = getattr(dm, "api_base", "http://127.0.0.1:11434") if dm else "http://127.0.0.1:11434"

    is_online, latency_ms = get_ollama_latency(api_base)
    if is_online and dm is not None and getattr(dm, "last_call_failed", False):
        dm.last_call_failed = False

    status_label = f"{latency_ms}ms" if is_online else "Offline"
    dot_color = "var(--accent, #10B981)" if is_online else "var(--warning, #F59E0B)"

    expander_title = f"{MODEL_DISPLAY_NAME} ({status_label})"

    with st.expander(expander_title, expanded=False):
        st.markdown(f"**Endpoint:** `{api_base}`")
        st.markdown(f"**Model:** `{MODEL_DISPLAY_NAME}`")
        st.markdown("**Temperature:** `0.1`")

        if not is_online:
            st.html(
                """
                <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 6px; padding: 8px; font-size: 11.5px; color: #F59E0B; margin: 8px 0;">
                    Ollama daemon is offline. Start it in terminal:<br>
                    <code style="background: rgba(0,0,0,0.3); padding: 2px 4px; border-radius: 4px; color: #E8EDF3;">ollama serve</code>
                </div>
                """
            )
            if st.button("Retry Connection", key="sidebar_retry_ollama_btn", width="stretch"):
                check_ollama_online.clear()
                get_ollama_latency.clear()
                st.rerun()
        else:
            if st.button("Test Connection", key="sidebar_test_ollama_btn", width="stretch"):
                check_ollama_online.clear()
                get_ollama_latency.clear()
                test_online, test_lat = get_ollama_latency(api_base)
                if test_online:
                    st.toast(f"Connected to {MODEL_DISPLAY_NAME} ({test_lat}ms)")
                else:
                    st.toast("Connection failed.")
                st.rerun()


def render_sidebar_footer() -> None:
    """Render sticky footer with Methodology links, version, and disclaimer trigger."""
    st.html(
        f"""
        <div class="sidebar-sticky-footer">
            <div class="sidebar-footer-links">
                <a href="#methodology" class="sidebar-footer-link">Methodology</a>
                <span class="sidebar-footer-sep">&bull;</span>
                <a href="#totality-principles" class="sidebar-footer-link">Totality Principles</a>
                <span class="sidebar-footer-sep">&bull;</span>
                <span class="sidebar-footer-version">v{APP_VERSION} ({GIT_SHA})</span>
            </div>
            <div class="sidebar-footer-disclaimer">
                Investigational decision-support tool.
            </div>
        </div>
        """
    )
    if st.button("Read full notice", key="sidebar_disclaimer_link_btn", width="stretch"):
        show_first_run_disclaimer_dialog()


def render_sidebar() -> None:
    """Render clinical sidebar telemetry and consultation controls."""
    with st.sidebar:
        # Brand row: 28px icon + "Kent-AI" wordmark
        st.html(
            f"""
            <div class="sidebar-brand-row">
                <div class="sidebar-brand-icon">
                    {get_icon('local_florist', size=22, color='var(--accent, #10B981)')}
                </div>
                <span class="sidebar-brand-wordmark">Kent-AI</span>
            </div>
            """
        )

        case: Optional[ClinicalCase] = st.session_state.get("current_case")

        # Active case card
        render_sidebar_active_case_card(case)

        # Repertory scope single source of truth control
        render_sidebar_scope_control(case)

        # Engine telemetry and diagnostic row
        render_sidebar_engine_row()

        st.markdown("---")

        # Persistent case tray
        render_sidebar_case_tray()

        # Sticky footer with Methodology and disclaimer
        render_sidebar_footer()
