"""Settings & Configuration View (Phase 7 & UI Overhaul).

Provides:
- Local LLM inference engine configuration and live connection test.
- Consultation preferences: default repertory scope, UI density, autosave toggle, and dialogue suggestions.
- Data management: export all consultations (JSON backup), import consultations, and safe bulk purge with typed confirmation.
- About and system version telemetry.
"""

from __future__ import annotations

import json
from datetime import datetime
import streamlit as st

from src.dashboard.components.busy import busy_slot
from src.dashboard.components.icons import get_icon
from src.dashboard.constants import (
    APP_VERSION,
    GIT_SHA,
    MODEL_DISPLAY_NAME,
    SCOPE_ALL,
    SCOPE_ALL_COUNT,
    SCOPE_MIND,
    SCOPE_MIND_COUNT,
)
from src.dashboard.components.ollama_status import check_ollama_online, get_ollama_latency
from src.data.case_store import (
    delete_case,
    get_app_setting,
    get_case,
    list_cases,
    save_case,
    set_app_setting,
)
from src.models.case import ClinicalCase


def render_settings_view() -> None:
    """Render Tab 6: System Configuration, Consultation Preferences, and Data Management."""
    st.html(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            {get_icon('settings', size=24, color='var(--accent, #10B981)')}
            <span style="font-size: 22px; font-weight: 800; color: var(--text, #E8EDF3);">Settings</span>
        </div>
        <div style="font-size: 13.5px; color: var(--text-muted, #A3B0C2); margin-bottom: 16px;">
            Manage inference engine settings, consultation defaults, and local database backups.
        </div>
        """
    )

    c_left, c_right = st.columns(2)

    # 1. Inference Engine Configuration
    with c_left:
        with st.container(border=True):
            st.html(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    {get_icon('tune', size=20, color='var(--accent, #10B981)')}
                    <h4 style="margin: 0; color: var(--text, #E8EDF3); font-size: 16px;">Inference Engine (Local Ollama)</h4>
                </div>
                """
            )
            st.text_input(
                "Ollama Daemon Endpoint:",
                value=st.session_state.get("ollama_endpoint", "http://127.0.0.1:11434"),
                key="settings_ollama_endpoint",
                help="Host URL where local Ollama daemon is running",
                disabled=True,
            )

            st.text_input(
                "Configured LLM Model:",
                value=MODEL_DISPLAY_NAME,
                key="settings_model_name",
                disabled=True,
                help="Derived from configs/chatbot.yaml",
            )

            c_test, c_status = st.columns([1.2, 2], vertical_alignment="center")
            with c_test:
                slot_test = st.empty()
                if slot_test.button("Test Connection", key="btn_test_ollama_settings", width="stretch"):
                    with busy_slot(slot_test, "Testing...", key="btn_test_ollama_settings", type="secondary"):
                        with st.spinner("Testing Ollama connection...", show_time=True):
                            is_online, latency_ms = get_ollama_latency()
                            st.session_state["_last_ollama_test"] = (is_online, latency_ms, datetime.now())
                            if is_online:
                                st.toast(f"Ollama Online - {latency_ms:.0f}ms round-trip")
                            else:
                                st.toast("Ollama Offline - Ensure 'ollama serve' is running")
                            st.rerun()

            with c_status:
                test_cache = st.session_state.get("_last_ollama_test")
                if test_cache:
                    is_online, latency_ms, _ = test_cache
                    checked_hint = " &middot; <span style='font-size:11px; color:var(--text-faint);'>checked just now</span>"
                else:
                    is_online, latency_ms = get_ollama_latency()
                    checked_hint = ""

                if is_online:
                    st.html(
                        f"""
                        <div style="font-size: 13px; color: var(--accent, #10B981); display: flex; align-items: center; gap: 6px;">
                            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--accent, #10B981);"></span>
                            <b>Online</b> ({latency_ms:.0f}ms round-trip){checked_hint}
                        </div>
                        """
                    )
                else:
                    st.html(
                        f"""
                        <div style="font-size: 13px; color: #F59E0B; display: flex; align-items: center; gap: 6px;">
                            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #F59E0B;"></span>
                            <b>Offline Fallback</b> (Run <code>ollama serve</code> in terminal){checked_hint}
                        </div>
                        """
                    )

        # 2. Consultation Preferences
        with st.container(border=True):
            st.html(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    {get_icon('checklist', size=20, color='var(--accent, #10B981)')}
                    <h4 style="margin: 0; color: var(--text, #E8EDF3); font-size: 16px;">Consultation Preferences</h4>
                </div>
                """
            )
            # Default Scope
            st.session_state["scope"] = SCOPE_MIND
            cur_c = st.session_state.get("current_case")
            if cur_c is not None and getattr(cur_c, "scope_chapter", None) != "MIND":
                cur_c.scope_chapter = "MIND"

            st.markdown(
                "<label style='font-size: 13px; font-weight: 600; color: var(--text, #E8EDF3); margin-bottom: 4px; display: block;'>Default Repertory Scope:</label>",
                unsafe_allow_html=True,
            )
            st.html(
                f"""
                <div class="scope-selector-container" style="max-width: 440px;">
                    <div class="scope-pill-active" tabindex="0" aria-label="Default Scope: MIND focus (Active)" title="MIND Chapter Focus (4,933 rubrics) - Currently Validated">
                        <div style="display: flex; align-items: center; gap: 7px;">
                            <span class="status-dot" style="background: var(--accent, #10B981); width: 7px; height: 7px; border-radius: 50%;"></span>
                            <span>MIND Chapter Focus</span>
                            <span style="font-size: 11.5px; color: var(--text-muted, #A3B0C2); font-weight: normal;">({SCOPE_MIND_COUNT:,} rubrics)</span>
                        </div>
                        <span class="scope-tag-active">Active</span>
                    </div>
                    <div class="scope-pill-disabled" tabindex="0" aria-label="All 37 Chapters: Coming soon in v2.0" data-tip="All 37 chapters vector indexing is in progress for the v2.0 release. Kent-AI currently operates in validated Chapter 1: MIND." title="All 37 chapters vector indexing is in progress for the v2.0 release. Kent-AI currently operates in validated Chapter 1: MIND.">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            {get_icon('lock', size=13, color='var(--text-faint, #8A98AE)')}
                            <span>All 37 Chapters</span>
                            <span style="font-size: 11px; color: var(--text-faint, #8A98AE);">({SCOPE_ALL_COUNT:,} rubrics)</span>
                        </div>
                        <span class="scope-tag-coming-soon">Coming Soon in v2.0</span>
                    </div>
                </div>
                <div style="font-size: 11.5px; color: var(--text-faint, #8A98AE); margin-top: 4px; margin-bottom: 12px; line-height: 1.4;">
                    Chapter 1 (MIND) is the currently validated clinical repertory scope (4,933 rubrics). Full 37-chapter indexing (74,513 rubrics) is scheduled for the v2.0 milestone.
                </div>
                """
            )

            # Display Density
            curr_density = st.session_state.get("ui_density", "Comfortable")
            new_density = st.segmented_control(
                "Display Density:",
                options=["Comfortable", "Compact"],
                default=curr_density,
                key="settings_density_control",
                help="Adjust table row height and padding",
            )
            if new_density and new_density != curr_density:
                st.session_state["ui_density"] = new_density

            # Autosave Toggle
            autosave = st.toggle(
                "Autosave consultation drafts",
                value=st.session_state.get("autosave_enabled", True),
                key="settings_autosave_toggle",
                help="Automatically persist extracted dimensions and dialogue turns to local SQLite storage",
            )
            st.session_state["autosave_enabled"] = autosave

            # Suggested Replies Toggle
            show_suggestions = st.toggle(
                "Show suggested replies in clinical dialogue",
                value=st.session_state.get("show_suggested_replies", True),
                key="settings_suggestions_toggle",
                help="Display step-aware quick reply chips in Patient speaking mode",
            )
            st.session_state["show_suggested_replies"] = show_suggestions

            # Clinical Decision Support Notice Preference
            st.divider()
            ack_status = st.session_state.get("has_acknowledged_disclaimer", False)
            c_ack_label, c_ack_btn = st.columns(2)
            with c_ack_label:
                st.caption(
                    "Clinical Notice: **Acknowledged** (hidden on reload)"
                    if ack_status
                    else "Clinical Notice: **Pending Acknowledgement**"
                )
            with c_ack_btn:
                if ack_status:
                    if st.button("Reset Notice", key="btn_reset_disclaimer", width="stretch"):
                        st.session_state["has_acknowledged_disclaimer"] = False
                        st.session_state["disclaimer_dialog_shown"] = False
                        set_app_setting("has_acknowledged_disclaimer", False)
                        st.toast("Notice reset - will show on reload.")
                        st.rerun()

    # 3. Data Management & Backups
    with c_right:
        with st.container(border=True):
            st.html(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    {get_icon('clinical_notes', size=20, color='var(--accent, #10B981)')}
                    <h4 style="margin: 0; color: var(--text, #E8EDF3); font-size: 16px;">Data Management & Backups</h4>
                </div>
                """
            )
            all_cases_meta = list_cases(limit=1000)
            total_cases = len(all_cases_meta)
            act_cnt = sum(1 for c in all_cases_meta if c.get("status") not in ("ARCHIVED", "DRAFT_EMPTY"))
            arc_cnt = sum(1 for c in all_cases_meta if c.get("status") == "ARCHIVED")
            drf_cnt = sum(1 for c in all_cases_meta if c.get("status") == "DRAFT_EMPTY" or (c.get("status") == "DRAFT" and c.get("total_symptoms", 0) == 0))
            st.markdown(f"Local consultation storage holds **{total_cases}** cases ({act_cnt} active &middot; {arc_cnt} archived &middot; {drf_cnt} empty drafts).")

            # Export All Cases Backup (On-Demand)
            backup_key = "settings_backup_cache"
            if backup_key not in st.session_state:
                slot_prep = st.empty()
                if slot_prep.button(f"Prepare Backup ({total_cases} Cases)", key="btn_prep_backup", width="stretch"):
                    with busy_slot(slot_prep, "Compiling backup...", key="btn_prep_backup", type="secondary"):
                        with st.spinner("Exporting all consultation records...", show_time=True):
                            all_cases_data = []
                            for meta in all_cases_meta:
                                c_obj = get_case(meta["case_id"])
                                if c_obj:
                                    all_cases_data.append(c_obj.to_dict())
                            st.session_state[backup_key] = json.dumps(
                                {
                                    "exported_at": datetime.now().isoformat(),
                                    "app_version": APP_VERSION,
                                    "case_count": len(all_cases_data),
                                    "cases": all_cases_data,
                                },
                                indent=2,
                            )
                            st.rerun()
            else:
                today_str = datetime.now().strftime("%Y%m%d")
                st.download_button(
                    label=f"Download Backup ({total_cases} Cases)",
                    data=st.session_state[backup_key],
                    file_name=f"kent_ai_backup_{today_str}.json",
                    mime="application/json",
                    width="stretch",
                    key="btn_export_all_cases",
                    help="Download full JSON archive of all saved consultations",
                    on_click="ignore",
                )

            st.markdown("---")
            # Import Consultations
            st.markdown("##### Import Consultations")
            uploaded = st.file_uploader(
                "Upload JSON backup file:",
                type=["json"],
                key="settings_import_uploader",
                help="Restore previously exported consultations",
            )
            if uploaded is not None:
                try:
                    import_data = json.load(uploaded)
                    cases_to_import = import_data.get("cases", [])
                    if isinstance(cases_to_import, list) and cases_to_import:
                        existing_ids = {m["case_id"] for m in all_cases_meta}
                        dup_count = sum(1 for c in cases_to_import if isinstance(c, dict) and c.get("case_id") in existing_ids)
                        st.info(f"Backup file contains **{len(cases_to_import)}** cases ({dup_count} duplicate IDs will be updated).")

                        slot_imp = st.empty()
                        if slot_imp.button(f"Confirm Import of {len(cases_to_import)} Cases", type="primary", width="stretch", key="btn_confirm_import"):
                            with busy_slot(slot_imp, "Importing...", key="btn_confirm_import", type="primary"):
                                with st.spinner("Writing cases to SQLite...", show_time=True):
                                    imported_count = 0
                                    for item in cases_to_import:
                                        try:
                                            c_instance = ClinicalCase.from_dict(item)
                                            save_case(c_instance)
                                            imported_count += 1
                                        except Exception:
                                            pass
                                    st.toast(f"Successfully imported {imported_count} cases.")
                                    st.rerun()
                except Exception as err:
                    st.error(f"Failed to parse uploaded backup file: {err}")

            st.markdown("---")
            # Safe Bulk Purge with Typed Confirmation
            st.markdown("##### Danger Zone: Purge Database")
            with st.expander("Delete all consultation records", expanded=False):
                st.warning("This action permanently deletes all patient consultations stored in SQLite.")
                confirm_typed = st.text_input(
                    "Type 'DELETE ALL' to confirm permanent purge:",
                    key="settings_delete_confirm_text",
                    placeholder="DELETE ALL",
                )
                can_delete = (confirm_typed.strip() == "DELETE ALL")
                slot_purge = st.empty()
                if slot_purge.button(
                    "Permanently Delete All Cases",
                    type="primary",
                    disabled=not can_delete,
                    width="stretch",
                    key="btn_purge_all_cases",
                    help="Requires exact confirmation phrase",
                ):
                    with busy_slot(slot_purge, "Purging...", key="btn_purge_all_cases", type="primary"):
                        with st.spinner("Purging local records...", show_time=True):
                            for meta in all_cases_meta:
                                delete_case(meta["case_id"])
                            st.toast("All consultation records deleted.")
                            st.rerun()

        # 4. About & System Information
        with st.container(border=True):
            st.html(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    {get_icon('verified', size=20, color='var(--accent, #10B981)')}
                    <h4 style="margin: 0; color: var(--text, #E8EDF3); font-size: 16px;">About Kent-AI</h4>
                </div>
                <div style="font-size: 13px; color: var(--text, #E8EDF3); line-height: 1.6;">
                    <div><b>Application Version:</b> <code>v{APP_VERSION}</code></div>
                    <div><b>Git Commit Short SHA:</b> <code>{GIT_SHA}</code></div>
                    <div><b>Data Storage:</b> Local SQLite (<code>data/cases/cases.sqlite</code>)</div>
                    <div><b>Repertory Database:</b> 74,513 rubrics (<code>data/raw/repertory.sqlite</code>)</div>
                    <div><b>Privacy Guarantee:</b> 100% On-Device Processing · Zero Network Egress</div>
                </div>
                """
            )
