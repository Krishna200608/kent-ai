"""Step 3 Repertorization & Analysis (Rubric Curation & Totality Grid) view (Phase 8 & UI Overhaul).

Provides:
- Classical Repertorization Matrix (rubrics as rows, remedies as columns) with mute & eliminatory toggles.
- Comparative candidate remedy ranking table with detailed score breakdown (grade weights, specificity, coverage).
- Expandable "Why this remedy" breakdown showing covered rubrics, grades, and score contributions.
- One-click Materia Medica dialog access for candidate remedies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import streamlit as st

from src.dashboard.components.busy import busy_slot
from src.dashboard.components.case_dialogs import show_remedy_dialog
from src.dashboard.components.icons import get_icon
from src.dashboard.components.totality_grid import render_classical_totality_matrix
from src.dashboard.constants import format_rubric_path
from src.dashboard.utils import esc
from src.data.case_store import save_case
from src.data.kent_db import KentDB
from src.models.case import ClinicalCase
from src.pipeline.orchestrator import PatientReport, rescore_report


def render_step3_analysis(
    current_case: ClinicalCase,
    report: Optional[PatientReport],
    db: KentDB,
    pipeline: Any,
) -> None:
    """Render Step 3: Repertory Rubric Curation & Comparative Totality Analysis."""
    st.html(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            {get_icon('grid_on', size=22, color='var(--accent, #10B981)')}
            <span style="font-size: 20px; font-weight: 800; color: var(--text, #E8EDF3);">
                Step 3: Repertory Rubric Curation & Totality Analysis
            </span>
        </div>
        <div style="font-size: 13px; color: var(--text-muted, #A3B0C2); margin-bottom: 14px;">
            Review retrieved repertory rubrics, eliminate non-matching remedies, and evaluate comparative totality candidate rankings.
        </div>
        """
    )

    if not report:
        st.info("No repertorization analysis performed yet for this case. Click below to analyze.")
        slot_empty = st.empty()
        if slot_empty.button("Run Repertorization Analysis", type="primary", key="btn_run_analysis_empty"):
            with busy_slot(slot_empty, "Analyzing rubrics...", key="btn_run_analysis_empty", type="primary"):
                with st.spinner("Searching Kent's Repertory and computing totality scores...", show_time=True):
                    skel = st.empty()
                    with skel.container():
                        st.skeleton(height=40, width="stretch")
                        st.skeleton(height=220, width="stretch")
                        st.skeleton(height=120, width="stretch")
                    report = pipeline.repertorize_case(current_case)
                    skel.empty()
                    st.session_state.current_report = report
                    current_case.report_data = report.to_dict()
                    save_case(current_case)
                    st.toast("Repertorization analysis complete.")
                    st.rerun()
        return

    # 1. Classical Totality Matrix
    active_rubrics = [r for r in report.matched_rubrics if not r.get("muted")]
    st.markdown(
        f"Retrieved **{len(report.matched_rubrics)}** matching rubrics across Dr. Kent's Repertory for Case **`{current_case.case_id}`** "
        f"({len(active_rubrics)} active). You may mute individual rubrics or mark keynotes as **Eliminatory** (mandatory)."
    )

    render_classical_totality_matrix(report, db, case=current_case, allow_toggles=True)

    # 2. Comparative Candidate Ranking Table & Score Breakdown
    remedies: List[Dict[str, Any]] = report.ranked_remedies or []
    if remedies:
        st.html(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; margin-top: 24px; margin-bottom: 8px;">
                {get_icon('analytics', size=20, color='var(--accent, #10B981)')}
                <span style="font-size: 17px; font-weight: 700; color: var(--text, #E8EDF3);">
                    Comparative Candidate Remedies & Score Breakdown
                </span>
            </div>
            <div style="font-size: 12.5px; color: var(--text-muted, #A3B0C2); margin-bottom: 12px;">
                Classical decision support presents candidate remedies comparatively across totality dimensions. The final prescription must always be differentiated against Materia Medica keynotes and modalities.
            </div>
            """
        )

        # Show top candidates with alternatives
        for rank_idx, rem in enumerate(remedies[:8], start=1):
            abbr = rem.get("abbreviation", "rem")
            name = rem.get("full_name") or abbr
            score = rem.get("score", 0.0)
            cov_count = rem.get("rubric_count", 0)
            cov_ratio = rem.get("coverage_ratio", 0.0)
            cov_pct = f"{cov_ratio * 100:.0f}%"
            covered_list = rem.get("rubrics_covered", [])

            card_title = f"#{rank_idx}  ·  {name} ({abbr})  ·  Score: {score}  ·  Covers {cov_count}/{len(active_rubrics)} ({cov_pct})"

            with st.expander(card_title, expanded=(rank_idx == 1)):
                c_head, c_act = st.columns([4, 1.5], vertical_alignment="center")
                with c_head:
                    st.html(
                        f"""
                        <div style="margin-bottom: 8px;">
                            <span style="font-size: 16px; font-weight: 800; color: var(--text, #E8EDF3);">{esc(name)}</span>
                            <span style="font-family: var(--font-mono, monospace); font-size: 12.5px; font-weight: 700; color: var(--accent, #10B981); background: var(--surface-2, #182330); padding: 2px 6px; border-radius: 4px; margin-left: 6px;">{esc(abbr)}</span>
                            <div style="font-size: 12.5px; color: var(--text-muted, #A3B0C2); margin-top: 4px;">
                                Totality Score: <b style="color: var(--accent, #10B981);">{score}</b> &middot;
                                Rubric Coverage: <b>{cov_count}/{len(active_rubrics)} ({cov_pct})</b>
                            </div>
                        </div>
                        """
                    )
                with c_act:
                    rem_id = rem.get("id") or rem.get("remedy_id")
                    if st.button("Inspect Materia Medica", key=f"btn_mm_diag_{abbr}_{rank_idx}", width="stretch"):
                        show_remedy_dialog(rem_id or abbr, db)

                # Explainability callout for Rank #1 leading candidate
                if rank_idx == 1 and len(remedies) > 1:
                    margin_v = score - remedies[1].get("score", 0.0)
                    g3_c = sum(1 for c in covered_list if c.get("grade") == 3)
                    st.html(
                        f"""
                        <div style="margin-bottom: 12px; padding: 8px 12px; background: rgba(16, 185, 129, 0.08); border-left: 3px solid #10B981; border-radius: 4px; font-size: 12px; color: var(--text, #E8EDF3);">
                            <b style="color: #34D399;">Leading Simillimum Indication:</b> Holds a <b>+{margin_v:.2f}</b> score lead over candidate #2 ({esc(remedies[1].get('abbreviation'))}) with <b>{g3_c}</b> Grade 3 keynote rubrics covered.
                        </div>
                        """
                    )

                # "Why this remedy" list of covered rubrics
                st.markdown("**Matched Repertory Rubrics & Grade Contributions:**")
                if not covered_list:
                    st.caption("No specific rubric details cataloged.")
                else:
                    for cov in covered_list:
                        cov_path = cov.get("path") or f"Rubric #{cov.get('rubric_id')}"
                        cov_disp = format_rubric_path(cov_path)
                        cov_grade = cov.get("grade", 1)
                        cov_sim = cov.get("similarity", 1.0)
                        cov_contrib = cov.get("contribution", 0.0)

                        badge_sym = "③" if cov_grade == 3 else ("②" if cov_grade == 2 else "①")
                        badge_css = f"badge-g{cov_grade}"
                        st.html(
                            f"""
                            <div style="font-size: 13px; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid var(--line, #243243); padding-bottom: 3px;">
                                <div style="font-family: var(--font-rubric, Georgia, serif); color: var(--text, #E8EDF3);">
                                    <span class="badge-grade-header {badge_css}" style="margin: 0; font-size: 11px;">{badge_sym} Grade {cov_grade}</span>
                                    <span style="margin-left: 6px;">{esc(cov_disp)}</span>
                                </div>
                                <div style="font-size: 11.5px; color: var(--text-muted, #A3B0C2); font-family: var(--font-mono, monospace);">
                                    +{cov_contrib:.2f} pts
                                </div>
                            </div>
                            """
                        )

    st.markdown("---")
    # 3. Step Navigation Action Bar (Sticky Bottom Nav)
    with st.container(key="sticky_bottom_nav"):
        col_s3_back, col_s3_recomp, col_s3_next = st.columns([1, 1.5, 1.5], vertical_alignment="center")
        with col_s3_back:
            if st.button("← Back to Review", width="stretch"):
                st.session_state.workspace_step = 2
                st.rerun()
        with col_s3_recomp:
            slot_recomp = st.empty()
            if slot_recomp.button("Recompute Totality Scores", type="secondary", width="stretch", key="btn_recompute_scores"):
                with busy_slot(slot_recomp, "Recomputing...", key="btn_recompute_scores", type="secondary"):
                    with st.spinner("Re-ranking remedies with active rubric filters...", show_time=True):
                        skel = st.empty()
                        with skel.container():
                            st.skeleton(height=180, width="stretch")
                        if report and hasattr(pipeline, "ranker"):
                            rescored = rescore_report(pipeline.ranker, report, current_case)
                            st.session_state.current_report = rescored
                            current_case.report_data = rescored.to_dict()
                        else:
                            report = pipeline.repertorize_case(current_case)
                            st.session_state.current_report = report
                            current_case.report_data = report.to_dict()
                        skel.empty()
                        save_case(current_case)
                        st.toast("Totality scores recomputed.")
                        st.rerun()
        with col_s3_next:
            if st.button("View Clinical Report →", type="primary", width="stretch", shortcut="Ctrl+Enter"):
                st.session_state.workspace_step = 4
                st.rerun()
