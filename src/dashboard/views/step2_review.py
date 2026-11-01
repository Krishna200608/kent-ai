"""Step 2 Clinical Review & 7-Dimension Validation view (Phase 8 & UI Overhaul).

Provides:
- Canonical 7-dimension symptom editing with provenance & confidence indicators.
- Physician Brief / Patient Clinical Case Summary with AI regeneration.
- Accessible symptom removal and inline addition per dimension.
- Kentian repertorization guidance and bottom navigation.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List
import streamlit as st

from src.dashboard.components.icons import get_icon
from src.dashboard.constants import (
    CANONICAL_TO_INTERNAL,
    INTERNAL_TO_CANONICAL,
    get_canonical_dimensions,
)
from src.dashboard.utils import esc
from src.data.case_store import save_case
from src.models.case import ClinicalCase

logger = logging.getLogger("dashboard.views.step2")


def render_step2_review(current_case: ClinicalCase, pipeline: Any) -> None:
    """Render Step 2: Clinical Review & 7-Dimension Validation."""
    active_scope = st.session_state.get("scope", "MIND focus")

    st.html(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            {get_icon('checklist', size=22, color='var(--accent, #10B981)')}
            <span style="font-size: 20px; font-weight: 800; color: var(--text, #E8EDF3);">
                Step 2: Clinical Review & 7-Dimension Validation
            </span>
        </div>
        <div style="font-size: 13px; color: var(--text-muted, #A3B0C2); margin-bottom: 14px;">
            Verify and curate extracted symptoms before repertorization. Adjust details, remove misclassifications, or add observed modalities.
        </div>
        """
    )

    # 1. Kentian Totality Guidance & Completeness
    filled_count = current_case.filled_dimensions_count
    missing_dims: List[str] = []
    if not current_case.dimensions.get("mental"):
        missing_dims.append("Mental & Emotional Generals")
    if not current_case.dimensions.get("modality_agg") and not current_case.dimensions.get("modality_amel"):
        missing_dims.append("Modalities (Aggravation / Amelioration)")

    if missing_dims:
        st.info(
            f"Kentian Totality Guidance: Dr. Kent emphasized that **{' and '.join(missing_dims)}** "
            "carry paramount weight when determining the simillimum. Consider adding them below if observed during clinical evaluation."
        )

    # 2. Patient Clinical Case Summary (Physician Brief)
    case_sum = getattr(current_case, "clinical_summary", "")
    if not case_sum and current_case.is_ready_for_repertorization:
        try:
            from src.pipeline.case_summarizer import CaseSummarizer
            current_case.clinical_summary = CaseSummarizer().generate_summary(current_case)
            save_case(current_case)
            case_sum = current_case.clinical_summary
        except Exception as err:
            logger.info("Summary auto-generation in Step 2: %s", err)

    if case_sum:
        with st.container(border=True):
            col_sum_title, col_sum_acts = st.columns([4, 2], vertical_alignment="center")
            with col_sum_title:
                st.html(
                    f"""
                    <div style="display: flex; align-items: center; gap: 8px;">
                        {get_icon('clinical_notes', size=18, color='var(--accent, #10B981)')}
                        <span style="font-weight: 700; font-size: 14px; color: var(--text, #E8EDF3);">
                            Patient Clinical Case Summary (Physician Brief)
                        </span>
                    </div>
                    """
                )
            with col_sum_acts:
                if st.button("↻ Regenerate with AI", key="btn_regen_summary_step2", help="Regenerate clinical brief using local LLM", width="stretch"):
                    with st.spinner("Synthesizing patient summary..."):
                        from src.pipeline.case_summarizer import CaseSummarizer
                        current_case.clinical_summary = CaseSummarizer().generate_summary(current_case, use_llm=True)
                        save_case(current_case)
                        st.toast("Regenerated clinical summary.")
                        st.rerun()

            st.html(
                f"""
                <div style="background: var(--surface-2, #182330); border: 1px solid var(--line, #243243); border-left: 4px solid var(--accent, #10B981); border-radius: 6px; padding: 12px 14px; font-size: 13.5px; line-height: 1.6; color: var(--text, #E8EDF3); margin: 6px 0 10px 0;">
                    {esc(getattr(current_case, "clinical_summary", ""))}
                </div>
                """
            )
            with st.expander("Edit Clinical Summary (Physician Adjustments)", expanded=False):
                edited_sum = st.text_area(
                    "Adjust case summary for medical records:",
                    value=getattr(current_case, "clinical_summary", ""),
                    height=90,
                    key="ta_edit_sum_step2",
                )
                if st.button("Save Edited Summary", key="btn_save_sum_step2", type="primary"):
                    current_case.clinical_summary = edited_sum.strip()
                    save_case(current_case)
                    st.toast("Clinical summary saved.")
                    st.rerun()

    # 3. Canonical 7-Dimension Grid
    canonical_dims = get_canonical_dimensions(scope=active_scope)
    dim_placeholders: Dict[str, str] = {
        "location": "e.g. forehead, temples, chest, stomach...",
        "sensation": "e.g. throbbing, burning, sharp stabs, dull ache...",
        "modality_agg": "e.g. motion, cold air, evening, after eating...",
        "modality_amel": "e.g. warm wraps, resting, fresh open air...",
        "temporal": "e.g. 3 AM, night, morning on waking, periodic...",
        "concomitant": "e.g. nausea with headache, chills, vertigo...",
        "mental": "e.g. irritable, anxious restlessness, fear of dark...",
    }

    # Render in 4 balanced columns
    cols = st.columns(4)
    for idx, dim in enumerate(canonical_dims):
        target_col = cols[idx % 4]
        internal_k = dim.internal_key
        placeholder_txt = dim_placeholders.get(internal_k, f"e.g. add {dim.label.lower()}...")

        badge_cls = {
            "location": "badge-loc",
            "sensation": "badge-sen",
            "modality_agg": "badge-agg",
            "modality_amel": "badge-amel",
            "temporal": "badge-temp",
            "concomitant": "badge-conc",
            "mental": "badge-ment",
        }.get(internal_k, "badge-ment")

        with target_col:
            with st.container(border=True):
                star_text = ""
                if dim.is_paramount:
                    star_text = " &middot; <span style='color: var(--accent, #10B981); font-weight: 700; font-size: 11px;'>Paramount</span>"
                elif dim.is_recommended:
                    star_text = " &middot; <span style='color: #F59E0B; font-weight: 600; font-size: 11px;'>Recommended</span>"

                st.html(
                    f"""
                    <div style="margin-bottom: 6px;">
                        <span style="font-weight: 700; color: var(--text, #E8EDF3); font-size: 13.5px;">{esc(dim.label)}</span>
                        <code style="font-size: 11px; margin-left: 4px;">({esc(dim.code)})</code>
                        {star_text}
                    </div>
                    """
                )

                items = current_case.dimensions.get(internal_k, [])
                if not items:
                    st.caption("None recorded")
                else:
                    for s_idx, s_val in enumerate(items):
                        c_txt, c_del = st.columns([3.8, 1.2], vertical_alignment="center")
                        with c_txt:
                            st.html(
                                f"""
                                <span class="badge {badge_cls}" style="font-size: 12px; display: inline-block; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="{esc(s_val)}">
                                    {esc(s_val)}
                                </span>
                                """
                            )
                        with c_del:
                            if st.button("Remove", key=f"del_{internal_k}_{s_idx}_{abs(hash(s_val)) % 10000}", help=f"Remove '{s_val}'"):
                                current_case.remove_symptom(internal_k, s_val)
                                save_case(current_case)
                                st.toast(f"Removed symptom from {dim.code}.")
                                st.rerun()

                # Add new symptom input
                new_item = st.text_input(
                    f"+ Add {dim.label}:",
                    key=f"inp_add_{internal_k}",
                    placeholder=placeholder_txt,
                    label_visibility="collapsed",
                )
                if st.button(f"+ Add to {dim.code}", key=f"btn_add_{internal_k}", width="stretch"):
                    if new_item.strip():
                        current_case.add_symptom(internal_k, new_item.strip())
                        save_case(current_case)
                        st.toast(f"Added symptom to {dim.code}.")
                        st.rerun()

    st.markdown("---")
    # 4. Step Navigation Action Bar
    col_back, col_fwd = st.columns([1, 2])
    with col_back:
        if st.button("← Back to Intake", width="stretch"):
            st.session_state.workspace_step = 1
            st.rerun()
    with col_fwd:
        can_repertorize = current_case.is_ready_for_repertorization
        if st.button(
            "Run Repertorization Analysis →",
            type="primary",
            disabled=not can_repertorize,
            width="stretch",
            help="Search Kent's Repertory and compute classical totality ranking",
        ):
            with st.spinner("Searching Kent's Repertory and computing totality scores..."):
                report = pipeline.repertorize_case(current_case)
                st.session_state.current_report = report
                current_case.report_data = report.to_dict()
                save_case(current_case)
                st.session_state.workspace_step = 3
                st.rerun()
        if not can_repertorize:
            st.caption("Add at least one symptom dimension above to enable analysis.")
