"""Unit tests for Kent-AI UI/UX Overhaul: tokens, constants, totality ring, and path formatting."""

from __future__ import annotations

import re
import pytest

from src.dashboard.constants import (
    APP_VERSION,
    CANONICAL_DIMENSIONS_ORDERED,
    GRADE_WEIGHTS,
    MODEL_DISPLAY_NAME,
    SCOPE_ALL_COUNT,
    SCOPE_MIND_COUNT,
    format_rubric_path,
    get_canonical_dimensions,
)
from src.dashboard.components.totality_ring import totality_ring
from src.models.case import ClinicalCase


def test_constants_definitions():
    """Verify core constants definitions and scope counts."""
    assert APP_VERSION == "2.0.0"
    assert MODEL_DISPLAY_NAME == "Llama 3 8B"
    assert SCOPE_MIND_COUNT == 4933
    assert SCOPE_ALL_COUNT == 74513
    assert GRADE_WEIGHTS[3] == 3.0
    assert GRADE_WEIGHTS[2] == 2.0
    assert GRADE_WEIGHTS[1] == 1.0


def test_canonical_dimensions_ordering():
    """Verify 7 canonical dimensions and MIND priority ordering."""
    assert len(CANONICAL_DIMENSIONS_ORDERED) == 7
    keys = [d.key for d in CANONICAL_DIMENSIONS_ORDERED]
    assert keys == ["mental", "location", "sensation", "worse", "better", "concomitant", "time"]

    # When scope is MIND, mental is ordered first
    mind_dims = get_canonical_dimensions("MIND focus")
    assert mind_dims[0].key == "mental"
    assert mind_dims[0].is_paramount is True

    # When scope is All chapters, physical sequence is used
    all_dims = get_canonical_dimensions("All chapters")
    assert all_dims[0].key == "location"


def test_format_rubric_path_breadcrumbs_and_time_dot():
    """Verify format_rubric_path replaces chevrons with ' › ' and repairs OCR trailing time dots."""
    # Empty
    assert format_rubric_path("") == ""

    # Standard path
    p1 = "HEAD > PAIN > forehead"
    assert format_rubric_path(p1) == "HEAD › PAIN › forehead"

    # Multi-level with OCR dropped dot on time abbreviation
    p2 = "MIND > ANGER, irascibility > forenoon > 11 a.m"
    assert format_rubric_path(p2) == "MIND › ANGER, irascibility › forenoon › 11 a.m."

    # Night time dropped dot
    p3 = "MIND > ANGUISH > night > 4 a.m"
    assert format_rubric_path(p3) == "MIND › ANGUISH › night › 4 a.m."

    # Already dotted time should NOT receive double dot
    p4 = "MIND > ANGUISH > night > 4 a.m."
    assert format_rubric_path(p4) == "MIND › ANGUISH › night › 4 a.m."

    # Afternoon p.m
    p5 = "STOMACH > PAIN > afternoon > 2 p.m"
    assert format_rubric_path(p5) == "STOMACH › PAIN › afternoon › 2 p.m."


def test_totality_ring_svg_rendering():
    """Verify totality ring generates valid accessible SVG glyphs."""
    # 0 dimensions lit
    svg0 = totality_ring(0, size=28)
    assert '<svg width="28" height="28"' in svg0
    assert 'aria-label="0 of 7 totality dimensions captured"' in svg0
    assert 'var(--line, #243243)' in svg0
    assert 'var(--accent, #10B981)' not in svg0

    # 4 dimensions lit by integer
    svg4 = totality_ring(4, size=28)
    assert 'aria-label="4 of 7 totality dimensions captured"' in svg4
    # Count lit segments
    assert svg4.count('stroke="var(--accent, #10B981)"') == 4
    assert svg4.count('stroke="var(--line, #243243)"') == 3

    # All 7 lit
    svg7 = totality_ring(7, size=32)
    assert 'aria-label="7 of 7 totality dimensions captured"' in svg7
    assert svg7.count('stroke="var(--accent, #10B981)"') == 7

    # From ClinicalCase object
    case = ClinicalCase(case_id="RING-001", patient_name="Test")
    case.add_symptom("mental", "fear of darkness")
    case.add_symptom("sensation", "burning")
    svg_case = totality_ring(case, size=36, show_count=True)
    assert 'aria-label="2 of 7 totality dimensions captured"' in svg_case
    assert svg_case.count('stroke="var(--accent, #10B981)"') == 2
    assert '>2</text>' in svg_case


def test_phase2_case_dialogs_defined():
    """Verify Patient Info and Disclaimer dialogs are defined and callable."""
    from src.dashboard.components.case_dialogs import show_patient_info_dialog, show_first_run_disclaimer_dialog
    assert callable(show_patient_info_dialog)
    assert callable(show_first_run_disclaimer_dialog)


