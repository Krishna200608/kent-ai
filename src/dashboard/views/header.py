"""Single-row top brand bar with engine telemetry and scope indicator (Phase 2 & UI Overhaul)."""

from __future__ import annotations

import streamlit as st

from src.dashboard.components.icons import get_icon
from src.dashboard.components.ollama_status import check_ollama_online
from src.dashboard.constants import MODEL_DISPLAY_NAME
from src.dashboard.utils import esc
from src.models.case import ClinicalCase


@st.fragment(run_every="2s")
def render_header() -> None:
    """Render single-row top brand navigation bar (<=56px) with engine telemetry."""
    active_scope = st.session_state.get("scope", st.session_state.get("repertory_scope", "MIND focus"))
    is_mind = "MIND" in str(active_scope)
    short_scope = "MIND · 4,933" if is_mind else "All · 74,513"

    dm = st.session_state.get("dialogue_manager")
    api_base = getattr(dm, "api_base", "http://127.0.0.1:11434") if dm else "http://127.0.0.1:11434"
    is_llm_online = check_ollama_online(api_base)
    if is_llm_online and dm is not None and getattr(dm, "last_call_failed", False):
        dm.last_call_failed = False

    llm_desc = f"{MODEL_DISPLAY_NAME} Online" if is_llm_online else "Offline Fallback (ollama serve)"
    dot_color = "#10B981" if is_llm_online else "#F59E0B"
    border_color = "rgba(16, 185, 129, 0.4)" if is_llm_online else "rgba(245, 158, 11, 0.4)"
    bg_color = "rgba(16, 185, 129, 0.1)" if is_llm_online else "rgba(245, 158, 11, 0.1)"
    icon_color = "#10B981" if is_llm_online else "#F59E0B"

    tooltip_text = (
        f"Active Scope: {active_scope} | "
        f"Dialogue LLM: {llm_desc} | "
        "Kent Knowledge Base: 74,513 rubrics across 37 chapters"
    )

    models_pill = ""
    if st.session_state.get("pipeline") is not None:
        models_pill = f"""
        <div class="session-badge-wrapper" tabindex="0" aria-label="Inference models warm and ready" data-tip="Inference Models: Ready (~18ms)" title="Inference models warm and ready">
            <span class="status-pill session-compact-pill" style="border-color: rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.1); font-size: 11px; padding: 2px 8px;">
                <span class="status-dot" style="background: #10B981;"></span>
                {get_icon('bolt', size=13, color='#10B981')}
                <span><b>Models ready</b></span>
            </span>
        </div>
        """

    st.html(
        f"""
        <div class="brand-header top-bar-header" style="height: 48px; min-height: 48px; max-height: 56px; padding: 6px 14px; margin-bottom: 8px;">
            <div class="brand-left" style="display: flex; align-items: center; gap: 8px;">
                <div class="brand-icon-box" style="width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3);">
                    {get_icon('local_florist', size=20, color='#10B981')}
                </div>
                <div>
                    <span style="font-weight: 800; font-size: 16px; color: var(--text, #E8EDF3); letter-spacing: -0.01em;">Kent-AI</span>
                    <span style="font-size: 11px; color: var(--text-faint, #8A98AE); margin-left: 6px;">Classical Decision Support</span>
                </div>
            </div>
            <div class="brand-pills" style="display: flex; align-items: center; gap: 8px;">
                <div class="session-badge-wrapper" tabindex="0" aria-label="Repertory Scope: {active_scope}" data-tip="Repertory Scope: {active_scope}" title="Repertory Scope: {active_scope}">
                    <span class="status-pill status-pill-focus session-compact-pill" style="font-size: 11px; padding: 2px 8px;">
                        <span class="status-dot"></span>
                        {get_icon('psychology' if is_mind else 'database', size=13, color='#10B981' if is_mind else '#06B6D4')}
                        <span><b>{short_scope}</b></span>
                    </span>
                </div>
                {models_pill}
                <div class="session-badge-wrapper" tabindex="0" aria-label="{tooltip_text}" data-tip="{tooltip_text}" title="{tooltip_text}">
                    <span class="status-pill session-compact-pill" style="border-color: {border_color}; background: {bg_color}; font-size: 11px; padding: 2px 8px;">
                        <span class="status-dot" style="background: {dot_color};"></span>
                        {get_icon('forum', size=13, color=icon_color)}
                        <span><b>{llm_desc}</b></span>
                    </span>
                </div>
            </div>
        </div>
        """
    )


__all__ = ["render_header"]
