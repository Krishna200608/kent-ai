"""Tab 3: Rubric Explorer view."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.dashboard.components.icons import get_icon
from src.dashboard.components.rubric_tree import render_rubric_card
from src.dashboard.dimensions import pluralize
from src.data.kent_db import KentDB


def render_rubric_explorer(db: KentDB, pipeline: Any) -> None:
    """Render Tab 3: Kent's Repertory & Rubric Search."""
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
