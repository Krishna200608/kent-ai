"""Unit tests for Streamlit Clinical Dashboard (Phase 7)."""

from __future__ import annotations

import pytest
from src.data.kent_db import KentDB
from src.pipeline.orchestrator import PatientReport
from src.dashboard.components.chat_viewer import render_slot_badges
from src.dashboard.components.rubric_tree import render_rubric_card


def test_kent_db_get_remedy_rubrics():
    """Verify KentDB.get_remedy_rubrics returns keynotes with correct schema."""
    db = KentDB()
    # Remedy 1 (Aconitum napellus / Acon.)
    keynotes = db.get_remedy_rubrics(remedy_id=1, min_grade=3, limit=5)
    assert isinstance(keynotes, list)
    assert len(keynotes) > 0
    first = keynotes[0]
    assert "rubric_id" in first
    assert "path" in first
    assert "grade" in first
    assert first["grade"] == 3


def test_render_slot_badges_empty_and_filled(monkeypatch):
    """Test slot badges rendering safely under empty and filled dictionary states."""
    rendered_markdown = []

    # Mock st.markdown
    import streamlit as st
    monkeypatch.setattr(st, "markdown", lambda text, **kw: rendered_markdown.append(text))

    # Empty slots
    render_slot_badges({})
    assert len(rendered_markdown) == 1
    assert "Listening for symptoms" in rendered_markdown[0]

    # Filled slots
    rendered_markdown.clear()
    sample_slots = {
        "location": ["head"],
        "sensation": ["throbbing"],
        "modality_agg": ["sun"],
        "modality_amel": ["cold"],
        "temporal": ["morning"],
        "mental": ["anxious"],
    }
    render_slot_badges(sample_slots)
    assert len(rendered_markdown) == 1
    assert "badge-loc" in rendered_markdown[0]
    assert "badge-sen" in rendered_markdown[0]
    assert "badge-agg" in rendered_markdown[0]


def test_patient_report_markdown_and_json_exports():
    """Ensure PatientReport exports clean markdown and JSON for dashboard download."""
    report = PatientReport(
        patient_id="TEST_CLINICAL_01",
        transcript="Severe throbbing headache worse from sun",
        dimensions={"location": ["head"], "sensation": ["throbbing"]},
        matched_rubrics=[
            {"rubric_id": 2797, "path": "HEAD > PAIN > sun, from", "similarity": 0.91}
        ],
        ranked_remedies=[
            {
                "remedy_id": 1,
                "abbreviation": "Bell.",
                "full_name": "Belladonna",
                "score": 3.0,
                "rubric_count": 1,
                "coverage_ratio": 1.0,
            }
        ],
    )

    md = report.to_markdown()
    assert "TEST_CLINICAL_01" in md
    assert "Belladonna" in md

    js = report.to_json()
    assert "TEST_CLINICAL_01" in js
    assert "Bell." in js
