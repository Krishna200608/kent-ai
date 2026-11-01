"""Docked action bar under chat input for review transition and terminal state buttons (Phase 14)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
import streamlit as st

from src.chatbot.state_machine import IntakeState
from src.dashboard.dimensions import KENT_DIMENSIONS_ORDERED
from src.dashboard.utils import esc, safe_rerun_fragment
from src.data.case_store import save_case

if TYPE_CHECKING:
    from src.chatbot.dialogue_manager import DialogueManager
    from src.models.case import ClinicalCase

logger = logging.getLogger("chat_actions")


def render_chat_action_bar(
    dm: DialogueManager,
    active_case: ClinicalCase | None,
) -> None:
    """Render single docked action bar under chat input."""
    current_state = dm.state_machine.current_state

    # 1. Terminal DONE state: render typed buttons from dm.get_action_options()
    if current_state == IntakeState.DONE:
        actions = dm.get_action_options()
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        cols = st.columns(len(actions))
        for idx, act in enumerate(actions):
            act_id = act.get("id")
            act_label = act.get("label", "")
            act_type = "primary" if act.get("type") == "primary" else "secondary"

            with cols[idx]:
                if st.button(act_label, type=act_type, width="stretch", key=f"btn_done_act_{act_id}"):
                    if act_id == "continue_review":
                        _proceed_to_review(dm, active_case)
                    elif act_id == "add_detail":
                        dm.state_machine.current_state = IntakeState.CLARIFICATION
                        dm.process_turn("I would like to add another detail.")
                        if active_case:
                            dm.sync_to_case(active_case)
                            save_case(active_case)
                        safe_rerun_fragment()
                    elif act_id == "start_new":
                        dm.reset()
                        dm.get_greeting()
                        if active_case:
                            active_case.dimensions = {k: [] for k in active_case.dimensions}
                            active_case.dialogue_history = []
                            active_case.extraction_meta = {"intake_mode": dm.intake_mode}
                            dm.sync_to_case(active_case)
                            save_case(active_case)
                        st.toast("Started new consultation.")
                        safe_rerun_fragment()
        return

    # 2. Ongoing intake: docked summary bar + Continue to Review button
    filled_count = sum(
        1 for dim in KENT_DIMENSIONS_ORDERED
        if (dim.key in dm.state_machine.filled_slots)
        or bool(dm.extracted_slots.get(dim.key))
        or (active_case is not None and bool(active_case.dimensions.get(dim.key)))
    )
    missing = [
        dim.label for dim in KENT_DIMENSIONS_ORDERED
        if not dm.extracted_slots.get(dim.key)
        and not (active_case is not None and active_case.dimensions.get(dim.key))
    ]

    col_info, col_btn = st.columns([3, 1.2], vertical_alignment="center")

    with col_info:
        if missing:
            missing_str = ", ".join(missing[:3])
            if len(missing) > 3:
                missing_str += f" (+{len(missing) - 3} more)"
            st.markdown(
                f"<div style='font-size: 13px; color: #9CA3AF;'>"
                f"<b style='color: #10B981;'>{filled_count} of 7</b> captured. "
                f"Not yet: <span style='color: #D1D5DB;'>{esc(missing_str)}</span>."
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='font-size: 13px; color: #10B981; font-weight: 600;'>"
                "All 7 symptom totality dimensions captured."
                "</div>",
                unsafe_allow_html=True,
            )

    with col_btn:
        can_proceed = filled_count >= 1
        if can_proceed:
            if st.button("Continue to Review →", type="primary", width="stretch", key="btn_chat_continue_to_review"):
                _proceed_to_review(dm, active_case)
        else:
            st.button(
                "Continue to Review →",
                type="primary",
                disabled=True,
                width="stretch",
                key="btn_chat_continue_to_review_disabled",
                help="Capture at least 1 symptom dimension to unlock Review.",
            )


def _proceed_to_review(dm: DialogueManager, active_case: ClinicalCase | None) -> None:
    """Synchronize case, generate summary if ready, and transition to Step 2."""
    if active_case:
        dm.sync_to_case(active_case)
        if not getattr(active_case, "clinical_summary", "") and active_case.is_ready_for_repertorization:
            try:
                from src.pipeline.case_summarizer import CaseSummarizer
                active_case.clinical_summary = CaseSummarizer().generate_summary(active_case)
            except Exception as e:
                logger.info("Auto-summary on review transition: %s", e)
        save_case(active_case)
    st.session_state.workspace_step = 2
    st.rerun(scope="app")