def test_phase2_action_bar_component():
    """Verify sticky action bar component is defined and callable."""
    from src.dashboard.components.action_bar import render_step_action_bar
    assert callable(render_step_action_bar)


def test_phase3_sidebar_exports_and_components():
    """Verify Phase 3 sidebar components and exports are defined."""
    from src.dashboard.views.sidebar import (
        render_sidebar,
        render_sidebar_case_tray,
        render_sidebar_active_case_card,
        render_sidebar_scope_control,
        render_sidebar_engine_row,
        render_sidebar_footer,
    )
    assert callable(render_sidebar)
    assert callable(render_sidebar_case_tray)
    assert callable(render_sidebar_active_case_card)
    assert callable(render_sidebar_scope_control)
    assert callable(render_sidebar_engine_row)
    assert callable(render_sidebar_footer)


def test_phase3_tray_persistence_sync():
    """Verify _sync_tray_to_case updates case.selected_rubric_ids from session tray."""
    import streamlit as st
    from src.dashboard.views.sidebar import _sync_tray_to_case
    from src.models.case import ClinicalCase

    case = ClinicalCase(case_id="TEST-TRAY-01", patient_name="Jane Doe")
    assert case.selected_rubric_ids == []

    st.session_state["case_tray"] = {
        "rubrics": [
            {"rubric_id": 101, "path": "MIND > ANXIETY"},
            {"id": 202, "path": "HEAD > PAIN"},
        ],
        "remedies": [],
    }

    _sync_tray_to_case(case)
    assert case.selected_rubric_ids == [101, 202]


def test_phase3_get_ollama_latency(monkeypatch):
    """Verify get_ollama_latency returns (bool, int) and respects mock pipeline."""
    from src.dashboard.components.ollama_status import get_ollama_latency

    # Mock environment returns (False, 0)
    monkeypatch.setenv("KENT_MOCK_PIPELINE", "1")
    online, lat = get_ollama_latency()
    assert online is False
    assert lat == 0


def test_phase4_case_snapshot_component():
    """Verify Case Snapshot rail component is defined and callable."""
    from src.dashboard.components.case_snapshot import render_case_snapshot
    assert callable(render_case_snapshot)


def test_phase4_step_aware_neutral_suggestions():
    """Verify neutral step-aware suggestion config map and suppression in practitioner mode."""
    import streamlit as st
    from src.chatbot.dialogue_manager import DialogueManager
    from src.dashboard.components.chat_chips import (
        NEUTRAL_STEP_SUGGESTIONS,
        render_quick_reply_chips,
    )

    assert "GREETING" in NEUTRAL_STEP_SUGGESTIONS
    assert "LOCATION" in NEUTRAL_STEP_SUGGESTIONS
    assert "SENSATION" in NEUTRAL_STEP_SUGGESTIONS
    assert "MODALITY" in NEUTRAL_STEP_SUGGESTIONS
    assert "TEMPORAL" in NEUTRAL_STEP_SUGGESTIONS
    assert "MENTAL" in NEUTRAL_STEP_SUGGESTIONS

    greeting_suggs = NEUTRAL_STEP_SUGGESTIONS["GREETING"]
    assert "I'd like to describe how I feel" in greeting_suggs
    assert "I have a physical complaint" in greeting_suggs
    assert "It's mostly emotional" in greeting_suggs

    dm = DialogueManager()

    # When Speaking as = Practitioner, chips must be hidden
    dm.set_intake_mode("practitioner")
    chips = render_quick_reply_chips(dm)
    assert chips is None

    # When show_suggested_replies is False, chips must be hidden
    dm.set_intake_mode("patient")
    st.session_state["show_suggested_replies"] = False
    chips = render_quick_reply_chips(dm)
    assert chips is None


def test_phase5_case_library_exports_and_helpers():
    """Verify Case Library exports and relative time formatter."""
    from datetime import datetime, timedelta
    from src.dashboard.components.case_library import format_relative_time, render_case_library

    assert callable(render_case_library)

    now = datetime.now()
    t_just_now = now.isoformat()
    t_minutes_ago = (now - timedelta(minutes=10)).isoformat()
    t_hours_ago = (now - timedelta(hours=3)).isoformat()
    t_yesterday = (now - timedelta(days=1)).isoformat()
    t_days_ago = (now - timedelta(days=4)).isoformat()

    assert format_relative_time(t_just_now) == "just now"
    assert "m ago" in format_relative_time(t_minutes_ago)
    assert "h ago" in format_relative_time(t_hours_ago)
    assert format_relative_time(t_yesterday) == "yesterday"
    assert "4d ago" == format_relative_time(t_days_ago)



