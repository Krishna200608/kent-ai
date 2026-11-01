"""Methodology & Classical Homeopathic Foundations View (Phase 7 & UI Overhaul).

Displays:
- Dr. J. T. Kent's Totality Principles and hierarchical symptom evaluation.
- Grade weights and totality scoring formula derived from constants.
- 7 totality dimensions and clinical scope definitions.
- Evaluation benchmarks with plain-language explanations.
- Full investigational clinical research notice (§3).
"""

from __future__ import annotations

import streamlit as st

from src.dashboard.components.icons import get_icon
from src.dashboard.constants import (
    EVALUATION_METRICS,
    GRADE_WEIGHTS,
    MODEL_DISPLAY_NAME,
    SCOPE_ALL_COUNT,
    SCOPE_MIND_COUNT,
    get_canonical_dimensions,
)


def render_methodology_view() -> None:
    """Render Tab 5: Classical Methodology & Clinical Decision-Support Foundations."""
    st.html(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            {get_icon('psychology', size=24, color='var(--accent, #10B981)')}
            <span style="font-size: 22px; font-weight: 800; color: var(--text, #E8EDF3);">
                Methodology & Totality Principles
            </span>
        </div>
        <div style="font-size: 13.5px; color: var(--text-muted, #A3B0C2); margin-bottom: 16px;">
            Classical homeopathic repertorization grounded in Dr. James Tyler Kent's framework, synthesized with biomedical NLP.
        </div>
        """
    )

    c_left, c_right = st.columns(2)

    # 1. Classical Totality Principles
    with c_left:
        with st.container(border=True):
            st.html(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    {get_icon('scale', size=20, color='var(--accent, #10B981)')}
                    <h4 style="margin: 0; color: var(--text, #E8EDF3); font-size: 16px;">1. Dr. J. T. Kent's Totality Principles</h4>
                </div>
                """
            )
            w3 = GRADE_WEIGHTS.get(3, 3.0)
            w2 = GRADE_WEIGHTS.get(2, 2.0)
            w1 = GRADE_WEIGHTS.get(1, 1.0)
            st.markdown(
                f"""
                Classical homeopathic repertorization evaluates the whole patient hierarchically according to Kentian principles:
                
                1. **Mental & Emotional Generals (Paramount)**: Will, affections, fears, intellect, grief, memory, and anxiety.
                2. **Physical Generals**: Reactions to temperature, weather, motion, food aversions, and diurnal rhythms.
                3. **Particular Symptoms (Localities)**: Specific bodily organs, localized sensations, and regional modalities.
                
                **Totality Scoring Formula:**
                - **Grade 3 (Bold · Confirmed)**: **{w3:.1f}×** weighting (repeatedly verified in provings and clinical practice)
                - **Grade 2 (Italic · Qualified)**: **{w2:.1f}×** weighting (confirmed by clinical observation)
                - **Grade 1 (Roman · Observed)**: **{w1:.1f}×** weighting (prover observation without broad clinical confirmation)
                - **Specificity Multiplier**: Computed via inverse rubric frequency, prioritizing uncommon characteristic keynotes over broad non-discriminating rubrics.
                """
            )

        with st.container(border=True):
            st.html(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    {get_icon('checklist', size=20, color='var(--accent, #10B981)')}
                    <h4 style="margin: 0; color: var(--text, #E8EDF3); font-size: 16px;">2. The 7 Totality Dimensions</h4>
                </div>
                """
            )
            st.markdown(
                "Clinical narrative is segmented into **7 totality dimensions** to construct a complete homeopathic symptom profile:"
            )
            dims = get_canonical_dimensions(scope="MIND focus")
            for idx, d in enumerate(dims, start=1):
                star = " &middot; <span style='color: var(--accent, #10B981); font-weight: 700;'>Paramount</span>" if d.is_paramount else (
                    " &middot; <span style='color: #F59E0B; font-weight: 600;'>Recommended</span>" if d.is_recommended else ""
                )
                st.html(
                    f"""
                    <div style="margin-bottom: 6px; font-size: 13px;">
                        <b>{idx}. {d.label}</b> ({d.code}){star}
                        <div style="color: var(--text-muted, #A3B0C2); font-size: 12px; margin-left: 14px;">{d.hint}</div>
                    </div>
                    """
                )

    # 2. NLP Architecture & Evaluation
    with c_right:
        with st.container(border=True):
            st.html(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    {get_icon('auto_fix_high', size=20, color='#60A5FA')}
                    <h4 style="margin: 0; color: var(--text, #E8EDF3); font-size: 16px;">3. Biomedical Encoders & Inference Architecture</h4>
                </div>
                """
            )
            st.markdown(
                f"""
                Kent-AI combines specialized biomedical language models with local generative arbitration:
                
                - **BioLinkBERT-Base (110M)**: Pretrained on PubMed citation graphs for high-precision entity span recognition.
                - **PubMedBERT (110M)**: In-domain clinical vocabulary achieving high rubric retrieval recall.
                - **Vector Repertory Index**: ChromaDB persistent index over {SCOPE_MIND_COUNT:,} MIND rubrics (expandable to {SCOPE_ALL_COUNT:,} rubrics across all 37 chapters).
                - **Two-Stage Hybrid Engine**: High-recall dense ensemble mining paired with **{MODEL_DISPLAY_NAME}** running locally via Ollama for zero-leakage clinical intake arbitration.
                """
            )

        with st.container(border=True):
            st.html(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    {get_icon('analytics', size=20, color='var(--accent, #10B981)')}
                    <h4 style="margin: 0; color: var(--text, #E8EDF3); font-size: 16px;">4. Verified Evaluation Benchmarks</h4>
                </div>
                """
            )
            for m_key, m_info in EVALUATION_METRICS.items():
                st.html(
                    f"""
                    <div style="margin-bottom: 10px; border-bottom: 1px solid var(--line, #243243); padding-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <span style="font-weight: 700; color: var(--text, #E8EDF3); font-size: 13.5px;">{m_info['label']}</span>
                            <span style="font-family: var(--font-mono, monospace); font-weight: 800; color: var(--accent, #10B981); font-size: 14.5px;">{m_info['value']}</span>
                        </div>
                        <div style="font-size: 12px; color: var(--text-muted, #A3B0C2); margin-top: 2px;">
                            {m_info['plain_explanation']}
                        </div>
                    </div>
                    """
                )

    # 3. Full Investigational Clinical Notice
    with st.container(border=True):
        st.html(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                {get_icon('verified', size=20, color='#FBBF24')}
                <h4 style="margin: 0; color: var(--text, #E8EDF3); font-size: 16px;">5. Clinical Decision-Support Notice</h4>
            </div>
            """
        )
        st.markdown(
            """
            Kent-AI is an investigational software platform designed to assist qualified practitioners by organizing and repertorizing clinical narrative.
            
            **It does not provide medical diagnoses, treatment directives, or autonomous prescriptions.**
            
            All repertorization rubrics, remedy rankings, and differential indications must be evaluated by a certified medical or homeopathic practitioner alongside primary Materia Medica literature and formal clinical judgment. All patient consultations remain confidential and encrypted on the local host device.
            """
        )

