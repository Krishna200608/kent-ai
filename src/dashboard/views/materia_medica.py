"""Tab 4: Materia Medica & Differential Comparison view (Phase 8 & UI Overhaul).

Provides:
- Searchable Materia Medica index of cataloged remedies with Latin nomenclature.
- Characteristic Grade 3 keynote rubrics formatted in --font-rubric.
- One-click access to Materia Medica modal dialog (show_remedy_dialog).
- Differential remedy side-by-side comparison.
"""

from __future__ import annotations

import streamlit as st

from src.dashboard.components.case_dialogs import show_remedy_dialog
from src.dashboard.components.icons import get_icon
from src.dashboard.components.remedy_comparison import render_remedy_comparison
from src.dashboard.constants import format_rubric_path
from src.dashboard.dimensions import pluralize
from src.dashboard.utils import esc
from src.data.kent_db import KentDB


def render_materia_medica_view(db: KentDB) -> None:
    """Render Tab 4: Materia Medica Index & Differential Remedy Comparison."""
    tab_mm_browse, tab_mm_diff = st.tabs(["Materia Medica Index", "Differential Remedy Comparison"])

    with tab_mm_browse:
        with st.container(border=True):
            st.html(
                f"""
                <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px;'>
                    {get_icon('medication', size=22, color='var(--accent, #10B981)')}
                    <h3 style='margin: 0; color: var(--text, #E8EDF3);'>Homeopathic Remedy Dictionary & MIND Keynotes</h3>
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
                    key="rem_filter_text",
                    placeholder="e.g. 'Lach', 'Phos', 'Nux-v', 'Ars', 'Acon'...",
                )
            with col_rem_clear:
                if st.button("Clear", help="Clear remedy search filter", width="stretch"):
                    st.session_state.rem_filter_text = ""
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
                    disp_name = name or abbr
                    card_title = f"{disp_name} ({abbr})  ·  {pluralize(mind_count, 'rubric', 'rubrics')} in MIND  ·  {pluralize(total_count, 'rubric', 'rubrics')} total"

                    with st.expander(card_title, expanded=False):
                        col_reminfo, col_remact = st.columns([4, 2], vertical_alignment="center")
                        with col_reminfo:
                            st.html(
                                f"""
                                <div style="margin-bottom: 8px;">
                                    <div style="font-size: 18px; font-weight: 800; color: var(--text, #E8EDF3);">
                                        {esc(disp_name)} <span style="color: var(--accent, #10B981); font-weight: 700;">({esc(abbr)})</span>
                                    </div>
                                    <div style="font-size: 12.5px; color: var(--text-muted, #A3B0C2); margin-top: 4px;">
                                        <span class="status-pill" style="color: var(--accent, #10B981); font-weight: 600;"><b>{mind_count}</b> in MIND</span>
                                        <span class="status-pill" style="margin-left: 6px;"><b>{total_count:,}</b> across all chapters</span>
                                    </div>
                                </div>
                                """
                            )
                        with col_remact:
                            c_dlg_btn, c_tray_btn = st.columns(2)
                            with c_dlg_btn:
                                if st.button("Inspect Details", key=f"btn_mm_insp_{r_id}", width="stretch", help="Open Materia Medica dialog"):
                                    show_remedy_dialog(r_id, db)
                            with c_tray_btn:
                                tray = st.session_state.get("case_tray", {"rubrics": [], "remedies": []})
                                is_in_tray = any(item.get("id") == r_id for item in tray.get("remedies", []))
                                rem_btn_key = f"tray_add_rem_{r_id}"
                                if is_in_tray:
                                    st.button("✓ Added", key=rem_btn_key, disabled=True, width="stretch")
                                else:
                                    if st.button("+ Add to tray", key=rem_btn_key, width="stretch", type="primary"):
                                        tray["remedies"].append({
                                            "id": r_id,
                                            "abbreviation": abbr,
                                            "full_name": name or abbr,
                                            "mind_rubrics": mind_count,
                                            "total_rubrics": total_count,
                                        })
                                        st.toast(f"Added {abbr} to case tray.")
                                        st.rerun()

                        keynotes = db.get_remedy_rubrics(r_id, min_grade=3, limit=14, prioritize_mind=prioritize_mind, rank_by_specificity=True)
                        if not keynotes:
                            st.write("No Grade 3 keynote rubrics cataloged for this remedy.")
                        else:
                            st.markdown(f"**Characteristic Grade 3 Keynotes ({pluralize(len(keynotes), 'keynote', 'keynotes')}):**")
                            for kn in keynotes:
                                is_mind_kn = kn.get("section_name") == "MIND" or str(kn["path"]).startswith("MIND")
                                mind_badge = f"<span class='badge badge-mind' style='margin-left: 6px;'>{get_icon('psychology', size=11, color='var(--accent, #10B981)')} MIND</span>" if is_mind_kn else ""
                                disp_kn_path = format_rubric_path(kn["path"])
                                r_count = kn.get("remedy_count", 0)
                                st.html(
                                    f"<div style='margin-bottom: 5px; display: flex; align-items: center; flex-wrap: wrap; gap: 6px; font-family: var(--font-rubric, Georgia, serif);'>"
                                    f"<span class='badge-g3' style='font-family: var(--font-ui, sans-serif); font-size: 11px;'>③ Bold</span> "
                                    f"<span style='font-size:13.5px; color:var(--text, #E8EDF3);'>{esc(disp_kn_path)}</span> "
                                    f"<span style='font-size:11px; color:var(--text-muted, #A3B0C2); font-family: var(--font-ui, sans-serif);'>({r_count} remedies)</span>"
                                    f"{mind_badge}"
                                    f"</div>"
                                )
            else:
                st.info(f"No remedies found matching '{rem_search}'.")

    with tab_mm_diff:
        render_remedy_comparison(db)
