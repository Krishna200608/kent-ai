"""PDF Clinical Report Exporter for Kent-AI.

Generates professional, printable clinical consultation summaries using ReportLab.
Adheres to Dr. J. T. Kent's classical repertorization methodology and modern
publication-grade clinical document design.
"""

from __future__ import annotations

import io
import re
from typing import Any, Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.models.case import ClinicalCase
from src.pipeline.orchestrator import PatientReport

# ---------------------------------------------------------------------------
# Design System & Color Palette (Modern Executive Clinical)
# ---------------------------------------------------------------------------
_PRIMARY_DARK = colors.HexColor("#0F172A")    # Deep Midnight Slate (Header / Banners)
_BRAND_EMERALD = colors.HexColor("#065F46")   # Rich Kent Emerald (Primary Brand)
_ACCENT_EMERALD = colors.HexColor("#059669")  # Vibrant Mint Emerald (Accents, Rules)
_LIGHT_EMERALD = colors.HexColor("#ECFDF5")   # Soft Mint Tint (Simillimum Highlight)
_BORDER_EMERALD = colors.HexColor("#10B981")  # Active Emerald Border
_GOLD_AMBER = colors.HexColor("#B45309")      # Deep Amber / Gold (Badges)
_LIGHT_AMBER = colors.HexColor("#FEF3C7")     # Light Amber Pill
_SLATE_HEADER = colors.HexColor("#1E293B")    # Table Column Headers
_SLATE_TEXT = colors.HexColor("#1F2937")      # Primary Readable Body Text
_SLATE_MUTED = colors.HexColor("#64748B")     # Secondary Labels & Meta
_CARD_BG = colors.HexColor("#F8FAFC")         # Polished Card Background
_CARD_ALT_ROW = colors.HexColor("#F1F5F9")    # Subtle Alternating Row
_BORDER_SUBTLE = colors.HexColor("#E2E8F0")   # Crisp Dividing Rules


def _clean_rubric_path(path: str) -> str:
    """Sanitize raw Kent repertory paths, stripping OCR artifacts and citations.

    Examples cleaned:
    - 'MIND > DELUSIONS, dead, corpse; som © 5 > head belongs...' -> 'MIND > DELUSIONS, dead, corpse > head belongs...'
    - 'MIND > RESTLESSNESS, nervousness > beadache, during...' -> '... > headache, during...'
    - Non-ASCII or corrupted unicode safely transliterated for standard Helvetica.
    """
    if not path:
        return ""

    p = path.replace("\ufffd", "").replace("©", "(c)")
    # Strip OCR citations e.g. '; som © 5', '; som 5', 'som (c) 5'
    p = re.sub(r";\s*som\s*\(?c\)?\s*\d+", "", p, flags=re.IGNORECASE)
    p = re.sub(r"\bsom\s*\(?c\)?\s*\d+\b", "", p, flags=re.IGNORECASE)
    p = re.sub(r"\bbeadache\b", "headache", p, flags=re.IGNORECASE)

    # Normalize semicolons and double spaces
    p = re.sub(r"\s*;\s*", ", ", p)
    p = re.sub(r"\s{2,}", " ", p)

    # Clean up orphan commas before hierarchy chevron
    p = re.sub(r",\s*>", " >", p)

    # Convert common unicode typography to ASCII safe characters
    replacements = {
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "*",
        "…": "...",
        "®": "(R)",
        "™": "(TM)",
    }
    for orig, rep in replacements.items():
        p = p.replace(orig, rep)

    # Final ASCII safety strip for Helvetica
    p = p.encode("ascii", errors="replace").decode("ascii").replace("?", "")
    return p.strip(" ,;")


