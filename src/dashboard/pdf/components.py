"""ReportLab Flowable section builders for Kent-AI clinical consultation reports."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from src.models.case import ClinicalCase
from src.dashboard.pdf.styles import (
    ACCENT_EMERALD,
    BORDER_EMERALD,
    BORDER_SUBTLE,
    BRAND_EMERALD,
    CARD_BG,
    LIGHT_EMERALD,
    PDFStylesheet,
    PRIMARY_DARK,
    SLATE_HEADER,
    SLATE_TEXT,
    clean_rubric_path,
)


def build_header_banner(
    case: ClinicalCase,
    full_timestamp: str,
    date_display: str,
    styles: PDFStylesheet,
) -> List[Any]:
    """1. Executive Title Hero Banner (Page 1)."""
    banner_data = [
        [
            Paragraph(
                "<b>KENT-AI CLINICAL DECISION SUPPORT</b>",
                styles.banner_title,
            ),
            Paragraph("CONFIDENTIAL MEDICAL REPORT", styles.banner_pill),
        ],
        [
            Paragraph(
                "Classical Homeopathic Totality Repertorization Summary  *  Dr. J. T. Kent Framework",
                styles.banner_subtitle,
            ),
            Paragraph(
                f"<b>Case ID:</b> {case.case_id}<br/><b>Date:</b> {date_display or 'Current'}",
                styles.banner_meta,
            ),
        ],
    ]
    t_banner = Table(banner_data, colWidths=[360, 180])
    t_banner.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PRIMARY_DARK),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
            ("TOPPADDING", (0, 1), (-1, 1), 2),
        ])
    )
    divider = HRFlowable(
        width="100%",
        thickness=2.5,
        color=ACCENT_EMERALD,
        spaceBefore=0,
        spaceAfter=8,
    )
    return [t_banner, divider]


def build_demographics_card(
    case: ClinicalCase,
    full_timestamp: str,
    styles: PDFStylesheet,
) -> List[Any]:
    """2. Patient Demographics & Intake Modality Grid."""
    demographics_disp = case.demographics_string
    if demographics_disp == "Demographics unspecified":
        if case.patient_age or case.patient_sex:
            demographics_disp = f"{case.patient_age or '—'} yrs | {case.patient_sex or 'Unspecified'}"
        else:
            demographics_disp = "Age & Sex Unspecified"

    scope_disp = case.scope_chapter or "All 37 Repertory Chapters"
    filled_dims = case.filled_dimensions_count
    total_syms = case.total_symptoms_count
    status_disp = case.status.upper() if case.status else "INTAKE"

    meta_grid = [
        [
            Paragraph(f"<b>Patient:</b> {case.patient_name}", styles.body_cell),
            Paragraph(f"<b>Scope:</b> {scope_disp}", styles.body_cell),
            Paragraph(f"<b>Status:</b> <b>{status_disp}</b>", styles.body_cell),
        ],
        [
            Paragraph(f"<b>Demographics:</b> {demographics_disp}", styles.body_cell),
            Paragraph(f"<b>Totality Capture:</b> {filled_dims}/7 Dimensions ({total_syms} Symptoms)", styles.body_cell),
            Paragraph(f"<b>Generated:</b> {full_timestamp or 'Just now'}", styles.body_cell),
        ],
    ]
    t_meta = Table(meta_grid, colWidths=[180, 200, 160])
    t_meta.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    return [t_meta, Spacer(1, 6)]


def build_clinical_summary_box(
    case: ClinicalCase,
    rep_dict: Optional[Dict[str, Any]],
    styles: PDFStylesheet,
) -> List[Any]:
    """Clinical Case Summary (Physician Brief) Card."""
    summary_text = (
        getattr(case, "clinical_summary", "")
        or (rep_dict.get("clinical_summary", "") if rep_dict else "")
        or ""
    ).strip()
    if not summary_text and case.is_ready_for_repertorization:
        from src.pipeline.case_summarizer import CaseSummarizer
        summary_text = CaseSummarizer._generate_extractive_summary(case)

    if not summary_text:
        return []

    summary_box_data = [
        [
            Paragraph("<font color='#065F46'><b>CLINICAL CASE SUMMARY (PHYSICIAN BRIEF)</b></font>", styles.body_bold),
        ],
        [
            Paragraph(
                summary_text,
                ParagraphStyle("SummaryBody", parent=styles.body_cell, fontSize=8, leading=11, textColor=SLATE_TEXT),
            ),
        ],
    ]
    t_summary = Table(summary_box_data, colWidths=[540])
    t_summary.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.7, BORDER_EMERALD),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
            ("TOPPADDING", (0, 1), (-1, 1), 2),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 4),
        ])
    )
    return [t_summary, Spacer(1, 6)]


def build_totality_table(
    case: ClinicalCase,
    styles: PDFStylesheet,
) -> List[Any]:
    """3. Section 1: Kent's 7-Dimension Clinical Totality."""
    elements: List[Any] = [
        Paragraph("1. Kent's 7-Dimension Clinical Totality", styles.section_heading),
        Paragraph(
            "Hierarchical breakdown of intake narrative across Kentian symptom totality dimensions.",
            styles.section_subheading,
        ),
    ]

    labels_map = [
        ("location", "1. Location (LOC)", "Anatomical site and path of symptom radiation"),
        ("sensation", "2. Sensation (SNS)", "Qualitative character of pain or physical sensation"),
        ("modality_agg", "3. Worse from (AGG)", "Aggravating modalities (factors worsening the condition)"),
        ("modality_amel", "4. Better from (AML)", "Ameliorating modalities (factors relieving the condition)"),
        ("concomitant", "5. Concomitants (CNC)", "Co-occurring physiological symptoms accompanying primary state"),
        ("temporal", "6. Time Pattern (TMP)", "Circadian periodicity, time of day/night, aggravation intervals"),
        ("mental", "7. Mental / Emotional (MNT)", "Psychological disposition, emotional state, temperament"),
    ]

    dim_rows = [
        [
            Paragraph("Dimension & Clinical Category", styles.th_style),
            Paragraph("Captured Clinical Symptoms & Expressions", styles.th_style),
        ]
    ]

    for key, lbl, _desc in labels_map:
        vals = case.dimensions.get(key, [])
        if vals:
            val_text = ", ".join(vals)
            val_p = Paragraph(val_text, styles.body_cell)
            dim_lbl_p = Paragraph(f"<b>{lbl}</b>", styles.body_bold)
        else:
            val_p = Paragraph("<i>Not recorded in intake</i>", styles.body_muted_italic)
            dim_lbl_p = Paragraph(f"<font color='#64748B'>{lbl}</font>", styles.body_cell)

        dim_rows.append([dim_lbl_p, val_p])

    t_dims = Table(dim_rows, colWidths=[175, 365])
    t_dims.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_EMERALD),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD_BG]),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
            ("PADDING", (0, 0), (-1, -1), 4.5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    elements.extend([t_dims, Spacer(1, 8)])
    return elements


def build_primary_simillimum_box(
    ranked_remedies: List[Dict[str, Any]],
    total_rubrics_count: int,
    styles: PDFStylesheet,
) -> List[Any]:
    """4. Primary Clinical Simillimum Feature Box (Hero Card)."""
    if not ranked_remedies:
        return []

    top_remedy = ranked_remedies[0]
    top_abbr = top_remedy.get("abbreviation", "—")
    top_name = top_remedy.get("full_name", "")
    top_score = top_remedy.get("score", 0.0)
    top_count = top_remedy.get("rubric_count", 0)
    top_ratio = top_remedy.get("coverage_ratio", 0.0) * 100
    top_margin = top_remedy.get("margin_to_next", 0.0)

    # Compute Kent Grade Profile from covered rubrics if available
    cov_items = top_remedy.get("rubrics_covered", [])
    if cov_items:
        g3 = sum(1 for x in cov_items if x.get("grade") == 3)
        g2 = sum(1 for x in cov_items if x.get("grade") == 2)
        g1 = sum(1 for x in cov_items if x.get("grade") == 1)
        grade_breakdown = f"<b>{g3}</b> Grade 3 (Bold)  *  <b>{g2}</b> Grade 2 (Italic)  *  <b>{g1}</b> Grade 1 (Plain)"
    else:
        grade_breakdown = "Verified Repertory Coverage"

    next_abbr = ranked_remedies[1].get("abbreviation", "") if len(ranked_remedies) > 1 else ""
    lead_str = f"+{top_margin:.2f} score lead over #2 ({next_abbr})" if next_abbr else "Solitary Leading Candidate"

    simillimum_box_data = [
        [
            Paragraph(
                "<font color='#065F46'><b>* PRIMARY CLINICAL SIMILLIMUM CANDIDATE (RANK #1)</b></font>",
                styles.body_bold,
            ),
            Paragraph(
                f"<font color='#065F46'><b>Totality Score: {top_score:.2f}</b></font>",
                ParagraphStyle("ScoreRight", parent=styles.body_bold, alignment=2),
            ),
        ],
        [
            Paragraph(
                f"<font size='13' color='#0F172A'><b>{top_abbr}</b></font>  "
                f"<font size='9.5' color='#334155'><i>({top_name})</i></font>",
                styles.body_cell,
            ),
            Paragraph(
                f"<font size='7.5' color='#059669'><b>{lead_str}</b></font>",
                ParagraphStyle("LeadRight", parent=styles.body_cell, alignment=2),
            ),
        ],
        [
            Paragraph(
                f"<b>Rubric Coverage:</b> {top_count} of {total_rubrics_count} rubrics ({top_ratio:.1f}%)"
                f"&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;<b>Kent Grade Weighting:</b> {grade_breakdown}",
                ParagraphStyle("SimilSub", parent=styles.body_cell, fontSize=7.5, leading=10, textColor=SLATE_TEXT),
            ),
            "",
        ],
    ]

    t_simillimum = Table(simillimum_box_data, colWidths=[380, 160])
    t_simillimum.setStyle(
        TableStyle([
            ("SPAN", (0, 2), (1, 2)),
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_EMERALD),
            ("BOX", (0, 0), (-1, -1), 1.2, BORDER_EMERALD),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
            ("TOPPADDING", (0, 1), (-1, 1), 1),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 3),
            ("TOPPADDING", (0, 2), (-1, 2), 2),
            ("BOTTOMPADDING", (0, 2), (-1, 2), 4),
        ])
    )
    return [KeepTogether(t_simillimum), Spacer(1, 8)]


