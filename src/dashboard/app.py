"""Streamlit Clinical Decision Support Dashboard for Kent-AI.

A clinician-centric clinical decision-support application built to Google Stitch UI/UX standards:
- 4-Step Consultation Stepper (1. Intake → 2. Review → 3. Analysis → 4. Report)
- Single typed ClinicalCase model as single source of truth
- Persistent SQLite Case Store and Case Library
- Classical Totality Repertory Grid (Rubrics as rows, Remedies as columns) with Mute & Eliminatory toggles
- High-contrast accessible design adhering to WCAG AA
- Professional PDF and JSON export suite
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project repository root is always in sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import streamlit as st

from src.dashboard.styles import inject_custom_css
from src.dashboard.components.busy import inject_busy_runtime
from src.dashboard.components.case_bar import render_case_bar
from src.dashboard.components.case_dialogs import show_first_run_disclaimer_dialog
from src.dashboard.components.case_library import render_case_library
from src.dashboard.session import (
    ENGINE_OPTIONS,
    get_db,
    get_pipeline,
    initialize_session,
)
from src.dashboard.views import (
    render_header,
    render_sidebar,
    render_sidebar_case_tray,
    render_bedside_dialogue_panel,
    render_step1_intake,
    render_step2_review,
    render_step3_analysis,
    render_dimensions_grid,
    render_repertorization_chart,
    render_report_view,
    render_step4_report,
    render_rubric_explorer,
    render_materia_medica_view,
    render_methodology_view,
    render_settings_view,
)
from src.models.case import ClinicalCase
from src.chatbot.dialogue_manager import DialogueManager

logger = logging.getLogger("dashboard")

# Set wide page layout
st.set_page_config(
    page_title="Kent-AI · Classical Homeopathic Repertorization (Kent Framework)",
    page_icon=":material/spa:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main application orchestrator delegating to modular views."""
    # Inject Google Stitch design system and full-screen responsive layout
    inject_custom_css()
    initialize_session()
    render_sidebar()
    render_header()

    if not st.session_state.get("has_acknowledged_disclaimer", False):
        if not st.session_state.get("disclaimer_dialog_shown", False):
            st.session_state["disclaimer_dialog_shown"] = True
            try:
                show_first_run_disclaimer_dialog()
            except Exception:
                pass

    db = get_db()
    pipeline = st.session_state.pipeline
    dm: DialogueManager = st.session_state.dialogue_manager
    current_case: ClinicalCase = st.session_state.current_case

    TAB_LABELS = [
        "Case Workspace",
        "Case Library",
        "Rubric Explorer",
        "Materia Medica",
        "Methodology",
        "Settings",
    ]
    tabs = dict(zip(TAB_LABELS, st.tabs(TAB_LABELS, key="main_tabs", on_change="rerun")))

    # =========================================================================
    # TAB 1: Case Workspace (4-Step Clinician Workflow)
    # =========================================================================
    with tabs["Case Workspace"]:
        if tabs["Case Workspace"].open:
            render_case_bar(current_case)
            step = st.session_state.get("workspace_step", 1)

            if step == 1:
                render_step1_intake(dm, current_case, pipeline)
            elif step == 2:
                render_step2_review(current_case, pipeline)
            elif step == 3:
                report = st.session_state.get("current_report")
                render_step3_analysis(current_case, report, db, pipeline)
            elif step == 4:
                render_step4_report(current_case, db)

    # =========================================================================
    # TAB 2: Case Library
    # =========================================================================
    with tabs["Case Library"]:
        if tabs["Case Library"].open:
            render_case_library(current_case)

    # =========================================================================
    # TAB 3: Rubric Explorer
    # =========================================================================
    with tabs["Rubric Explorer"]:
        if tabs["Rubric Explorer"].open:
            render_rubric_explorer(db, pipeline)

    # =========================================================================
    # TAB 4: Materia Medica & Differential Comparison
    # =========================================================================
    with tabs["Materia Medica"]:
        if tabs["Materia Medica"].open:
            render_materia_medica_view(db)

    # =========================================================================
    # TAB 5: Settings & Methodology
    # =========================================================================
    with tabs["Methodology"]:
        if tabs["Methodology"].open:
            render_methodology_view()

    with tabs["Settings"]:
        if tabs["Settings"].open:
            render_settings_view()

    # Inject busy/loading feedback runtime (must be at end of main)
    inject_busy_runtime()

    # Footer Disclaimer
    st.html(
        """
        <div class="persistent-clinical-disclaimer">
            <span><b>Clinical Research Notice:</b> Kent-AI is an investigational decision-support tool. It does not provide medical diagnoses or prescriptions. Always verify repertory findings against primary homeopathic literature.</span>
        </div>
        """
    )


# Re-exports for backward compatibility
__all__ = [
    "ENGINE_OPTIONS",
    "get_db",
    "get_pipeline",
    "initialize_session",
    "render_header",
    "render_sidebar",
    "render_sidebar_case_tray",
    "render_bedside_dialogue_panel",
    "render_dimensions_grid",
    "render_repertorization_chart",
    "render_report_view",
    "main",
]


if __name__ == "__main__":
    main()
