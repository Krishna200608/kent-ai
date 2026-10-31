"""Smoke tests for Streamlit Clinical Decision Support Dashboard (AppTest).

Tests end-to-end clinician workflows across all 4 consultation steps,
case persistence, chat interactions, and navigation.
"""

from __future__ import annotations

import os
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

# Force mock mode at module load time so Streamlit @st.cache_resource uses mock pipeline
os.environ["KENT_MOCK_PIPELINE"] = "1"

from src.models.case import ClinicalCase
from src.data.case_store import get_case, init_case_db, save_case

_APP_PATH = str(Path(__file__).resolve().parent.parent / "src" / "dashboard" / "app.py")


@pytest.fixture(autouse=True)
def mock_app_env(monkeypatch):
    """Ensure fast, deterministic mock execution for all AppTest smoke runs."""
    monkeypatch.setenv("KENT_MOCK_PIPELINE", "1")


def test_smoke_intake_initial_render():
    """Verify fresh consultation renders Step 1 (Intake) with steps 3 and 4 disabled."""
    at = AppTest.from_file(_APP_PATH, default_timeout=30)
    at.run()

    assert not at.exception
    assert "current_case" in at.session_state
    assert at.session_state["workspace_step"] == 1

    case: ClinicalCase = at.session_state["current_case"]
    assert case is not None
    assert case.is_blank

    # Verify stepper buttons: Steps 3 and 4 must be disabled on a fresh case
    step3_btn = next((b for b in at.button if "3." in b.label or "Analysis" in b.label), None)
    step4_btn = next((b for b in at.button if "4." in b.label or "Report" in b.label), None)
    assert step3_btn is not None
    assert step3_btn.disabled is True
    assert step4_btn is not None
    assert step4_btn.disabled is True

    # Verify chat input is mounted
    assert len(at.chat_input) >= 1


def test_smoke_chat_interaction_and_case_sync():
    """Verify sending a clinical symptom in chat updates symptoms and persists draft."""
    at = AppTest.from_file(_APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception

    # Submit patient complaint via chat input
    at.chat_input[0].set_value("Severe throbbing headache in forehead, worse from heat").run()
    assert not at.exception

    dm = at.session_state["dialogue_manager"]
    assert len(dm.history) >= 2  # user + assistant

    case: ClinicalCase = at.session_state["current_case"]
    assert not case.is_blank
    assert case.filled_dimensions_count >= 1

    # Verify draft was persisted in SQLite
    saved_case = get_case(case.case_id)
    assert saved_case is not None


def test_smoke_step_2_review_navigation():
    """Verify switching to Step 2 (Review) renders symptom review and totality matrix."""
    at = AppTest.from_file(_APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception

    # Navigate to Step 2
    step2_btn = next((b for b in at.button if "2." in b.label or "Review" in b.label), None)
    assert step2_btn is not None
    assert step2_btn.disabled is False

    step2_btn.click().run()
    assert not at.exception
    assert at.session_state["workspace_step"] == 2


def test_smoke_step_3_analysis_and_step_4_report():
    """Verify Step 3 (Analysis) matrix and Step 4 (Report) render with populated case."""
    at = AppTest.from_file(_APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception

    # Populate case with symptoms
    case: ClinicalCase = at.session_state["current_case"]
    case.add_symptom("location", "head and forehead")
    case.add_symptom("sensation", "throbbing, pounding")
    case.add_symptom("mental", "severe anxiety with fear of death")
    case.add_symptom("modality_agg", "warmth, movement")

    # Run repertorization using cached mock pipeline
    pipeline = at.session_state["pipeline"]
    report = pipeline.repertorize_case(case)
    at.session_state["current_report"] = report

    # Step 3: Analysis
    at.session_state["workspace_step"] = 3
    at.run()
    assert not at.exception

    # Step 4: Report View
    at.session_state["workspace_step"] = 4
    at.run()
    assert not at.exception


def test_smoke_intake_mode_toggle():
    """Verify switching between Patient and Practitioner intake modes."""
    at = AppTest.from_file(_APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception

    dm = at.session_state["dialogue_manager"]
    assert dm.intake_mode == "patient"

    # Set to Practitioner
    ctrl = at.segmented_control(key="intake_style_control")
    if ctrl:
        ctrl.set_value("Practitioner").run()
        assert not at.exception
        assert dm.intake_mode == "practitioner"
