"""PDF Clinical Report Exporter for Kent-AI.

Generates professional, printable clinical consultation summaries using ReportLab.
Adheres to Dr. J. T. Kent's classical repertorization methodology and modern
publication-grade clinical document design.
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate

from src.models.case import ClinicalCase
from src.pipeline.orchestrator import PatientReport
from src.dashboard.pdf.canvas import NumberedCanvas, make_canvas_factory, _make_canvas_factory
from src.dashboard.pdf.styles import clean_rubric_path, _clean_rubric_path, get_pdf_stylesheet
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

# Re-exports for 100% backward compatibility
__all__ = [
    "generate_case_pdf",
    "NumberedCanvas",
    "make_canvas_factory",
    "_make_canvas_factory",
    "clean_rubric_path",
    "_clean_rubric_path",
]


def generate_case_pdf(
    case: ClinicalCase,
    report: Optional[PatientReport] = None,
) -> bytes:
    """Generate a publication-grade clinical consultation PDF as raw bytes.

    Features:
    - Executive midnight/emerald clinical brand banner
    - Clean demographics grid with totality dimension completion
    - Formatted 7-Dimension Kentian Totality card
    - Prominent Primary Clinical Simillimum Feature Box
    - Ranked remedy differential table with Latin names and Kent grade distribution
    - OCR-sanitized repertory rubric paths with similarity score badges
    - Two-pass running header and footer with dynamic 'Page X of Y' pagination
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=40,
        bottomMargin=45,
    )

    styles = get_pdf_stylesheet()
    story: List[Any] = []

    # Format timestamps
    date_display = (case.updated_at[:10] if case.updated_at else "")
    time_display = (case.updated_at[11:16] if len(case.updated_at or "") >= 16 else "")
    full_timestamp = f"{date_display} {time_display}".strip()

    # 1. Header Banner
    story.extend(build_header_banner(case, full_timestamp, date_display, styles))

    # 2. Patient Demographics & Intake Modality Grid
    story.extend(build_demographics_card(case, full_timestamp, styles))

    # Retrieve repertorization data
    rep_dict: Optional[Dict[str, Any]] = None
    if report is not None:
        rep_dict = report.to_dict()
    elif case.report_data:
        rep_dict = case.report_data

    # 3. Clinical Case Summary (Physician Brief) Card
    story.extend(build_clinical_summary_box(case, rep_dict, styles))

    # 4. Section 1: Kent's 7-Dimension Clinical Totality
    story.extend(build_totality_table(case, styles))

    ranked_remedies = rep_dict.get("ranked_remedies", []) if rep_dict else []
    active_rubrics = [r for r in rep_dict.get("matched_rubrics", []) if not r.get("muted")] if rep_dict else []
    total_rubrics_count = len(active_rubrics)

    # 5. Primary Clinical Simillimum Feature Box (Hero Card)
    story.extend(build_primary_simillimum_box(ranked_remedies, total_rubrics_count, styles))

    # 6. Section 2: Ranked Remedy Candidates (Differential Table)
    story.extend(build_ranked_remedies_table(ranked_remedies, total_rubrics_count, styles))

    # 7. Section 3: Supporting Kent Repertory Rubrics
    story.extend(build_supporting_rubrics_table(active_rubrics, styles))

    # 8. Clinical Research Notice / Legal Disclaimer Box
    story.extend(build_disclaimer_card(styles))

    # Build document using dynamic NumberedCanvas factory
    canvas_factory = make_canvas_factory(
        case_id=case.case_id or "CASE-RECORD",
        date_str=full_timestamp or date_display,
    )
    doc.build(story, canvasmaker=canvas_factory)

    return buffer.getvalue()
