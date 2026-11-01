"""Clinical narrative guidance rail and totality completeness checklist."""

from __future__ import annotations

from typing import TYPE_CHECKING
import streamlit as st

from src.dashboard.components.icons import get_icon
from src.dashboard.utils import esc

if TYPE_CHECKING:
    from src.models.case import ClinicalCase


def render_intake_guide_rail(case: ClinicalCase) -> None:
    """Render the right guidance rail with a 6-item completeness checklist and local privacy notice.

    Args:
        case: Current active ClinicalCase.
    """
    with st.container(border=True):
        st.html(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                {get_icon('clinical_notes', size=18, color='#10B981')}
                <span style="font-size: 15px; font-weight: 700; color: #F9FAFB;">What to Include</span>
            </div>
            """
        )
        st.markdown(
            "<div style='font-size: 12.5px; color: #9CA3AF; margin-bottom: 12px; line-height: 1.4;'>"
            "A complete homeopathic totality covers these key clinical elements. "
            "Kent-AI automatically maps them to Kent's 7 Dimensions:"
            "</div>",
            unsafe_allow_html=True,
        )

        dims = case.dimensions or {}
        items = [
            (
                "Location",
                "Where in the body (e.g. forehead, right knee, pit of stomach)",
                bool(dims.get("location")),
            ),
            (
                "Sensation",
                "What it feels like (e.g. throbbing, burning, stitching, dull ache)",
                bool(dims.get("sensation")),
            ),
            (
                "Worse From",
                "Aggravations and triggers (e.g. cold air, bright light, motion)",
                bool(dims.get("modality_agg")),
            ),
            (
                "Better From",
                "Ameliorations and soothing factors (e.g. warmth, quiet rest, open air)",
                bool(dims.get("modality_amel")),
            ),
            (
                "Time Pattern",
                "Times of day or periodicity (e.g. 3 AM, morning on waking, evening)",
                bool(dims.get("temporal")),
            ),
            (
                "Concomitants & Mood",
                "Co-occurring symptoms and emotional state (e.g. nausea, anxiety, restlessness)",
                bool(dims.get("concomitant") or dims.get("mental")),
            ),
        ]

        for label, desc, is_captured in items:
            status_text = "Captured" if is_captured else "Not captured"
            status_color = "#34D399" if is_captured else "#8492A6"
            icon_name = "check_circle" if is_captured else "radio_button_unchecked"
            border_style = "border-left: 3px solid #10B981;" if is_captured else "border-left: 3px solid rgba(255, 255, 255, 0.1);"

            st.html(
                f"""
                <div style="background: rgba(255, 255, 255, 0.03); {border_style} padding: 8px 10px; border-radius: 4px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                        <span style="font-size: 13px; font-weight: 600; color: #F3F4F6;">{esc(label)}</span>
                        <span style="font-size: 11px; font-weight: 700; color: {status_color}; display: inline-flex; align-items: center; gap: 4px;">
                            {get_icon(icon_name, size=13, color=status_color)} {esc(status_text)}
                        </span>
                    </div>
                    <div style="font-size: 11.5px; color: #9CA3AF; line-height: 1.3;">{esc(desc)}</div>
                </div>
                """
            )

        st.markdown(
            "<div style='margin-top: 16px; padding-top: 10px; border-top: 1px solid rgba(255, 255, 255, 0.08); font-size: 11.5px; color: #8492A6;'>"
            "🛡️ Case data is stored locally on this device."
            "</div>",
            unsafe_allow_html=True,
        )

