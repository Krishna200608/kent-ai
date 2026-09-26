"""Rubric card and remedy inspector component (Phase 7)."""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict, List

from src.dashboard.components.icons import get_icon
from src.data.kent_db import KentDB


def render_rubric_card(rubric: Dict[str, Any], db: KentDB) -> None:
    """Render an individual rubric card with path, similarity, and expandable remedies."""
    r_id = rubric.get("rubric_id") or rubric.get("id")
    path = rubric.get("path") or f"Rubric #{r_id}"
    sim = rubric.get("similarity")
    remedy_count = rubric.get("remedy_count", 0)

    sim_badge = ""
    if sim is not None:
        sim_badge = f"<span class='status-pill' style='float: right;'>Sim: {sim:.3f}</span>"

    st.markdown(
        f"""
        <div class="stGlassCard" style="padding: 16px; margin-bottom: 12px;">
            {sim_badge}
            <div style="font-size: 11px; color: #9CA3AF; text-transform: uppercase; display: flex; align-items: center; gap: 4px;">
                {get_icon('bookmark', color='#06B6D4', size=14)}
                <span>Rubric #{r_id}</span>
            </div>
            <div style="font-weight: 700; font-size: 15px; color: #F9FAFB; margin: 4px 0 8px 0;">{path}</div>
            <div style="font-size: 12px; color: #06B6D4;">Remedies in Kent's Repertory: <b>{remedy_count}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(f"Inspect remedies for: {path.split('>')[-1].strip()}", icon=":material/medication:"):
        remedies = db.get_remedies(int(r_id))
        if not remedies:
            st.write("No remedies cataloged under this rubric.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                g3 = [r for r in remedies if r["grade"] == 3]
                st.markdown(f"**Grade 3 (Bold / Confirmed):** ({len(g3)})")
                for r in g3[:15]:
                    name = r.get("full_name") or r.get("abbreviation")
                    abbr = r.get("abbreviation") or ""
                    st.markdown(f"<span class='grade-3'>{name}</span> <span style='color:#6B7280; font-size:11px;'>({abbr})</span>", unsafe_allow_html=True)
            with col2:
                g2 = [r for r in remedies if r["grade"] == 2]
                st.markdown(f"**Grade 2 (Italics / Qualified):** ({len(g2)})")
                for r in g2[:15]:
                    name = r.get("full_name") or r.get("abbreviation")
                    abbr = r.get("abbreviation") or ""
                    st.markdown(f"<span class='grade-2'>{name}</span> <span style='color:#6B7280; font-size:11px;'>({abbr})</span>", unsafe_allow_html=True)
            with col3:
                g1 = [r for r in remedies if r["grade"] == 1]
                st.markdown(f"**Grade 1 (Plain):** ({len(g1)})")
                for r in g1[:15]:
                    name = r.get("full_name") or r.get("abbreviation")
                    abbr = r.get("abbreviation") or ""
                    st.markdown(f"<span class='grade-1'>{name}</span> <span style='color:#6B7280; font-size:11px;'>({abbr})</span>", unsafe_allow_html=True)
