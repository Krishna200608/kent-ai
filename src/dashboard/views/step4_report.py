"""Step 4 Clinical Report view, charts, and dimensions grid."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.components.icons import get_icon
from src.dashboard.components.rubric_tree import render_rubric_card
from src.dashboard.components.totality_grid import render_classical_totality_matrix
from src.dashboard.dimensions import DIMENSION_MAP, pluralize
from src.dashboard.pdf_exporter import generate_case_pdf
from src.dashboard.utils import esc
from src.data.kent_db import KentDB
from src.models.case import ClinicalCase
from src.pipeline.orchestrator import PatientReport

logger = logging.getLogger("dashboard.views.step4")


def render_dimensions_grid(dims: Dict[str, Any], report: Optional[PatientReport] = None):
    """Render 7-dimension clinical findings in clean cards with provenance affordances."""
    col1, col2, col3, col4 = st.columns(4)

    prov_hint = "Extracted from clinical dialogue and mapped to Kent totality dimensions"
    if report and report.matched_rubrics:
        top_cand = report.matched_rubrics[0]
        cand_path = top_cand.get("path") or top_cand.get("name") or "Repertory rubric"
        prov_hint = f"Matched rubric: {cand_path} (Totality Ranker)"

    # Build entity lookup from report.entities to surface agreement and confidence
    entity_lookup: Dict[str, Dict[str, Any]] = {}
    if report and getattr(report, "entities", None):
        for ent in report.entities:
            if isinstance(ent, dict):
                t_key = ent.get("text", "").strip().lower()
                if t_key and t_key not in entity_lookup:
                    entity_lookup[t_key] = ent

    def format_badge(val: str, badge_cls: str, dim_code: str, dim_label: str) -> str:
        ent_meta = entity_lookup.get(val.strip().lower(), {})
        badge_extra = ""
        if ent_meta.get("is_unanimous"):
            badge_extra = ' <span style="font-size: 9.5px; background: rgba(16,185,129,0.22); color: #34D399; border: 1px solid rgba(16,185,129,0.4); border-radius: 3px; padding: 1px 4px; margin-left: 4px; font-weight: 700;">4/4 Unanimous</span>'
        elif ent_meta.get("votes") and ent_meta.get("total_models"):
            votes = ent_meta['votes']
            total = ent_meta['total_models']
            badge_extra = f' <span style="font-size: 9.5px; background: rgba(59,130,246,0.22); color: #93C5FD; border: 1px solid rgba(59,130,246,0.4); border-radius: 3px; padding: 1px 4px; margin-left: 4px; font-weight: 600;">{votes}/{total} agreed</span>'
        elif ent_meta.get("confidence"):
            conf_pct = int(ent_meta["confidence"] * 100)
            badge_extra = f' <span style="font-size: 9.5px; background: rgba(147,51,234,0.22); color: #D8B4FE; border: 1px solid rgba(147,51,234,0.4); border-radius: 3px; padding: 1px 4px; margin-left: 4px; font-weight: 600;">{conf_pct}%</span>'

        return (
            f'<span class="badge {badge_cls}" tabindex="0" aria-label="Dimension: {dim_label} ({dim_code}) | Finding: {val}" data-tip="Dimension: {dim_label} ({dim_code}) | Finding: {val}&#10;Provenance: {prov_hint}" title="Dimension: {dim_label} ({dim_code}) | Finding: {val}&#10;Provenance: {prov_hint}">'
            f'{val}{badge_extra}</span>'
        )

    d_loc = DIMENSION_MAP["location"]
    d_sen = DIMENSION_MAP["sensation"]
    d_agg = DIMENSION_MAP["modality_agg"]
    d_amel = DIMENSION_MAP["modality_amel"]
    d_conc = DIMENSION_MAP["concomitant"]
    d_temp = DIMENSION_MAP["temporal"]
    d_ment = DIMENSION_MAP["mental"]

    with col1:
        st.markdown(f"**{d_loc.label} ({d_loc.code}):**")
        locs = dims.get("location") or dims.get("LOC", [])
        st.html("".join(format_badge(l, d_loc.badge_class, d_loc.code, d_loc.label) for l in locs) if locs else "<span style='color:#8492A6; font-size:13px;'>None recorded</span>")

        st.markdown(f"**{d_sen.label} ({d_sen.code}):**")
        sens = dims.get("sensation") or dims.get("SEN", [])
        st.html("".join(format_badge(s, d_sen.badge_class, d_sen.code, d_sen.label) for s in sens) if sens else "<span style='color:#8492A6; font-size:13px;'>None recorded</span>")

    with col2:
        st.markdown(f"**{d_agg.label} ({d_agg.code}):**")
        aggs = dims.get("modality_agg") or dims.get("MOD_AGG", [])
        st.html("".join(format_badge(a, d_agg.badge_class, d_agg.code, d_agg.label) for a in aggs) if aggs else "<span style='color:#8492A6; font-size:13px;'>None recorded</span>")

        st.markdown(f"**{d_amel.label} ({d_amel.code}):**")
        amels = dims.get("modality_amel") or dims.get("MOD_AMEL", [])
        st.html("".join(format_badge(a, d_amel.badge_class, d_amel.code, d_amel.label) for a in amels) if amels else "<span style='color:#8492A6; font-size:13px;'>None recorded</span>")

    with col3:
        st.markdown(f"**{d_temp.label} ({d_temp.code}):**")
        temps = dims.get("temporal") or dims.get("TEMP", [])
        st.html("".join(format_badge(t, d_temp.badge_class, d_temp.code, d_temp.label) for t in temps) if temps else "<span style='color:#8492A6; font-size:13px;'>None recorded</span>")

        st.markdown(f"**{d_conc.label} ({d_conc.code}):**")
        concs = dims.get("concomitant") or dims.get("CONC", [])
        st.html("".join(format_badge(c, d_conc.badge_class, d_conc.code, d_conc.label) for c in concs) if concs else "<span style='color:#8492A6; font-size:13px;'>None recorded</span>")

    with col4:
        st.markdown(f"**{d_ment.label} ({d_ment.code}):**")
        ments = dims.get("mental") or dims.get("MENT", [])
        st.html("".join(format_badge(m, d_ment.badge_class, d_ment.code, d_ment.label) for m in ments) if ments else "<span style='color:#8492A6; font-size:13px;'>None recorded</span>")

        st.markdown("**Negated / Excluded:**")
        negs = dims.get("negated") or dims.get("NEG", [])
        st.html("".join(format_badge(n, "badge-neg", "NEG", "Negated") for n in negs) if negs else "<span style='color:#8492A6; font-size:13px;'>None</span>")


def render_repertorization_chart(remedies: List[Dict[str, Any]]):
    """Render interactive Plotly horizontal bar chart of totality scores."""
    if not remedies:
        st.info("No remedies match the specified totality threshold.")
        return

    top_remedies = remedies[:12]
    df = pd.DataFrame(top_remedies)
    df = df.iloc[::-1]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=df["abbreviation"] + " (" + df["full_name"] + ")",
            x=df["score"],
            orientation="h",
            marker=dict(
                color=df["score"],
                colorscale=[[0, "#06B6D4"], [0.5, "#10B981"], [1, "#34D399"]],
                showscale=False,
                line=dict(color="rgba(255,255,255,0.15)", width=1),
            ),
            text=[f"Score: {s:.2f} ({pluralize(c, 'rubric', 'rubrics')})" for s, c in zip(df["score"], df["rubric_count"])],
            textposition="auto",
            hoverinfo="text",
        )
    )

    fig.update_layout(
        title="<b>Candidate Remedies: Grade-Weighted Totality Scores</b>",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F9FAFB", family="Outfit"),
        xaxis=dict(
            title="Weighted Totality Score",
            gridcolor="rgba(255,255,255,0.06)",
            zerolinecolor="rgba(255,255,255,0.1)",
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.0)",
            tickfont=dict(size=12),
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        height=380,
    )

    st.plotly_chart(fig, width="stretch")


def render_report_view(report: PatientReport, db: KentDB, case: Optional[ClinicalCase] = None):
    """Render comprehensive clinical repertorization decision-support report."""
    with st.container(border=True, key="report_card"):
        col_rep_head, col_rep_dl = st.columns([3, 1])
        with col_rep_head:
            st.html(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    {get_icon('clinical_notes', size=24, color='#10B981')}
                    <h3 style="margin: 0;">Case Repertorization Report &mdash; <code>{esc(report.patient_id)}</code></h3>
                </div>
                """
            )
            if case:
                st.markdown(f"**Patient**: {case.patient_name} ({case.demographics_string}) &nbsp;&middot;&nbsp; **Chief Complaint**: {case.chief_complaint or 'Clinical Consultation'}")
        with col_rep_dl:
            if case:
                pdf_key = f"rep_pdf_{case.case_id}_{case.updated_at}"
                pdf_bytes = st.session_state.get(pdf_key)
                if not pdf_bytes:
                    if st.button("Prepare PDF Export", key="btn_prep_rep_pdf", width="stretch"):
                        with st.spinner("Compiling PDF report..."):
                            st.session_state[pdf_key] = generate_case_pdf(case)
                            st.rerun()
                else:
                    st.download_button(
                        "Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"{case.case_id}_clinical_report.pdf",
                        mime="application/pdf",
                        width="stretch",
                        key="btn_rep_dl_pdf",
                    )
            st.download_button(
                "Export Markdown",
                data=report.to_markdown(),
                file_name=f"{report.patient_id}_repertorization.md",
                mime="text/markdown",
                width="stretch",
                key="btn_rep_dl_md",
            )
        st.markdown("---")

        summary_to_show = getattr(report, "clinical_summary", "") or (case.clinical_summary if case else "")
        if not summary_to_show and case and case.is_ready_for_repertorization:
            try:
                from src.pipeline.case_summarizer import CaseSummarizer
                summary_to_show = CaseSummarizer().generate_summary(case, use_llm=False)
            except Exception:
                pass

        if summary_to_show:
            st.html(
                f"""
                <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(16, 185, 129, 0.35); border-left: 4px solid #10B981; border-radius: 8px; padding: 14px 16px; margin: 10px 0 16px 0;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                        {get_icon('clinical_notes', size=18, color='#10B981')}
                        <span style="font-weight: 700; font-size: 13px; color: #10B981; letter-spacing: 0.02em;">CLINICAL CASE SUMMARY (PHYSICIAN BRIEF)</span>
                    </div>
                    <div style="font-size: 13.5px; line-height: 1.6; color: #F3F4F6;">
                        {esc(summary_to_show)}
                    </div>
                </div>
                """
            )

        st.html(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; margin: 12px 0 8px 0;">
                {get_icon('account_tree', size=20, color='#06B6D4')}
                <h4 style="margin: 0;">1. Validated 7-Dimension Clinical Totality</h4>
            </div>
            """
        )
        render_dimensions_grid(report.dimensions, report=report)

    remedies = report.ranked_remedies
    active_rubrics = [r for r in report.matched_rubrics if not r.get("muted")]
    if remedies:
        top_rem = remedies[0]
        margin_html = ""
        if len(remedies) > 1:
            margin = top_rem.get("score", 0.0) - remedies[1].get("score", 0.0)
            margin_html = f"<span style='color: #9CA3AF; font-size: 13px; margin-left: 8px;'>Score advantage: <b>+{margin:.2f}</b> over candidate #2 ({remedies[1].get('abbreviation')})</span>"

        st.html(
            f"""
            <div class="hero-simillimum">
                <div style="font-size: 12px; text-transform: uppercase; color: #34D399; font-weight: 700; letter-spacing: 0.05em; display: flex; align-items: center; gap: 6px;">
                    {get_icon('verified', size=16, color='#34D399')}
                    <span>Leading Candidates for Practitioner Review</span>
                </div>
                <div style="font-size: 26px; font-weight: 800; color: #FFFFFF; margin: 6px 0;">
                    {top_rem.get('full_name')} <span style="color: #34D399; font-size: 20px;">({top_rem.get('abbreviation')})</span>
                </div>
                <div style="font-size: 14px; color: #D1D5DB;">
                    Covers <b>{top_rem.get('rubric_count')} of {len(active_rubrics)}</b> symptom rubrics ({top_rem.get('coverage_ratio', 0)*100:.0f}% coverage) with a weighted totality score of <b>{top_rem.get('score')}</b>.
                    {margin_html}
                </div>
                <div style="font-size: 11.5px; color: #9CA3AF; margin-top: 6px; font-style: italic;">
                    Clinical decision-support indication based on Dr. Kent's Repertory; verify keynotes and constitutional picture before prescription.
                </div>
            </div>
            """
        )

        st.html(
            f"""
            <div style="display: flex; align-items: center; justify-content: space-between; margin: 16px 0 8px 0;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    {get_icon('bar_chart', size=20, color='#10B981')}
                    <h4 style="margin: 0;">2. Remedy Totality Ranking</h4>
                </div>
            </div>
            """
        )
        render_repertorization_chart(remedies)
        st.markdown(
            "<div style='font-size: 11.5px; color: #9CA3AF; margin-top: 4px; margin-bottom: 8px;'>"
            "<b>Ranking Method:</b> Classical Totality prioritizes candidate remedies covering the highest number of patient rubrics, then sorts by grade-weighted score."
            "</div>",
            unsafe_allow_html=True,
        )

        with st.expander("View Candidate Breakdown Table", expanded=False):
            table_data = []
            for idx, r in enumerate(remedies[:10], start=1):
                cov_pct = f"{r.get('coverage_ratio', 0)*100:.0f}%"
                table_data.append({
                    "Rank": f"#{idx}",
                    "Remedy": r.get("abbreviation"),
                    "Full Name": r.get("full_name"),
                    "Score": r.get("score"),
                    "Coverage": f"{r.get('rubric_count')}/{len(active_rubrics)} ({cov_pct})",
                })
            st.dataframe(pd.DataFrame(table_data), width="stretch", hide_index=True)

        st.html(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; margin: 20px 0 8px 0;">
                {get_icon('grid_on', size=20, color='#FBBF24')}
                <h4 style="margin: 0;">3. Classical Repertorization Matrix (Remedies &times; Rubrics)</h4>
            </div>
            """
        )
        render_classical_totality_matrix(report, db, case=case, allow_toggles=True)

    st.html(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin: 20px 0 8px 0;">
            {get_icon('format_list_bulleted', size=20, color='#34D399')}
            <h4 style="margin: 0;">4. Matched Kent Repertory Rubrics ({len(active_rubrics)})</h4>
        </div>
        """
    )
    for r in active_rubrics:
        render_rubric_card(r, db)


def render_step4_report(current_case: ClinicalCase, db: KentDB) -> None:
    """Render Step 4: Clinical Report view."""
    report = st.session_state.get("current_report")
    if not report and current_case.report_data:
        try:
            report = PatientReport(
                patient_id=current_case.report_data.get("patient_id", current_case.case_id),
                transcript=current_case.report_data.get("transcript", ""),
                dimensions=current_case.report_data.get("dimensions", current_case.dimensions),
                matched_rubrics=current_case.report_data.get("matched_rubrics", []),
                ranked_remedies=current_case.report_data.get("ranked_remedies", []),
                search_queries=current_case.report_data.get("search_queries", []),
                entities=current_case.report_data.get("entities", []),
            )
            st.session_state.current_report = report
        except Exception:
            pass

    if report:
        col_back_rep, _ = st.columns([1, 4])
        with col_back_rep:
            if st.button("← Back to Rubric Curation", width="stretch"):
                st.session_state.workspace_step = 3
                st.rerun()

        render_report_view(report, db, case=current_case)
    else:
        st.warning("No report generated for this case yet. Please complete Steps 1 & 2 first.")
        if st.button("Go to Step 1 (Intake)", type="primary"):
            st.session_state.workspace_step = 1
            st.rerun()