class NumberedCanvas(canvas.Canvas):
    """Two-pass ReportLab Canvas that computes total page count dynamically.

    Draws running clinical header banners on Page 2+ and confidentiality footers
    with 'Page X of Y' across all pages.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Dict[str, Any]] = []
        self._case_id = kwargs.pop("case_id", "CASE-RECORD")
        self._date_str = kwargs.pop("date_str", "")

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def _draw_page_decorations(self, total_pages: int) -> None:
        self.saveState()

        # Running Top Header on Page 2+
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(_BRAND_EMERALD)
            self.drawString(36, 762, "KENT-AI CLINICAL DECISION SUPPORT")

            self.setFont("Helvetica", 7.5)
            self.setFillColor(_SLATE_MUTED)
            self.drawString(195, 762, f"|   Case: {self._case_id}   |   Classical Totality Repertorization")

            self.setFont("Helvetica-Bold", 7)
            self.setFillColor(_GOLD_AMBER)
            self.drawRightString(576, 762, "CONFIDENTIAL MEDICAL RECORD")

            self.setStrokeColor(_BORDER_SUBTLE)
            self.setLineWidth(0.6)
            self.line(36, 755, 576, 755)

        # Running Bottom Footer on all pages
        self.setStrokeColor(_BORDER_SUBTLE)
        self.setLineWidth(0.6)
        self.line(36, 32, 576, 32)

        self.setFont("Helvetica", 7)
        self.setFillColor(_SLATE_MUTED)
        self.drawString(
            36,
            22,
            "Kent-AI Decision Support System  *  Investigational Medical Tool (Not a Prescriptive Diagnosis)",
        )

        date_disp = f"Generated: {self._date_str}" if self._date_str else "Generated"
        self.drawCentredString(320, 22, date_disp)

        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(_SLATE_HEADER)
        self.drawRightString(576, 22, f"Page {self._pageNumber} of {total_pages}")

        self.restoreState()


def _make_canvas_factory(case_id: str, date_str: str):
    """Return a canvas factory bound to the active case metadata."""

    def _factory(*args: Any, **kwargs: Any) -> NumberedCanvas:
        return NumberedCanvas(*args, case_id=case_id, date_str=date_str, **kwargs)

    return _factory


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

    styles = getSampleStyleSheet()

    # Base typography styles
    banner_title = ParagraphStyle(
        "BannerTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.white,
    )
    banner_subtitle = ParagraphStyle(
        "BannerSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#A7F3D0"),
    )
    banner_meta = ParagraphStyle(
        "BannerMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#E2E8F0"),
        alignment=2,  # Right-aligned
    )
    banner_pill = ParagraphStyle(
        "BannerPill",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#FCD34D"),
        alignment=2,
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=_PRIMARY_DARK,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True,
    )
    section_subheading = ParagraphStyle(
        "SectionSubheading",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=_SLATE_MUTED,
        spaceAfter=5,
        keepWithNext=True,
    )

    body_cell = ParagraphStyle(
        "BodyCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=_SLATE_TEXT,
    )
    body_bold = ParagraphStyle(
        "BodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=_PRIMARY_DARK,
    )
    body_muted_italic = ParagraphStyle(
        "BodyMutedItalic",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=_SLATE_MUTED,
    )

    th_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.white,
    )
    th_style_center = ParagraphStyle(
        "TableHeaderCenter",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.white,
        alignment=1,
    )

    cell_center = ParagraphStyle(
        "CellCenter",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=_SLATE_TEXT,
        alignment=1,
    )
    cell_bold_center = ParagraphStyle(
        "CellBoldCenter",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=_PRIMARY_DARK,
        alignment=1,
    )

    disclaimer_text = ParagraphStyle(
        "DisclaimerText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9.5,
        textColor=_SLATE_MUTED,
    )
    disclaimer_title = ParagraphStyle(
        "DisclaimerTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=_PRIMARY_DARK,
    )

    story: List[Any] = []

    # -----------------------------------------------------------------------
    # 1. Executive Title Hero Banner (Page 1)
    # -----------------------------------------------------------------------
    date_display = (case.updated_at[:10] if case.updated_at else "")
    time_display = (case.updated_at[11:16] if len(case.updated_at or "") >= 16 else "")
    full_timestamp = f"{date_display} {time_display}".strip()

    banner_data = [
        [
            Paragraph(
                "<b>KENT-AI CLINICAL DECISION SUPPORT</b>",
                banner_title,
            ),
            Paragraph("CONFIDENTIAL MEDICAL REPORT", banner_pill),
        ],
        [
            Paragraph(
                "Classical Homeopathic Totality Repertorization Summary  *  Dr. J. T. Kent Framework",
                banner_subtitle,
            ),
            Paragraph(
                f"<b>Case ID:</b> {case.case_id}<br/><b>Date:</b> {date_display or 'Current'}",
                banner_meta,
            ),
        ],
    ]
    t_banner = Table(banner_data, colWidths=[360, 180])
    t_banner.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _PRIMARY_DARK),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
            ("TOPPADDING", (0, 1), (-1, 1), 2),
        ])
    )
    story.append(t_banner)
    story.append(
        HRFlowable(
            width="100%",
            thickness=2.5,
            color=_ACCENT_EMERALD,
            spaceBefore=0,
            spaceAfter=8,
        )
    )

    # -----------------------------------------------------------------------
    # 2. Patient Demographics & Intake Modality Grid
    # -----------------------------------------------------------------------
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
            Paragraph(f"<b>Patient:</b> {case.patient_name}", body_cell),
            Paragraph(f"<b>Scope:</b> {scope_disp}", body_cell),
            Paragraph(f"<b>Status:</b> <b>{status_disp}</b>", body_cell),
        ],
        [
            Paragraph(f"<b>Demographics:</b> {demographics_disp}", body_cell),
            Paragraph(f"<b>Totality Capture:</b> {filled_dims}/7 Dimensions ({total_syms} Symptoms)", body_cell),
            Paragraph(f"<b>Generated:</b> {full_timestamp or 'Just now'}", body_cell),
        ],
    ]
    t_meta = Table(meta_grid, colWidths=[180, 200, 160])
    t_meta.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, _BORDER_SUBTLE),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, _BORDER_SUBTLE),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    story.append(t_meta)
    story.append(Spacer(1, 6))

    # Retrieve repertorization data
    rep_dict: Optional[Dict[str, Any]] = None
    if report is not None:
        rep_dict = report.to_dict()
    elif case.report_data:
        rep_dict = case.report_data

    # -----------------------------------------------------------------------
    # Clinical Case Summary (Physician Brief) Card
    # -----------------------------------------------------------------------
    summary_text = (
        case.clinical_summary
        or (rep_dict.get("clinical_summary", "") if rep_dict else "")
        or ""
    ).strip()
    if not summary_text and case.is_ready_for_repertorization:
        from src.pipeline.case_summarizer import CaseSummarizer
        summary_text = CaseSummarizer._generate_extractive_summary(case)

    if summary_text:
        summary_box_data = [
            [
                Paragraph("<font color='#065F46'><b>CLINICAL CASE SUMMARY (PHYSICIAN BRIEF)</b></font>", body_bold),
            ],
            [
                Paragraph(
                    summary_text,
                    ParagraphStyle("SummaryBody", parent=body_cell, fontSize=8, leading=11, textColor=_SLATE_TEXT),
                ),
            ],
        ]
        t_summary = Table(summary_box_data, colWidths=[540])
        t_summary.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), _CARD_BG),
                ("BOX", (0, 0), (-1, -1), 0.7, _BORDER_EMERALD),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                ("TOPPADDING", (0, 1), (-1, 1), 2),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 4),
            ])
        )
        story.append(t_summary)
        story.append(Spacer(1, 6))

    # -----------------------------------------------------------------------
    # 3. Section 1: Kent's 7-Dimension Clinical Totality
    # -----------------------------------------------------------------------
    story.append(
        Paragraph("1. Kent's 7-Dimension Clinical Totality", section_heading)
    )
    story.append(
        Paragraph(
            "Hierarchical breakdown of intake narrative across Kentian symptom totality dimensions.",
            section_subheading,
        )
    )

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
            Paragraph("Dimension & Clinical Category", th_style),
            Paragraph("Captured Clinical Symptoms & Expressions", th_style),
        ]
    ]

    for key, lbl, desc in labels_map:
        vals = case.dimensions.get(key, [])
        if vals:
            val_text = ", ".join(vals)
            val_p = Paragraph(val_text, body_cell)
            dim_lbl_p = Paragraph(f"<b>{lbl}</b>", body_bold)
        else:
            val_p = Paragraph("<i>Not recorded in intake</i>", body_muted_italic)
            dim_lbl_p = Paragraph(f"<font color='#64748B'>{lbl}</font>", body_cell)

        dim_rows.append([dim_lbl_p, val_p])

    t_dims = Table(dim_rows, colWidths=[175, 365])
    t_dims.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _BRAND_EMERALD),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _CARD_BG]),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDER_SUBTLE),
            ("PADDING", (0, 0), (-1, -1), 4.5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    story.append(t_dims)
    story.append(Spacer(1, 8))

    # Retrieve repertorization data
    rep_dict: Optional[Dict[str, Any]] = None
    if report is not None:
        rep_dict = report.to_dict()
    elif case.report_data:
        rep_dict = case.report_data

    ranked_remedies = rep_dict.get("ranked_remedies", []) if rep_dict else []
    active_rubrics = [r for r in rep_dict.get("matched_rubrics", []) if not r.get("muted")] if rep_dict else []
    total_rubrics_count = len(active_rubrics)

    # -----------------------------------------------------------------------
    # 4. Primary Clinical Simillimum Feature Box (Hero Card)
    # -----------------------------------------------------------------------
    if ranked_remedies:
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
                    body_bold,
                ),
                Paragraph(
                    f"<font color='#065F46'><b>Totality Score: {top_score:.2f}</b></font>",
                    ParagraphStyle("ScoreRight", parent=body_bold, alignment=2),
                ),
            ],
            [
                Paragraph(
                    f"<font size='13' color='#0F172A'><b>{top_abbr}</b></font>  "
                    f"<font size='9.5' color='#334155'><i>({top_name})</i></font>",
                    body_cell,
                ),
                Paragraph(
                    f"<font size='7.5' color='#059669'><b>{lead_str}</b></font>",
                    ParagraphStyle("LeadRight", parent=body_cell, alignment=2),
                ),
            ],
            [
                Paragraph(
                    f"<b>Rubric Coverage:</b> {top_count} of {total_rubrics_count} rubrics ({top_ratio:.1f}%)"
                    f"&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;<b>Kent Grade Weighting:</b> {grade_breakdown}",
                    ParagraphStyle("SimilSub", parent=body_cell, fontSize=7.5, leading=10, textColor=_SLATE_TEXT),
                ),
                "",
            ],
        ]

        t_simillimum = Table(simillimum_box_data, colWidths=[380, 160])
        t_simillimum.setStyle(
            TableStyle([
                ("SPAN", (0, 2), (1, 2)),  # Span metric row across full card width
                ("BACKGROUND", (0, 0), (-1, -1), _LIGHT_EMERALD),
                ("BOX", (0, 0), (-1, -1), 1.2, _BORDER_EMERALD),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                ("TOPPADDING", (0, 1), (-1, 1), 1),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 3),
                ("TOPPADDING", (0, 2), (-1, 2), 2),
                ("BOTTOMPADDING", (0, 2), (-1, 2), 4),
            ])
        )
        story.append(KeepTogether(t_simillimum))
        story.append(Spacer(1, 8))

    # -----------------------------------------------------------------------
    # 5. Section 2: Ranked Remedy Candidates (Differential Table)
    # -----------------------------------------------------------------------
    if ranked_remedies:
        story.append(
            Paragraph("2. Ranked Remedy Candidates (Totality Differential)", section_heading)
        )
        story.append(
            Paragraph(
                "Algorithmic synthesis weighted by Kent's 3-grade rubric scores and semantic relevance.",
                section_subheading,
            )
        )

        display_rems = ranked_remedies[:8]
        rem_rows = [
            [
                Paragraph("Rank", th_style_center),
                Paragraph("Remedy", th_style),
                Paragraph("Full Botanical / Mineral Name", th_style),
                Paragraph("Kent Grade Profile", th_style_center),
                Paragraph("Score", th_style_center),
                Paragraph("Coverage", th_style_center),
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

            # Highlight Rank #1 with amber/gold styling
            if idx == 1:
                rank_p = Paragraph(f"<font color='#B45309'><b>#{idx}</b></font>", cell_bold_center)
                rem_p = Paragraph(f"<font color='#065F46'><b>{r.get('abbreviation', '')}</b></font>", body_bold)
            else:
                rank_p = Paragraph(f"#{idx}", cell_center)
                rem_p = Paragraph(f"<b>{r.get('abbreviation', '')}</b>", body_cell)

            rem_rows.append([
                rank_p,
                rem_p,
                Paragraph(f"<i>{r.get('full_name', '')}</i>", body_cell),
                Paragraph(grade_str, cell_center),
                Paragraph(f"<b>{score_val:.2f}</b>", cell_bold_center),
                Paragraph(cov_str, cell_center),
            ])

        t_rems = Table(rem_rows, colWidths=[38, 62, 185, 105, 60, 90])
        t_rems.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), _SLATE_HEADER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _CARD_BG]),
                # Special soft highlight on row 1 (simillimum)
                ("BACKGROUND", (0, 1), (-1, 1), _LIGHT_EMERALD),
                ("GRID", (0, 0), (-1, -1), 0.5, _BORDER_SUBTLE),
                ("PADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        story.append(t_rems)
        story.append(Spacer(1, 10))

    # -----------------------------------------------------------------------
    # 6. Section 3: Supporting Kent Repertory Rubrics
    # -----------------------------------------------------------------------
    if active_rubrics:
        story.append(
            Paragraph("3. Supporting Kent Repertory Rubrics & Clinical Evidence", section_heading)
        )
        story.append(
            Paragraph(
                "Retrieved via neural semantic search against Kent's 74,513 rubrics with cleaned hierarchy paths.",
                section_subheading,
            )
        )

        rub_rows = [
            [
                Paragraph("#", th_style_center),
                Paragraph("Kent Repertory Hierarchy Path", th_style),
                Paragraph("Match Relevance", th_style_center),
                Paragraph("Remedies", th_style_center),
            ]
        ]

        display_rubrics = active_rubrics[:12]
        for idx, r in enumerate(display_rubrics, start=1):
            raw_path = r.get("path") or f"Rubric #{r.get('rubric_id')}"
            cleaned_path = _clean_rubric_path(raw_path)

            sim_val = r.get("similarity", 0.0)
            if sim_val >= 0.70:
                tier_badge = f"<font color='#065F46'><b>Strong</b> ({sim_val:.2f})</font>"
            elif sim_val >= 0.50:
                tier_badge = f"<font color='#0284C7'>Good ({sim_val:.2f})</font>"
            else:
                tier_badge = f"<font color='#64748B'>Fair ({sim_val:.2f})</font>"

            remedy_ct = r.get("remedy_count", "—")

            rub_rows.append([
                Paragraph(f"<b>R{idx}</b>", cell_bold_center),
                Paragraph(cleaned_path, body_cell),
                Paragraph(tier_badge, cell_center),
                Paragraph(str(remedy_ct), cell_center),
            ])

        t_rubs = Table(rub_rows, colWidths=[32, 353, 85, 70], repeatRows=1)
        t_rubs.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), _SLATE_HEADER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _CARD_BG]),
                ("GRID", (0, 0), (-1, -1), 0.5, _BORDER_SUBTLE),
                ("PADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        story.append(t_rubs)
        story.append(Spacer(1, 10))

    # -----------------------------------------------------------------------
    # 7. Clinical Research Notice / Legal Disclaimer Box
    # -----------------------------------------------------------------------
    disclaimer_box_data = [
        [
            Paragraph("<b>Clinical Research Notice & Decision Support Disclaimer</b>", disclaimer_title),
        ],
        [
            Paragraph(
                "Kent-AI is an experimental clinical decision-support system built for registered homeopathic practitioners, "
                "educators, and researchers. Repertorization totals and simillimum rankings are computed algorithmically from "
                "Dr. J. T. Kent's Repertory and semantic embeddings. This report does not formulate a medical diagnosis, prognosis, "
                "or prescription. All remedy recommendations and rubric selections must be critically evaluated against primary "
                "Materia Medica (Hahnemann, Kent, Boericke, Allen) and individualized patient clinical evaluation.",
                disclaimer_text,
            ),
        ],
    ]
    t_disclaimer = Table(disclaimer_box_data, colWidths=[540])
    t_disclaimer.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.6, _BORDER_SUBTLE),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
            ("TOPPADDING", (0, 1), (-1, 1), 2),
        ])
    )
    story.append(KeepTogether(t_disclaimer))

    # Build document using dynamic NumberedCanvas factory
    canvas_factory = _make_canvas_factory(
        case_id=case.case_id or "CASE-RECORD",
        date_str=full_timestamp or date_display,
    )
    doc.build(story, canvasmaker=canvas_factory)

    return buffer.getvalue()
