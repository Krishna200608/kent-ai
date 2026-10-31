"""Two-pass ReportLab Canvas for dynamic pagination and running headers/footers."""

from __future__ import annotations

from typing import Any, Dict, List

from reportlab.pdfgen import canvas
from src.dashboard.pdf.styles import (
    BRAND_EMERALD,
    BORDER_SUBTLE,
    GOLD_AMBER,
    SLATE_HEADER,
    SLATE_MUTED,
)


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
            self.setFillColor(BRAND_EMERALD)
            self.drawString(36, 762, "KENT-AI CLINICAL DECISION SUPPORT")

            self.setFont("Helvetica", 7.5)
            self.setFillColor(SLATE_MUTED)
            self.drawString(195, 762, f"|   Case: {self._case_id}   |   Classical Totality Repertorization")

            self.setFont("Helvetica-Bold", 7)
            self.setFillColor(GOLD_AMBER)
            self.drawRightString(576, 762, "CONFIDENTIAL MEDICAL RECORD")

            self.setStrokeColor(BORDER_SUBTLE)
            self.setLineWidth(0.6)
            self.line(36, 755, 576, 755)

        # Running Bottom Footer on all pages
        self.setStrokeColor(BORDER_SUBTLE)
        self.setLineWidth(0.6)
        self.line(36, 32, 576, 32)

        self.setFont("Helvetica", 7)
        self.setFillColor(SLATE_MUTED)
        self.drawString(
            36,
            22,
            "Kent-AI Decision Support System  *  Investigational Medical Tool (Not a Prescriptive Diagnosis)",
        )

        date_disp = f"Generated: {self._date_str}" if self._date_str else "Generated"
        self.drawCentredString(320, 22, date_disp)

        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(SLATE_HEADER)
        self.drawRightString(576, 22, f"Page {self._pageNumber} of {total_pages}")

        self.restoreState()


def make_canvas_factory(case_id: str, date_str: str):
    """Return a canvas factory bound to the active case metadata."""

    def _factory(*args: Any, **kwargs: Any) -> NumberedCanvas:
        return NumberedCanvas(*args, case_id=case_id, date_str=date_str, **kwargs)

    return _factory


_make_canvas_factory = make_canvas_factory
