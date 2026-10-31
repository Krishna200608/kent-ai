"""Streamlit Clinical Decision Support Dashboard for Kent-AI.

A clinician-centric clinical decision-support application built to Google Stitch UI/UX standards:
- 4-Step Consultation Stepper (1. Intake → 2. Review → 3. Analysis → 4. Report)
- Single typed ClinicalCase model as single source of truth
- Persistent SQLite Case Store and Case Library
- Classical Totality Repertory Grid (Rubrics as rows, Remedies as columns) with Mute & Eliminatory toggles
- High-contrast accessible design adhering to WCAG AA
- Professional PDF and JSON export suite
"""

from __future__ import annotations

import copy
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project repository root is always in sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import importlib
import src.config as config_mod
from src.config import get_project_root
import src.chatbot.dialogue_manager as _dm_mod
importlib.reload(_dm_mod)
from src.chatbot.dialogue_manager import DialogueManager, get_min_dimensions_to_unlock
from src.chatbot.state_machine import IntakeState
from src.data.kent_db import KentDB
from src.data.case_store import generate_case_id, get_case, list_cases, save_case
from src.models.case import ClinicalCase
from src.models.symptom_ner import SymptomNER
from src.models.ensemble import EnsembleNER
from src.models.hybrid_pipeline import HybridPipelineOrchestrator
try:
    from src.pipeline.orchestrator import PatientReport, PipelineOrchestrator, rescore_report
except ImportError:
    import src.pipeline.orchestrator as _orch_mod
    importlib.reload(_orch_mod)
    from src.pipeline.orchestrator import PatientReport, PipelineOrchestrator, rescore_report
from src.search.embedder import RubricEmbedder
from src.search.ranker import RemedyRanker
from src.search.vector_store import RubricVectorStore

try:
    from src.dashboard.styles import inject_custom_css
except ImportError:
    import src.dashboard.styles as _styles_mod
    importlib.reload(_styles_mod)
    from src.dashboard.styles import inject_custom_css
from src.dashboard.utils import esc, safe_rerun_fragment
from src.dashboard.components.icons import get_icon
import src.dashboard.components.chat_viewer as _cv_mod
importlib.reload(_cv_mod)
from src.dashboard.components.chat_viewer import (
    check_ollama_online,
    format_chat_transcript,
    render_chat_interface,
    render_slot_badges,
)
from src.dashboard.components.rubric_tree import render_rubric_card
from src.dashboard.components.case_bar import render_case_bar
from src.dashboard.components.totality_grid import render_classical_totality_matrix
from src.dashboard.components.case_library import render_case_library
from src.dashboard.components.remedy_comparison import render_remedy_comparison
from src.dashboard.pdf_exporter import generate_case_pdf
from src.dashboard.dimensions import (
    DIMENSION_MAP,
    KENT_DIMENSIONS_ORDERED,
    get_dimension,
    get_dimension_by_code,
    get_engine_dimensions_summary,
    pluralize,
)

logger = logging.getLogger("dashboard")

# Canonical Inference Engine Options for Clinician Workspace
ENGINE_OPTIONS = [
    "BioLinkBERT Fast Mode (~18ms)",
    "PubMedBERT (Top Rubric Alignment)",
    "Multi-Model Ensemble (4 Encoders, Majority Voting)",
    "Two-Stage Hybrid (Ensemble Mining + LLaMA 3 Arbitration)",
]

