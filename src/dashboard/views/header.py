"""Brand header and consultation status bar."""

from __future__ import annotations

import streamlit as st

from src.dashboard.components.chat_viewer import check_ollama_online
from src.dashboard.components.icons import get_icon
from src.models.case import ClinicalCase


def render_header():
    """Render top brand navigation bar with clinical logo and active consultation telemetry."""
    active_scope = st.session_state.get("repertory_scope", "MIND Chapter Focus (4,933 rubrics)")
    is_mind = "MIND" in active_scope
    short_scope = "MIND" if is_mind else "All Chapters"

    case: ClinicalCase | None = st.session_state.get("current_case")
    case_label = case.case_id if case else "Active Case"

    dm = st.session_state.get("dialogue_manager")
    is_llm_online = check_ollama_online()
    llm_desc = "LLaMA 3:8B Online" if is_llm_online else "Rule-based Fallback"

    tooltip_text = (
        f"Active Scope: {active_scope} | "
        f"Dialogue LLM: {llm_desc} | "
        "Kent Knowledge Base: 74,513 rubrics across 37 chapters"
    )

    st.html(
        f"""
        <div class="brand-header">
            <div class="brand-left">
                <div class="brand-icon-box">
                    {get_icon('local_florist', size=26, color='#10B981')}
                </div>
                <div>
                    <div class="brand-title">Kent-AI Clinical Decision Support</div>
                    <div class="brand-subtitle">Classical Homeopathic Repertorization &middot; Dr. J. T. Kent Framework</div>
                </div>
            </div>
            <div class="brand-pills">
                <div class="session-badge-wrapper" tabindex="0" aria-label="{tooltip_text}" data-tip="{tooltip_text}" title="{tooltip_text}">
                    <span class="status-pill status-pill-focus session-compact-pill">
                        <span class="status-dot"></span>
                        {get_icon('psychology' if is_mind else 'database', size=14, color='#10B981' if is_mind else '#06B6D4')}
                        <span>Scope: <b>{short_scope}</b></span>
                    </span>
                </div>
                <div class="session-badge-wrapper">
                    <span class="status-pill session-compact-pill" style="border-color: rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.1);">
                        <span class="status-dot" style="background: {'#10B981' if is_llm_online else '#9CA3AF'};"></span>
                        {get_icon('forum', size=14, color='#10B981' if is_llm_online else '#9CA3AF')}
                        <span><b>{llm_desc}</b></span>
                    </span>
                </div>
            </div>
        </div>
        """
    )
