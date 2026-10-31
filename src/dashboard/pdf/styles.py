"""Color palette constants, typography styles, and sanitization for Kent-AI PDF reports."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

# ---------------------------------------------------------------------------
# Design System & Color Palette (Modern Executive Clinical)
# ---------------------------------------------------------------------------
PRIMARY_DARK = colors.HexColor("#0F172A")    # Deep Midnight Slate (Header / Banners)
BRAND_EMERALD = colors.HexColor("#065F46")   # Rich Kent Emerald (Primary Brand)
ACCENT_EMERALD = colors.HexColor("#059669")  # Vibrant Mint Emerald (Accents, Rules)
LIGHT_EMERALD = colors.HexColor("#ECFDF5")   # Soft Mint Tint (Simillimum Highlight)
BORDER_EMERALD = colors.HexColor("#10B981")  # Active Emerald Border
GOLD_AMBER = colors.HexColor("#B45309")      # Deep Amber / Gold (Badges)
LIGHT_AMBER = colors.HexColor("#FEF3C7")     # Light Amber Pill
SLATE_HEADER = colors.HexColor("#1E293B")    # Table Column Headers
SLATE_TEXT = colors.HexColor("#1F2937")      # Primary Readable Body Text
SLATE_MUTED = colors.HexColor("#64748B")     # Secondary Labels & Meta
CARD_BG = colors.HexColor("#F8FAFC")         # Polished Card Background
CARD_ALT_ROW = colors.HexColor("#F1F5F9")    # Subtle Alternating Row
BORDER_SUBTLE = colors.HexColor("#E2E8F0")   # Crisp Dividing Rules

# Backwards-compatible aliases
_PRIMARY_DARK = PRIMARY_DARK
_BRAND_EMERALD = BRAND_EMERALD
_ACCENT_EMERALD = ACCENT_EMERALD
_LIGHT_EMERALD = LIGHT_EMERALD
_BORDER_EMERALD = BORDER_EMERALD
_GOLD_AMBER = GOLD_AMBER
_LIGHT_AMBER = LIGHT_AMBER
_SLATE_HEADER = SLATE_HEADER
_SLATE_TEXT = SLATE_TEXT
_SLATE_MUTED = SLATE_MUTED
_CARD_BG = CARD_BG
_CARD_ALT_ROW = CARD_ALT_ROW
_BORDER_SUBTLE = BORDER_SUBTLE


def clean_rubric_path(path: str) -> str:
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


_clean_rubric_path = clean_rubric_path


@dataclass(frozen=True)
class PDFStylesheet:
    """Typed container for ReportLab ParagraphStyle instances used across reports."""

    banner_title: ParagraphStyle
    banner_subtitle: ParagraphStyle
    banner_meta: ParagraphStyle
    banner_pill: ParagraphStyle
    section_heading: ParagraphStyle
    section_subheading: ParagraphStyle
    body_cell: ParagraphStyle
    body_bold: ParagraphStyle
    body_muted_italic: ParagraphStyle
    th_style: ParagraphStyle
    th_style_center: ParagraphStyle
    cell_center: ParagraphStyle
    cell_bold_center: ParagraphStyle
    disclaimer_text: ParagraphStyle
    disclaimer_title: ParagraphStyle


def get_pdf_stylesheet() -> PDFStylesheet:
    """Instantiate and return the canonical ReportLab typography hierarchy."""
    styles = getSampleStyleSheet()

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
        textColor=PRIMARY_DARK,
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
        textColor=SLATE_MUTED,
        spaceAfter=5,
        keepWithNext=True,
    )

    body_cell = ParagraphStyle(
        "BodyCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=SLATE_TEXT,
    )
    body_bold = ParagraphStyle(
        "BodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=PRIMARY_DARK,
    )
    body_muted_italic = ParagraphStyle(
        "BodyMutedItalic",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=SLATE_MUTED,
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
        textColor=SLATE_TEXT,
        alignment=1,
    )
    cell_bold_center = ParagraphStyle(
        "CellBoldCenter",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=PRIMARY_DARK,
        alignment=1,
    )

    disclaimer_text = ParagraphStyle(
        "DisclaimerText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9.5,
        textColor=SLATE_MUTED,
    )
    disclaimer_title = ParagraphStyle(
        "DisclaimerTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=PRIMARY_DARK,
    )

    return PDFStylesheet(
        banner_title=banner_title,
        banner_subtitle=banner_subtitle,
        banner_meta=banner_meta,
        banner_pill=banner_pill,
        section_heading=section_heading,
        section_subheading=section_subheading,
        body_cell=body_cell,
        body_bold=body_bold,
        body_muted_italic=body_muted_italic,
        th_style=th_style,
        th_style_center=th_style_center,
        cell_center=cell_center,
        cell_bold_center=cell_bold_center,
        disclaimer_text=disclaimer_text,
        disclaimer_title=disclaimer_title,
    )
