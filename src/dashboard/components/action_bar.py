"""Sticky consultation action bar component (Phase 2 & UI Overhaul).

Provides consistent bottom navigation on every consultation step:
Back · Save draft · Continue to <Next Step>
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional
import streamlit as st

from src.dashboard.components.icons import get_icon
from src.dashboard.utils import esc
from src.dashboard.components.busy import busy_slot
from src.data.case_store import save_case
from src.models.case import ClinicalCase


def render_step_action_bar(
    case: ClinicalCase,
    current_step: int,
    next_ready: bool = True,
    next_step_num: Optional[int] = None,
    next_label: str = "Review",
    prev_step_num: Optional[int] = None,
    prev_label: str = "Intake",
    disabled_reason: str = "Complete required symptoms to continue",
) -> None:
    """Render sticky bottom navigation bar with Back, Save draft, and Continue actions."""
    st.markdown("<div style='height: 48px;'></div>", unsafe_allow_html=True)

    with st.container(key="sticky_action_bar"):
        col_back, col_save, col_next = st.columns([2, 2.5, 4], vertical_alignment="center")

        # 1. Back Action
        with col_back:
            if prev_step_num is not None:
                if st.button(
                    f"← Back to {prev_label}",
                    type="secondary",
                    key=f"act_bar_prev_{current_step}",
                    width="stretch",
                ):
                    st.session_state.workspace_step = prev_step_num
                    st.rerun()

        # 2. Save Draft Action
        with col_save:
            saved_time = st.session_state.get(f"last_saved_time_{case.case_id}")
            save_help = f"Last saved at {saved_time}" if saved_time else "Save draft to local SQLite"
            slot_save = st.empty()
            if slot_save.button(
                "Save draft",
                type="secondary",
                key=f"act_bar_save_{current_step}",
                width="stretch",
                help=save_help,
            ):
                with busy_slot(slot_save, "Saving...", key=f"act_bar_save_{current_step}", type="secondary"):
                    save_case(case)
                    now_str = datetime.now().strftime("%H:%M")
                    st.session_state[f"last_saved_time_{case.case_id}"] = now_str
                    st.session_state[f"act_bar_saved_flash_{current_step}"] = True
                    st.toast(f"Draft saved at {now_str}")
                    st.rerun()
            if st.session_state.pop(f"act_bar_saved_flash_{current_step}", False):
                st.caption("✓ Saved")

        # 3. Continue to Next Step Action
        with col_next:
            if next_step_num is not None:
                btn_help = "" if next_ready else disabled_reason
                if st.button(
                    f"Continue to {next_label} →",
                    type="primary",
                    disabled=not next_ready,
                    key=f"act_bar_next_{current_step}",
                    width="stretch",
                    help=btn_help,
                ):
                    save_case(case)
                    st.session_state.workspace_step = next_step_num
                    st.rerun()

