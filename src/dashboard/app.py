"""Streamlit Clinical Dashboard for Kent-AI (Phase 7).

A state-of-the-art clinical interface built to Google Stitch UI/UX design standards:
- Sleek dark glassmorphic styling
- 4 comprehensive clinical workspaces (Intake Chatbot, Repertorization Engine, Rubric Explorer, Materia Medica)
- Interactive Plotly totality ranking charts
- Real-time 7-dimension symptom visualization
"""

from __future__ import annotations

import copy
import logging
import sys
import uuid
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
import src.dashboard.styles as dashboard_styles
importlib.reload(dashboard_styles)
from src.dashboard.styles import inject_custom_css

import src.dashboard.components.rubric_tree as rubric_tree_mod
importlib.reload(rubric_tree_mod)
from src.dashboard.components.rubric_tree import render_rubric_card

import src.dashboard.components.chat_viewer as chat_viewer_mod
importlib.reload(chat_viewer_mod)
from src.dashboard.components.chat_viewer import render_chat_interface, render_slot_badges

import src.dashboard.dimensions as dimensions_mod
importlib.reload(dimensions_mod)
from src.dashboard.dimensions import (
    DIMENSION_MAP,
    KENT_DIMENSIONS_ORDERED,
    get_dimension,
    get_dimension_by_code,
    get_engine_dimensions_summary,
    pluralize,
)

from src.chatbot.dialogue_manager import DialogueManager
from src.dashboard.components.chat_viewer import check_ollama_online
from src.dashboard.components.icons import get_icon
from src.data.kent_db import KentDB
from src.pipeline.orchestrator import PatientReport, PipelineOrchestrator
from src.search.embedder import RubricEmbedder
from src.search.ranker import RemedyRanker
from src.search.vector_store import RubricVectorStore

logger = logging.getLogger("dashboard")

