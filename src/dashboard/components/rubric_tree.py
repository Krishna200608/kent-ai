"""Rubric card and remedy inspector component (Phase 6 & UI Overhaul).

Renders:
- Collapsed rubric row with breadcrumbs in --font-rubric, specificity tag, similarity bar, and + Add action.
- Expanded row showing remedies grouped by non-empty grades with (3)/(2)/(1) badges and Materia Medica dialog chips.
- Safe ID handling and query keyword highlighting.
"""

from __future__ import annotations

import html
import re
from typing import Any, Dict, List, Optional
import streamlit as st

from src.dashboard.components.case_dialogs import show_remedy_dialog
from src.dashboard.components.icons import get_icon
from src.dashboard.constants import (
    GRADE_LABELS,
    format_rubric_path,
    get_rubric_specificity,
)
from src.dashboard.dimensions import pluralize
from src.data.case_store import save_case
from src.data.kent_db import KentDB


def highlight_query_words(text: str, query: Optional[str]) -> str:
    """Highlight matched query words in text safely with HTML escaping."""
    escaped_text = html.escape(text)
    if not query or not query.strip():
        return escaped_text

    tokens = [re.escape(w) for w in re.findall(r"\w+", query) if len(w) >= 2]
    if not tokens:
        return escaped_text

    pattern = re.compile(rf"(\b(?:{'|'.join(tokens)})\b)", re.IGNORECASE)
    return pattern.sub(r'<mark class="query-match">\1</mark>', escaped_text)


