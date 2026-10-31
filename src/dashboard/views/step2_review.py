"""Step 2 Clinical Review & 7-Dimension Validation view."""

from __future__ import annotations

import logging
from typing import Any, Dict

import streamlit as st

from src.dashboard.components.icons import get_icon
from src.dashboard.utils import esc
from src.data.case_store import save_case
from src.models.case import ClinicalCase

logger = logging.getLogger("dashboard.views.step2")


def render_step2_review(current_case: ClinicalCase, pipeline: Any) -> None:
    """Render Step 2: Clinical Review & 7-Dimension Validation."""
    st.markdown("#### Step 2: Clinical Review & 7-Dimension Validation")
    st.markdown(
        "<div style='font-size: 13px; color: #9CA3AF; margin-bottom: 14px;'>"
        "Verify symptoms captured during intake before repertorization. Add missing modalities, delete misclassifications, or adjust details."
        "</div>",
        unsafe_allow_html=True,
    )

    # Completeness & Kentian Guidance
    filled_count = current_case.filled_dimensions_count
    missing_dims = []
    if not current_case.dimensions.get("mental"):
        missing_dims.append("Mental & Emotional Generals")
    if not current_case.dimensions.get("modality_agg") and not current_case.dimensions.get("modality_amel"):
        missing_dims.append("Modalities (Worse/Better)")

    if missing_dims:
        st.info(
            f"💡 **Kentian Repertorization Advice**: Dr. Kent emphasized that **{' and '.join(missing_dims)}** "
            "carry paramount weight when finding the simillimum. Consider adding them below if observed."
        )

    # Auto-generate or display Patient Clinical Case Summary (Physician Brief)
    case_sum = getattr(current_case, "clinical_summary", "")
    if not case_sum and current_case.is_ready_for_repertorization:
        try:
            from src.pipeline.case_summarizer import CaseSummarizer
            current_case.clinical_summary = CaseSummarizer().generate_summary(current_case)
            save_case(current_case)
            case_sum = current_case.clinical_summary
        except Exception as e:
            logger.info("Summary auto-generation in Step 2: %s", e)

    if case_sum:
        with st.container(border=True):
            col_sum_title, col_sum_acts = st.columns([4, 2], vertical_alignment="center")
            with col_sum_title:
                st.html(
                    f"""
                    <div style="display: flex; align-items: center; gap: 8px;">
                        {get_icon('clinical_notes', size=18, color='#10B981')}
                        <span style="font-weight: 700; font-size: 14px; color: #F9FAFB;">Patient Clinical Case Summary (Physician Brief)</span>
                    </div>
                    """
                )
            with col_sum_acts:
                if st.button("↻ Regenerate with AI", key="btn_regen_summary_step2", help="Regenerate clinical brief using local LLaMA 3"):
                    with st.spinner("Synthesizing patient summary..."):
                        from src.pipeline.case_summarizer import CaseSummarizer
                        current_case.clinical_summary = CaseSummarizer().generate_summary(current_case, use_llm=True)
                        save_case(current_case)
                        st.rerun()

            st.markdown(
                f"""
                <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 12px 14px; font-size: 13.5px; line-height: 1.55; color: #E2E8F0; margin: 6px 0 10px 0;">
                    {esc(getattr(current_case, "clinical_summary", ""))}
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("Edit Clinical Summary (Physician Adjustments)", expanded=False):
                edited_sum = st.text_area("Adjust case summary for medical records:", value=getattr(current_case, "clinical_summary", ""), height=90, key="ta_edit_sum_step2")
                if st.button("Save Edited Summary", key="btn_save_sum_step2"):
                    current_case.clinical_summary = edited_sum.strip()
                    save_case(current_case)
                    st.toast("Clinical summary saved.", icon="✅")
                    st.rerun()

    # 4 Columns of Cards
    c1, c2, c3, c4 = st.columns(4)

    dim_placeholders: Dict[str, str] = {
        "location": "e.g. forehead, temples, chest, stomach...",
        "sensation": "e.g. throbbing, burning, sharp stabs, dull ache...",
        "modality_agg": "e.g. motion, cold air, evening, after eating...",
        "modality_amel": "e.g. warm wraps, resting, fresh open air...",
        "temporal": "e.g. 3 AM, night, morning on waking, periodic...",
        "concomitant": "e.g. nausea with headache, chills, vertigo...",
        "mental": "e.g. irritable, anxious restlessness, depression...",
    }

    def render_dim_editor(col, dim_key: str, dim_label: str, badge_cls: str, code: str):
        placeholder_txt = dim_placeholders.get(dim_key, f"e.g. add {dim_label.lower()}...")
        with col:
            with st.container(border=True):
                st.markdown(f"**{dim_label}** `({code})`")
                items = current_case.dimensions.get(dim_key, [])
                if not items:
                    st.caption("None recorded")
                else:
                    for idx, item in enumerate(items):
                        c_txt, c_del = st.columns([4, 1])
                        with c_txt:
                            st.markdown(f"<span class='badge {badge_cls}' style='font-size:12px;'>{item}</span>", unsafe_allow_html=True)
                        with c_del:
                            if st.button("✕", key=f"del_{dim_key}_{idx}_{item}", help=f"Remove '{item}'"):
                                current_case.remove_symptom(dim_key, item)
                                save_case(current_case)
                                st.rerun()

                # Add new item input with dimension-tailored placeholder
                new_item = st.text_input(f"+ Add {dim_label}:", key=f"inp_add_{dim_key}", placeholder=placeholder_txt)
                if st.button(f"+ Add to {code}", key=f"btn_add_{dim_key}", width="stretch"):
                    if new_item.strip():
                        current_case.add_symptom(dim_key, new_item.strip())
                        save_case(current_case)
                        st.rerun()

    render_dim_editor(c1, "location", "Location", "badge-loc", "LOC")
    render_dim_editor(c1, "sensation", "Sensation", "badge-sen", "SEN")

    render_dim_editor(c2, "modality_agg", "Worse from (Aggravation)", "badge-agg", "MOD_AGG")
    render_dim_editor(c2, "modality_amel", "Better from (Amelioration)", "badge-amel", "MOD_AMEL")

    render_dim_editor(c3, "temporal", "Time Pattern", "badge-temp", "TEMP")
    render_dim_editor(c3, "concomitant", "Concomitant Symptom", "badge-conc", "CONC")

    render_dim_editor(c4, "mental", "Mental / Emotional", "badge-ment", "MENT")

    st.markdown("---")
    col_back, col_fwd = st.columns([1, 2])
    with col_back:
        if st.button("← Back to Intake", width="stretch"):
            st.session_state.workspace_step = 1
            st.rerun()
    with col_fwd:
        can_repertorize = current_case.is_ready_for_repertorization
        if st.button("Run Repertorization Analysis →", type="primary", disabled=not can_repertorize, width="stretch", help="Search Kent's Repertory and compute classical totality ranking"):
            with st.spinner("Searching Kent's Repertory and computing totality scores..."):
                report = pipeline.repertorize_case(current_case)
                st.session_state.current_report = report
                current_case.report_data = report.to_dict()
                save_case(current_case)
                st.session_state.workspace_step = 3
                st.rerun()
        if not can_repertorize:
            st.caption("Add at least one symptom dimension above to enable analysis.")