def build_ranked_remedies_table(
    ranked_remedies: List[Dict[str, Any]],
    total_rubrics_count: int,
    styles: PDFStylesheet,
) -> List[Any]:
    """5. Section 2: Ranked Remedy Candidates (Differential Table)."""
    if not ranked_remedies:
        return []

    elements: List[Any] = [
        Paragraph("2. Ranked Remedy Candidates (Totality Differential)", styles.section_heading),
        Paragraph(
            "Algorithmic synthesis weighted by Kent's 3-grade rubric scores and semantic relevance.",
            styles.section_subheading,
        ),
    ]

    display_rems = ranked_remedies[:8]
    rem_rows = [
        [
            Paragraph("Rank", styles.th_style_center),
            Paragraph("Remedy", styles.th_style),
            Paragraph("Full Botanical / Mineral Name", styles.th_style),
            Paragraph("Kent Grade Profile", styles.th_style_center),
            Paragraph("Score", styles.th_style_center),
            Paragraph("Coverage", styles.th_style_center),
        ]
    ]

    for idx, r in enumerate(display_rems, start=1):
        cov = r.get("rubrics_covered", [])
        if cov:
            g3 = sum(1 for x in cov if x.get("grade") == 3)
            g2 = sum(1 for x in cov if x.get("grade") == 2)
            g1 = sum(1 for x in cov if x.get("grade") == 1)
            grade_str = f"<b>{g3}</b> G3 * {g2} G2 * {g1} G1"
        else:
            grade_str = "—"

        cov_count = r.get("rubric_count", 0)
        cov_pct = (r.get("coverage_ratio", 0.0) * 100) if total_rubrics_count else 0
        cov_str = f"{cov_count}/{total_rubrics_count} ({cov_pct:.0f}%)"

        score_val = r.get("score", 0.0)

        if idx == 1:
            rank_p = Paragraph(f"<font color='#B45309'><b>#{idx}</b></font>", styles.cell_bold_center)
            rem_p = Paragraph(f"<font color='#065F46'><b>{r.get('abbreviation', '')}</b></font>", styles.body_bold)
        else:
            rank_p = Paragraph(f"#{idx}", styles.cell_center)
            rem_p = Paragraph(f"<b>{r.get('abbreviation', '')}</b>", styles.body_cell)

        rem_rows.append([
            rank_p,
            rem_p,
            Paragraph(f"<i>{r.get('full_name', '')}</i>", styles.body_cell),
            Paragraph(grade_str, styles.cell_center),
            Paragraph(f"<b>{score_val:.2f}</b>", styles.cell_bold_center),
            Paragraph(cov_str, styles.cell_center),
        ])

    t_rems = Table(rem_rows, colWidths=[38, 62, 185, 105, 60, 90])
    t_rems.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), SLATE_HEADER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD_BG]),
            ("BACKGROUND", (0, 1), (-1, 1), LIGHT_EMERALD),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    elements.extend([t_rems, Spacer(1, 10)])
    return elements


