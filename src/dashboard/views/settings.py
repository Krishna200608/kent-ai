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
    get_case,
    list_cases,
    save_case,
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
                if st.button("Test Connection", key="btn_test_ollama_settings", width="stretch"):
                    is_online, latency_ms = get_ollama_latency()
                    if is_online:
                        st.toast(f"Ollama Online · {latency_ms:.0f}ms round-trip")
                    else:
                        st.toast("Ollama Offline · Ensure 'ollama serve' is running")
                    st.rerun()

            with c_status:
                is_online, latency_ms = get_ollama_latency()
                if is_online:
                    st.html(
                        f"""
                        <div style="font-size: 13px; color: var(--accent, #10B981); display: flex; align-items: center; gap: 6px;">
                            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--accent, #10B981);"></span>
                            <b>Online</b> ({latency_ms:.0f}ms round-trip)
                        </div>
                        """
                    )
                else:
                    st.html(
                        f"""
                        <div style="font-size: 13px; color: #F59E0B; display: flex; align-items: center; gap: 6px;">
                            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #F59E0B;"></span>
                            <b>Offline Fallback</b> (Run <code>ollama serve</code> in terminal)
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
            curr_scope = st.session_state.get("scope", SCOPE_MIND)
            new_scope = st.segmented_control(
                "Default Repertory Scope:",
                options=[SCOPE_MIND, SCOPE_ALL],
                default=curr_scope,
                key="settings_scope_control",
                help="Scope determines the default chapter focus for Rubric Explorer and Repertorization",
            )
            if new_scope and new_scope != curr_scope:
                st.session_state["scope"] = new_scope
                cur_c = st.session_state.get("current_case")
                if cur_c is not None:
                    cur_c.scope_chapter = 1 if new_scope == SCOPE_MIND else None
                st.rerun()

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
            st.markdown(f"Local consultation storage holds **{total_cases}** cases.")

            # Export All Cases Backup
            all_cases_data = []
            for meta in all_cases_meta:
                c_obj = get_case(meta["case_id"])
                if c_obj:
                    all_cases_data.append(c_obj.to_dict())

            export_payload = json.dumps(
                {
                    "exported_at": datetime.now().isoformat(),
                    "app_version": APP_VERSION,
                    "case_count": len(all_cases_data),
                    "cases": all_cases_data,
                },
                indent=2,
            )

            today_str = datetime.now().strftime("%Y%m%d")
            st.download_button(
                label=f"Export All Cases ({total_cases}) to JSON",
                data=export_payload,
                file_name=f"kent_ai_backup_{today_str}.json",
                mime="application/json",
                width="stretch",
                key="btn_export_all_cases",
                help="Download full JSON archive of all saved consultations",
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
                        if st.button(f"Confirm Import of {len(cases_to_import)} Cases", type="primary", width="stretch", key="btn_confirm_import"):
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
                if st.button(
                    "Permanently Delete All Cases",
                    type="primary",
                    disabled=not can_delete,
                    width="stretch",
                    key="btn_purge_all_cases",
                    help="Requires exact confirmation phrase",
                ):
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
