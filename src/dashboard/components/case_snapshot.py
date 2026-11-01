"""Sticky Case Snapshot rail component (Phase 4 & UI Overhaul).

Replaces the redundant Totality Strip, Active Case Summary, and What to Include lists.
Renders the 7 canonical dimensions in prioritized order, row states (empty, captured,
low-confidence, edited), readiness indicators, and step continuation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional
import streamlit as st

from src.dashboard.components.busy import busy_slot
from src.dashboard.components.icons import get_icon
from src.dashboard.constants import (
    CANONICAL_DIMENSIONS_ORDERED,
    SCOPE_MIND,
    get_canonical_dimensions,
)
from src.dashboard.utils import esc
from src.data.case_store import save_case
from src.models.case import ClinicalCase

if TYPE_CHECKING:
    from src.chatbot.dialogue_manager import DialogueManager


def render_case_snapshot(
    case: ClinicalCase,
    dm: Optional[DialogueManager] = None,
    scope: str = SCOPE_MIND,
) -> None:
    """Render the sticky Case Snapshot rail in the right 30% column."""
    active_scope = st.session_state.get("scope", scope)
    canonical_dims = get_canonical_dimensions(active_scope)

    extraction_meta: Dict[str, Any] = getattr(case, "extraction_meta", {}) or {}
    edited_dims: List[str] = extraction_meta.get("edited", [])
    confidence_map: Dict[str, float] = extraction_meta.get("confidence", {})
    provenance_map: Dict[str, List[str]] = extraction_meta.get("provenance", {})

    # Compute filled count
    filled_count = 0
    mental_captured = False

    for dim in canonical_dims:
        c_items = case.dimensions.get(dim.internal_key, [])
        if not c_items and dm:
            c_items = dm.extracted_slots.get(dim.internal_key, [])
        if c_items:
            filled_count += 1
            if dim.internal_key == "mental":
                mental_captured = True

    st.html(
        f"""
        <div class="case-snapshot-header">
            <div style="display: flex; align-items: center; gap: 8px;">
                {get_icon('track_changes', size=16, color='var(--accent, #10B981)')}
                <span style="font-size: 14px; font-weight: 700; color: var(--text, #E8EDF3);">Case Snapshot</span>
            </div>
            <span class="step-counter-badge" style="font-size: 11px;">{filled_count}/7 Captured</span>
        </div>
        """
    )

    # 7 Canonical rows
    for dim in canonical_dims:
        items = case.dimensions.get(dim.internal_key, [])
        if not items and dm:
            items = dm.extracted_slots.get(dim.internal_key, [])

        if items:
            val_text = ", ".join(items)
            is_edited = dim.internal_key in edited_dims
            conf = confidence_map.get(dim.internal_key, 1.0)
            is_low_conf = conf < 0.65

            if is_edited:
                state_badge = "<span class='snap-state-tag edited'>Edited</span>"
                row_cls = "state-edited"
            elif is_low_conf:
                state_badge = "<span class='snap-state-tag low-conf'>Review</span>"
                row_cls = "state-low-confidence"
            else:
                state_badge = "<span class='snap-state-tag captured'>Captured</span>"
                row_cls = "state-captured"

            col_row, col_act = st.columns([5, 1], vertical_alignment="center")
            with col_row:
                st.html(
                    f"""
                    <div class="snapshot-row {row_cls}">
                        <div class="snapshot-row-header">
                            <span class="snapshot-dim-label">{esc(dim.label)}</span>
                            {state_badge}
                        </div>
                        <div class="snapshot-dim-val" title="{esc(val_text)}">{esc(val_text)}</div>
                    </div>
                    """
                )
            with col_act:
                with st.popover("✎"):
                    st.markdown(f"##### {dim.label}")
                    prov_list = provenance_map.get(dim.internal_key, [])
                    if prov_list:
                        st.caption(f"**Source Text:** \"{esc(prov_list[0])}\"")
                    if dim.internal_key in confidence_map:
                        st.caption(f"**Extraction Confidence:** {int(conf * 100)}%")

                    edit_val = st.text_input(
                        "Edit captured symptoms (comma separated):",
                        value=val_text,
                        key=f"snap_edit_input_{dim.key}",
                    )
                    slot_edit = st.empty()
                    if slot_edit.button("Save Edit", key=f"snap_save_btn_{dim.key}", type="primary", width="stretch"):
                        with busy_slot(slot_edit, "Saving...", key=f"snap_save_btn_{dim.key}", type="primary"):
                            new_items = [s.strip() for s in edit_val.split(",") if s.strip()]
                            case.dimensions[dim.internal_key] = new_items
                            if dm:
                                dm.extracted_slots[dim.internal_key] = new_items
                            if "edited" not in extraction_meta:
                                extraction_meta["edited"] = []
                            if dim.internal_key not in extraction_meta["edited"]:
                                extraction_meta["edited"].append(dim.internal_key)
                            case.extraction_meta = extraction_meta
                            save_case(case)
                            st.session_state[f"snap_saved_flash_{dim.key}"] = True
                            st.toast(f"Updated {dim.label}.")
                            st.rerun()
                    if st.session_state.pop(f"snap_saved_flash_{dim.key}", False):
                        st.caption("✓ Saved")

        else:
            st.html(
                f"""
                <div class="snapshot-row state-empty">
                    <div class="snapshot-row-header">
                        <span class="snapshot-dim-label" style="color: var(--text-muted, #A3B0C2);">{esc(dim.label)}</span>
                        <span class="snapshot-dim-hint">{esc(dim.hint)}</span>
                    </div>
                    <div class="snapshot-dim-empty">Not yet recorded</div>
                </div>
                """
            )

    # Readiness & Continuation Area
    missing_rec = [
        d.label for d in canonical_dims
        if d.is_recommended and not (
            case.dimensions.get(d.internal_key) or (dm and dm.extracted_slots.get(d.internal_key))
        )
    ]
    missing_str = f"Missing: {', '.join(missing_rec)}" if missing_rec else "All recommended captured"

    st.html(
        f"""
        <div class="snapshot-readiness-line">
            <b>Ready:</b> {filled_count}/7 &bull; {esc(missing_str)}
        </div>
        """
    )

    # Soft warnings
    if filled_count >= 1 and filled_count < 3:
        st.html(
            """
            <div class="snapshot-soft-warning">
                Tip: Capturing at least 3 dimensions improves repertory ranking precision.
            </div>
            """
        )

    if "MIND" in active_scope and not mental_captured and filled_count >= 1:
        st.html(
            """
            <div class="snapshot-soft-warning">
                MIND Chapter Focus is active, but Mental/Emotional symptoms are not yet captured.
            </div>
            """
        )

    # Primary Continue Button
    is_ready = filled_count >= 1
    if st.button(
        "Continue to Review →",
        type="primary",
        disabled=not is_ready,
        key="snapshot_continue_step2_btn",
        width="stretch",
        help="Proceed to Step 2 to review and confirm symptom totality" if is_ready else "Capture at least 1 symptom dimension to proceed",
    ):
        st.session_state.workspace_step = 2
        st.rerun()

    # Overflow Actions Popover at bottom of rail
    st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)
    with st.popover("••• Case Actions", width="stretch", help="Export or reset case"):
        st.markdown("##### Consultation Actions")
        if dm:
            from src.dashboard.components.chat_header import format_chat_transcript_md
            transcript_text = format_chat_transcript_md(dm)
            st.download_button(
                "Export Transcript (.md)",
                data=transcript_text,
                file_name=f"{case.case_id}_transcript.md",
                mime="text/markdown",
                width="stretch",
                key="snapshot_export_md_btn",
            )
        st.markdown("---")
        st.markdown(
            f"<div style='font-size: 11px; color: var(--text-faint, #8A98AE); margin-bottom: 6px;'>"
            f"Active: <b>{esc(case.case_id)}</b> &bull; {filled_count} dimensions"
            f"</div>",
            unsafe_allow_html=True,
        )
        if st.button("Load Demo Case", type="secondary", width="stretch", key="snapshot_load_demo_btn", help="Load demonstration clinical case"):
            from src.dashboard.components.demo_case import create_demo_case
            demo_case = create_demo_case()
            st.session_state.current_case = demo_case
            save_case(demo_case)
            if dm:
                dm.reset()
                dm.resume_from_case(demo_case)
            st.toast("Loaded demonstration clinical case.")
            st.rerun()

        if st.button("Start Over (Reset Case)", type="secondary", width="stretch", key="snapshot_reset_case_btn"):
            if dm:
                dm.reset()
                dm.get_greeting()
            case.dimensions = {k: [] for k in case.dimensions}
            case.transcript = ""
            case.clinical_summary = ""
            case.report_data = None
            save_case(case)
            st.toast("Consultation reset.")
            st.rerun()
