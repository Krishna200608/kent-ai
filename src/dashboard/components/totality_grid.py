"""Classical Homeopathic Totality Grid Component (Phase 1 & 7).

Implements standard repertory software layout (Homeorep, RadarOpus, Kent's Repertorium):
- Rubrics as ROWS with hierarchical clinical breadcrumbs.
- Remedies as COLUMNS with Latin names on hover and rank indicators.
- Heat-mapped Kentian grades: Grade 3 (Bold), Grade 2 (Italics), Grade 1 (Plain).
- Reactive rubric controls: Mute (disable) and Eliminatory (mandatory rubric).
"""

from __future__ import annotations

import html
from typing import Any, Dict, List, Optional

import streamlit as st

from src.dashboard.components.icons import get_icon
from src.data.kent_db import KentDB
from src.models.case import ClinicalCase
from src.pipeline.orchestrator import PatientReport


def render_classical_totality_matrix(
    report: PatientReport,
    db: KentDB,
    case: Optional[ClinicalCase] = None,
    allow_toggles: bool = True,
) -> None:
    """Render authentic classical repertorization matrix (Rubrics as Rows, Remedies as Columns)."""
    remedies = report.ranked_remedies[:12]
    rubrics = report.matched_rubrics
    if not remedies or not rubrics:
        st.info("No rubrics or candidate remedies available to display in matrix.")
        return

    # Pre-fetch remedies for each rubric to obtain exact Kentian grades
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

    # Optional interactive mute / eliminate toggles
    if allow_toggles and case is not None:
        with st.expander("Filter & Weight Rubrics (Mute / Eliminatory)", expanded=False):
            st.markdown(
                "<div style='font-size: 12px; color: #9CA3AF; margin-bottom: 8px;'>"
                "<b>Mute:</b> Exclude symptom from scoring without deleting it. &nbsp;|&nbsp; "
                "<b>Eliminatory:</b> Require remedies to cover this specific rubric (classical eliminatory method)."
                "</div>",
                unsafe_allow_html=True,
            )
            c_header = st.columns([6, 2, 2])
            with c_header[0]:
                st.markdown("<span style='font-size:11.5px; font-weight:700; color:#9CA3AF;'>Rubric</span>", unsafe_allow_html=True)
            with c_header[1]:
                st.markdown("<span style='font-size:11.5px; font-weight:700; color:#9CA3AF;'>Status</span>", unsafe_allow_html=True)
            with c_header[2]:
                st.markdown("<span style='font-size:11.5px; font-weight:700; color:#9CA3AF;'>Eliminatory</span>", unsafe_allow_html=True)

            changed = False
            for r in rubrics:
                r_id = int(r.get("rubric_id") or r.get("id"))
                r_path = r.get("path", f"Rubric #{r_id}")
                is_muted = r_id in (case.muted_rubric_ids or [])
                is_elim = r_id in (case.eliminatory_rubric_ids or [])

                cols = st.columns([6, 2, 2])
                with cols[0]:
                    st.markdown(f"<div style='font-size:12px; color:#F3F4F6;'>{r_path}</div>", unsafe_allow_html=True)
                with cols[1]:
                    mute_state = st.checkbox("Mute", value=is_muted, key=f"mute_chk_{r_id}")
                    if mute_state != is_muted:
                        if mute_state:
                            case.muted_rubric_ids.append(r_id)
                        else:
                            case.muted_rubric_ids.remove(r_id)
                        changed = True
                with cols[2]:
                    elim_state = st.checkbox("Must Have", value=is_elim, key=f"elim_chk_{r_id}", disabled=is_muted)
                    if elim_state != is_elim:
                        if elim_state:
                            case.eliminatory_rubric_ids.append(r_id)
                        else:
                            case.eliminatory_rubric_ids.remove(r_id)
                        changed = True

            if changed:
                st.toast("Rubric filtering updated. Recomputing totality scores...")
                st.rerun()

    # Build Classical Totality Table
    # Sticky Table Header: Remedy Abbreviations as Columns
    th_cells = [
        '<th style="min-width: 280px; text-align: left; position: sticky; left: 0; background: #111827; z-index: 2;">Symptom Rubric</th>',
        '<th style="width: 70px; text-align: center;">Weight</th>',
    ]

    for rem in remedies:
        abbr = rem.get("abbreviation", "")
        name = rem.get("full_name", abbr)
        score = rem.get("score", 0.0)
        rank = rem.get("rank", 1)
        th_cells.append(
            f'<th style="min-width: 58px; text-align: center;" title="#{rank} {html.escape(name)}&#10;Score: {score:.2f}">'
            f'<div style="font-size: 13px; font-weight: 800; color: #10B981;">{abbr}</div>'
            f'<div style="font-size: 9.5px; color: #9CA3AF; font-weight: normal;">#{rank}</div>'
            f'</th>'
        )

    # Table Body: Rubrics as Rows
    tbody_rows = []
    muted_set = set(case.muted_rubric_ids if case else [])
    elim_set = set(case.eliminatory_rubric_ids if case else [])

    for idx, r in enumerate(rubrics, start=1):
        r_id = int(r.get("rubric_id") or r.get("id"))
        full_path = r.get("path") or f"Rubric #{r_id}"
        sim = r.get("similarity", 1.0)

        # Hierarchical Breadcrumbs
        parts = [p.strip() for p in full_path.split(">")]
        if len(parts) > 1:
            crumb_prefix = " &rsaquo; ".join(parts[:-1])
            crumb_leaf = parts[-1]
            breadcrumb_html = f'<div style="font-size: 10px; color: #9CA3AF;">{crumb_prefix}</div><div style="font-size: 12px; font-weight: 700; color: #F9FAFB;">{crumb_leaf}</div>'
        else:
            breadcrumb_html = f'<div style="font-size: 12px; font-weight: 700; color: #F9FAFB;">{full_path}</div>'

        # Badges
        status_badges = []
        if r_id in elim_set:
            status_badges.append('<span class="status-pill" style="color:#EF4444; border-color:#EF4444; font-size:9.5px;">ELIM</span>')
        if r_id in muted_set:
            status_badges.append('<span class="status-pill" style="color:#6B7280; font-size:9.5px;">MUTED</span>')
        badge_str = " ".join(status_badges)

        row_tds = [
            f'<td style="position: sticky; left: 0; background: #111827; z-index: 1;">'
            f'<div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">'
            f'<div>{breadcrumb_html}</div>'
            f'<div>{badge_str}</div>'
            f'</div>'
            f'</td>',
            f'<td style="text-align: center; font-size: 11px; color: #34D399;">{sim:.2f}</td>',
        ]

        # Remedy Grade Cells
        for rem in remedies:
            abbr_clean = (rem.get("abbreviation") or "").rstrip(".").lower()
            grade = rubric_remedy_map.get(r_id, {}).get(abbr_clean)

            if grade == 3:
                row_tds.append('<td style="text-align: center;"><span class="grade-3" title="Grade 3 (Characteristic Keynote)">3</span></td>')
            elif grade == 2:
                row_tds.append('<td style="text-align: center;"><span class="grade-2" title="Grade 2 (Well-Verified)">2</span></td>')
            elif grade == 1:
                row_tds.append('<td style="text-align: center;"><span class="grade-1" title="Grade 1 (Clinical)">1</span></td>')
            else:
                row_tds.append('<td style="text-align: center; color: #374151;">&middot;</td>')

        row_opacity = "opacity: 0.45;" if r_id in muted_set else ""
        tbody_rows.append(f'<tr style="{row_opacity}">{"".join(row_tds)}</tr>')

    # Summary Rows: Totality Score & Rubric Count
    score_tds = [
        '<td style="position: sticky; left: 0; background: #0F172A; font-weight: 700; color: #F9FAFB;">Total Weighted Score</td>',
        '<td></td>',
    ]
    count_tds = [
        '<td style="position: sticky; left: 0; background: #0F172A; font-weight: 700; color: #F9FAFB;">Rubric Coverage (Hits)</td>',
        '<td></td>',
    ]

    for rem in remedies:
        score_tds.append(f'<td style="text-align: center; font-weight: 800; color: #10B981; font-size: 13px;">{rem.get("score", 0):.2f}</td>')
        count_tds.append(f'<td style="text-align: center; font-weight: 700; color: #F3F4F6; font-size: 12px;">{rem.get("rubric_count", 0)}/{len(rubrics)}</td>')

    tfoot_html = f"""
    <tfoot>
        <tr style="background: #0F172A; border-top: 2px solid #374151;">{"".join(score_tds)}</tr>
        <tr style="background: #0F172A;">{"".join(count_tds)}</tr>
    </tfoot>
    """

    table_html = f"""
    <div style="overflow-x: auto; margin-top: 10px; margin-bottom: 12px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08);">
        <table class="repertory-grid" style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr>{"".join(th_cells)}</tr>
            </thead>
            <tbody>
                {"".join(tbody_rows)}
            </tbody>
            {tfoot_html}
        </table>
    </div>
    <div style="font-size: 12px; color: #9CA3AF; display: flex; justify-content: space-between; align-items: center; margin-top: 6px;">
        <div>
            <b>Grade Legend:</b> &nbsp;
            <span class="grade-3">3</span> Bold Keynote &nbsp;|&nbsp;
            <span class="grade-2">2</span> Italic Characteristic &nbsp;|&nbsp;
            <span class="grade-1">1</span> Plain Verified &nbsp;|&nbsp;
            <span style="color:#6B7280;">&middot;</span> Unlisted
        </div>
        <div style="font-style: italic;">Hover remedy abbreviations for full Latin names.</div>
    </div>
    """
    st.html(table_html)