# Set wide page layout
st.set_page_config(
    page_title="Kent-AI Clinical Decision Support",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_db() -> KentDB:
    """Cache Kent database DAL instance."""
    return KentDB()


@st.cache_resource
def get_pipeline(engine_name: str = "BioLinkBERT Fast Mode (~18ms)"):
    """Cache dense vector store, embedder, and pipeline orchestrator for selected engine."""
    mock_mode = os.environ.get("KENT_MOCK_PIPELINE", "0") == "1"
    embedder = RubricEmbedder(mock_mode=mock_mode)
    vector_store = RubricVectorStore(embedder=embedder, in_memory=mock_mode)
    ranker = RemedyRanker()
    root = get_project_root()

    if mock_mode:
        if "Two-Stage Hybrid" in engine_name:
            return HybridPipelineOrchestrator(vector_store=vector_store, ranker=ranker, mock_mode=True)
        ner = SymptomNER(mock_mode=True)
        return PipelineOrchestrator(ner=ner, vector_store=vector_store, ranker=ranker, mock_mode=True)

    if "PubMedBERT" in engine_name:
        model_p = root / "data" / "models" / "pubmedbert_homeoNER"
        ner = SymptomNER(model_path=model_p, mock_mode=False)
        return PipelineOrchestrator(ner=ner, vector_store=vector_store, ranker=ranker, mock_mode=False)
    elif "Multi-Model Ensemble" in engine_name:
        ensemble = EnsembleNER(mock_mode=False)
        return PipelineOrchestrator(ner=ensemble, vector_store=vector_store, ranker=ranker, mock_mode=False)
    elif "Two-Stage Hybrid" in engine_name:
        return HybridPipelineOrchestrator(vector_store=vector_store, ranker=ranker, mock_mode=False)
    else:
        # Default: BioLinkBERT SOTA (~18ms)
        model_p = root / "data" / "models" / "biolinkbert_homeoNER"
        ner = SymptomNER(model_path=model_p, mock_mode=False)
        return PipelineOrchestrator(ner=ner, vector_store=vector_store, ranker=ranker, mock_mode=False)


def initialize_session():
    """Initialize stateful consultation variables and active ClinicalCase model."""
    if "current_case" not in st.session_state:
        new_cid = generate_case_id()
        fresh_case = ClinicalCase(case_id=new_cid)
        st.session_state.current_case = fresh_case

    case: ClinicalCase = st.session_state.current_case

    if "workspace_step" not in st.session_state:
        st.session_state.workspace_step = 1

    if "inference_engine" not in st.session_state:
        st.session_state.inference_engine = ENGINE_OPTIONS[0]
    active_engine = st.session_state.inference_engine

    if "pipeline" not in st.session_state:
        st.session_state.pipeline = get_pipeline(active_engine)

    if "dialogue_manager" not in st.session_state or not hasattr(st.session_state.dialogue_manager, "is_ollama_online"):
        mock_dm = os.environ.get("KENT_MOCK_PIPELINE", "0") == "1"
        dm = DialogueManager(
            orchestrator=st.session_state.pipeline,
            model_name="llama3:8b",
            mock_mode=mock_dm,
        )
        dm.load_from_case(case)
        st.session_state.dialogue_manager = dm
    else:
        dm = st.session_state.dialogue_manager
        dm.orchestrator = st.session_state.pipeline
        if getattr(dm, "api_base", None) in ("http://localhost:11434", None):
            dm.api_base = "http://127.0.0.1:11434"

    if "current_report" not in st.session_state:
        st.session_state.current_report = None
        # Re-hydrate report from case if stored
        if case.report_data:
            try:
                st.session_state.current_report = PatientReport(
                    patient_id=case.report_data.get("patient_id", case.case_id),
                    transcript=case.report_data.get("transcript", ""),
                    dimensions=case.report_data.get("dimensions", case.dimensions),
                    matched_rubrics=case.report_data.get("matched_rubrics", []),
                    ranked_remedies=case.report_data.get("ranked_remedies", []),
                    search_queries=case.report_data.get("search_queries", []),
                    entities=case.report_data.get("entities", []),
                )
            except Exception as e:
                logger.warning(f"Failed to rehydrate report from case: {e}")

    if "repertory_scope" not in st.session_state:
        st.session_state.repertory_scope = "MIND Chapter Focus (4,933 rubrics)"
    if "case_tray" not in st.session_state:
        st.session_state.case_tray = {"rubrics": [], "remedies": []}
    if "show_dev_details" not in st.session_state:
        st.session_state.show_dev_details = False
    if "ranking_sort_mode" not in st.session_state:
        st.session_state.ranking_sort_mode = "totality"


def render_header():
    """Render top brand navigation bar with clinical logo and active consultation telemetry."""
    active_scope = st.session_state.get("repertory_scope", "MIND Chapter Focus (4,933 rubrics)")
    is_mind = "MIND" in active_scope
    short_scope = "MIND" if is_mind else "All Chapters"

    case: ClinicalCase | None = st.session_state.get("current_case")
    case_label = case.case_id if case else "Active Case"

    dm = st.session_state.get("dialogue_manager")
    is_llm_online = check_ollama_online()
    llm_desc = "LLaMA 3:8B Online" if is_llm_online else "Rule-based Fallback"

    tooltip_text = (
        f"Active Scope: {active_scope} | "
        f"Dialogue LLM: {llm_desc} | "
        "Kent Knowledge Base: 74,513 rubrics across 37 chapters"
    )

    st.html(
        f"""
        <div class="brand-header">
            <div class="brand-left">
                <div class="brand-icon-box">
                    {get_icon('local_florist', size=26, color='#10B981')}
                </div>
                <div>
                    <div class="brand-title">Kent-AI Clinical Decision Support</div>
                    <div class="brand-subtitle">Classical Homeopathic Repertorization &middot; Dr. J. T. Kent Framework</div>
                </div>
            </div>
            <div class="brand-pills">
                <div class="session-badge-wrapper" title="{tooltip_text}">
                    <span class="status-pill status-pill-focus session-compact-pill">
                        <span class="status-dot"></span>
                        {get_icon('psychology' if is_mind else 'database', size=14, color='#10B981' if is_mind else '#06B6D4')}
                        <span>Scope: <b>{short_scope}</b></span>
                    </span>
                </div>
                <div class="session-badge-wrapper">
                    <span class="status-pill session-compact-pill" style="border-color: rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.1);">
                        <span class="status-dot" style="background: {'#10B981' if is_llm_online else '#9CA3AF'};"></span>
                        {get_icon('forum', size=14, color='#10B981' if is_llm_online else '#9CA3AF')}
                        <span><b>{llm_desc}</b></span>
                    </span>
                </div>
            </div>
        </div>
        """
    )


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
            f'<span class="badge {badge_cls}" title="Dimension: {dim_label} ({dim_code}) | Finding: {val}&#10;Provenance: {prov_hint}">'
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

        col1, col2 = st.columns([3, 2])
        with col1:
            st.html(
                f"""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        {get_icon('bar_chart', size=20, color='#10B981')}
                        <h4 style="margin: 0;">2. Remedy Totality Ranking</h4>
                    </div>
                </div>
                """
            )
            render_repertorization_chart(remedies)
            st.markdown(
                "<div style='font-size: 11.5px; color: #9CA3AF; margin-top: 4px;'>"
                "<b>Ranking Method:</b> Classical Totality prioritizes candidate remedies covering the highest number of patient rubrics, then sorts by grade-weighted score."
                "</div>",
                unsafe_allow_html=True,
            )

        with col2:
            st.html(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    {get_icon('table_chart', size=20, color='#A78BFA')}
                    <h4 style="margin: 0;">3. Top Candidate Breakdown</h4>
                </div>
                """
            )
            table_data = []
            for idx, r in enumerate(remedies[:8], start=1):
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
                <h4 style="margin: 0;">4. Classical Repertorization Matrix (Remedies &times; Rubrics)</h4>
            </div>
            """
        )
        render_classical_totality_matrix(report, db, case=case, allow_toggles=True)

    st.html(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin: 20px 0 8px 0;">
            {get_icon('format_list_bulleted', size=20, color='#34D399')}
            <h4 style="margin: 0;">5. Matched Kent Repertory Rubrics ({len(active_rubrics)})</h4>
        </div>
        """
    )
    for r in active_rubrics:
        render_rubric_card(r, db)


def render_sidebar_case_tray():
    """Render persistent Current Case tray in sidebar."""
    tray = st.session_state.get("case_tray", {"rubrics": [], "remedies": []})
    rubrics = tray.get("rubrics", [])
    remedies = tray.get("remedies", [])
    total_items = len(rubrics) + len(remedies)

    st.markdown("---")
    st.html(
        f"""
        <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;'>
            <div style='display: flex; align-items: center; gap: 6px;'>
                {get_icon('briefcase', size=16, color='#10B981')}
                <span style='font-size: 14px; font-weight: 700; color: #F9FAFB;'>Current Case Tray</span>
            </div>
            <span class='step-counter-badge'>{pluralize(total_items, "item", "items")}</span>
        </div>
        """
    )

    if total_items == 0:
        st.markdown(
            '<div style="font-size: 12px; color: #8492A6; margin-bottom: 8px;">'
            'No items collected yet. Click <b>+ Add to case</b> on rubrics or remedies in Explorer or Materia Medica.'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # List rubrics
    if rubrics:
        st.markdown(f"**Selected Rubrics ({pluralize(len(rubrics), 'rubric', 'rubrics')}):**")
        for idx, r in enumerate(rubrics):
            col_r_txt, col_r_del = st.columns([5, 1])
            with col_r_txt:
                r_name = r.get("path") or r.get("name", "Rubric")
                if len(r_name) > 34:
                    r_name = "..." + r_name[-31:]
                st.markdown(f"<span style='font-size: 11.5px; color: #E5E7EB;'>&bull; {r_name}</span>", unsafe_allow_html=True)
            with col_r_del:
                if st.button("✕", key=f"del_tray_r_{idx}", help="Remove rubric from case"):
                    tray["rubrics"].pop(idx)
                    st.rerun()

    # List remedies
    if remedies:
        st.markdown(f"**Selected Remedies ({pluralize(len(remedies), 'remedy', 'remedies')}):**")
        for idx, rem in enumerate(remedies):
            col_rem_txt, col_rem_del = st.columns([5, 1])
            with col_rem_txt:
                rem_name = rem.get('full_name') or rem.get('abbreviation')
                rem_abbr = rem.get('abbreviation') or ''
                st.markdown(f"<span style='font-size: 11.5px; color: #34D399;'>&bull; {rem_name} ({rem_abbr})</span>", unsafe_allow_html=True)
            with col_rem_del:
                if st.button("✕", key=f"del_tray_rem_{idx}", help="Remove remedy from case"):
                    tray["remedies"].pop(idx)
                    st.rerun()

    col_btn1, col_btn2 = st.columns([3, 2])
    with col_btn1:
        if rubrics and st.button("Repertorize This Case", type="primary", width="stretch", key="tray_repertorize_btn"):
            pipeline = st.session_state.pipeline
            ranked = pipeline.ranker.rank(rubrics, top_n=10)
            report = PatientReport(
                patient_id=f"TRAY-{uuid.uuid4().hex[:6].upper()}",
                transcript=f"Totality compiled from {pluralize(len(rubrics), 'manually selected rubric', 'manually selected rubrics')} in Case Tray.",
                dimensions={"case_rubrics": [r.get("path") or r.get("name") for r in rubrics]},
                matched_rubrics=rubrics,
                ranked_remedies=ranked,
                search_queries=[r.get("path", "") for r in rubrics],
            )
            st.session_state.current_report = report
            st.session_state.workspace_step = 4
            st.toast("Case repertorized! Displayed in Step 4 Report.")
            st.rerun()
    with col_btn2:
        if st.button("Clear Tray", key="clear_all_tray", width="stretch"):
            st.session_state.case_tray = {"rubrics": [], "remedies": []}
            st.rerun()


def render_sidebar():
    """Render clinical sidebar telemetry and consultation controls."""
    with st.sidebar:
        st.html(
            f"""
            <div style='text-align: center; margin-bottom: 16px; padding: 4px 8px;'>
                <div style='margin-bottom: 8px; display: inline-flex; justify-content: center; align-items: center; width: 50px; height: 50px; border-radius: 14px; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3);'>
                    {get_icon('local_florist', size=28, color='#10B981')}
                </div>
                <div style='font-size: 16px; font-weight: 800; color: #10B981; line-height: 1.25;'>Kent-AI Clinical Decision Support</div>
                <div style='font-size: 11px; color: #9CA3AF; margin-top: 2px;'>Classical Decision Support</div>
            </div>
            """
        )

        case: ClinicalCase | None = st.session_state.get("current_case")

        st.html(
            f"""
            <div style='display: flex; align-items: center; gap: 6px; margin: 10px 0 6px 0;'>
                {get_icon('tune', size=16, color='#10B981')}
                <span style='font-size: 13px; font-weight: 700; color: #F9FAFB;'>Repertory Scope Selection</span>
            </div>
            """
        )
        scope_options = [
            "MIND Chapter Focus (4,933 rubrics)",
            "All 37 Chapters (74,513 rubrics)",
        ]
        curr_scope = st.session_state.get("repertory_scope", scope_options[0])
        default_idx = 0 if "MIND" in curr_scope else 1
        new_scope = st.radio(
            "Repertory Scope Control",
            scope_options,
            index=default_idx,
            key="repertory_scope",
            label_visibility="collapsed",
            help="Single source of truth for intake analysis and repertorization across all workspaces.",
        )

        if case:
            case.scope_chapter = "MIND" if "MIND" in new_scope else "ALL"

        with st.expander("Inference Engine & Settings", expanded=False):
            curr_engine = st.session_state.get("inference_engine", ENGINE_OPTIONS[0])
            default_eng_idx = 0
            for i, opt in enumerate(ENGINE_OPTIONS):
                if opt == curr_engine:
                    default_eng_idx = i
                    break

            selected_engine = st.radio(
                "Inference Engine",
                ENGINE_OPTIONS,
                index=default_eng_idx,
                key="engine_radio_select",
                label_visibility="collapsed",
                help="Select underlying NLP architecture for token extraction and symptom classification.",
            )
            if selected_engine != st.session_state.get("inference_engine"):
                st.session_state.inference_engine = selected_engine
                st.session_state.pipeline = get_pipeline(selected_engine)
                if "dialogue_manager" in st.session_state and hasattr(st.session_state.dialogue_manager, "orchestrator"):
                    st.session_state.dialogue_manager.orchestrator = st.session_state.pipeline
                st.rerun()

            st.toggle(
                "Developer telemetry",
                value=st.session_state.get("show_dev_details", False),
                key="show_dev_details",
                help="Toggle low-level system latency, rubric IDs, and model details.",
            )

        render_sidebar_case_tray()

        st.markdown("---")
        with st.expander("Dr. Kent's Totality Principles", expanded=False):
            st.markdown(
                '<div style="font-size: 12px; color: #D1D5DB; line-height: 1.5; font-style: italic;">'
                '“The mental symptoms are the most important, for they express the very man himself. '
                'Next in importance are the physical generals, especially those related to time, temperature, and weather.”'
                '<div style="font-weight: 700; color: #10B981; margin-top: 4px; font-style: normal;">— Dr. J. T. Kent</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        st.html(
            """
            <div style='font-size: 11px; color: #6B7280; text-align: justify; margin-top: 14px;'>
                <b>Investigational Tool:</b> Kent-AI is an academic clinical decision-support and repertorization research system. It does not replace qualified homeopathic or medical evaluation.
            </div>
            """
        )


@st.fragment
def render_bedside_dialogue_panel(dm: DialogueManager, current_case: ClinicalCase) -> None:
    """Render Bedside Dialogue chat and intake controls in an isolated fragment."""
    col_chat, col_ctrl = st.columns([3, 1])
    with col_ctrl:
        with st.container(border=True):
            st.html(
                f"""
                <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 12px;'>
                    {get_icon('tune', size=18, color='#10B981')}
                    <span style='font-size: 15px; font-weight: 700; color: #F9FAFB;'>Intake Controls</span>
                </div>
                """
            )

            st.markdown("<div style='font-size: 13px; font-weight: 700; color: #D1D5DB; margin-bottom: 6px;'>Active Case Summary:</div>", unsafe_allow_html=True)
            filled_items = []
            for dim in KENT_DIMENSIONS_ORDERED:
                vals = current_case.dimensions.get(dim.key, [])
                if vals:
                    filled_items.append((dim.label, ", ".join(vals), dim.badge_class, dim.tooltip))

            if filled_items:
                for d_label, d_val, b_cls, d_tip in filled_items:
                    st.markdown(f"<div style='font-size: 12px; margin-bottom: 4px;' title='{d_tip}'><span class='badge {b_cls}' style='font-size:11px; padding:2px 6px;'>{d_label}</span> <span style='color:#F9FAFB;'>{d_val}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='font-size: 12px; color: #8492A6; margin-bottom: 8px; font-style: italic;'>No symptoms captured yet. Converse in the dialogue console to extract dimensions.</div>", unsafe_allow_html=True)

            st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)

            collected_count = current_case.filled_dimensions_count
            min_dims = get_min_dimensions_to_unlock()
            can_proceed = current_case.is_ready_for_repertorization or (collected_count >= min_dims)

            if can_proceed:
                if st.button("Proceed to Clinical Review →", type="primary", width="stretch", key="btn_proceed_review"):
                    dm.sync_to_case(current_case)
                    save_case(current_case)
                    st.session_state.workspace_step = 2
                    st.rerun(scope="app")
            else:
                st.button("Proceed to Clinical Review →", type="primary", disabled=True, width="stretch", help=f"Capture at least {min_dims} symptom dimension to unlock.", key="btn_proceed_review_disabled")
                st.markdown(f"<div style='font-size: 11.5px; color: #9CA3AF; margin-top: 4px;'>Requires at least {min_dims} dimension &mdash; currently {collected_count}/7.</div>", unsafe_allow_html=True)

            st.markdown("---")

            with st.popover("Export Consultation Transcript", width="stretch"):
                st.markdown("##### Consultation Transcript")
                transcript_text = format_chat_transcript(dm)
                st.download_button(
                    label="Download Chat (.txt)",
                    data=transcript_text,
                    file_name=f"{current_case.case_id}_consultation.txt",
                    mime="text/plain",
                    width="stretch",
                    key="sidebar_ctrl_download_txt",
                )
                st.code(transcript_text, language="markdown")

            st.markdown("---")

            if st.session_state.get("confirm_intake_reset", False):
                st.warning("Clear all intake symptoms?")
                col_cf1, col_cf2 = st.columns(2)
                with col_cf1:
                    if st.button("Yes, Clear", type="primary", width="stretch", key="confirm_reset_yes"):
                        dm.reset()
                        dm.get_greeting()
                        current_case.dimensions = {k: [] for k in current_case.dimensions}
                        save_case(current_case)
                        st.session_state.current_report = None
                        st.session_state.confirm_intake_reset = False
                        st.toast("Consultation reset.")
                        safe_rerun_fragment()
                with col_cf2:
                    if st.button("Cancel", width="stretch", key="confirm_reset_no"):
                        st.session_state.confirm_intake_reset = False
                        safe_rerun_fragment()
            else:
                if st.button("Reset Consultation", type="secondary", width="stretch", key="btn_reset_consult"):
                    st.session_state.confirm_intake_reset = True
                    safe_rerun_fragment()

    with col_chat:
        render_chat_interface(dm)


def main():
    # Inject Google Stitch design system and full-screen responsive layout
    inject_custom_css()
    initialize_session()
    render_sidebar()
    render_header()

    db = get_db()
    pipeline = st.session_state.pipeline
    dm: DialogueManager = st.session_state.dialogue_manager
    current_case: ClinicalCase = st.session_state.current_case

    tab_workspace, tab_library, tab_explorer, tab_mm, tab_settings = st.tabs([
        "Case Workspace",
        "Case Library",
        "Rubric Explorer",
        "Materia Medica",
        "Settings & Methodology",
    ])

    # =========================================================================
    # TAB 1: Case Workspace (4-Step Clinician Workflow)
    # =========================================================================
    with tab_workspace:
        render_case_bar(current_case)
        step = st.session_state.get("workspace_step", 1)

        # ---------------------------------------------------------------------
        # STEP 1: Patient Intake (Bedside Chat or Paste Narrative)
        # ---------------------------------------------------------------------
        if step == 1:
            st.markdown("#### Step 1: Patient Clinical Intake")
            intake_mode = st.radio(
                "Intake Modality:",
                ["Bedside Dialogue (Chatbot)", "Paste Clinical Narrative (Text)"],
                horizontal=True,
                key="intake_mode_select",
            )

            if intake_mode == "Bedside Dialogue (Chatbot)":
                render_bedside_dialogue_panel(dm, current_case)

            else:
                # Paste Clinical Narrative mode
                with st.container(border=True):
                    example_cases = {
                        "Select a clinical vignette (or enter free text below)...": "",
                        "Case 1: Severe anxiety in morning, worse alone (MIND)": "Doctor, I feel terribly anxious and depressed every morning, worse when alone. My thoughts race with fear and dread. I have no fever and no nausea.",
                        "Case 2: Absent-minded & forgetful on waking (MIND)": "Patient complains of extreme absent-mindedness and difficulty concentrating, especially in the morning after waking up, with trembling hands and restless pacing.",
                        "Case 3: Fear of dark & crowds with weeping (MIND)": "Patient reports overwhelming fear in the dark and in crowded places. Weeps easily upon any emotional upset, feels completely forsaken and abandoned, relieved by fresh open air.",
                        "Case 4: Extreme irritability & impatience with anger (MIND)": "Patient is exceedingly irritable, cannot bear contradiction or noise, full of wrath and quick to anger over trifles, intensely restless at night.",
                    }

                    selected_example = st.selectbox("Pre-load Clinical Vignette:", list(example_cases.keys()))
                    default_text = example_cases.get(selected_example, "")

                    user_case_text = st.text_area(
                        "Patient Clinical Narrative:",
                        value=default_text,
                        placeholder="Describe patient symptoms in free text...",
                        height=140,
                    )

                    col_p_run, col_p_info = st.columns([2, 4], vertical_alignment="center")
                    with col_p_run:
                        if st.button("Extract Symptoms & Proceed →", type="primary", disabled=not bool(user_case_text.strip()), width="stretch"):
                            with st.spinner("Extracting 7 clinical dimensions..."):
                                raw_rep = pipeline.process_transcript(transcript=user_case_text, section_id=1 if "MIND" in current_case.scope_chapter else None)
                                # Load extracted dimensions into current_case directly
                                for dkey, vals in raw_rep.dimensions.items():
                                    norm_key = dkey.lower()
                                    if norm_key in current_case.dimensions:
                                        for v in vals:
                                            current_case.add_symptom(norm_key, v)
                                current_case.chief_complaint = user_case_text[:120] + ("..." if len(user_case_text) > 120 else "")
                                save_case(current_case)
                                dm.load_from_case(current_case)
                                st.session_state.workspace_step = 2
                                st.rerun()

                    with col_p_info:
                        st.caption("Extracts Location, Sensation, Modalities, Concomitants, Temporal, and Mental generals directly into Clinical Review.")

        # ---------------------------------------------------------------------
        # STEP 2: Clinical Review (Validate, Add, and Delete 7-Dimensions)
        # ---------------------------------------------------------------------
        elif step == 2:
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
            if not current_case.clinical_summary and current_case.is_ready_for_repertorization:
                try:
                    from src.pipeline.case_summarizer import CaseSummarizer
                    current_case.clinical_summary = CaseSummarizer().generate_summary(current_case)
                    save_case(current_case)
                except Exception as e:
                    logger.info("Summary auto-generation in Step 2: %s", e)

            if current_case.clinical_summary:
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
                            {esc(current_case.clinical_summary)}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    with st.expander("Edit Clinical Summary (Physician Adjustments)", expanded=False):
                        edited_sum = st.text_area("Adjust case summary for medical records:", value=current_case.clinical_summary, height=90, key="ta_edit_sum_step2")
                        if st.button("Save Edited Summary", key="btn_save_sum_step2"):
                            current_case.clinical_summary = edited_sum.strip()
                            save_case(current_case)
                            st.toast("Clinical summary saved.", icon="✅")
                            st.rerun()

            # 4 Columns of Cards
            c1, c2, c3, c4 = st.columns(4)

            def render_dim_editor(col, dim_key: str, dim_label: str, badge_cls: str, code: str):
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

                        # Add new item input
                        new_item = st.text_input(f"+ Add {dim_label}:", key=f"inp_add_{dim_key}", placeholder="e.g. throbbing...")
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

        # ---------------------------------------------------------------------
        # STEP 3: Repertorization & Analysis (Rubric Curation)
        # ---------------------------------------------------------------------
        elif step == 3:
            st.markdown("#### Step 3: Repertory Rubric Curation & Filtering")
            report = st.session_state.get("current_report")

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

        # ---------------------------------------------------------------------
        # STEP 4: Clinical Report
        # ---------------------------------------------------------------------
        elif step == 4:
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

    # =========================================================================
    # TAB 2: Case Library
    # =========================================================================
    with tab_library:
        render_case_library(current_case)

    # =========================================================================
    # TAB 3: Rubric Explorer
    # =========================================================================
    with tab_explorer:
        with st.container(border=True):
            st.html(
                f"""
                <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px;'>
                    {get_icon('psychology', size=22, color='#10B981')}
                    <h3 style='margin: 0;'>Kent's Repertory & Rubric Search</h3>
                </div>
                """
            )
            st.markdown("Search **74,513 digitized rubrics** using meaning-based dense vector search or exact words.")

            col_search, col_sec = st.columns([3, 1])
            with col_search:
                search_query = st.text_input(
                    "Search Rubric:",
                    value="anxiety dark",
                    placeholder="e.g. 'anxiety dark', 'fear alone', 'absent-minded', 'weeping easily'...",
                )
            with col_sec:
                sections = db.get_sections()
                mind_opt = "1: MIND (4,933 rubrics - Focus Chapter)"
                all_opt = "All Chapters (74,513 rubrics)"
                sec_options = [mind_opt, all_opt] + [f"{s['id']}: {s['name']}" for s in sections if s['id'] != 1]
                selected_sec_str = st.selectbox("Section / Chapter:", sec_options, index=0)
                chosen_sec_id = 1
                if selected_sec_str == all_opt:
                    chosen_sec_id = None
                elif ":" in selected_sec_str:
                    chosen_sec_id = int(selected_sec_str.split(":")[0])

            col_mode, col_sort, col_limit = st.columns([2, 1.5, 1])
            with col_mode:
                search_mode = st.radio("Search Mode:", ["Meaning-based", "Exact words"], horizontal=True)
            with col_sort:
                sort_by = st.selectbox("Sort By:", ["Relevance (Similarity)", "Remedy Count (High to Low)"])
            with col_limit:
                limit = st.select_slider("Results:", options=[15, 30, 50], value=15)

            search_clicked = st.button("Search Rubrics", type="primary", width="stretch")

        if (search_clicked or search_query) and search_query.strip():
            with st.spinner("Searching rubrics..."):
                if search_mode == "Meaning-based":
                    raw_results = pipeline.vector_store.query(
                        query_text=search_query,
                        top_k=max(limit, 30),
                        section_id=chosen_sec_id,
                    )
                else:
                    raw_results = db.search_rubrics(
                        query=search_query,
                        section_id=chosen_sec_id,
                        limit=max(limit, 30),
                    )

            filtered_results = [r for r in raw_results if r.get("remedy_count", 0) > 0]
            if "Remedy Count" in sort_by:
                filtered_results = sorted(filtered_results, key=lambda r: r.get("remedy_count", 0), reverse=True)

            display_results = filtered_results[:limit]
            if display_results:
                st.markdown(f"Displaying **{len(display_results)}** matching {pluralize(len(display_results), 'rubric', 'rubrics', include_count=False)}:")
                for r in display_results:
                    render_rubric_card(r, db, query=search_query)
            else:
                st.info("No rubrics matched the specified search criteria.")

    # =========================================================================
    # TAB 4: Materia Medica & Differential Comparison
    # =========================================================================
    with tab_mm:
        tab_mm_browse, tab_mm_diff = st.tabs(["Materia Medica Index", "Differential Remedy Comparison"])

        with tab_mm_browse:
            with st.container(border=True):
                st.html(
                    f"""
                    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px;'>
                        {get_icon('medication', size=22, color='#10B981')}
                        <h3 style='margin: 0;'>Homeopathic Remedy Dictionary & MIND Keynotes</h3>
                    </div>
                    """
                )
                st.markdown("Browse cataloged remedies with Latin names, abbreviations, and characteristic Grade 3 keynotes.")

                col_rem_search, col_rem_clear, col_rem_toggle = st.columns([3.5, 0.9, 2.4], vertical_alignment="bottom")
                with col_rem_search:
                    if "rem_filter_text" not in st.session_state:
                        st.session_state.rem_filter_text = "Lach"
                    rem_search = st.text_input(
                        "Filter Remedy by Name or Abbreviation:",
                        value=st.session_state.rem_filter_text,
                        key="rem_input_widget",
                        placeholder="e.g. 'Lach', 'Phos', 'Nux-v', 'Ars', 'Acon'...",
                    )
                    st.session_state.rem_filter_text = rem_search
                with col_rem_clear:
                    if st.button("✕ Clear", help="Clear remedy search filter", width="stretch"):
                        st.session_state.rem_filter_text = ""
                        st.session_state.rem_input_widget = ""
                        st.rerun()
                with col_rem_toggle:
                    prioritize_mind = st.checkbox(
                        "Prioritize MIND Keynotes",
                        value=True,
                        help="Sort characteristic Grade 3 symptoms so that mental & emotional rubrics appear first.",
                    )

            if rem_search.strip():
                with db.connect() as conn:
                    cur = conn.cursor()
                    query = """
                        SELECT 
                            r.id,
                            r.abbreviation,
                            r.full_name,
                            r.normalized,
                            (SELECT COUNT(*) FROM rubric_remedies rr WHERE rr.remedy_id = r.id) as total_rubrics,
                            (SELECT COUNT(*) FROM rubric_remedies rr JOIN rubrics rb ON rr.rubric_id = rb.id WHERE rr.remedy_id = r.id AND rb.section_id = 1) as mind_rubrics
                        FROM remedies r
                        WHERE r.abbreviation LIKE ? OR r.full_name LIKE ? OR r.normalized LIKE ?
                        ORDER BY mind_rubrics DESC, total_rubrics DESC
                        LIMIT 20
                    """
                    like_term = f"%{rem_search.strip()}%"
                    cur.execute(query, (like_term, like_term, like_term))
                    remedy_rows = cur.fetchall()

                if remedy_rows:
                    st.markdown(f"Found **{len(remedy_rows)}** cataloged {pluralize(len(remedy_rows), 'remedy', 'remedies', include_count=False)}:")
                    for row in remedy_rows:
                        r_id, abbr, name = row["id"], row["abbreviation"], row["full_name"]
                        total_count, mind_count = row["total_rubrics"], row["mind_rubrics"]
                        card_title = f"{name or abbr} ({abbr})  ·  {pluralize(mind_count, 'rubric', 'rubrics')} in MIND  ·  {pluralize(total_count, 'rubric', 'rubrics')} total"

                        with st.expander(card_title, expanded=False):
                            col_reminfo, col_remact = st.columns(2)
                            with col_reminfo:
                                st.html(
                                    f"""
                                    <div style="margin-bottom: 8px;">
                                        <div style="font-size: 18px; font-weight: 800; color: #FFFFFF;">
                                            {name or abbr} <span style="color: #34D399; font-weight: 700;">({abbr})</span>
                                        </div>
                                        <div style="font-size: 12.5px; color: #9CA3AF; margin-top: 4px;">
                                            <span class="status-pill" style="color: #10B981;"><b>{mind_count}</b> in MIND</span>
                                            <span class="status-pill" style="margin-left: 6px;"><b>{total_count:,}</b> across all chapters</span>
                                        </div>
                                    </div>
                                    """
                                )
                            with col_remact:
                                tray = st.session_state.get("case_tray", {"rubrics": [], "remedies": []})
                                is_in_tray = any(item.get("id") == r_id for item in tray.get("remedies", []))
                                rem_btn_key = f"tray_add_rem_{r_id}"
                                if is_in_tray:
                                    st.button("✓ Added to Case Tray", key=rem_btn_key, disabled=True, width="stretch")
                                else:
                                    if st.button("+ Add to case tray", key=rem_btn_key, width="stretch"):
                                        tray["remedies"].append({
                                            "id": r_id,
                                            "abbreviation": abbr,
                                            "full_name": name or abbr,
                                            "mind_rubrics": mind_count,
                                            "total_rubrics": total_count,
                                        })
                                        st.toast(f"Added {abbr} to case tray.")
                                        st.rerun()

                            keynotes = db.get_remedy_rubrics(r_id, min_grade=3, limit=16, prioritize_mind=prioritize_mind, rank_by_specificity=True)
                            if not keynotes:
                                st.write("No Grade 3 keynote rubrics cataloged for this remedy.")
                            else:
                                st.markdown(f"**Characteristic Grade 3 Keynotes ({pluralize(len(keynotes), 'keynote', 'keynotes')}):**")
                                for kn in keynotes:
                                    is_mind_kn = kn.get("section_name") == "MIND" or str(kn["path"]).startswith("MIND")
                                    mind_badge = f"<span class='badge badge-mind' style='margin-left: 6px;'>{get_icon('psychology', size=11, color='#10B981')} MIND</span>" if is_mind_kn else ""
                                    st.html(
                                        f"<div style='margin-bottom: 5px; display: flex; align-items: center; flex-wrap: wrap; gap: 4px;'>"
                                        f"<span class='grade-3'>Grade 3</span> "
                                        f"<span style='font-size:13px; color:#F9FAFB;'>{kn['path']}</span> "
                                        f"<span style='font-size:11px; color:#06B6D4;'>({kn.get('section_name')})</span>"
                                        f"{mind_badge}"
                                        f"</div>"
                                    )
                else:
                    st.info(f"No remedies found matching '{rem_search}'.")

        with tab_mm_diff:
            render_remedy_comparison(db)

    # =========================================================================
    # TAB 5: Settings & Methodology
    # =========================================================================
    with tab_settings:
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
                st.markdown(
                    """
                    Classical homeopathic repertorization adheres to the hierarchical evaluation of symptoms established by Dr. James Tyler Kent:
                    
                    1. **Mental & Emotional Generals (Paramount)**: Will, affections, memory, intellect, anxiety, grief, and fears.
                    2. **Physical Generals**: Reaction to environment, temperature, weather, motion, posture, time of day.
                    3. **Particular Symptoms (Localities)**: Specific bodily organs, sensations, and local modalities.
                    
                    **Totality Scoring Formula:**
                    - Grade 3 (Bold): **3.0×** weighting (confirmed by multiple provers & clinical cures)
                    - Grade 2 (Italics): **2.0×** weighting (qualified by clinical observation)
                    - Grade 1 (Roman): **1.0×** weighting (occasional prover observation)
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
                    """
                    Kent-AI integrates specialized biomedical language models fine-tuned on 15-class BIO token classification:
                    
                    - **BioLinkBERT-Base (110M)**: Pretrained on PubMed citation graphs. Evaluated at ~18ms latency with high token precision.
                    - **PubMedBERT (110M)**: Biomedical domain-specific vocabulary achieving 41.56% Recall@20 on held-out clinical cases.
                    - **4-Encoder Ensemble (414M)**: Majority voting across BioLinkBERT, PubMedBERT, Bio_ClinicalBERT, and DeBERTa-v3.
                    - **Two-Stage Hybrid**: High-recall ensemble extraction paired with LLaMA 3.1 8B contextual arbitration.
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

    # Footer Disclaimer
    st.html(
        """
        <div class="persistent-clinical-disclaimer">
            <span><b>Clinical Research Notice:</b> Kent-AI is an investigational decision-support tool. It does not provide medical diagnoses or prescriptions. Always verify repertory findings against primary homeopathic literature.</span>
        </div>
        """
    )


if __name__ == "__main__":
    main()
