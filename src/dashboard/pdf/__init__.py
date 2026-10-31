"""ReportLab clinical document generator package for Kent-AI."""

from __future__ import annotations

from src.dashboard.pdf.canvas import NumberedCanvas, make_canvas_factory
from src.dashboard.pdf.styles import (
    clean_rubric_path,
    get_pdf_stylesheet,
    PRIMARY_DARK,
    BRAND_EMERALD,
    ACCENT_EMERALD,
    LIGHT_EMERALD,
    BORDER_EMERALD,
    GOLD_AMBER,
    LIGHT_AMBER,
    SLATE_HEADER,
    SLATE_TEXT,
    SLATE_MUTED,
    CARD_BG,
    CARD_ALT_ROW,
    BORDER_SUBTLE,
)
from src.dashboard.pdf.components import (
    build_header_banner,
    build_demographics_card,
    build_clinical_summary_box,
    build_totality_table,
    build_primary_simillimum_box,
    build_ranked_remedies_table,
    build_supporting_rubrics_table,
    build_disclaimer_card,
)

__all__ = [
    "NumberedCanvas",
    "make_canvas_factory",
    "clean_rubric_path",
    "get_pdf_stylesheet",
    "build_header_banner",
    "build_demographics_card",
    "build_clinical_summary_box",
    "build_totality_table",
    "build_primary_simillimum_box",
    "build_ranked_remedies_table",
    "build_supporting_rubrics_table",
    "build_disclaimer_card",
    "PRIMARY_DARK",
    "BRAND_EMERALD",
    "ACCENT_EMERALD",
    "LIGHT_EMERALD",
    "BORDER_EMERALD",
    "GOLD_AMBER",
    "LIGHT_AMBER",
    "SLATE_HEADER",
    "SLATE_TEXT",
    "SLATE_MUTED",
    "CARD_BG",
    "CARD_ALT_ROW",
    "BORDER_SUBTLE",
]
