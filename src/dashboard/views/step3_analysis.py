"""Step 3 Repertorization & Analysis (Rubric Curation & Totality Grid) view."""

from __future__ import annotations

from typing import Any, Optional

import streamlit as st

from src.data.case_store import save_case
from src.data.kent_db import KentDB
from src.models.case import ClinicalCase
from src.pipeline.orchestrator import PatientReport, rescore_report
from src.dashboard.components.totality_grid import render_classical_totality_matrix


def render_step3_analysis(
    current_case: ClinicalCase,
    report: Optional[PatientReport],
    db: KentDB,
    pipeline: Any,
) -> None:
    """Render Step 3: Repertory Rubric Curation & Filtering."""
    st.markdown("#### Step 3: Repertory Rubric Curation & Filtering")

    if not report:
        st.info("No repertorization analysis performed yet. Click below to analyze.")
        if st.button("Run Repertorization Analysis", type="primary"):
            report = pipeline.repertorize_case(current_case)
            st.session_state.current_report = report
            current_case.report_data = report.to_dict()
            save_case(current_case)
            st.rerun()
    else:
        st.markdown(
            f"Retrieved **{len(report.matched_rubrics)}** matching rubrics across Dr. Kent's Repertory for Case **{current_case.case_id}**. "
            "You may mute individual rubrics or mark keynotes as **Eliminatory** (mandatory)."
        )

        # Classical repertorization matrix with interactive toggles
        render_classical_totality_matrix(report, db, case=current_case, allow_toggles=True)

        st.markdown("---")
        col_s3_back, col_s3_recomp, col_s3_next = st.columns([1, 1.5, 1.5])
        with col_s3_back:
            if st.button("← Back to Review", width="stretch"):
                st.session_state.workspace_step = 2
                st.rerun()
        with col_s3_recomp:
            if st.button("Recompute Totality Scores", type="secondary", width="stretch"):
                with st.spinner("Re-ranking remedies with active rubric filters..."):
                    if report and hasattr(pipeline, "ranker"):
                        rescored = rescore_report(pipeline.ranker, report, current_case)
                        st.session_state.current_report = rescored
                        current_case.report_data = rescored.to_dict()
                    else:
                        report = pipeline.repertorize_case(current_case)
                        st.session_state.current_report = report
                        current_case.report_data = report.to_dict()
                    save_case(current_case)
                    st.toast("Totality scores recomputed.")
                    st.rerun()
        with col_s3_next:
            if st.button("View Clinical Report →", type="primary", width="stretch"):
                st.session_state.workspace_step = 4
                st.rerun()