def build_supporting_rubrics_table(
    active_rubrics: List[Dict[str, Any]],
    styles: PDFStylesheet,
) -> List[Any]:
    """6. Section 3: Supporting Kent Repertory Rubrics."""
    if not active_rubrics:
        return []

    elements: List[Any] = [
        Paragraph("3. Supporting Kent Repertory Rubrics & Clinical Evidence", styles.section_heading),
        Paragraph(
            "Retrieved via neural semantic search against Kent's 74,513 rubrics with cleaned hierarchy paths.",
            styles.section_subheading,
        ),
    ]

    rub_rows = [
        [
            Paragraph("#", styles.th_style_center),
            Paragraph("Kent Repertory Hierarchy Path", styles.th_style),
            Paragraph("Match Relevance", styles.th_style_center),
            Paragraph("Remedies", styles.th_style_center),
        ]
    ]

    display_rubrics = active_rubrics[:12]
    for idx, r in enumerate(display_rubrics, start=1):
        raw_path = r.get("path") or f"Rubric #{r.get('rubric_id')}"
        cleaned_path = clean_rubric_path(raw_path)

        sim_val = r.get("similarity", 0.0)
        if sim_val >= 0.70:
            tier_badge = f"<font color='#065F46'><b>Strong</b> ({sim_val:.2f})</font>"
        elif sim_val >= 0.50:
            tier_badge = f"<font color='#0284C7'>Good ({sim_val:.2f})</font>"
        else:
            tier_badge = f"<font color='#64748B'>Fair ({sim_val:.2f})</font>"

        remedy_ct = r.get("remedy_count", "—")

        rub_rows.append([
            Paragraph(f"<b>R{idx}</b>", styles.cell_bold_center),
            Paragraph(cleaned_path, styles.body_cell),
            Paragraph(tier_badge, styles.cell_center),
            Paragraph(str(remedy_ct), styles.cell_center),
        ])

    t_rubs = Table(rub_rows, colWidths=[32, 353, 85, 70], repeatRows=1)
    t_rubs.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), SLATE_HEADER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD_BG]),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_SUBTLE),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    elements.extend([t_rubs, Spacer(1, 10)])
    return elements


def build_disclaimer_card(styles: PDFStylesheet) -> List[Any]:
    """7. Clinical Research Notice / Legal Disclaimer Box."""
    disclaimer_box_data = [
        [
            Paragraph("<b>Clinical Research Notice & Decision Support Disclaimer</b>", styles.disclaimer_title),
        ],
        [
            Paragraph(
                "Kent-AI is an experimental clinical decision-support system built for registered homeopathic practitioners, "
                "educators, and researchers. Repertorization totals and simillimum rankings are computed algorithmically from "
                "Dr. J. T. Kent's Repertory and semantic embeddings. This report does not formulate a medical diagnosis, prognosis, "
                "or prescription. All remedy recommendations and rubric selections must be critically evaluated against primary "
                "Materia Medica (Hahnemann, Kent, Boericke, Allen) and individualized patient clinical evaluation.",
                styles.disclaimer_text,
            ),
        ],
    ]
    t_disclaimer = Table(disclaimer_box_data, colWidths=[540])
    t_disclaimer.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.6, BORDER_SUBTLE),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
            ("TOPPADDING", (0, 1), (-1, 1), 2),
        ])
    )
    return [KeepTogether(t_disclaimer)]
