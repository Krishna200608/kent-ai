"""Rubric Explorer & Repertory Search View (Phase 6 & UI Overhaul).

Provides:
- Single-row search form in st.form with query input, mode segmented control (Meaning | Exact | Hybrid),
  result count segmented control (10 / 15 / 25 / 50), and Enter-submittable Search button.
- Scope-aware caption (Searching MIND · 4,933 rubrics) and conditional chapter selector when in All chapters scope.
- Advanced filters expander: minimum similarity, remedy-count range, and multi-sort.
- Sticky "Add selected (n)" multi-select action bar.
- Empty states with clinical query suggestions.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
import streamlit as st

from src.dashboard.components.icons import get_icon
from src.dashboard.components.rubric_tree import render_rubric_card
from src.dashboard.constants import (
    SCOPE_ALL,
    SCOPE_ALL_COUNT,
    SCOPE_MIND,
    SCOPE_MIND_COUNT,
)
from src.dashboard.dimensions import pluralize
from src.data.case_store import save_case
from src.data.kent_db import KentDB


def hybrid_rubric_search(
    query: str,
    db: KentDB,
    vector_store: Any,
    section_id: Optional[int] = None,
    limit: int = 30,
) -> List[Dict[str, Any]]:
    """Blend dense vector semantic search with exact lexical keyword matching."""
    top_k = max(limit * 2, 40)
    sem_results: List[Dict[str, Any]] = []
    if vector_store is not None:
        try:
            sem_results = vector_store.query(
                query_text=query,
                top_k=top_k,
                section_id=section_id,
            )
        except Exception:
            sem_results = []

    exact_results: List[Dict[str, Any]] = []
    if db is not None:
        try:
            exact_results = db.search_rubrics(
                query=query,
                section_id=section_id,
                limit=top_k,
            )
        except Exception:
            exact_results = []

    candidates: Dict[int, Dict[str, Any]] = {}

    for r in sem_results:
        raw_id = r.get("id") or r.get("rubric_id")
        if raw_id is None:
            continue
        try:
            r_id = int(str(raw_id).replace("rubric_", "").strip())
        except (ValueError, TypeError):
            continue
        candidates[r_id] = {
            **r,
            "id": r_id,
            "rubric_id": r_id,
            "sem_score": float(r.get("similarity", 0.0)),
            "lex_score": 0.0,
        }

    terms = [w.lower() for w in re.findall(r"\w+", query) if len(w) >= 2]
    for rank, r in enumerate(exact_results):
        raw_id = r.get("id") or r.get("rubric_id")
        if raw_id is None:
            continue
        try:
            r_id = int(str(raw_id).replace("rubric_", "").strip())
        except (ValueError, TypeError):
            continue

        path_lower = (r.get("path") or "").lower()
        matched = sum(1 for t in terms if t in path_lower)
        overlap = (matched / max(len(terms), 1)) if terms else 0.5
        rr_score = 1.0 / (rank + 1.0)
        lex_score = 0.6 * overlap + 0.4 * rr_score

        if r_id in candidates:
            candidates[r_id]["lex_score"] = max(candidates[r_id]["lex_score"], lex_score)
        else:
            candidates[r_id] = {
                **r,
                "id": r_id,
                "rubric_id": r_id,
                "sem_score": 0.0,
                "lex_score": lex_score,
            }

    merged: List[Dict[str, Any]] = []
    for c in candidates.values():
        sem = c.get("sem_score", 0.0)
        lex = c.get("lex_score", 0.0)
        if sem > 0.0 and lex > 0.0:
            blended = 0.65 * sem + 0.35 * min(lex, 1.0)
        elif sem > 0.0:
            blended = sem * 0.85
        else:
            blended = lex * 0.75
        c["similarity"] = round(blended, 4)
        merged.append(c)

    merged.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)
    return merged


def render_rubric_explorer(db: KentDB, pipeline: Any) -> None:
    """Render Rubric Explorer view with compact single-row search and advanced filtering."""
    active_scope = st.session_state.get("scope", SCOPE_MIND)
    is_mind_scope = (active_scope == SCOPE_MIND)

    # 1. Search Card Header
    st.html(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            {get_icon('psychology', size=22, color='var(--accent, #10B981)')}
            <span style="font-size: 20px; font-weight: 800; color: var(--text, #E8EDF3);">Rubric Explorer</span>
        </div>
        """
    )

    # 2. Single-Row Search Form
    with st.form(key="rubric_search_form", clear_on_submit=False):
        c_query, c_mode, c_limit, c_btn = st.columns([4, 2.5, 1.8, 1.1], vertical_alignment="bottom")

        with c_query:
            search_query = st.text_input(
                "Search rubrics:",
                value=st.session_state.get("explorer_query", "anxiety dark"),
                placeholder="e.g. fear of dark, anxiety in the evening",
                key="explorer_query_input",
                help="Enter clinical symptoms, modalities, triggers, or rubrics",
            )

        with c_mode:
            search_mode = st.segmented_control(
                "Search mode:",
                options=["Meaning", "Exact", "Hybrid"],
                default="Meaning",
                key="explorer_search_mode",
                help="Meaning: BioLinkBERT dense vector search · Exact: Exact word match · Hybrid: Blended lexical + semantic score",
            ) or "Meaning"

        with c_limit:
            limit = st.segmented_control(
                "Results:",
                options=[10, 15, 25, 50],
                default=15,
                key="explorer_limit",
                help="Maximum number of rubrics to return",
            ) or 15

        with c_btn:
            search_submitted = st.form_submit_button(
                "Search",
                type="primary",
                width="stretch",
            )

    # 3. Scope Caption & Conditional Chapter Selector
    chosen_sec_id: Optional[int] = 1 if is_mind_scope else None
    if is_mind_scope:
        st.html(
            f"""
            <div style="font-size: 12.5px; color: var(--text-muted, #A3B0C2); margin-top: -6px; margin-bottom: 10px;">
                Searching <b style="color: var(--accent, #10B981);">MIND · {SCOPE_MIND_COUNT:,} rubrics</b>
                <span style="color: var(--text-faint, #8A98AE); margin-left: 8px;">(Change scope in sidebar to search all 37 chapters)</span>
            </div>
            """
        )
    else:
        c_cap, c_sec = st.columns([1.5, 2.5], vertical_alignment="center")
        with c_cap:
            st.html(
                f"""
                <div style="font-size: 12.5px; color: var(--text-muted, #A3B0C2);">
                    Searching <b style="color: var(--text, #E8EDF3);">All chapters · {SCOPE_ALL_COUNT:,} rubrics</b>
                </div>
                """
            )
        with c_sec:
            sections = db.get_sections() if db else []
            sec_options = ["All Chapters (74,513 rubrics)"] + [f"{s['id']}: {s['name']}" for s in sections]
            selected_sec_str = st.selectbox(
                "Filter chapter / section:",
                sec_options,
                index=0,
                key="explorer_section_select",
                label_visibility="collapsed",
            )
            if selected_sec_str != "All Chapters (74,513 rubrics)" and ":" in selected_sec_str:
                chosen_sec_id = int(selected_sec_str.split(":")[0])

    # 4. Advanced Filters Expander
    with st.expander("Advanced filters", expanded=False):
        c_sim, c_rems, c_sort = st.columns([1.5, 1.8, 1.7])
        with c_sim:
            min_similarity = st.slider(
                "Minimum similarity:",
                min_value=0.0,
                max_value=1.0,
                value=0.35,
                step=0.05,
                help="Filter out weak semantic matches (default: 0.35)",
            )
        with c_rems:
            rems_range = st.slider(
                "Remedy count range:",
                min_value=1,
                max_value=300,
                value=(1, 300),
                step=1,
                help="Filter between highly specific rubrics (≤20) and broad rubrics (≥80)",
            )
        with c_sort:
            sort_by = st.selectbox(
                "Sort results by:",
                [
                    "Relevance (Similarity)",
                    "Remedy count (High to Low)",
                    "Remedy count (Low to High - Specific)",
                    "Alphabetical (A–Z)",
                ],
                index=0,
                key="explorer_sort_by",
            )

    # 5. Search Execution (submit-only: results cached in session_state)
    query_clean = (search_query or "").strip()
    # Only execute a new search when the form was explicitly submitted.
    # Cached results are re-displayed between submissions to avoid redundant
    # vector queries on every Streamlit rerun (CONVENTIONS §19 – lazy search).
    if search_submitted and query_clean:
        st.session_state["explorer_query"] = query_clean
        st.session_state["explorer_results"] = None  # invalidate cache
        with st.spinner("Searching Repertory rubrics..."):
            if search_mode == "Meaning":
                if pipeline and hasattr(pipeline, "vector_store") and pipeline.vector_store:
                    raw_results = pipeline.vector_store.query(
                        query_text=query_clean,
                        top_k=max(int(limit) * 2, 35),
                        section_id=chosen_sec_id,
                    )
                else:
                    raw_results = db.search_rubrics(
                        query=query_clean,
                        section_id=chosen_sec_id,
                        limit=max(int(limit) * 2, 35),
                    )
            elif search_mode == "Exact":
                raw_results = db.search_rubrics(
                    query=query_clean,
                    section_id=chosen_sec_id,
                    limit=max(int(limit) * 2, 35),
                )
            else:
                vs = pipeline.vector_store if (pipeline and hasattr(pipeline, "vector_store")) else None
                raw_results = hybrid_rubric_search(
                    query=query_clean,
                    db=db,
                    vector_store=vs,
                    section_id=chosen_sec_id,
                    limit=max(int(limit) * 2, 35),
                )

        # 6. Apply filters
        min_rems, max_rems = rems_range
        filtered_results: List[Dict[str, Any]] = []
        for r in raw_results:
            rc = r.get("remedy_count", 0)
            sim_val = r.get("similarity")
            if rc <= 0:
                continue
            if not (min_rems <= rc <= max_rems):
                continue
            if sim_val is not None and sim_val < min_similarity:
                continue
            filtered_results.append(r)

        # 7. Apply sorting
        if "Remedy count (High to Low)" in sort_by:
            filtered_results.sort(key=lambda r: r.get("remedy_count", 0), reverse=True)
        elif "Remedy count (Low to High" in sort_by:
            filtered_results.sort(key=lambda r: r.get("remedy_count", 0))
        elif "Alphabetical" in sort_by:
            filtered_results.sort(key=lambda r: (r.get("path") or "").lower())
        else:
            filtered_results.sort(key=lambda r: r.get("similarity", 0.0) or 0.0, reverse=True)

        display_results = filtered_results[:int(limit)]
        st.session_state["explorer_results"] = display_results
        st.session_state["explorer_query_display"] = query_clean

        # 8. Render Results or No-Results State
        _display = display_results
    else:
        # Not submitting: use cached results from previous search (if any)
        _display = st.session_state.get("explorer_results", [])
        query_clean = st.session_state.get("explorer_query_display", query_clean)

    display_results = _display or []

    if display_results:
        st.html(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 8px;">
                <div style="font-size: 13.5px; color: var(--text-muted, #A3B0C2);">
                    Found <b style="color: var(--text, #E8EDF3);">{len(display_results)}</b> matching {pluralize(len(display_results), 'rubric', 'rubrics', include_count=False)}
                </div>
            </div>
            """
        )

        # Render rubric cards with multi-select support
        selected_rubrics_in_view: List[Dict[str, Any]] = []
        for r in display_results:
            is_chk = render_rubric_card(
                rubric=r,
                db=db,
                query=query_clean,
                selectable=True,
                is_selected=False,
            )
            if is_chk:
                selected_rubrics_in_view.append(r)

        # Sticky Multi-Select Action Bar when ≥1 checked
        if selected_rubrics_in_view:
            c_sel_text, c_sel_btn = st.columns([3, 1.5], vertical_alignment="center")
            with c_sel_text:
                st.html(
                    f"""
                    <div class="sticky-explorer-bar">
                        <span style="font-weight: 700; color: var(--text, #E8EDF3);">
                            {len(selected_rubrics_in_view)} rubrics selected
                        </span>
                    </div>
                    """
                )
            with c_sel_btn:
                if st.button(
                    f"Add {len(selected_rubrics_in_view)} to Case Tray",
                    type="primary",
                    width="stretch",
                    key="btn_add_selected_rubrics",
                ):
                    if "case_tray" not in st.session_state:
                        st.session_state.case_tray = {"rubrics": [], "remedies": []}
                    cur_c = st.session_state.get("current_case")

                    added_count = 0
                    for sel_r in selected_rubrics_in_view:
                        raw_id = sel_r.get("id") or sel_r.get("rubric_id")
                        try:
                            sel_id = int(str(raw_id).replace("rubric_", "").strip())
                        except (ValueError, TypeError):
                            continue

                        in_tray = any(item.get("id") == sel_id for item in st.session_state.case_tray.get("rubrics", []))
                        if not in_tray:
                            path_val = sel_r.get("path", f"Rubric #{sel_id}")
                            leaf_val = path_val.split(" › ")[-1] if " › " in path_val else path_val
                            st.session_state.case_tray["rubrics"].append({
                                "id": sel_id,
                                "rubric_id": sel_id,
                                "path": path_val,
                                "name": leaf_val,
                                "similarity": sel_r.get("similarity", 1.0),
                                "remedy_count": sel_r.get("remedy_count", 0),
                            })
                            if cur_c is not None and sel_id not in cur_c.selected_rubric_ids:
                                cur_c.selected_rubric_ids.append(sel_id)
                            added_count += 1

                    if cur_c is not None and added_count > 0:
                        try:
                            save_case(cur_c)
                        except Exception:
                            pass

                    st.toast(f"Added {added_count} rubrics to Case Tray.")
                    st.rerun()

    else:
        if st.session_state.get("explorer_results") is None and not search_submitted:
            # First load – show empty state, guide user to search
            st.info("Enter a clinical symptom query above and click Search.")
        else:
            st.info("No rubrics matched the specified search criteria.")
            st.markdown("##### Suggested Clinical Searches:")
            sug_cols = st.columns(4)
            suggestions = [
                ("Anxiety in evening", "anxiety evening"),
                ("Fear of darkness", "fear dark"),
                ("Pulsating headache", "headache pulsating"),
                ("Restless after midnight", "restlessness midnight"),
            ]
            for idx, (label, q_val) in enumerate(suggestions):
                with sug_cols[idx]:
                    if st.button(label, key=f"sug_btn_{idx}", width="stretch"):
                        st.session_state["explorer_query"] = q_val
                        st.rerun()
