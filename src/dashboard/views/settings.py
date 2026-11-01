"""Tab 5: Settings & Methodology view."""

from __future__ import annotations

import streamlit as st

from src.dashboard.components.icons import get_icon
from src.dashboard.constants import GRADE_WEIGHTS, MODEL_DISPLAY_NAME


def render_settings_view() -> None:
    """Render Tab 5: Classical Methodology & Clinical NLP Foundations."""
    st.markdown("### Classical Methodology & Clinical NLP Foundations")
    col_m1, col_m2 = st.columns(2)

    with col_m1:
        with st.container(border=True):
            st.html(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    {get_icon('scale', size=20, color='#10B981')}
                    <h4 style="margin: 0;">1. Dr. J. T. Kent's Totality Principles</h4>
                </div>
                """
            )
            w3 = GRADE_WEIGHTS.get(3, 3.0)
            w2 = GRADE_WEIGHTS.get(2, 2.0)
            w1 = GRADE_WEIGHTS.get(1, 1.0)
            st.markdown(
                f"""
                Classical homeopathic repertorization adheres to the hierarchical evaluation of symptoms established by Dr. James Tyler Kent:
                
                1. **Mental & Emotional Generals (Paramount)**: Will, affections, memory, intellect, anxiety, grief, and fears.
                2. **Physical Generals**: Reaction to environment, temperature, weather, motion, posture, time of day.
                3. **Particular Symptoms (Localities)**: Specific bodily organs, sensations, and local modalities.
                
                **Totality Scoring Formula:**
                - Grade 3 (Bold): **{w3:.1f}×** weighting (confirmed by multiple provers & clinical cures)
                - Grade 2 (Italics): **{w2:.1f}×** weighting (qualified by clinical observation)
                - Grade 1 (Roman): **{w1:.1f}×** weighting (occasional prover observation)
                - Specificity Multiplier: Evaluated via inverse rubric frequency, granting higher value to uncommon, characteristic keynotes.
                """
            )

    with col_m2:
        with st.container(border=True):
            st.html(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    {get_icon('auto_fix_high', size=20, color='#60A5FA')}
                    <h4 style="margin: 0;">2. NLP Inference Encoders & Architecture</h4>
                </div>
                """
            )
            st.markdown(
                f"""
                Kent-AI integrates specialized biomedical language models fine-tuned on 15-class BIO token classification:
                
                - **BioLinkBERT-Base (110M)**: Pretrained on PubMed citation graphs. Evaluated at ~18ms latency with high token precision.
                - **PubMedBERT (110M)**: Biomedical domain-specific vocabulary achieving 41.56% Recall@20 on held-out clinical cases.
                - **4-Encoder Ensemble (414M)**: Majority voting across BioLinkBERT, PubMedBERT, Bio_ClinicalBERT, and DeBERTa-v3.
                - **Two-Stage Hybrid**: High-recall ensemble extraction paired with {MODEL_DISPLAY_NAME} contextual arbitration.
                """
            )

    with st.container(border=True):
        st.html(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                {get_icon('verified', size=20, color='#FBBF24')}
                <h4 style="margin: 0;">3. Clinical Decision-Support Notice</h4>
            </div>
            """
        )
        st.markdown(
            """
            Kent-AI is an investigational clinical decision-support system designed to assist practitioners by synthesizing complex repertory data.
            **It does not provide medical diagnoses, treatment plans, or autonomous prescriptions.**
            All repertorization indications must be evaluated by a certified medical or homeopathic practitioner alongside primary literature.
            """
        )
