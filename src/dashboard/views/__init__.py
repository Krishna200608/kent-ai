"""Views package for Kent-AI Dashboard."""

from src.dashboard.views.header import render_header
from src.dashboard.views.sidebar import render_sidebar, render_sidebar_case_tray
from src.dashboard.views.step1_intake import render_bedside_dialogue_panel, render_step1_intake
from src.dashboard.views.step2_review import render_step2_review
from src.dashboard.views.step3_analysis import render_step3_analysis
from src.dashboard.views.step4_report import (
    render_dimensions_grid,
    render_repertorization_chart,
    render_report_view,
    render_step4_report,
)
from src.dashboard.views.explorer import render_rubric_explorer
from src.dashboard.views.materia_medica import render_materia_medica_view
from src.dashboard.views.methodology import render_methodology_view
from src.dashboard.views.settings import render_settings_view

__all__ = [
    "render_header",
    "render_sidebar",
    "render_sidebar_case_tray",
    "render_bedside_dialogue_panel",
    "render_step1_intake",
    "render_step2_review",
    "render_step3_analysis",
    "render_dimensions_grid",
    "render_repertorization_chart",
    "render_report_view",
    "render_step4_report",
    "render_rubric_explorer",
    "render_materia_medica_view",
    "render_methodology_view",
    "render_settings_view",
]
