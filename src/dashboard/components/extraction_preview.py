"""Two-column interactive extraction preview with highlighted spans and clinical chips."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional
import streamlit as st

from src.dashboard.components.icons import get_icon
from src.dashboard.dimensions import KENT_DIMENSIONS_ORDERED
from src.dashboard.utils import esc, safe_rerun_fragment
from src.pipeline.narrative import missing_recommended_dimensions

if TYPE_CHECKING:
    from src.chatbot.dialogue_manager import DialogueManager
    from src.models.case import ClinicalCase


def build_highlighted_narrative_html(text: str, spans: List[Dict[str, Any]]) -> str:
    """Build safe HTML of narrative text with non-overlapping <mark> tags per dimension.

    Guarantees:
    - HTML is escaped (raw script/tags stay inert).
    - Offsets clamped to [0, len(text)].
    - Overlapping spans resolved deterministically.
    - If offsets missing or None, plain escaped text is returned.

    Args:
        text: Clinical narrative raw text.
        spans: List of dicts with 'start', 'end', and 'code' or 'label'.

    Returns:
        Safe HTML string ready to render.
    """
    if not text:
        return ""

    valid_spans: List[Dict[str, Any]] = []
    text_len = len(text)
    for sp in spans:
        s = sp.get("start")
        e = sp.get("end")
        if s is not None and e is not None:
            try:
                s_int = int(s)
                e_int = int(e)
                clamped_s = max(0, min(s_int, text_len))
                clamped_e = max(clamped_s, min(e_int, text_len))
                if clamped_e > clamped_s:
                    valid_spans.append({
                        "start": clamped_s,
                        "end": clamped_e,
                        "code": str(sp.get("code") or sp.get("label") or "DIM").upper(),
                    })
            except (ValueError, TypeError):
                continue

    if not valid_spans:
        return f"<div style='white-space: pre-wrap; line-height: 1.6; color: #E5E7EB; font-size: 13.5px;'>{esc(text)}</div>"

    # Sort spans by start asc, end desc
    valid_spans.sort(key=lambda x: (x["start"], -x["end"]))

    # Resolve overlaps greedily (first span wins)
    non_overlapping: List[Dict[str, Any]] = []
    cur_end = 0
    for sp in valid_spans:
        if sp["start"] >= cur_end:
            non_overlapping.append(sp)
            cur_end = sp["end"]

    parts: List[str] = []
    last_idx = 0
    for sp in non_overlapping:
        s = sp["start"]
        e = sp["end"]
        if s > last_idx:
            parts.append(esc(text[last_idx:s]))
        code = esc(sp["code"])
        cls_code = f"mark-{code.lower()}"
        span_content = esc(text[s:e])
        parts.append(
            f'<mark class="dim-mark {cls_code}">{span_content}'
            f'<span class="mark-tag">{code}</span></mark>'
        )
        last_idx = e

    if last_idx < text_len:
        parts.append(esc(text[last_idx:]))

    return f"<div class='highlighted-narrative-container' style='white-space: pre-wrap; line-height: 1.8; color: #F3F4F6; font-size: 13.5px;'>{''.join(parts)}</div>"


def render_extraction_preview(case: ClinicalCase, dm: DialogueManager) -> None:
    """Render two-column extraction preview: highlighted narrative and extracted chips."""
    meta = getattr(case, "extraction_meta", {}) or {}
    items_by_dim = meta.get("items", {})

    # Collect spans for left column
    all_spans: List[Dict[str, Any]] = []
    for dim in KENT_DIMENSIONS_ORDERED:
        for it in items_by_dim.get(dim.key, []):
            if it.get("start") is not None and it.get("end") is not None:
                all_spans.append({
                    "start": it["start"],
                    "end": it["end"],
                    "code": dim.code,
                })

    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        with st.container(border=True):
            st.html(
                f"""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-size: 14px; font-weight: 700; color: #F9FAFB; display: flex; align-items: center; gap: 6px;">
                        {get_icon('auto_awesome', size=16, color='#10B981')} Annotated Narrative
                    </span>
                    <span style="font-size: 11px; color: #9CA3AF;">{len(all_spans)} extracted spans</span>
                </div>
                """
            )
            narrative_html = build_highlighted_narrative_html(case.transcript, all_spans)
            st.html(narrative_html)

    with col_right:
        with st.container(border=True):
            st.html(
                f"""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-size: 14px; font-weight: 700; color: #F9FAFB; display: flex; align-items: center; gap: 6px;">
                        {get_icon('hub', size=16, color='#10B981')} Extracted 7 Dimensions
                    </span>
                    <span style="font-size: 11px; color: #34D399; font-weight: 600;">{case.filled_dimensions_count}/7 Captured</span>
                </div>
                """
            )

            # Build confidence lookup
            conf_map: Dict[str, float] = {}
            for d_key, it_list in items_by_dim.items():
                for it in it_list:
                    if "text" in it and "confidence" in it and it["confidence"] is not None:
                        conf_map[it["text"].strip().lower()] = float(it["confidence"])

            has_any = False
            for dim in KENT_DIMENSIONS_ORDERED:
                vals = case.dimensions.get(dim.key, [])
                if vals:
                    has_any = True
                    chips_html = []
                    for v in vals:
                        c_val = conf_map.get(v.strip().lower(), 1.0)
                        check_badge = (
                            '<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #FBBF24; font-size: 10px; margin-left: 4px; padding: 1px 4px;">Check</span>'
                            if c_val < 0.5
                            else ""
                        )
                        chips_html.append(
                            f'<span class="badge {dim.badge_class}" style="font-size: 11.5px; padding: 2px 7px; margin-right: 4px; margin-bottom: 4px; display: inline-block;">'
                            f'{esc(v)}{check_badge}</span>'
                        )
                    st.html(
                        f"""
                        <div style="margin-bottom: 8px;">
                            <div style="font-size: 11.5px; font-weight: 700; color: #9CA3AF; margin-bottom: 2px;">{esc(dim.label)}</div>
                            <div>{''.join(chips_html)}</div>
                        </div>
                        """
                    )

            if not has_any:
                st.caption("No symptom dimensions captured.")

            # Negated findings
            negated = meta.get("negated", [])
            if negated:
                neg_chips = "".join(
                    f'<span class="badge badge-neg" style="font-size: 11.5px; padding: 2px 7px; margin-right: 4px; margin-bottom: 4px; display: inline-block;">'
                    f'{get_icon("block", size=11, color="#F87171")} {esc(n)}</span>'
                    for n in negated
                )
                st.html(
                    f"""
                    <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255, 255, 255, 0.08);">
                        <div style="font-size: 11.5px; font-weight: 700; color: #F87171; margin-bottom: 4px;">Denied (Negated Findings)</div>
                        <div>{neg_chips}</div>
                    </div>
                    """
                )

    # Missing recommended dimensions check
    missing_rec = missing_recommended_dimensions(case)
    if missing_rec:
        rec_str = ", ".join(missing_rec)
        st.warning(
            f"Not yet captured: **{rec_str}**. These strongly shape the homeopathic repertorization.",
            icon="⚠️",
        )
        col_m1, col_m2 = st.columns([1, 1])
        with col_m1:
            if st.button("Fill gaps with dialogue", type="secondary", width="stretch", key="btn_fill_gaps_dialogue"):
                dm.load_from_case(case)
                st.session_state.intake_mode_select = "Guided conversation"
                st.session_state.paste_preview = None
                st.rerun(scope="app")
        with col_m2:
            if st.button("Continue anyway →", type="primary", width="stretch", key="btn_continue_anyway"):
                st.session_state.workspace_step = 2
                st.rerun(scope="app")
    else:
        # Standard buttons
        col_act1, col_act2 = st.columns([1, 1])
        with col_act1:
            if st.button("Edit text", type="secondary", width="stretch", key="btn_edit_paste_text"):
                st.session_state.paste_preview = None
                safe_rerun_fragment()
        with col_act2:
            if st.button("Continue to Review →", type="primary", width="stretch", key="btn_continue_to_review"):
                st.session_state.workspace_step = 2
                st.rerun(scope="app")
