"""Streamlit Clinical Dashboard for Kent-AI (Phase 7).

A state-of-the-art clinical interface built to Google Stitch UI/UX design standards:
- Sleek dark glassmorphic styling
- 4 comprehensive clinical workspaces (Intake Chatbot, Repertorization Engine, Rubric Explorer, Materia Medica)
- Interactive Plotly totality ranking charts
- Real-time 7-dimension symptom visualization
"""

from __future__ import annotations

import logging
import sys
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

from src.chatbot.dialogue_manager import DialogueManager
from src.dashboard.components.chat_viewer import render_chat_interface, render_slot_badges
from src.dashboard.components.icons import get_icon
from src.dashboard.components.rubric_tree import render_rubric_card
from src.dashboard.styles import inject_custom_css
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
    if "dialogue_manager" not in st.session_state:
        st.session_state.dialogue_manager = DialogueManager(
            orchestrator=st.session_state.pipeline,
            model_name="llama3:8b",
            mock_mode=False,
        )
        st.session_state.dialogue_manager.get_greeting()
    if "current_report" not in st.session_state:
        st.session_state.current_report = None


def render_header():
    """Render top brand navigation bar with glowing clinical indicators."""
    st.markdown(
        f"""
        <div class="brand-header">
            <div class="brand-left">
                <div class="brand-icon-box">
                    {get_icon('local_florist', size=26, color='#10B981')}
                </div>
                <div>
                    <div class="brand-title">Kent-AI Clinical Assistant</div>
                    <div class="brand-subtitle">Classical Homeopathic Repertorization & AI Intake</div>
                </div>
            </div>
            <div class="brand-pills">
                <span class="status-pill">
                    <span class="status-dot"></span>
                    {get_icon('memory', size=14, color='#10B981')}
                    <span>LLM: llama3:8b</span>
                </span>
                <span class="status-pill status-pill-info">
                    <span class="status-dot status-dot-cyan"></span>
                    {get_icon('database', size=14, color='#06B6D4')}
                    <span>Vector Store: 74,513 Rubrics</span>
                </span>
                <span class="status-pill status-pill-purple">
                    {get_icon('menu_book', size=14, color='#A78BFA')}
                    <span>Repertory: 37 Chapters</span>
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dimensions_grid(dims: Dict[str, Any]):
    """Render 7-dimension clinical findings in clean cards."""
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("**Location (LOC):**")
        locs = dims.get("location", [])
        st.markdown("".join(f'<span class="badge badge-loc">{l}</span>' for l in locs) if locs else "<span style='color:#6B7280; font-size:13px;'>None</span>", unsafe_allow_html=True)

        st.markdown("**Sensation (SEN):**")
        sens = dims.get("sensation", [])
        st.markdown("".join(f'<span class="badge badge-sen">{s}</span>' for s in sens) if sens else "<span style='color:#6B7280; font-size:13px;'>None</span>", unsafe_allow_html=True)

    with col2:
        st.markdown("**Aggravations (MOD_AGG):**")
        aggs = dims.get("modality_agg", [])
        st.markdown("".join(f'<span class="badge badge-agg">{a}</span>' for a in aggs) if aggs else "<span style='color:#6B7280; font-size:13px;'>None</span>", unsafe_allow_html=True)

        st.markdown("**Ameliorations (MOD_AMEL):**")
        amels = dims.get("modality_amel", [])
        st.markdown("".join(f'<span class="badge badge-amel">{a}</span>' for a in amels) if amels else "<span style='color:#6B7280; font-size:13px;'>None</span>", unsafe_allow_html=True)

    with col3:
        st.markdown("**Temporal (TEMP):**")
        temps = dims.get("temporal", [])
        st.markdown("".join(f'<span class="badge badge-temp">{t}</span>' for t in temps) if temps else "<span style='color:#6B7280; font-size:13px;'>None</span>", unsafe_allow_html=True)

        st.markdown("**Concomitants (CONC):**")
        concs = dims.get("concomitant", [])
        st.markdown("".join(f'<span class="badge badge-conc">{c}</span>' for c in concs) if concs else "<span style='color:#6B7280; font-size:13px;'>None</span>", unsafe_allow_html=True)

    with col4:
        st.markdown("**Mental / Emotional (MENT):**")
        ments = dims.get("mental", [])
        st.markdown("".join(f'<span class="badge badge-ment">{m}</span>' for m in ments) if ments else "<span style='color:#6B7280; font-size:13px;'>None</span>", unsafe_allow_html=True)

        st.markdown("**Negated / Denied:**")
        negs = dims.get("negated", [])
        st.markdown("".join(f'<span class="badge badge-neg">{n}</span>' for n in negs) if negs else "<span style='color:#6B7280; font-size:13px;'>None</span>", unsafe_allow_html=True)


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
            text=[f"Score: {s:.2f} ({c} rubrics)" for s, c in zip(df["score"], df["rubric_count"])],
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
        r_id = int(r.get("rubric_id") or r.get("id"))
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
        if len(short_label) > 20:
            short_label = short_label[:18] + "..."
        headers_html += f"<th title='{full_p}' style='font-size: 11px;'>R{idx}: {short_label}</th>"

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
            r_id = int(r.get("rubric_id") or r.get("id"))
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
    <div style='overflow-x: auto; margin-top: 10px; margin-bottom: 20px;'>
        <table class='repertory-grid'>
            <thead>
                <tr>{headers_html}</tr>
            </thead>
            <tbody>
                {''.join(rows_html)}
            </tbody>
        </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


def render_report_view(report: PatientReport, db: KentDB):
    """Render comprehensive clinical repertorization report."""
    st.markdown('<div class="stGlassCard">', unsafe_allow_html=True)
    col_rep_head, col_rep_dl = st.columns([3, 1])
    with col_rep_head:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                {get_icon('clinical_notes', size=24, color='#10B981')}
                <h3 style="margin: 0;">Case Analysis Report — <code>{report.patient_id}</code></h3>
            </div>
            """,
            unsafe_allow_html=True,
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
    
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin: 12px 0 8px 0;">
            {get_icon('account_tree', size=20, color='#06B6D4')}
            <h4 style="margin: 0;">1. 7-Dimension Clinical Parsing</h4>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_dimensions_grid(report.dimensions)
    st.markdown('</div>', unsafe_allow_html=True)

    remedies = report.ranked_remedies
    if remedies:
        top_rem = remedies[0]
        st.markdown(
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
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    {get_icon('bar_chart', size=20, color='#10B981')}
                    <h4 style="margin: 0;">2. Remedy Totality Ranking</h4>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_repertorization_chart(remedies)
        with col2:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    {get_icon('table_chart', size=20, color='#A78BFA')}
                    <h4 style="margin: 0;">3. Top Remedy Breakdown</h4>
                </div>
                """,
                unsafe_allow_html=True,
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

        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; margin: 16px 0 8px 0;">
                {get_icon('grid_on', size=20, color='#FBBF24')}
                <h4 style="margin: 0;">4. Classical Repertorization Totality Matrix (Remedies × Rubrics)</h4>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_totality_matrix(report, db)

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin: 16px 0 8px 0;">
            {get_icon('format_list_bulleted', size=20, color='#34D399')}
            <h4 style="margin: 0;">5. Matched Kent Repertory Rubrics</h4>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for r in report.matched_rubrics:
        render_rubric_card(r, db)



def render_sidebar():
    """Render Google Stitch clinical telemetry and quick-case loader."""
    with st.sidebar:
        st.markdown(
            f"""
            <div style='text-align: center; margin-bottom: 20px;'>
                <div style='margin-bottom: 8px; display: inline-flex; justify-content: center; align-items: center; width: 64px; height: 64px; border-radius: 16px; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3);'>
                    {get_icon('local_florist', size=38, color='#10B981')}
                </div>
                <div style='font-size: 18px; font-weight: 800; color: #10B981;'>Kent-AI Clinical Suite</div>
                <div style='font-size: 11px; color: #9CA3AF;'>Classical Homeopathy + Generative AI</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style='display: flex; align-items: center; gap: 6px; margin: 16px 0 8px 0;'>
                {get_icon('sensors', size=18, color='#06B6D4')}
                <span style='font-size: 15px; font-weight: 700; color: #F9FAFB;'>System Telemetry</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="stitch-metric" style="margin-bottom: 8px;">
                <div class="stitch-metric-val">llama3:8b</div>
                <div class="stitch-metric-lbl">Inference LLM (Ollama)</div>
            </div>
            <div class="stitch-metric" style="margin-bottom: 8px;">
                <div class="stitch-metric-val">74,513</div>
                <div class="stitch-metric-lbl">Dense Rubric Vectors</div>
            </div>
            <div class="stitch-metric" style="margin-bottom: 16px;">
                <div class="stitch-metric-val">37 Chapters</div>
                <div class="stitch-metric-lbl">Kent's Repertory DB</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown(
            f"""
            <div style='display: flex; align-items: center; gap: 6px; margin: 12px 0 8px 0;'>
                {get_icon('scale', size=18, color='#FBBF24')}
                <span style='font-size: 15px; font-weight: 700; color: #F9FAFB;'>Totality Weights (Kentian)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div style='font-size: 12px; color: #D1D5DB; line-height: 1.8;'>
                • <span class='grade-3'>Grade 3</span> : <b>3.0×</b> (Confirmed / Bold)<br>
                • <span class='grade-2'>Grade 2</span> : <b>2.0×</b> (Qualified / Italic)<br>
                • <span class='grade-1'>Grade 1</span> : <b>1.0×</b> (Plain / Roman)<br>
                • <i>Specificity</i> : Inverse rubric frequency
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown(
            """
            <div style='font-size: 11px; color: #6B7280; text-align: justify;'>
                <b>Investigational Tool:</b> Kent-AI is an academic clinical decision-support and repertorization research system. It does not replace qualified homeopathic or medical evaluation.
            </div>
            """,
            unsafe_allow_html=True,
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
        "Rubric Explorer (74k)",
        "Materia Medica Index",
    ])

    # =========================================================================
    # TAB 1: Live Patient Consultation (Chatbot)
    # =========================================================================
    with tab1:
        col_chat, col_ctrl = st.columns([3, 1])
        with col_ctrl:
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 14px;'>
                        {get_icon('tune', size=20, color='#10B981')}
                        <span style='font-size: 16px; font-weight: 700; color: #F9FAFB;'>Intake Controls</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Generate Full Repertorization", type="primary", use_container_width=True):
                    transcript = dm.get_full_transcript()
                    if transcript.strip():
                        with st.spinner("Analyzing totality and ranking remedies..."):
                            report = pipeline.process_transcript(transcript)
                            st.session_state.current_report = report
                        st.success("Repertorization complete! Scroll down to view report.")
                    else:
                        st.warning("Please chat with Kent-AI first before generating report.")

                if st.button("Reset Consultation", type="secondary", use_container_width=True):
                    dm.reset()
                    dm.get_greeting()
                    st.session_state.current_report = None
                    st.rerun()

                st.markdown("---")
                st.markdown("<div style='font-size: 12px; color: #9CA3AF;'><b>Tips for consultation:</b><br>Speak naturally about how you feel, time of day, what worsens or improves pain, and mood.</div>", unsafe_allow_html=True)

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
            st.markdown(
                f"""
                <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px;'>
                    {get_icon('analytics', size=22, color='#10B981')}
                    <h3 style='margin: 0;'>Instant Clinical Repertorization</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("Input patient clinical narrative directly to extract 7 dimensions, retrieve matching rubrics across Kent's 74,513 rubrics, and compute remedy totality.")

            example_cases = {
                "Select an example or type below...": "",
                "Case 1: Severe anxiety in morning, worse alone": "Doctor, I feel terribly anxious and depressed every morning, worse when alone. I have no fever and no nausea.",
                "Case 2: Forehead splitting headache from sun": "Patient reports severe splitting throbbing headache right in the forehead, aggravated by sun exposure and bright light, relieved by cold application and rest in dark room.",
                "Case 3: Absent-minded & forgetful in morning": "Patient complains of extreme absent-mindedness and difficulty concentrating, especially in the morning after waking up, with trembling hands.",
            }

            selected_example = st.selectbox("Pre-load Clinical Vignette:", list(example_cases.keys()))
            default_text = example_cases.get(selected_example, "")

            user_case_text = st.text_area(
                "Patient Clinical Narrative:",
                value=default_text or "Doctor, I feel terribly anxious and depressed every morning, worse when alone. I have no fever and no nausea.",
                height=120,
            )

            col_opt1, col_opt2, col_opt3 = st.columns([1, 1, 1])
            with col_opt1:
                top_k_rubrics = st.slider("Rubrics per query:", 1, 5, 3)
            with col_opt2:
                top_remedies_count = st.slider("Top remedies to rank:", 5, 20, 10)
            with col_opt3:
                sections = db.get_sections()
                sec_options = ["All Chapters (74,513 rubrics)"] + [f"{s['id']}: {s['name']}" for s in sections]
                section_choice = st.selectbox("Filter Chapter:", sec_options, index=0)
                sec_id = None
                if section_choice != "All Chapters (74,513 rubrics)":
                    sec_id = int(section_choice.split(":")[0])

            run_btn = st.button("Analyze & Repertorize Case", type="primary", use_container_width=True)

        if run_btn and user_case_text.strip():
            with st.spinner("Extracting 7-dimensions via LLaMA 3, retrieving rubrics from ChromaDB, and computing totality..."):
                report = pipeline.process_transcript(
                    transcript=user_case_text,
                    top_rubrics_per_query=top_k_rubrics,
                    top_remedies=top_remedies_count,
                    section_id=sec_id,
                )
                render_report_view(report, db)

    # =========================================================================
    # TAB 3: Kent's Rubric Explorer (74,513 Rubrics)
    # =========================================================================
    with tab3:
        with st.container(border=True):
            st.markdown(
                f"""
                <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px;'>
                    {get_icon('search', size=22, color='#10B981')}
                    <h3 style='margin: 0;'>Kent's Repertory Dense & Lexical Search</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("Query all **74,513 digitized rubrics** using semantic vectors or exact text search.")

            col_search, col_sec = st.columns([3, 1])
            with col_search:
                search_query = st.text_input("Search Rubric (e.g. 'headache sun', 'anxiety dark', 'restless sleep'):", value="headache sun")
            with col_sec:
                sections = db.get_sections()
                sec_options = ["All Chapters"] + [f"{s['id']}: {s['name']}" for s in sections]
                selected_sec_str = st.selectbox("Section / Chapter:", sec_options)
                chosen_sec_id = None
                if selected_sec_str != "All Chapters":
                    chosen_sec_id = int(selected_sec_str.split(":")[0])

            search_mode = st.radio("Search Algorithm:", ["Dense Semantic Search (all-MiniLM-L6-v2)", "Exact FTS5 Lexical Search"], horizontal=True)
            search_clicked = st.button("Search Rubrics", type="primary", use_container_width=True)

        if (search_clicked or search_query) and search_query.strip():
            with st.spinner("Searching rubrics..."):
                if "Dense" in search_mode:
                    results = pipeline.vector_store.query(
                        query_text=search_query,
                        top_k=15,
                        section_id=chosen_sec_id,
                    )
                else:
                    results = db.search_rubrics(
                        query=search_query,
                        section_id=chosen_sec_id,
                        limit=15,
                    )

            if results:
                st.markdown(f"Found **{len(results)}** matching rubrics:")
                for r in results:
                    render_rubric_card(r, db)
            else:
                st.info("No rubrics matched the specified search.")

    # =========================================================================
    # TAB 4: Materia Medica & Remedy Index
    # =========================================================================
    with tab4:
        with st.container(border=True):
            st.markdown(
                f"""
                <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px;'>
                    {get_icon('medication', size=22, color='#10B981')}
                    <h3 style='margin: 0;'>Homeopathic Remedy Dictionary</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("Browse remedies cataloged in Kent's Repertory with full Latin names, abbreviations, and characteristic keynotes.")

            rem_search = st.text_input("Filter Remedy by Name or Abbreviation (e.g. 'Lach', 'Phos', 'Nux-v', 'Ars'):", value="Lach")

        if rem_search.strip():
            with db.connect() as conn:
                cur = conn.cursor()
                query = """
                    SELECT 
                        r.id,
                        r.abbreviation,
                        r.full_name,
                        r.normalized,
                        (SELECT COUNT(*) FROM rubric_remedies rr WHERE rr.remedy_id = r.id) as total_rubrics
                    FROM remedies r
                    WHERE r.abbreviation LIKE ? OR r.full_name LIKE ? OR r.normalized LIKE ?
                    ORDER BY total_rubrics DESC
                    LIMIT 15
                """
                like_term = f"%{rem_search.strip()}%"
                cur.execute(query, (like_term, like_term, like_term))
                remedy_rows = cur.fetchall()

            if remedy_rows:
                for row in remedy_rows:
                    r_id, abbr, name, norm, count = row["id"], row["abbreviation"], row["full_name"], row["normalized"], row["total_rubrics"]
                    st.markdown(
                        f"""
                        <div class="stGlassCard" style="padding: 16px; margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="font-size: 20px; font-weight: 800; color: #FFFFFF;">{name or abbr}</span>
                                    <span style="color: #34D399; font-weight: 700; margin-left: 8px;">({abbr})</span>
                                    <div style="font-size: 13px; color: #9CA3AF; margin-top: 4px;">Standardized: <code>{norm or abbr}</code></div>
                                </div>
                                <div style="text-align: right;">
                                    <span class="status-pill">{count} rubrics</span>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    with st.expander(f"Inspect Characteristic Keynotes for {name or abbr} (Grade 3)", icon=":material/key:"):
                        keynotes = db.get_remedy_rubrics(r_id, min_grade=3, limit=12)
                        if not keynotes:
                            st.write("No Grade 3 keynote rubrics cataloged for this remedy.")
                        else:
                            for kn in keynotes:
                                st.markdown(
                                    f"<div style='margin-bottom: 4px;'><span class='grade-3'>Grade 3</span> <span style='font-size:13px; color:#F9FAFB;'>{kn['path']}</span> <span style='font-size:11px; color:#06B6D4;'>({kn.get('section_name')})</span></div>",
                                    unsafe_allow_html=True,
                                )
            else:
                st.info(f"No remedies found matching '{rem_search}'.")


if __name__ == "__main__":
    main()
