"""PDF Clinical Report Exporter for Kent-AI.

Generates professional, printable clinical consultation summaries using reportlab.
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.models.case import ClinicalCase
from src.pipeline.orchestrator import PatientReport


def generate_case_pdf(
    case: ClinicalCase,
    report: Optional[PatientReport] = None,
) -> bytes:
    """Generate a clean, high-contrast clinical consultation PDF as raw bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#065F46"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4B5563"),
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1F2937"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1F2937"),
    )
    bold_label = ParagraphStyle(
        "BoldLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#111827"),
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#6B7280"),
    )

    story: List[Any] = []

    # Title & Header
    story.append(Paragraph("KENT-AI CLINICAL DECISION SUPPORT", title_style))
    story.append(Paragraph("Homeopathic Totality Repertorization Summary", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#059669"), spaceBefore=2, spaceAfter=8))

    # Case Demographics Table
    demo_data = [
        [
            Paragraph("<b>Case ID:</b> " + case.case_id, body_style),
            Paragraph("<b>Date:</b> " + case.updated_at[:10], body_style),
        ],
        [
            Paragraph("<b>Patient:</b> " + case.patient_name, body_style),
            Paragraph(
                f"<b>Demographics:</b> {case.patient_age or '—'} yrs | {case.patient_sex or 'Unspecified'}",
                body_style,
            ),
        ],
        [
            Paragraph(
                f"<b>Scope:</b> {case.scope_chapter or 'All 37 Chapters'} | <b>Method:</b> Classical Totality",
                body_style,
            ),
            Paragraph(f"<b>Status:</b> {case.status.capitalize()}", body_style),
        ],
    ]
    t_demo = Table(demo_data, colWidths=[270, 270])
    t_demo.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ])
    )
    story.append(t_demo)
    story.append(Spacer(1, 10))

    # 1. 7-Dimension Totality Section
    story.append(Paragraph("1. Kent's 7-Dimension Clinical Totality", section_heading))
    dim_rows = [
        [Paragraph("Dimension", bold_label), Paragraph("Captured Clinical Symptoms", bold_label)]
    ]
    labels_map = {
        "location": "Location",
        "sensation": "Sensation",
        "modality_agg": "Worse from (Aggravation)",
        "modality_amel": "Better from (Amelioration)",
        "concomitant": "Concomitants",
        "temporal": "Time Pattern",
        "mental": "Mental / Emotional",
    }
    for k, lbl in labels_map.items():
        vals = case.dimensions.get(k, [])
        val_str = ", ".join(vals) if vals else "None recorded"
        dim_rows.append([Paragraph(lbl, bold_label), Paragraph(val_str, body_style)])

    t_dims = Table(dim_rows, colWidths=[180, 360])
    t_dims.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#065F46")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_dims)
    story.append(Spacer(1, 10))

    # Report Data
    rep_dict: Optional[Dict[str, Any]] = None
    if report is not None:
        rep_dict = report.to_dict()
    elif case.report_data:
        rep_dict = case.report_data

    # 2. Leading Remedy Candidates
    active_rubrics = [r for r in rep_dict.get("matched_rubrics", []) if not r.get("muted")]
    if rep_dict and rep_dict.get("ranked_remedies"):
        story.append(Paragraph("2. Leading Remedy Candidates (Totality Ranking)", section_heading))
        rems = rep_dict["ranked_remedies"][:8]
        total_r = len(active_rubrics)

        rem_rows = [
            [
                Paragraph("Rank", bold_label),
                Paragraph("Remedy", bold_label),
                Paragraph("Full Latin Name", bold_label),
                Paragraph("Score", bold_label),
                Paragraph("Rubric Coverage", bold_label),
            ]
        ]
        for idx, r in enumerate(rems, start=1):
            cov_str = f"{r.get('rubric_count', 0)}/{total_r}"
            rem_rows.append([
                Paragraph(f"#{idx}", bold_label),
                Paragraph(f"<b>{r.get('abbreviation', '')}</b>", body_style),
                Paragraph(r.get("full_name", ""), body_style),
                Paragraph(f"{r.get('score', 0):.2f}", body_style),
                Paragraph(cov_str, body_style),
            ])

        t_rems = Table(rem_rows, colWidths=[40, 70, 230, 80, 120])
        t_rems.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ])
        )
        story.append(t_rems)
        story.append(Spacer(1, 10))

    # 3. Matched Rubrics Table
    if active_rubrics:
        story.append(Paragraph("3. Supporting Kent Repertory Rubrics", section_heading))
        rub_rows = [
            [
                Paragraph("#", bold_label),
                Paragraph("Kent Repertory Rubric Path", bold_label),
                Paragraph("Remedies", bold_label),
            ]
        ]
        for idx, r in enumerate(active_rubrics[:12], start=1):
            p_text = r.get("path") or f"Rubric #{r.get('rubric_id')}"
            rub_rows.append([
                Paragraph(f"R{idx}", bold_label),
                Paragraph(p_text, body_style),
                Paragraph(str(r.get("remedy_count", "—")), body_style),
            ])

        t_rubs = Table(rub_rows, colWidths=[30, 430, 80])
        t_rubs.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ])
        )
        story.append(t_rubs)
        story.append(Spacer(1, 12))

    # Clinical Disclaimer Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#9CA3AF"), spaceBefore=4, spaceAfter=6))
    story.append(
        Paragraph(
            "<b>Clinical Research Notice:</b> Kent-AI is an investigational clinical decision-support system. "
            "It does not deliver medical diagnoses or clinical prescriptions. Always cross-examine repertory findings "
            "against primary Materia Medica and individual patient evaluation.",
            disclaimer_style,
        )
    )

    doc.build(story)
    return buffer.getvalue()
