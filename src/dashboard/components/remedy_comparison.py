"""Differential Diagnosis & Side-by-Side Remedy Comparison Component (Phase 1 & 7).

Enables clinicians to compare 2 or 3 candidate remedies side-by-side, analyzing
shared totality symptoms, differential keynotes, and chapter representations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import streamlit as st

from src.dashboard.components.icons import get_icon
from src.data.kent_db import KentDB


def render_remedy_comparison(db: KentDB) -> None:
    """Render side-by-side differential comparison of 2 or 3 homeopathic remedies."""
    st.html(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            {get_icon('compare_arrows', size=22, color='#10B981')}
            <h4 style="margin: 0;">Differential Materia Medica: Remedy Comparison</h4>
        </div>
        """
    )
    st.markdown(
        "<div style='font-size: 13px; color: #9CA3AF; margin-bottom: 12px;'>"
        "Compare characteristic symptoms, mental generals, and differentiating keynotes across 2 or 3 candidate remedies."
        "</div>",
        unsafe_allow_html=True,
    )

    # Preload remedy catalogue for autocomplete selector
    with db.connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, abbreviation, full_name, 
                   (SELECT COUNT(*) FROM rubric_remedies WHERE remedy_id = r.id) as total_rubrics
            FROM remedies r
            WHERE abbreviation IS NOT NULL AND abbreviation != ''
            ORDER BY total_rubrics DESC
            LIMIT 250
            """
        )
        remedy_options = cur.fetchall()

    rem_label_map = {
        f"{r['abbreviation']} — {r['full_name']} ({r['total_rubrics']} rubrics)": r['id']
        for r in remedy_options
    }
    labels_list = list(rem_label_map.keys())

    default_sel = []
    if len(labels_list) >= 2:
        default_sel = [labels_list[0], labels_list[1]]

    selected_labels = st.multiselect(
        "Select 2 or 3 remedies to differentiate:",
        options=labels_list,
        default=default_sel,
        max_selections=3,
        key="diff_remedies_multiselect",
        help="Type remedy abbreviation (e.g. 'Ars', 'Phos', 'Lach', 'Nux-v', 'Puls', 'Lyc')",
    )

    if len(selected_labels) < 2:
        st.info("Please select at least 2 remedies above to view their differential comparison.")
        return

    selected_ids = [rem_label_map[lbl] for lbl in selected_labels]

    # Fetch detailed stats for each selected remedy
    remedy_details: List[Dict[str, Any]] = []
    with db.connect() as conn:
        cur = conn.cursor()
        for r_id in selected_ids:
            cur.execute(
                """
                SELECT 
                    r.id, r.abbreviation, r.full_name, r.normalized,
                    (SELECT COUNT(*) FROM rubric_remedies rr WHERE rr.remedy_id = r.id) as total_rubrics,
                    (SELECT COUNT(*) FROM rubric_remedies rr JOIN rubrics rb ON rr.rubric_id = rb.id WHERE rr.remedy_id = r.id AND rb.section_id = 1) as mind_rubrics
                FROM remedies r
                WHERE r.id = ?
                """,
                (r_id,),
            )
            row = cur.fetchone()
            if row:
                keynotes = db.get_remedy_rubrics(r_id, min_grade=3, limit=12, prioritize_mind=True, rank_by_specificity=True)
                remedy_details.append({
                    "id": row["id"],
                    "abbreviation": row["abbreviation"],
                    "full_name": row["full_name"],
                    "total_rubrics": row["total_rubrics"],
                    "mind_rubrics": row["mind_rubrics"],
                    "keynotes": keynotes,
                })

    # Render side-by-side columns
    cols = st.columns(len(remedy_details))
    for idx, rem in enumerate(remedy_details):
        with cols[idx]:
            with st.container(border=True):
                st.html(
                    f"""
                    <div style="border-bottom: 2px solid #10B981; padding-bottom: 8px; margin-bottom: 10px;">
                        <div style="font-size: 20px; font-weight: 800; color: #FFFFFF;">
                            {rem['abbreviation']}
                        </div>
                        <div style="font-size: 13px; color: #34D399; font-weight: 600;">
                            {rem['full_name']}
                        </div>
                        <div style="font-size: 11.5px; color: #9CA3AF; margin-top: 4px;">
                            <span><b>{rem['mind_rubrics']}</b> in MIND</span> &middot;
                            <span><b>{rem['total_rubrics']:,}</b> total rubrics</span>
                        </div>
                    </div>
                    """
                )

                st.markdown("<div style='font-size: 12px; font-weight: 700; color: #E5E7EB; margin-bottom: 6px;'>Top Characteristic Keynotes:</div>", unsafe_allow_html=True)
                for kn in rem["keynotes"][:8]:
                    p = kn.get("path", "")
                    clean_leaf = p.split(">")[-1].strip() if ">" in p else p
                    is_mind = kn.get("section_name") == "MIND" or str(p).startswith("MIND")
                    sec_badge = "<span class='badge badge-mind' style='font-size:9px;'>MIND</span>" if is_mind else f"<span style='font-size:9.5px; color:#06B6D4;'>{kn.get('section_name')}</span>"
                    st.html(
                        f"""
                        <div style="font-size: 11.5px; margin-bottom: 5px; line-height: 1.3;" title="{p}">
                            <span class="grade-3" style="font-size: 10px;">3</span>
                            <span style="color: #F9FAFB;">{clean_leaf}</span>
                            {sec_badge}
                        </div>
                        """
                    )