def render_rubric_card(
    rubric: Dict[str, Any],
    db: KentDB,
    query: Optional[str] = None,
    allow_add_to_case: bool = True,
    omit_chapter_prefix: bool = True,
    selectable: bool = False,
    is_selected: bool = False,
) -> bool:
    """Render an individual rubric card with collapsed breadcrumb row and expanded remedy groups.
    
    Returns:
        bool: True if the multi-select checkbox is checked, False otherwise.
    """
    raw_id = rubric.get("rubric_id") if rubric.get("rubric_id") is not None else rubric.get("id")
    r_id: Optional[int] = None
    if raw_id is not None:
        try:
            clean_str = str(raw_id).replace("rubric_", "").strip()
            r_id = int(clean_str)
        except (ValueError, TypeError):
            r_id = None

    display_id = str(r_id) if r_id is not None else (str(raw_id) if raw_id is not None else "N/A")
    path = rubric.get("path") or f"Rubric #{display_id}"
    sim = rubric.get("similarity")
    remedy_count = rubric.get("remedy_count", 0)

    # 1. Format hierarchy path into prefix and leaf symptom with ' › ' breadcrumbs
    formatted_path = format_rubric_path(path)
    if " › " in formatted_path:
        parts = formatted_path.split(" › ")
        prefix = " › ".join(p.strip() for p in parts[:-1])
        leaf = parts[-1].strip()
    else:
        prefix = ""
        leaf = formatted_path

    # Omit MIND chapter prefix when viewing within single chapter scope
    disp_prefix = prefix
    if omit_chapter_prefix and (prefix == "MIND" or prefix.startswith("MIND ›")):
        disp_prefix = prefix[4:].lstrip(" ›").strip()

    # Query highlighting for hierarchy
    high_prefix = highlight_query_words(disp_prefix, query) if disp_prefix else ""
    high_leaf = highlight_query_words(leaf, query)

    # 2. Specificity and remedy count badge
    specificity = get_rubric_specificity(remedy_count)
    spec_css = f"badge-{specificity.lower()}"
    count_noun = pluralize(remedy_count, "remedy", "remedies")
    spec_html = (
        f"<span class='badge-specificity {spec_css}'>{specificity} · {count_noun}</span>"
        if remedy_count > 0
        else "<span class='badge-specificity badge-broad'>No remedies listed</span>"
    )

    # 3. Thin similarity bar + %
    sim_html = ""
    sim_pct_label = ""
    if sim is not None:
        pct = int(round(sim * 100))
        sim_pct_label = f"{pct}%"
        sim_html = (
            f"<div class='sim-metric' tabindex='0' aria-label='Semantic similarity to your query, not clinical relevance' "
            f"title='Semantic similarity to your query, not clinical relevance'>"
            f"<div class='sim-track'><div class='sim-fill' style='width: {pct}%;'></div></div>"
            f"<span class='sim-pct'>{pct}%</span>"
            f"</div>"
        )

    # 4. MIND chapter badge
    is_mind = str(path).startswith("MIND") or rubric.get("section_id") == 1
    show_dev = st.session_state.get("show_dev_details", False) if hasattr(st, "session_state") else False
    disp_style = "display: inline-flex;" if show_dev else "display: none;"
    mind_badge = (
        f"<span class='badge badge-mind' tabindex='0' aria-label='MIND CHAPTER' data-tip='MIND CHAPTER' title='MIND CHAPTER' style='{disp_style} margin-left: 6px; vertical-align: middle;'>"
        f"{get_icon('psychology', size=12, color='#10B981')} MIND CHAPTER"
        f"</span>"
    ) if is_mind else ""

    dev_id_badge = f"<span class='rubric-dev-id'>#{display_id}</span>" if (show_dev and display_id != 'N/A') else ""

    # Path breadcrumb HTML
    path_hierarchy_html = (
        f"<span class='rubric-path-breadcrumb'><span class='rubric-ancestors'>{high_prefix} › </span><strong class='rubric-leaf'>{high_leaf}</strong></span>"
        if high_prefix
        else f"<span class='rubric-path-breadcrumb'><strong class='rubric-leaf'>{high_leaf}</strong></span>"
    )

    # Expander header title
    if disp_prefix:
        expander_title = f"{disp_prefix} › {leaf}  ({specificity} · {count_noun})"
    else:
        expander_title = f"{leaf}  ({specificity} · {count_noun})"
    if sim_pct_label:
        expander_title += f"  ·  {sim_pct_label} match"

    checked = is_selected
    if selectable and r_id is not None:
        checked = st.checkbox(
            f"Select {leaf}",
            value=is_selected,
            key=f"chk_rubric_{r_id}",
            label_visibility="collapsed",
        )

    exp = st.expander(expander_title, expanded=False)
    with exp:
        col_hdr, col_act = st.columns(2)

        with col_hdr:
            # Render card header for accessibility, badges, and test compatibility
            st.html(
                f"""
                <div style="margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                    <div>
                        {path_hierarchy_html}
                        {dev_id_badge}
                        {mind_badge}
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px; margin-left: auto;">
                        {spec_html}
                        {sim_html}
                    </div>
                </div>
                """
            )

        with col_act:
            if allow_add_to_case and r_id is not None:
                tray = st.session_state.get("case_tray", {"rubrics": [], "remedies": []}) if hasattr(st, "session_state") else {"rubrics": []}
                is_in_tray = any(item.get("id") == r_id for item in tray.get("rubrics", []))
                card_key = f"tray_add_r_{r_id}"
                if is_in_tray:
                    st.button("✓ Added", key=card_key, disabled=True, width="stretch")
                else:
                    if st.button("+ Add to case", key=card_key, type="primary", width="stretch", help="Add this rubric to case tray"):
                        if "case_tray" not in st.session_state:
                            st.session_state.case_tray = {"rubrics": [], "remedies": []}
                        st.session_state.case_tray["rubrics"].append({
                            "id": r_id,
                            "rubric_id": r_id,
                            "path": path,
                            "name": leaf,
                            "similarity": sim or 1.0,
                            "remedy_count": remedy_count,
                        })
                        cur_c = st.session_state.get("current_case")
                        if cur_c is not None:
                            if r_id not in cur_c.selected_rubric_ids:
                                cur_c.selected_rubric_ids.append(r_id)
                            try:
                                save_case(cur_c)
                            except Exception:
                                pass
                        st.toast(f"Added '{leaf}' to case tray.")
                        st.rerun()

        # Expanded row: remedies only grouped by non-empty grades with ③/②/① badges (lazy: only when .open)
        remedies: List[Dict[str, Any]] = []
        if getattr(exp, "open", True) and r_id is not None and db is not None:
            try:
                remedies = db.get_remedies(r_id)
            except Exception:
                remedies = []

        if not remedies:
            st.write("No remedies cataloged under this rubric.")
        else:
            for grade in [3, 2, 1]:
                grade_rems = [r for r in remedies if r.get("grade") == grade]
                if not grade_rems:
                    continue  # Hide empty grades entirely

                badge_sym = "③" if grade == 3 else ("②" if grade == 2 else "①")
                grade_name = (
                    "Bold · Confirmed" if grade == 3
                    else ("Italic · Qualified" if grade == 2 else "Roman · Observed")
                )
                badge_css = f"badge-g{grade}"
                font_style = (
                    "font-weight: 800;" if grade == 3
                    else ("font-style: italic; font-weight: 600;" if grade == 2 else "font-weight: 400;")
                )

                st.html(
                    f"""
                    <div class="badge-grade-header {badge_css}">
                        <span>{badge_sym}</span>
                        <span style="{font_style}">{grade_name}</span>
                        <span style="color: var(--text-muted, #A3B0C2); font-size: 11px; margin-left: 4px;">({len(grade_rems)})</span>
                    </div>
                    """
                )

                # Interactive chips opening Materia Medica dialog
                num_chips = min(max(len(grade_rems), 1), 6)
                chip_cols = st.columns(num_chips)
                for idx, rem in enumerate(grade_rems[:24]):
                    with chip_cols[idx % num_chips]:
                        abbr = rem.get("abbreviation") or rem.get("name") or "rem"
                        full = rem.get("full_name") or abbr
                        rem_id = rem.get("id") or rem.get("remedy_id")
                        if st.button(
                            abbr,
                            key=f"chip_rem_{r_id}_{rem_id}_{grade}_{idx}",
                            help=f"{full} ({abbr}) · Grade {grade} · Click for Materia Medica",
                            width="stretch",
                        ):
                            show_remedy_dialog(rem_id or abbr, db)

                if len(grade_rems) > 24:
                    with st.expander(f"+ Show {len(grade_rems) - 24} more Grade {grade} remedies", expanded=False):
                        more_cols = st.columns(6)
                        for idx, rem in enumerate(grade_rems[24:], start=24):
                            with more_cols[idx % 6]:
                                abbr = rem.get("abbreviation") or rem.get("name") or "rem"
                                full = rem.get("full_name") or abbr
                                rem_id = rem.get("id") or rem.get("remedy_id")
                                if st.button(
                                    abbr,
                                    key=f"chip_more_{r_id}_{rem_id}_{grade}_{idx}",
                                    help=f"{full} ({abbr}) · Grade {grade} · Click for Materia Medica",
                                    width="stretch",
                                ):
                                    show_remedy_dialog(rem_id or abbr, db)

    return checked