# Set wide page layout
st.set_page_config(
    page_title="Kent-AI — Clinical Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_db() -> KentDB:
    """Cache Kent database DAL instance."""
    return KentDB()


@st.cache_resource
def get_pipeline() -> PipelineOrchestrator:
    """Cache dense vector store, embedder, and pipeline orchestrator."""
    embedder = RubricEmbedder(mock_mode=False)
    vector_store = RubricVectorStore(embedder=embedder)
    ranker = RemedyRanker()
    return PipelineOrchestrator(
        vector_store=vector_store,
        ranker=ranker,
        mock_mode=False,
    )


def initialize_session():
    """Initialize stateful consultation variables."""
    if "pipeline" not in st.session_state:
        st.session_state.pipeline = get_pipeline()
    if "dialogue_manager" not in st.session_state or not hasattr(st.session_state.dialogue_manager, "is_ollama_online"):
        st.session_state.dialogue_manager = DialogueManager(
            orchestrator=st.session_state.pipeline,
            model_name="llama3:8b",
            mock_mode=False,
        )
        st.session_state.dialogue_manager.get_greeting()
    if "current_report" not in st.session_state:
        st.session_state.current_report = None
    if "repertory_scope" not in st.session_state:
        st.session_state.repertory_scope = "MIND Chapter Focus (4,933 rubrics)"
    if "case_tray" not in st.session_state:
        st.session_state.case_tray = {"rubrics": [], "remedies": []}
    if "show_dev_details" not in st.session_state:
        st.session_state.show_dev_details = False


def render_header():
    """Render top brand navigation bar with consolidated session telemetry pill (Task 4)."""
    active_scope = st.session_state.get("repertory_scope", "MIND Chapter Focus (4,933 rubrics)")
    is_mind = "MIND" in active_scope
    short_scope = "MIND (4.9k)" if is_mind else "All Chapters (74k)"
    
    dm = st.session_state.get("dialogue_manager")
    is_llm_online = dm.is_ollama_online() if (dm and hasattr(dm, "is_ollama_online")) else check_ollama_online()
    engine_desc = "llama3:8b (Online)" if is_llm_online else "Offline (Rule-based Fallback)"
    
    tooltip_text = (
        f"Active Scope: {active_scope}&#10;"
        f"Inference Engine: {engine_desc}&#10;"
        "Kent Knowledge Base: 74,513 rubrics across 37 chapters&#10;"
        "Single source of truth configured in sidebar."
    )
    
    st.html(
        f"""
        <div class="brand-header">
            <div class="brand-left">
                <div class="brand-icon-box">
                    {get_icon('psychology', size=26, color='#10B981')}
                </div>
                <div>
                    <div class="brand-title">Kent-AI Clinical Assistant</div>
                    <div class="brand-subtitle">Classical Homeopathic Repertorization & Decision Support</div>
                </div>
            </div>
            <div class="brand-pills">
                <div class="session-badge-wrapper" title="{tooltip_text}">
                    <span class="status-pill status-pill-focus session-compact-pill">
                        <span class="status-dot"></span>
                        {get_icon('psychology' if is_mind else 'database', size=14, color='#10B981' if is_mind else '#06B6D4')}
                        <span>Session: <b>{short_scope}</b></span>
                        <span class="session-pill-tooltip-trigger" style="margin-left: 4px; font-size: 11px; opacity: 0.85;">ⓘ</span>
                    </span>
                    <div class="session-popover-content">
                        <div style="font-weight: 700; color: #10B981; margin-bottom: 6px; font-size: 13px; display: flex; align-items: center; gap: 6px;">
                            {get_icon('sensors', size=14, color='#10B981')} Session Details
                        </div>
                        <div style="margin-bottom: 4px; color: #D1D5DB; font-size: 12px;">• <b>Active Scope:</b> {active_scope}</div>
                        <div style="margin-bottom: 4px; color: {'#10B981' if is_llm_online else '#F59E0B'}; font-size: 12px;">• <b>Engine:</b> {engine_desc}</div>
                        <div style="margin-bottom: 6px; color: #D1D5DB; font-size: 12px;">• <b>Knowledge Base:</b> 74,513 rubrics (37 Chapters)</div>
                        <div style="font-size: 11px; color: #9CA3AF; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 5px; margin-top: 6px;">
                            Configured via sidebar scope control.
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    )


def render_dimensions_grid(dims: Dict[str, Any], report: Optional[PatientReport] = None):
    """Render 7-dimension clinical findings in clean cards with why provenance affordances."""
    col1, col2, col3, col4 = st.columns(4)

    prov_hint = "Extracted from clinical dialogue and mapped to Kent totality dimensions"
    if report and report.matched_rubrics:
        top_cand = report.matched_rubrics[0]
        cand_path = top_cand.get("path") or top_cand.get("name") or "Repertory rubric"
        prov_hint = f"Matched rubric: {cand_path} (Totality Ranker)"

    def format_badge(val: str, badge_cls: str, dim_code: str, dim_label: str) -> str:
        return (
            f'<span class="badge {badge_cls}" title="Dimension: {dim_label} ({dim_code}) | Entity: {val}&#10;Provenance: {prov_hint}">'
            f'{val} <span class="badge-why-hint" title="Provenance: {prov_hint}">why?</span></span>'
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
        locs = dims.get("location", [])
        st.html("".join(format_badge(l, d_loc.badge_class, d_loc.code, d_loc.label) for l in locs) if locs else "<span style='color:#8492A6; font-size:13px;'>None</span>")

        st.markdown(f"**{d_sen.label} ({d_sen.code}):**")
        sens = dims.get("sensation", [])
        st.html("".join(format_badge(s, d_sen.badge_class, d_sen.code, d_sen.label) for s in sens) if sens else "<span style='color:#8492A6; font-size:13px;'>None</span>")

    with col2:
        st.markdown(f"**{d_agg.label} ({d_agg.code}):**")
        aggs = dims.get("modality_agg", [])
        st.html("".join(format_badge(a, d_agg.badge_class, d_agg.code, d_agg.label) for a in aggs) if aggs else "<span style='color:#8492A6; font-size:13px;'>None</span>")

        st.markdown(f"**{d_amel.label} ({d_amel.code}):**")
        amels = dims.get("modality_amel", [])
        st.html("".join(format_badge(a, d_amel.badge_class, d_amel.code, d_amel.label) for a in amels) if amels else "<span style='color:#8492A6; font-size:13px;'>None</span>")

    with col3:
        st.markdown(f"**{d_temp.label} ({d_temp.code}):**")
        temps = dims.get("temporal", [])
        st.html("".join(format_badge(t, d_temp.badge_class, d_temp.code, d_temp.label) for t in temps) if temps else "<span style='color:#8492A6; font-size:13px;'>None</span>")

        st.markdown(f"**{d_conc.label} ({d_conc.code}):**")
        concs = dims.get("concomitant", [])
        st.html("".join(format_badge(c, d_conc.badge_class, d_conc.code, d_conc.label) for c in concs) if concs else "<span style='color:#8492A6; font-size:13px;'>None</span>")

    with col4:
        st.markdown(f"**{d_ment.label} ({d_ment.code}):**")
        ments = dims.get("mental", [])
        st.html("".join(format_badge(m, d_ment.badge_class, d_ment.code, d_ment.label) for m in ments) if ments else "<span style='color:#8492A6; font-size:13px;'>None</span>")

        st.markdown("**Negated / Denied:**")
        negs = dims.get("negated", [])
        st.html("".join(format_badge(n, "badge-neg", "NEG", "Negated") for n in negs) if negs else "<span style='color:#8492A6; font-size:13px;'>None</span>")



def render_repertorization_chart(remedies: List[Dict[str, Any]]):
    """Render interactive Plotly horizontal bar chart of totality scores."""
    if not remedies:
        st.info("No remedies match the specified totality threshold.")
        return

    top_remedies = remedies[:12]
    df = pd.DataFrame(top_remedies)
    
    # Sort ascending for horizontal bar chart (top remedy at the top)
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
        title="<b>Remedy Totality Ranking (Grade-Weighted Score)</b>",
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
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_totality_matrix(report: PatientReport, db: KentDB) -> None:
    """Render classical Kentian totality matrix grid with remedies vs rubrics."""
    remedies = report.ranked_remedies[:10]
    rubrics = report.matched_rubrics
    if not remedies or not rubrics:
        return

    # Pre-fetch remedies for each rubric to know grades
    rubric_remedy_map: Dict[int, Dict[str, int]] = {}
    for r in rubrics:
        raw_id = r.get("rubric_id") if r.get("rubric_id") is not None else r.get("id")
        if raw_id is None:
            continue
        try:
            r_id = int(str(raw_id).replace("rubric_", "").strip())
        except (ValueError, TypeError):
            continue
        entries = db.get_remedies(r_id)
        rubric_remedy_map[r_id] = {
            (e.get("abbreviation") or "").rstrip(".").lower(): e.get("grade", 1)
            for e in entries
        }

    # Build HTML table
    headers_html = "<th>Rank</th><th>Remedy</th><th>Score</th><th>Coverage</th>"
    for idx, r in enumerate(rubrics, start=1):
        full_p = r.get("path") or ""
        short_label = full_p.split(">")[-1].strip()
        if len(short_label) > 22:
            short_label = short_label[:20] + "..."
        matched_query = r.get("query") or r.get("matched_symptom") or ""
        if len(matched_query) > 20:
            matched_query = matched_query[:18] + ".."
        query_sub = f"<div style='font-size: 10px; color: #10B981; font-weight: normal; margin-top: 2px;' title='Matched finding: {r.get('query', '')}'>↳ {matched_query}</div>" if matched_query else ""
        headers_html += f"<th title='{full_p}&#10;Matched finding: {r.get('query', short_label)}' style='font-size: 11.5px;'>R{idx}: {short_label}{query_sub}</th>"

    rows_html = []
    for rank, rem in enumerate(remedies, start=1):
        abbr = rem.get("abbreviation", "")
        name = rem.get("full_name", abbr)
        score = rem.get("score", 0.0)
        cov = f"{rem.get('rubric_count', 0)}/{len(rubrics)}"
        clean_abbr = abbr.rstrip(".").lower()

        row_tds = [
            f"<td><b>#{rank}</b></td>",
            f"<td><span style='color: #10B981; font-weight:700;'>{abbr}</span> <span style='font-size:11px; color:#9CA3AF;'>({name})</span></td>",
            f"<td><b>{score:.2f}</b></td>",
            f"<td><span class='status-pill' style='font-size:11px; padding:2px 8px;'>{cov}</span></td>",
        ]

        for r in rubrics:
            raw_id = r.get("rubric_id") if r.get("rubric_id") is not None else r.get("id")
            try:
                r_id = int(str(raw_id).replace("rubric_", "").strip()) if raw_id is not None else -1
            except (ValueError, TypeError):
                r_id = -1
            grade = rubric_remedy_map.get(r_id, {}).get(clean_abbr)
            if grade == 3:
                row_tds.append("<td><span class='grade-3'>3</span></td>")
            elif grade == 2:
                row_tds.append("<td><span class='grade-2'>2</span></td>")
            elif grade == 1:
                row_tds.append("<td><span class='grade-1'>1</span></td>")
            else:
                row_tds.append("<td style='color: #4B5563; text-align:center;'>·</td>")

        rows_html.append(f"<tr>{''.join(row_tds)}</tr>")

    table_html = f"""
    <div style='overflow-x: auto; margin-top: 10px; margin-bottom: 12px;'>
        <table class='repertory-grid'>
            <thead>
                <tr>{headers_html}</tr>
            </thead>
            <tbody>
                {''.join(rows_html)}
            </tbody>
        </table>
    </div>
    <div style='font-size: 12px; color: #9CA3AF; margin-top: 4px; font-style: italic;'>
        <b>Clinical Note:</b> Decision-support analysis based on Dr. Kent's Repertory; does not constitute a clinical prescription or medical diagnosis.
    </div>
    """
    st.html(table_html)


def render_report_view(report: PatientReport, db: KentDB):
    """Render comprehensive clinical repertorization report."""
    st.html('<div class="stGlassCard">')
    col_rep_head, col_rep_dl = st.columns([3, 1])
    with col_rep_head:
        st.html(
        f"""
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                {get_icon('clinical_notes', size=24, color='#10B981')}
                <h3 style="margin: 0;">Case Analysis Report — <code>{report.patient_id}</code></h3>
            </div>
            """
    )
        st.markdown(f"> *\"{report.transcript}\"*")
    with col_rep_dl:
        st.download_button(
            "Export Report (MD)",
            data=report.to_markdown(),
            file_name=f"{report.patient_id}_repertorization.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.download_button(
            "Export Data (JSON)",
            data=report.to_json(),
            file_name=f"{report.patient_id}_data.json",
            mime="application/json",
            use_container_width=True,
        )
    st.markdown("---")
    
    st.html(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin: 12px 0 8px 0;">
            {get_icon('account_tree', size=20, color='#06B6D4')}
            <h4 style="margin: 0;">1. 7-Dimension Clinical Parsing</h4>
        </div>
        """
    )
    render_dimensions_grid(report.dimensions, report=report)
    st.html('</div>')

    remedies = report.ranked_remedies
    if remedies:
        top_rem = remedies[0]
        st.html(
        f"""
            <div class="hero-simillimum">
                <div style="font-size: 13px; text-transform: uppercase; color: #34D399; font-weight: 700; letter-spacing: 0.05em; display: flex; align-items: center; gap: 6px;">
                    {get_icon('verified', size=16, color='#34D399')}
                    <span>Primary Simillimum Indication</span>
                </div>
                <div style="font-size: 26px; font-weight: 800; color: #FFFFFF; margin: 6px 0;">
                    {top_rem.get('full_name')} <span style="color: #34D399; font-size: 20px;">({top_rem.get('abbreviation')})</span>
                </div>
                <div style="font-size: 14px; color: #D1D5DB;">
                    Covering <b>{top_rem.get('rubric_count')} of {len(report.matched_rubrics)}</b> symptom rubrics ({top_rem.get('coverage_ratio', 0)*100:.0f}% coverage) with a weighted totality score of <b>{top_rem.get('score')}</b>.
                </div>
            </div>
            """
    )

        col1, col2 = st.columns([3, 2])
        with col1:
            st.html(
        f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    {get_icon('bar_chart', size=20, color='#10B981')}
                    <h4 style="margin: 0;">2. Remedy Totality Ranking</h4>
                </div>
                """
    )
            render_repertorization_chart(remedies)
        with col2:
            st.html(
        f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    {get_icon('table_chart', size=20, color='#A78BFA')}
                    <h4 style="margin: 0;">3. Top Remedy Breakdown</h4>
                </div>
                """
    )
            table_data = []
            for idx, r in enumerate(remedies[:8], start=1):
                table_data.append({
                    "Rank": idx,
                    "Remedy": r.get("abbreviation"),
                    "Full Name": r.get("full_name"),
                    "Score": r.get("score"),
                    "Rubrics": f"{r.get('rubric_count')}/{len(report.matched_rubrics)}",
                })
            st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

        st.html(
        f"""
            <div style="display: flex; align-items: center; gap: 8px; margin: 16px 0 8px 0;">
                {get_icon('grid_on', size=20, color='#FBBF24')}
                <h4 style="margin: 0;">4. Classical Repertorization Totality Matrix (Remedies × Rubrics)</h4>
            </div>
            """
    )
        render_totality_matrix(report, db)

    st.html(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin: 16px 0 8px 0;">
            {get_icon('format_list_bulleted', size=20, color='#34D399')}
            <h4 style="margin: 0;">5. Matched Kent Repertory Rubrics</h4>
        </div>
        """
    )
    for r in report.matched_rubrics:
        render_rubric_card(r, db)



def render_sidebar_case_tray():
    """Render persistent Current Case tray in sidebar (Phase 6)."""
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

    dm = st.session_state.get("dialogue_manager")
    intake_items = []
    if dm and hasattr(dm, "extracted_slots"):
        for slot_key, slot_vals in dm.extracted_slots.items():
            if slot_vals:
                intake_items.append((slot_key, ", ".join(slot_vals)))

    if intake_items:
        with st.expander(f"Intake Dimensions ({pluralize(len(intake_items), 'dimension', 'dimensions')})", expanded=False):
            for skey, svals in intake_items:
                st.markdown(f"<div style='font-size: 11px; margin-bottom: 2px;'><b style='color:#10B981;'>{skey}:</b> <span style='color:#E5E7EB;'>{svals}</span></div>", unsafe_allow_html=True)

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
                st.markdown(f"<span style='font-size: 11.5px; color: #E5E7EB;'>• {r_name}</span>", unsafe_allow_html=True)
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
                st.markdown(f"<span style='font-size: 11.5px; color: #34D399;'>• {rem_name} ({rem_abbr})</span>", unsafe_allow_html=True)
            with col_rem_del:
                if st.button("✕", key=f"del_tray_rem_{idx}", help="Remove remedy from case"):
                    tray["remedies"].pop(idx)
                    st.rerun()

    col_btn1, col_btn2 = st.columns([3, 2])
    with col_btn1:
        if rubrics and st.button("Repertorize This Case", type="primary", use_container_width=True, key="tray_repertorize_btn"):
            pipeline = get_pipeline()
            db = get_db()
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
            st.toast("Case repertorized! Report displayed below in intake tab.")
            st.rerun()
    with col_btn2:
        if st.button("Clear Tray", key="clear_all_tray", use_container_width=True):
            st.session_state.case_tray = {"rubrics": [], "remedies": []}
            st.rerun()



def render_sidebar():
    """Render Google Stitch clinical telemetry and quick-case loader."""
    with st.sidebar:
        st.html(
        f"""
            <div style='text-align: center; margin-bottom: 20px;'>
                <div style='margin-bottom: 8px; display: inline-flex; justify-content: center; align-items: center; width: 64px; height: 64px; border-radius: 16px; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3);'>
                    {get_icon('local_florist', size=38, color='#10B981')}
                </div>
                <div style='font-size: 18px; font-weight: 800; color: #10B981;'>Kent-AI Clinical Suite</div>
                <div style='font-size: 11px; color: #9CA3AF;'>Classical Homeopathy + Generative AI</div>
            </div>
            """
    )

        with st.expander("Dr. Kent's Principle on Mental Symptoms", expanded=False):
            st.markdown(
                '<div style="font-size: 12.5px; color: #D1D5DB; line-height: 1.5; font-style: italic;">'
                '“The mental symptoms are the most important, for they express the very man himself.”'
                '<div style="font-weight: 700; color: #10B981; margin-top: 4px; font-style: normal;">— Dr. J. T. Kent</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        st.html(
            f"""
            <div style='display: flex; align-items: center; gap: 6px; margin: 12px 0 6px 0;'>
                {get_icon('tune', size=16, color='#10B981')}
                <span style='font-size: 14px; font-weight: 700; color: #F9FAFB;'>Repertory Scope Selection</span>
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

        # Warn if switching scope mid-consultation
        dm_inst = st.session_state.get("dialogue_manager")
        if dm_inst and len(dm_inst.history) > 2 and "All" in new_scope and "prev_scope_is_mind" not in st.session_state:
            st.session_state.prev_scope_is_mind = True
            st.warning("⚠️ Scope switched to All 37 Chapters mid-intake. Analysis will retrieve across all 74k rubrics.")

        # Developer Details Toggle
        st.markdown("---")
        st.toggle(
            "Developer details",
            value=st.session_state.get("show_dev_details", False),
            key="show_dev_details",
            help="Toggle low-level model architecture, rubric IDs, and system telemetry.",
        )

        if st.session_state.get("show_dev_details", False):
            st.html(
                f"""
                <div style='display: flex; align-items: center; gap: 6px; margin: 10px 0 8px 0;'>
                    {get_icon('sensors', size=16, color='#06B6D4')}
                    <span style='font-size: 14px; font-weight: 700; color: #F9FAFB;'>System Telemetry</span>
                </div>
                """
            )
            st.html(
                """
                <div class="stitch-metric" style="margin-bottom: 8px;">
                    <div class="stitch-metric-val">llama3:8b</div>
                    <div class="stitch-metric-lbl">Inference LLM (Ollama)</div>
                </div>
                <div class="stitch-metric" style="margin-bottom: 8px; border-color: rgba(16, 185, 129, 0.4);">
                    <div class="stitch-metric-val" style="color: #10B981;">4,933</div>
                    <div class="stitch-metric-lbl">Active Chapter Rubrics (MIND)</div>
                </div>
                <div class="stitch-metric" style="margin-bottom: 12px;">
                    <div class="stitch-metric-val">74,513</div>
                    <div class="stitch-metric-lbl">Full Repertory DB (37 Ch.)</div>
                </div>
                """
            )

        # Phase 6: Persistent Case Tray in Sidebar
        render_sidebar_case_tray()

        st.markdown("---")
        st.html(
        f"""
            <div style='display: flex; align-items: center; gap: 6px; margin: 12px 0 8px 0;'>
                {get_icon('scale', size=18, color='#FBBF24')}
                <span style='font-size: 15px; font-weight: 700; color: #F9FAFB;'>Totality Weights (Kentian)</span>
            </div>
            """
    )
        st.html(
        """
            <div style='font-size: 12px; color: #D1D5DB; line-height: 1.8;'>
                • <span class='grade-3'>Grade 3</span> : <b>3.0×</b> (Confirmed / Bold)<br>
                • <span class='grade-2'>Grade 2</span> : <b>2.0×</b> (Qualified / Italic)<br>
                • <span class='grade-1'>Grade 1</span> : <b>1.0×</b> (Plain / Roman)<br>
                • <i>Specificity</i> : Inverse rubric frequency
            </div>
            """
    )

        st.markdown("---")
        st.html(
        """
            <div style='font-size: 11px; color: #6B7280; text-align: justify;'>
                <b>Investigational Tool:</b> Kent-AI is an academic clinical decision-support and repertorization research system. It does not replace qualified homeopathic or medical evaluation.
            </div>
            """
    )


def main():
    inject_custom_css()
    initialize_session()
    render_sidebar()
    render_header()

    db = get_db()
    pipeline = st.session_state.pipeline
    dm: DialogueManager = st.session_state.dialogue_manager

    tab1, tab2, tab3, tab4 = st.tabs([
        "Live Patient Intake",
        "Repertorization Engine",
        "Rubric Explorer",
        "Materia Medica Index",
    ])

    # =========================================================================
    # TAB 1: Live Patient Consultation (Chatbot)
    # =========================================================================
    with tab1:
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

                # Phase 2 item 7: Live Case Summary in right panel
                st.markdown("<div style='font-size: 13px; font-weight: 700; color: #D1D5DB; margin-bottom: 6px;'>Active Case Summary:</div>", unsafe_allow_html=True)
                active_scope = st.session_state.get("repertory_scope", "MIND Chapter Focus (4,933 rubrics)")
                is_mind = "MIND" in active_scope

                # Count filled slots from canonical dimension map
                filled_items = []
                for dim in KENT_DIMENSIONS_ORDERED:
                    vals = dm.extracted_slots.get(dim.key, [])
                    if vals:
                        filled_items.append((dim.label, ", ".join(vals), dim.badge_class, dim.tooltip))

                if filled_items:
                    for d_label, d_val, b_cls, d_tip in filled_items:
                        st.markdown(f"<div style='font-size: 12px; margin-bottom: 4px;' title='{d_tip}'><span class='badge {b_cls}' style='font-size:11px; padding:2px 6px;'>{d_label}</span> <span style='color:#F9FAFB;'>{d_val}</span></div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='font-size: 12px; color: #8492A6; margin-bottom: 8px; font-style: italic;'>No symptoms captured yet. Converse in the dialogue console to extract dimensions.</div>", unsafe_allow_html=True)

                st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)

                # Phase 2 item 3: Disable button until minimum data exists (complaint + at least 1 modality)
                has_complaint = bool(dm.extracted_slots.get("location")) or bool(dm.extracted_slots.get("sensation")) or bool(dm.extracted_slots.get("mental")) or (len(dm.history) >= 3)
                has_modality = bool(dm.extracted_slots.get("modality_agg")) or bool(dm.extracted_slots.get("modality_amel"))
                can_generate = has_complaint and has_modality
                collected_count = len(filled_items)

                button_label = f"Generate Repertorization ({collected_count}/7)"
                if can_generate:
                    if st.button(button_label, type="primary", use_container_width=True):
                        transcript = dm.get_full_transcript()
                        if transcript.strip():
                            with st.spinner("Analyzing totality and ranking remedies..."):
                                sec_filter = 1 if is_mind else None
                                report = pipeline.process_transcript(transcript, section_id=sec_filter)
                                st.session_state.current_report = report
                            st.success("Repertorization complete! Scroll down to view report.")
                        else:
                            st.warning("Please chat with Kent-AI first before generating report.")
                else:
                    st.button(button_label, type="primary", disabled=True, use_container_width=True, help="Requires at least a primary complaint and one modality before generating repertorization.")
                    st.markdown(f"<div style='font-size: 11.5px; color: #9CA3AF; margin-top: 4px;'>Requires primary complaint + at least one modality ({collected_count}/7 collected).</div>", unsafe_allow_html=True)

                st.markdown("---")

                # Phase 2 item 4: Reset Consultation as quiet action with confirmation
                if st.session_state.get("confirm_intake_reset", False):
                    st.warning("Clear all intake symptoms?")
                    col_cf1, col_cf2 = st.columns(2)
                    with col_cf1:
                        if st.button("Yes, Clear", type="primary", use_container_width=True, key="confirm_reset_yes"):
                            dm.reset()
                            dm.get_greeting()
                            st.session_state.current_report = None
                            st.session_state.confirm_intake_reset = False
                            st.toast("Consultation reset.")
                            st.rerun()
                    with col_cf2:
                        if st.button("Cancel", use_container_width=True, key="confirm_reset_no"):
                            st.session_state.confirm_intake_reset = False
                            st.rerun()
                else:
                    if st.button("Reset Consultation", type="secondary", use_container_width=True):
                        st.session_state.confirm_intake_reset = True
                        st.rerun()

                st.markdown("---")

                # Phase 2 item 7: Move Kentian Intake Guidance into a '?' popover
                with st.popover("Intake Guidance (?)"):
                    st.markdown(
                        "<div style='font-size: 12.5px; color: #D1D5DB; line-height: 1.5;'>"
                        "<b>Kentian Intake Guidance:</b><br>"
                        "Prioritize mental & emotional generals (anxiety, fears, grief, restlessness) "
                        "alongside physical modalities (aggravation/amelioration times, temperatures, weather)."
                        "</div>",
                        unsafe_allow_html=True,
                    )

        with col_chat:
            render_chat_interface(dm)

        # If report generated from chat, display it below
        if st.session_state.current_report:
            st.markdown("---")
            render_report_view(st.session_state.current_report, db)

    # =========================================================================
    # TAB 2: Direct Clinical Repertorization Engine
    # =========================================================================
    with tab2:
        with st.container(border=True):
            st.html(
                f"""
                <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px;'>
                    {get_icon('psychology', size=22, color='#10B981')}
                    <h3 style='margin: 0;'>Clinical Repertorization Engine</h3>
                </div>
                """
            )
            st.markdown(
                f"Input patient clinical narrative to extract Dr. Kent's **7 clinical dimensions** "
                f"({get_engine_dimensions_summary()}), retrieve matching rubrics, and compute totality."
            )

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
                placeholder="Describe patient symptoms in free text (e.g., 'Anxious and depressed every morning, worse when alone. Thoughts race with fear and dread. No fever, no nausea.')...",
                height=120,
            )

            with st.expander("Advanced Settings", expanded=False):
                col_opt1, col_opt2, col_opt3 = st.columns([1, 1, 1])
                with col_opt1:
                    top_k_rubrics = st.slider("Matches per symptom:", 1, 5, 3, help="Candidate rubrics to retrieve per extracted symptom dimension")
                with col_opt2:
                    top_remedies_count = st.slider("Remedies to show:", 5, 20, 10, help="Number of ranked homeopathic remedies to show in totality grid")
                with col_opt3:
                    sections = db.get_sections()
                    mind_opt = "1: MIND (4,933 rubrics - Focus Chapter)"
                    all_opt = "All Chapters (74,513 rubrics)"
                    sec_options = [mind_opt, all_opt] + [f"{s['id']}: {s['name']}" for s in sections if s['id'] != 1]
                    section_choice = st.selectbox("Filter Chapter:", sec_options, index=0)
                    sec_id = 1
                    if section_choice == all_opt:
                        sec_id = None
                    elif ":" in section_choice:
                        sec_id = int(section_choice.split(":")[0])

            has_narrative = bool(user_case_text and user_case_text.strip())
            run_btn = st.button(
                "Analyze & Repertorize Case",
                type="primary",
                disabled=not has_narrative,
                use_container_width=True,
                help="Input clinical narrative above to analyze and repertorize." if not has_narrative else "Extract 7 dimensions and compute totality ranking.",
            )

        if run_btn and user_case_text.strip():
            with st.spinner("Extracting 7-dimensions via LLaMA 3, retrieving rubrics from ChromaDB, and computing totality..."):
                report = pipeline.process_transcript(
                    transcript=user_case_text,
                    top_rubrics_per_query=top_k_rubrics,
                    top_remedies=top_remedies_count,
                    section_id=sec_id,
                )
                st.session_state.tab2_report = report
                st.session_state.tab2_active_dims = copy.deepcopy(report.dimensions)

        # If report generated in Tab 2, display extracted symptom chips and repertorization report
        active_t2_report = st.session_state.get("tab2_report")
        if active_t2_report:
            st.markdown("---")
            with st.container(border=True):
                st.html(
                    f"""
                    <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;'>
                        <div style='display: flex; align-items: center; gap: 8px;'>
                            {get_icon('filter_alt', size=18, color='#10B981')}
                            <h4 style='margin: 0;'>Extracted Clinical Symptoms & Modalities (Active Filter)</h4>
                        </div>
                        <span style='font-size: 11.5px; color: #9CA3AF;'>Filter symptoms before totality ranking</span>
                    </div>
                    """
                )

                dims = st.session_state.get("tab2_active_dims", active_t2_report.dimensions)
                dim_cols = st.columns(4)
                active_symptoms_list = []

                with dim_cols[0]:
                    st.markdown(f"**{DIMENSION_MAP['location'].label} & {DIMENSION_MAP['sensation'].label}:**")
                    locs = dims.get("location", []) + dims.get("sensation", [])
                    for i, item in enumerate(locs):
                        c = st.checkbox(item, value=True, key=f"t2_symptom_{i}_{item}")
                        if c:
                            active_symptoms_list.append(item)
                    if not locs:
                        st.caption("None identified")

                with dim_cols[1]:
                    st.markdown(f"**Modalities ({DIMENSION_MAP['modality_agg'].label} / {DIMENSION_MAP['modality_amel'].label}):**")
                    mods = [f"worse: {m}" for m in dims.get("modality_agg", [])] + [f"better: {m}" for m in dims.get("modality_amel", [])]
                    for i, item in enumerate(mods):
                        c = st.checkbox(item, value=True, key=f"t2_mod_{i}_{item}")
                        if c:
                            active_symptoms_list.append(item)
                    if not mods:
                        st.caption("None identified")

                with dim_cols[2]:
                    st.markdown(f"**{DIMENSION_MAP['mental'].label} & {DIMENSION_MAP['temporal'].label}:**")
                    ments = dims.get("mental", []) + dims.get("temporal", [])
                    for i, item in enumerate(ments):
                        c = st.checkbox(item, value=True, key=f"t2_ment_{i}_{item}")
                        if c:
                            active_symptoms_list.append(item)
                    if not ments:
                        st.caption("None identified")

                with dim_cols[3]:
                    st.markdown("**Negated / Excluded:**")
                    negs = dims.get("negated", [])
                    for item in negs:
                        st.markdown(f"<span class='badge badge-neg'>{item}</span>", unsafe_allow_html=True)
                    if not negs:
                        st.caption("None")

                col_re_btn, col_re_note = st.columns([1.5, 3])
                with col_re_btn:
                    if st.button("Re-run Repertorization", type="secondary", use_container_width=True, help="Re-run totality ranking with active selected symptoms"):
                        if active_symptoms_list:
                            mod_transcript = ". ".join(active_symptoms_list)
                            with st.spinner("Re-evaluating totality with modified symptoms..."):
                                new_report = pipeline.process_transcript(
                                    transcript=mod_transcript,
                                    top_rubrics_per_query=top_k_rubrics if 'top_k_rubrics' in locals() else 3,
                                    top_remedies=top_remedies_count if 'top_remedies_count' in locals() else 10,
                                    section_id=sec_id if 'sec_id' in locals() else 1,
                                )
                                st.session_state.tab2_report = new_report
                                st.toast("Totality updated with modified symptoms.")
                                st.rerun()

            render_report_view(active_t2_report, db)

    # =========================================================================
    # TAB 3: Kent's MIND Rubric Explorer (4,933 Rubrics)
    # =========================================================================
    with tab3:
        with st.container(border=True):
            st.html(
                f"""
                <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px;'>
                    {get_icon('psychology', size=22, color='#10B981')}
                    <h3 style='margin: 0;'>Kent's MIND Repertory & Rubric Search</h3>
                </div>
                """
            )
            st.markdown("Explore **4,933 digitized MIND rubrics** using meaning-based semantic search or exact words.")

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

            col_filt1, col_filt2 = st.columns(2)
            with col_filt1:
                show_weak = st.checkbox("Show weaker matches (< 0.52 similarity)", value=False)
            with col_filt2:
                hide_empty = st.checkbox("Hide rubrics with 0 remedies", value=True)

            search_clicked = st.button("Search Rubrics", type="primary", use_container_width=True)

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

            # Filter out weaker matches if toggled off (recalibrated to 0.52)
            filtered_results = raw_results
            if not show_weak and search_mode == "Meaning-based":
                filtered_results = [r for r in filtered_results if r.get("similarity", 1.0) >= 0.52]

            # Filter empty rubrics
            if hide_empty:
                filtered_results = [r for r in filtered_results if r.get("remedy_count", 0) > 0]

            # Sort
            if "Remedy Count" in sort_by:
                filtered_results = sorted(filtered_results, key=lambda r: r.get("remedy_count", 0), reverse=True)

            display_results = filtered_results[:limit]

            if display_results:
                st.markdown(f"Displaying **{len(display_results)}** {pluralize(len(display_results), 'matching rubric', 'matching rubrics', include_count=False)}:")
                for r in display_results:
                    render_rubric_card(r, db, query=search_query)
            else:
                st.info("No rubrics matched the specified search and filter criteria.")

    # =========================================================================
    # TAB 4: Materia Medica & Remedy Index
    # =========================================================================
    with tab4:
        with st.container(border=True):
            st.html(
                f"""
                <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px;'>
                    {get_icon('medication', size=22, color='#10B981')}
                    <h3 style='margin: 0;'>Homeopathic Remedy Dictionary & MIND Keynotes</h3>
                </div>
                """
            )
            st.markdown("Browse cataloged remedies in Kent's Repertory with full Latin names, abbreviations, and characteristic Grade 3 keynotes.")

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
                if st.button("✕ Clear", help="Clear remedy search filter", use_container_width=True):
                    st.session_state.rem_filter_text = ""
                    st.session_state.rem_input_widget = ""
                    st.rerun()
            with col_rem_toggle:
                prioritize_mind = st.checkbox(
                    "Prioritize MIND Keynotes",
                    value=True,
                    help="Sort characteristic Grade 3 symptoms so that mental & emotional rubrics appear first in the keynote list.",
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
                    r_id, abbr, name, norm = row["id"], row["abbreviation"], row["full_name"], row["normalized"]
                    total_count, mind_count = row["total_rubrics"], row["mind_rubrics"]

                    show_dev = st.session_state.get("show_dev_details", False)
                    dev_norm = f"<span class='rubric-dev-id'>Std: {norm or abbr}</span>" if show_dev else ""

                    card_title = f"{name or abbr} ({abbr})  ·  {pluralize(mind_count, 'rubric', 'rubrics')} in MIND  ·  {pluralize(total_count, 'rubric', 'rubrics')} across all chapters"

                    with st.expander(card_title, expanded=False):
                        col_reminfo, col_remact = st.columns(2)
                        with col_reminfo:
                            st.html(
                                f"""
                                <div style="margin-bottom: 8px;">
                                    <div style="font-size: 18px; font-weight: 800; color: #FFFFFF;">
                                        {name or abbr} <span style="color: #34D399; font-weight: 700;">({abbr})</span>
                                        {dev_norm}
                                    </div>
                                    <div style="font-size: 12.5px; color: #9CA3AF; margin-top: 4px;">
                                        <span class="status-pill" style="color: #10B981;" title="Present in {pluralize(mind_count, 'rubric', 'rubrics')} of Chapter 1 (MIND)"><b>{mind_count}</b> in MIND</span>
                                        <span class="status-pill" style="margin-left: 6px;" title="Present in {pluralize(total_count, 'rubric', 'rubrics')} across all 37 chapters of Kent Repertory"><b>{total_count:,}</b> across all chapters</span>
                                    </div>
                                </div>
                                """
                            )
                        with col_remact:
                            tray = st.session_state.get("case_tray", {"rubrics": [], "remedies": []})
                            is_in_tray = any(item.get("id") == r_id for item in tray.get("remedies", []))
                            rem_btn_key = f"tray_add_rem_{r_id}"
                            if is_in_tray:
                                st.button("✓ Added to Case", key=rem_btn_key, disabled=True, use_container_width=True)
                            else:
                                if st.button("+ Add to case", key=rem_btn_key, use_container_width=True):
                                    if "case_tray" not in st.session_state:
                                        st.session_state.case_tray = {"rubrics": [], "remedies": []}
                                    st.session_state.case_tray["remedies"].append({
                                        "id": r_id,
                                        "abbreviation": abbr,
                                        "full_name": name or abbr,
                                        "mind_rubrics": mind_count,
                                        "total_rubrics": total_count,
                                    })
                                    st.toast(f"Added {abbr} to case tray.")
                                    st.rerun()

                        # Characteristic Grade 3 Keynotes inside the single card
                        keynotes = db.get_remedy_rubrics(r_id, min_grade=3, limit=16)
                        if not keynotes:
                            st.write("No Grade 3 keynote rubrics cataloged for this remedy.")
                        else:
                            if prioritize_mind:
                                keynotes = sorted(
                                    keynotes,
                                    key=lambda kn: (0 if (kn.get("section_name") == "MIND" or str(kn["path"]).startswith("MIND")) else 1)
                                )
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

    # =========================================================================
    # TASK 7: Short One-Line High-Contrast Clinical Disclaimer Footer
    # =========================================================================
    st.html(
        """
        <div class="persistent-clinical-disclaimer">
            <span><b>Clinical Research Notice:</b> Kent-AI is an investigational decision-support tool. It does not provide medical diagnoses or prescriptions. Always verify repertory findings against primary homeopathic literature.</span>
        </div>
        """
    )


if __name__ == "__main__":
    main()
