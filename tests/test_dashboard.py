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

    # Mock st.markdown and st.html
    import streamlit as st
    monkeypatch.setattr(st, "markdown", lambda text, **kw: rendered_markdown.append(text))
    if hasattr(st, "html"):
        monkeypatch.setattr(st, "html", lambda text, **kw: rendered_markdown.append(text))

    # Empty slots - 7-segment HUD renders unfilled segments
    render_slot_badges({})
    assert len(rendered_markdown) == 1
    assert "hud-segments-grid" in rendered_markdown[0]
    assert "hud-segment-unfilled" in rendered_markdown[0]
    assert "LOC" in rendered_markdown[0]
    assert "MENT" in rendered_markdown[0]

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


def test_render_rubric_card_mind_badge(monkeypatch):
    """Verify that render_rubric_card displays an explicit MIND chapter badge for MIND rubrics."""
    import streamlit as st
    html_rendered = []
    monkeypatch.setattr(st, "html", lambda text, **kw: html_rendered.append(text))
    # Mock expander
    class DummyExpander:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    monkeypatch.setattr(st, "expander", lambda *args, **kw: DummyExpander())

    db = KentDB()
    # MIND rubric
    mind_rubric = {
        "rubric_id": 1,
        "path": "MIND > ABANDONED > feels he is",
        "similarity": 0.95,
        "remedy_count": 14,
        "section_id": 1,
    }
    render_rubric_card(mind_rubric, db)
    assert len(html_rendered) >= 1
    assert "MIND CHAPTER" in html_rendered[0]

    # Non-MIND rubric
    html_rendered.clear()
    head_rubric = {
        "rubric_id": 2797,
        "path": "HEAD > PAIN > sun, from",
        "similarity": 0.88,
        "remedy_count": 25,
        "section_id": 3,
    }
    render_rubric_card(head_rubric, db)
    assert len(html_rendered) >= 1
    assert "MIND CHAPTER" not in html_rendered[0]


def test_render_rubric_card_safe_id_handling(monkeypatch):
    """Verify render_rubric_card handles None, string prefix, and invalid IDs without crashing."""
    import streamlit as st
    html_rendered = []
    writes = []
    monkeypatch.setattr(st, "html", lambda text, **kw: html_rendered.append(text))
    monkeypatch.setattr(st, "write", lambda text, **kw: writes.append(text))
    monkeypatch.setattr(st, "markdown", lambda text, **kw: None)

    class DummyColumns:
        def __enter__(self): return self
        def __exit__(self, *args): pass

    monkeypatch.setattr(st, "columns", lambda n: [DummyColumns() for _ in range(n)])

    class DummyExpander:
        def __enter__(self): return self
        def __exit__(self, *args): pass

    monkeypatch.setattr(st, "expander", lambda *args, **kw: DummyExpander())

    db = KentDB()

    # Case 1: Missing ID / None
    render_rubric_card({"path": "MIND > ANXIETY"}, db)
    assert any("No remedies cataloged" in w for w in writes)

    # Case 2: String formatted ID with prefix
    writes.clear()
    render_rubric_card({"id": "rubric_4", "path": "MIND > ANXIETY"}, db)
    # Rubric #4 has remedies in Kent DB
    assert len(html_rendered) > 0

    # Case 3: Completely invalid ID
    writes.clear()
    render_rubric_card({"id": "corrupted_id", "path": "MIND > UNKNOWN"}, db)
    assert any("No remedies cataloged" in w for w in writes)


